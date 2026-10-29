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
