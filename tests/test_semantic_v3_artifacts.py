"""No-model checks for the frozen V3 report and manual review evidence."""

import json

from historical_identity import historical_blob

from evals.provenance import ROOT, byte_hash, suite_hashes
from evals.semantic_runner import CASE_PATH, load_suite, verify_report
from evals.semantic_schemas import SemanticReport
from evals.semantic_validators import strings

DIRECTORY = ROOT / "Documentation/evaluation_v3"


def test_official_v3_recomputes():
    report = SemanticReport.model_validate_json(
        (DIRECTORY / "semantic_baseline_3trial.json").read_bytes()
    )
    verify_report(report)
    assert report.trials_per_case == 3
    assert report.totals.trials_attempted == 36
    assert len(report.cases) == 12


def test_official_manifest_and_behavior_identity():
    manifest = json.loads((DIRECTORY / "provenance.json").read_bytes())
    for name, expected in manifest["artifact_sha256"].items():
        assert byte_hash(ROOT / name) == expected, name
    assert suite_hashes(CASE_PATH) == (
        manifest["suite_byte_sha256"],
        manifest["suite_semantic_sha256"],
    )
    # Exact working-file hashes describe the local experiment. Git blob identity
    # additionally verifies preservation on CI with different newline checkout.
    for name, expected in manifest["behavior_git_blob_sha1"].items():
        actual = historical_blob(name)
        assert actual == expected, name


def test_every_trial_has_grounded_manual_review():
    report = SemanticReport.model_validate_json(
        (DIRECTORY / "semantic_baseline_3trial.json").read_bytes()
    )
    review = json.loads((DIRECTORY / "manual_review.json").read_bytes())
    cases = {c.test_id: c for c in load_suite().cases}
    trials = {(c.test_id, t.trial): t for c in report.cases for t in c.trials}
    rows = review["trials"]
    identities = [(r["case_id"], r["trial"]) for r in rows]
    assert len(identities) == len(set(identities)) == 36
    assert set(identities) == set(trials)
    for row in rows:
        trial = trials[row["case_id"], row["trial"]]
        assert row["official_outcome"] == (
            "error" if trial.error else "pass" if trial.passed else "fail"
        )
        assert row["assessment"] and row["confidence"] in {"high", "moderate", "low"}
        assert row["facts"] == [
            f.model_dump(mode="json") for f in cases[row["case_id"]].facts
        ]
        for evidence in row["evidence"]:
            assert trial.response is not None
            assert any(
                evidence["quote"] in text
                for text in strings(trial.response[evidence["field"]])
            )
        for term in row["absent_terms"]:
            assert term not in json.dumps(trial.response)
        if trial.error is not None:
            assert row["classification"] == "application_error"
        else:
            assert row["evidence"]
            assert row["classification"] in {
                "true_positive_failure",
                "true_negative_pass",
                "suspected_false_positive",
                "suspected_false_negative",
            }


def test_review_markdown_covers_each_trial():
    review = json.loads((DIRECTORY / "manual_review.json").read_bytes())
    markdown = (DIRECTORY / "manual_review.md").read_text(encoding="utf-8")
    for row in review["trials"]:
        assert f"{row['case_id']} / trial {row['trial']}" in markdown
