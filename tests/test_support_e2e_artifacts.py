"""Replay fresh live artifacts and review quotations without model/network calls."""

import hashlib
import json
import statistics
import subprocess
from collections import Counter

from app.evidence_inspector import build_inspector, collect_evidence
from app.reference_loader import get_relevant_references
from app.retrieval.orchestration import retrieve_for_analysis
from app.schemas import GovernanceRiskResponse, SocAlertResponse
from app.soc_query import soc_retrieval_query
from evals.evidence_support_e2e.runner import cases, identity, request_for
from evals.provenance import ROOT

FOLDER = ROOT / "Documentation/evidence_support_e2e"
DIMENSIONS = (
    "unsupported_factual_claim",
    "unsupported_authority_claim",
    "positive_control_information_lost",
    "source_applicability",
    "benign_or_uncertain_false_positive",
)


def load(name):
    return json.loads((FOLDER / name).read_bytes())


def test_live_artifact_schedule_provenance_and_original_defect_are_preserved():
    report, manifest = load("results.json"), load("provenance.json")
    assert report["identity"] == identity()
    assert report["runtime"]["git_commit"] == manifest["launch_sha"]
    assert manifest["launch_sha"] == "379853ee6040039627823ac357d7120e8390cca9"
    assert report["runtime"]["git_dirty"] is False
    assert report["runtime"]["model"] == "qwen3:8b"
    assert report["runtime"]["temperature"] == 0.1
    assert report["runtime"]["seed"] is None
    assert manifest["journal_records_equal_report"] is True
    assert manifest["executing_app_dashboard_changes_during_run"] == []
    for name, expected in manifest["artifact_sha256"].items():
        assert hashlib.sha256((FOLDER / name).read_bytes()).hexdigest() == expected
    original = subprocess.check_output(
        ["git", "ls-tree", "-r", manifest["launch_sha"], "app", "dashboard"],
        cwd=ROOT,
        text=True,
    )
    assert {
        fields[3]: fields[2]
        for line in original.splitlines()
        if (fields := line.split(maxsplit=3))
    } == manifest["launch_source_git_blobs"]
    rows = report["records"]
    assert len(rows) == 8
    for case, row in zip(cases(), rows, strict=True):
        request = request_for(case)
        assert case["case_id"] == row["case_id"]
        assert (
            row["request_sha256"]
            == hashlib.sha256(request.model_dump_json().encode()).hexdigest()
        )
        assert row["error"] is None and row["response"] is not None
        assert len(row["model_attempts"]) == 1
        attempt = row["model_attempts"][0]
        assert attempt["status"] == "response_received"
        assert attempt["configured_num_ctx"] == (
            8192 if case["workflow"] == "soc_alert" else None
        )
        assert attempt["complete_context_required"] is (case["workflow"] == "soc_alert")
        assert len(row["audit_outcomes"]) == 1
        assert row["audit_outcomes"][0]["success"]
        assert row["audit_outcomes"][0]["source_ids"] == [
            s["source_id"] for s in row["response"]["analysis"]["source_references"]
        ]
        assert all(
            value
            for key, value in row["checks"].items()
            if key != "case_identity_exact"
        )
    # Do not retroactively repair the archived model output or its original score.
    note = next(row for row in rows if row["case_id"] == "ESE-NOTE")
    assert note["response"]["analysis"]["alert_id"] == "VENDOR-110"
    assert note["checks"]["case_identity_exact"] is False
    assert sum(r["checks"]["case_identity_exact"] for r in rows) == 7


def test_actual_retrieval_and_passive_inspector_replay_from_archived_analysis(
    monkeypatch,
):
    monkeypatch.setenv("RETRIEVAL_BACKEND", "legacy")
    monkeypatch.delenv("RETRIEVAL_SHADOW_BACKEND", raising=False)
    for case, row in zip(cases(), load("results.json")["records"], strict=True):
        request = request_for(case)
        soc = case["workflow"] == "soc_alert"
        query = soc_retrieval_query(request) if soc else request.model_dump_json()
        with collect_evidence(case["workflow"]) as capture:
            retrieve_for_analysis(
                case["workflow"],
                query,
                5 if soc else 6,
                legacy_loader=get_relevant_references,
            )
        response = (SocAlertResponse if soc else GovernanceRiskResponse).model_validate(
            row["response"]["analysis"]
        )
        replay = build_inspector(capture, request, response)
        # Replay every original field exactly; the additive 4.6 field inventory is
        # tested separately and never written into the frozen live artifact.
        assert (
            replay.model_dump(mode="json", exclude={"field_anchors"})
            == row["response"]["metadata"]["evidence_inspector"]
        )
        assert all(
            c.assessment.verification_status == "not_verified"
            and c.assessment.provenance == "model_proposed"
            and c.assessment.relationship == "unassessed"
            for c in replay.claims
        )


def test_manual_reviews_are_complete_quote_bound_and_summary_is_reproducible():
    rows, review, summary = (
        load("results.json")["records"],
        load("manual_review.json"),
        load("summary.json"),
    )
    assert review["status"] == "complete; eight scheduled candidate attempts reviewed"
    assert review["judgment_revisions"] == []
    assert len(review["reviews"]) == len(rows) == 8
    for row, item in zip(rows, review["reviews"], strict=True):
        assert item["case_id"] == row["case_id"]
        assert (
            item["record_sha256"]
            == hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
        )
        for dimension in DIMENSIONS:
            assert item[dimension] in {"absent", "present", "ambiguous"}
        assert item["quotes"] and item["rationale"]
        for quote in item["quotes"]:
            assert quote["value"] == row["response"]["analysis"][quote["field"]]
    assert summary["manual_dimensions"] == {
        dimension: dict(Counter(item[dimension] for item in review["reviews"]))
        for dimension in DIMENSIONS
    }
    assert summary["returned"] == summary["actual_model_requests"] == 8
    assert summary["withheld"] == summary["repair_attempts"] == 0
    assert (
        summary["latency_seconds"]["median"]
        == statistics.median(r["latency_ms"] for r in rows) / 1000
    )
    assert summary["machine_checks"] == {
        key: {"passed": sum(r["checks"][key] for r in rows), "denominator": 8}
        for key in rows[0]["checks"]
    }
