import hashlib
import json
import subprocess

from evals.grounding_stabilization.runner import (
    cases,
    checks,
    digest,
    identity,
    request_for,
)
from evals.provenance import ROOT

FOLDER = ROOT / "Documentation/grounding_stabilization"


def test_untreated_report_identity_schedule_actual_authorization_and_review():
    report = json.loads((FOLDER / "baseline.json").read_bytes())
    provenance = json.loads((FOLDER / "baseline_provenance.json").read_bytes())
    assert (
        hashlib.sha256((FOLDER / "baseline.json").read_bytes()).hexdigest()
        == provenance["report_sha256"]
    )
    assert report["identity"] == identity()
    assert not report["runtime"]["git_dirty"]
    assert report["runtime"]["git_commit"] == "4baae12cb14522a6706fe2d18d8c02d672a16ea8"
    assert provenance["journal_records_equal_report"] is True
    assert provenance["untreated_application_changes_from_sprint3"] == []
    review = json.loads((FOLDER / "baseline_manual_review.json").read_bytes())
    assert len(report["records"]) == len(review["reviews"]) == 8
    for case, row, item in zip(
        cases(), report["records"], review["reviews"], strict=True
    ):
        assert row["case_id"] == item["case_id"] == case["case_id"]
        assert row["request_sha256"] == digest(
            request_for(case).model_dump(mode="json")
        )
        assert item["record_sha256"] == digest(row)
        if row["result"] is not None:
            assert row["checks"] == checks(
                row["result"], row["retrieval"][0]["source_ids"], case
            )
            for quote in item["quotes"]:
                assert quote["value"] == row["result"][quote["field"]]
    prior = json.loads(
        subprocess.check_output(
            [
                "git",
                "show",
                "41250f9:Documentation/grounding_stabilization/baseline_manual_review.json",
            ],
            cwd=ROOT,
        )
    )
    assert review["reviews"][: len(prior["reviews"])] == prior["reviews"]
    assert review["judgment_revisions"] == []


def test_offline_query_controls_replay_without_changing_original_diagnostic():
    from app.reference_loader import (
        get_relevant_references,
        load_references,
        normalize_text,
        score_reference,
    )
    from app.retrieval.orchestration import lexical_search
    from app.soc_query import soc_retrieval_query
    from evals.microsoft_reliability.cases import load_cases
    from evals.microsoft_reliability.runner import request_for as prior_request

    requests = {
        case["case_id"]: request_for(case)
        for case in cases()
        if case["workflow"] == "soc_alert"
    }
    requests.update(
        {
            c["case_id"]: prior_request(c)
            for c in load_cases()
            if c["case_id"] in {"REL-SOC-002", "REL-SOC-006", "REL-SOC-010"}
        }
    )
    card = next(
        c
        for c in load_references("soc_alert")
        if c["source_id"] == "SOC-BRUTE-FORCE-SUCCESS"
    )
    report = json.loads((FOLDER / "query_controls.json").read_bytes())
    assert len(report["records"]) == len(requests) == 8
    for row in report["records"]:
        request = requests[row["case_id"]]
        assert row["request_sha256"] == digest(request.model_dump(mode="json"))
        variants = {
            "prior_full_request": request.model_dump_json(),
            "factual_tables": soc_retrieval_query(request),
        }
        for name, query in variants.items():
            expected = row["variants"][name]
            assert (
                expected["query_sha256"] == hashlib.sha256(query.encode()).hexdigest()
            )
            assert expected["authentication_card_keyword_score"] == score_reference(
                set(normalize_text(query)), card
            )
            assert expected["legacy_top5"] == [
                r["source_id"] for r in get_relevant_references("soc_alert", query, 5)
            ]
            assert expected["lexical_top5"] == [
                h.record.source_id for h in lexical_search("soc_alert", query, 5)
            ]
