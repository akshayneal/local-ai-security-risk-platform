"""Frozen V3.1 evidence verification without model calls or scorer changes."""

import json

from historical_identity import historical_blob

from evals.provenance import ROOT, byte_hash, suite_hashes
from evals.semantic_runner_v31 import CASE_PATH, load_suite, verify_report
from evals.semantic_schemas_v31 import SemanticReport
from evals.semantic_validators import strings

DIRECTORY = ROOT / "Documentation/evaluation_v3_1"


def test_official_v31_report_recomputes():
    report = SemanticReport.model_validate_json(
        (DIRECTORY / "semantic_baseline_3trial.json").read_bytes()
    )
    verify_report(report)
    assert report.report_version == report.scorer_version == "3.1"
    assert report.trials_per_case == 3
    assert report.totals.trials_attempted == 39
    assert len(report.cases) == 13


def test_manifest_and_behavior_identity():
    manifest = json.loads((DIRECTORY / "provenance.json").read_bytes())
    for name, expected in manifest["artifact_sha256"].items():
        assert byte_hash(ROOT / name) == expected, name
    assert suite_hashes(CASE_PATH) == (
        manifest["suite_byte_sha256"],
        manifest["suite_semantic_sha256"],
    )
    for name, expected in manifest["behavior_git_blob_sha1"].items():
        actual = historical_blob(name)
        assert actual == expected, name


def test_every_trial_review_has_exact_evidence_and_answer_key():
    report = SemanticReport.model_validate_json(
        (DIRECTORY / "semantic_baseline_3trial.json").read_bytes()
    )
    review = json.loads((DIRECTORY / "manual_review.json").read_bytes())
    cases = {c.test_id: c for c in load_suite().cases}
    trials = {(c.test_id, t.trial): t for c in report.cases for t in c.trials}
    identities = [(r["case_id"], r["trial"]) for r in review["trials"]]
    assert len(identities) == len(set(identities)) == 39
    assert set(identities) == set(trials)
    for row in review["trials"]:
        case = cases[row["case_id"]]
        trial = trials[row["case_id"], row["trial"]]
        assert row["facts"] == [f.model_dump(mode="json") for f in case.facts]
        assert row["protocol"] == (
            case.protocol.model_dump(mode="json") if case.protocol else None
        )
        assert row["endpoints"] == [e.model_dump(mode="json") for e in case.endpoints]
        assert row["official_outcome"] == (
            "error" if trial.error else "pass" if trial.passed else "fail"
        )
        assert row["assessment"] and row["confidence"] in {"high", "moderate", "low"}
        assert "other_unscored_defects" in row
        for evidence in row["evidence"]:
            assert trial.response is not None
            assert any(
                evidence["quote"] in text
                for text in strings(trial.response[evidence["field"]])
            )
        for term in row["absent_terms"]:
            assert term not in json.dumps(trial.response)
        if trial.error:
            assert row["classification"] == "application_error"
        else:
            assert row["evidence"]
            assert row["classification"] in {
                "true_negative_pass",
                "true_positive_failure",
                "suspected_false_positive",
                "suspected_false_negative",
            }


def test_review_and_expectation_documentation_covers_inventory():
    review = json.loads((DIRECTORY / "manual_review.json").read_bytes())
    markdown = (DIRECTORY / "manual_review.md").read_text(encoding="utf-8")
    for row in review["trials"]:
        assert f"{row['case_id']} / trial {row['trial']}" in markdown
    expectations = json.loads((DIRECTORY / "expectation_check.json").read_bytes())
    assert [r["hypothesis"] for r in expectations["hypotheses"]] == list(range(1, 8))
    for row in expectations["hypotheses"]:
        assert all(
            row[key]
            for key in [
                "expected",
                "actual",
                "assessment",
                "likely_reason",
                "confidence",
            ]
        )
