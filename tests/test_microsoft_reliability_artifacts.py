"""Offline replay and identity checks for the new experiment's official artifacts."""

import hashlib
import json
import subprocess

from evals.microsoft_reliability.cases import load_cases
from evals.microsoft_reliability.runner import (
    ROOT,
    aggregate,
    digest,
    identity,
    request_for,
)

DIRECTORY = ROOT / "Documentation/microsoft_reliability"


def test_baseline_complete_exact_schedule_provenance_and_replay():
    report = json.loads((DIRECTORY / "baseline.json").read_bytes())
    manifest = json.loads((DIRECTORY / "baseline_provenance.json").read_bytes())
    assert (
        hashlib.sha256((DIRECTORY / "baseline.json").read_bytes()).hexdigest()
        == manifest["baseline_sha256"]
    )
    assert report["identity"] == identity() == manifest["suite_identity"]
    expected = [
        (c["case_id"], trial, digest(request_for(c).model_dump(mode="json")))
        for c in load_cases()
        for trial in range(1, c["trials"] + 1)
    ]
    assert [
        (r["case_id"], r["trial"], r["request_sha256"]) for r in report["records"]
    ] == expected
    assert report["metrics"] == aggregate(report["records"])
    assert report["metrics"]["attempts"] == 32
    assert report["metrics"]["returned"] == 29
    assert report["runtime"]["git_commit"] == "3f33cca014ff7865981afcedacdc69107bb5f6d2"
    assert not report["runtime"]["git_dirty"]
    assert all(
        a["configured_num_ctx"] is None
        for r in report["records"]
        for a in r["model_attempts"]
    )
    snapshot = json.loads((DIRECTORY / "recovery_snapshot.json").read_bytes())
    for old, row in zip(
        snapshot["completed_schedule_prefix"], report["records"], strict=False
    ):
        assert old["record_sha256"] == digest(row)


def test_manual_review_complete_quotes_bound_and_prior_judgments_preserved():
    report = json.loads((DIRECTORY / "baseline.json").read_bytes())
    review = json.loads((DIRECTORY / "baseline_manual_review.json").read_bytes())
    assert len(review["reviews"]) == len(report["records"]) == 32
    for item, row in zip(review["reviews"], report["records"], strict=True):
        assert (item["case_id"], item["trial"]) == (row["case_id"], row["trial"])
        assert review["baseline_record_sha256"][
            f"{row['case_id']}/{row['trial']}"
        ] == digest(row)
        for quote in item["quotes"]:
            assert quote["text"] in str(row["result"][quote["field"]])
        if row["result"] is None:
            assert all(
                item[k] == "unassessable"
                for k in (
                    "material_omission",
                    "unsupported_factual_claim",
                    "unsupported_authority_claim",
                    "overclaiming",
                    "source_applicability",
                )
            )
    prior = json.loads(
        subprocess.check_output(
            [
                "git",
                "show",
                "58304d0:Documentation/microsoft_reliability/baseline_manual_review.json",
            ],
            cwd=ROOT,
        )
    )
    assert review["reviews"][: len(prior["reviews"])] == prior["reviews"]
    assert review["judgment_revisions"] == []
