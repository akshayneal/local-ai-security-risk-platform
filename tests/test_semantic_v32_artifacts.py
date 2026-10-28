"""Verify the frozen V3.2 experiment, review evidence and portable identities."""

import json
import re
import subprocess
from collections import Counter
from pathlib import Path

from evals.provenance import ROOT, byte_hash, suite_hashes
from evals.semantic_runner_v32 import CASE_PATH, load_suite, verify_report
from evals.semantic_schemas_v32 import SemanticReport
from evals.semantic_validators import strings

DIRECTORY = ROOT / "Documentation/evaluation_v3_2"


def read_report():
    return SemanticReport.model_validate_json(
        (DIRECTORY / "semantic_baseline_3trial.json").read_bytes()
    )


def test_official_report_recomputes():
    report = read_report()
    verify_report(report)
    assert report.report_version == report.scorer_version == "3.2"
    assert report.trials_per_case == 3
    assert len(report.cases) == 14
    assert report.totals.trials_requested == report.totals.trials_attempted == 42
    assert report.positive_control_totals.trials_requested == 15
    assert not report.provenance.git_dirty
    assert report.provenance.temperature == 0.1
    assert report.provenance.seed_state == "not_configured"


def test_manifest_artifacts_behavior_and_framework_freeze():
    report = read_report()
    manifest = json.loads((DIRECTORY / "provenance.json").read_bytes())
    for name, expected in manifest["artifact_sha256"].items():
        assert byte_hash(ROOT / name) == expected, name
    assert manifest["runtime"] == report.provenance.model_dump(mode="json")
    assert manifest["framework_commit"] == report.provenance.git_commit
    assert manifest["file_sha256"] == report.file_sha256
    assert suite_hashes(CASE_PATH) == (
        manifest["suite_byte_sha256"],
        manifest["suite_semantic_sha256"],
    )
    for name, expected in manifest["behavior_git_blob_sha1"].items():
        actual = subprocess.check_output(
            ["git", "hash-object", f"--path={name}", name], cwd=ROOT, text=True
        ).strip()
        assert actual == expected, name
        framework = subprocess.check_output(
            ["git", "rev-parse", f"{manifest['framework_commit']}:{name}"],
            cwd=ROOT,
            text=True,
        ).strip()
        assert framework == expected, name


def test_complete_review_exact_quotes_keys_and_classifications():
    report = read_report()
    review = json.loads((DIRECTORY / "manual_review.json").read_bytes())
    cases = {c.test_id: c for c in load_suite().cases}
    trials = {(c.test_id, t.trial): t for c in report.cases for t in c.trials}
    identities = [(r["case_id"], r["trial"]) for r in review["trials"]]
    assert len(identities) == len(set(identities)) == 42
    assert set(identities) == set(trials)
    for row in review["trials"]:
        case, trial = cases[row["case_id"]], trials[row["case_id"], row["trial"]]
        assert row["facts"] == [f.model_dump(mode="json") for f in case.facts]
        assert row["known_values"] == [
            v.model_dump(mode="json") for v in case.known_values
        ]
        assert row["protocol"] == (
            case.protocol.model_dump(mode="json") if case.protocol else None
        )
        assert row["endpoints"] == [e.model_dump(mode="json") for e in case.endpoints]
        assert row["official_outcome"] == (
            "error" if trial.error else "pass" if trial.passed else "fail"
        )
        assert row["assessment"] and row["confidence"] in {"high", "moderate", "low"}
        assert row["classification"] in {
            "bounded_true_pass",
            "genuine_semantic_failure",
            "suspected_false_positive",
            "suspected_false_negative",
            "application_error",
        }
        if trial.error:
            assert row["classification"] == "application_error"
        else:
            assert row["evidence"]
            for evidence in row["evidence"]:
                assert evidence["quote"] and any(
                    evidence["quote"] in text
                    for text in strings(trial.response[evidence["field"]])
                )
        for term in row["absent_terms"]:
            assert term not in json.dumps(trial.response)
        for field in [
            "validator_false_positives",
            "validator_false_negatives",
            "other_unscored_defects",
        ]:
            assert field in row
            for finding in row[field]:
                assert finding["reason"] and finding["confidence"] in {
                    "high",
                    "moderate",
                    "low",
                }
        if row["classification"] == "suspected_false_positive":
            assert (
                not trial.passed
                and not trial.error
                and row["validator_false_positives"]
            )
        if row["classification"] == "suspected_false_negative":
            assert row["validator_false_negatives"]
    assert review["summary"]["classification_counts"] == dict(
        Counter(r["classification"] for r in review["trials"])
    )
    assert review["official_scores_unchanged"] is True
    assert review["summary"]["false_positive_trials"] == sum(
        bool(r["validator_false_positives"]) for r in review["trials"]
    )
    assert review["summary"]["false_negative_trials"] == sum(
        bool(r["validator_false_negatives"]) for r in review["trials"]
    )


def test_ledgers_and_document_links():
    review = json.loads((DIRECTORY / "manual_review.json").read_bytes())
    markdown = (DIRECTORY / "manual_review.md").read_text(encoding="utf-8")
    for row in review["trials"]:
        assert f"{row['case_id']} / trial {row['trial']}" in markdown
    ledger = json.loads((DIRECTORY / "expectation_check.json").read_bytes())
    assert [r["hypothesis"] for r in ledger["hypotheses"]] == list(range(1, 8))
    for row in ledger["hypotheses"]:
        assert all(
            row[k]
            for k in ["expected", "actual", "assessment", "explanation", "confidence"]
        )
    for path in [
        ROOT / "Documentation/16_semantic_evaluation_v3_2.md",
        ROOT / "Documentation/17_semantic_v3_2_sprint_report.md",
        DIRECTORY / "manual_review.md",
        DIRECTORY / "failure_triage.md",
    ]:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if target.startswith(("https://", "http://", "#")):
                continue
            relative = target.split("#", 1)[0]
            assert Path(path.parent / relative).is_file(), (path.name, target)
