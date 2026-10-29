"""Frozen treatment/comparison/review verification without model calls."""

import json
import re
import subprocess
from collections import Counter

from app.output_policy import validate_soc_output
from evals.provenance import ROOT, byte_hash
from evals.semantic_runner_v32 import load_suite, verify_report
from evals.semantic_schemas_v32 import SemanticReport
from evals.semantic_treatment_compare import compare_reports
from evals.semantic_validators import strings

DIRECTORY = ROOT / "Documentation/evaluation_v3_2"


def report(name):
    return SemanticReport.model_validate_json((DIRECTORY / name).read_bytes())


def test_treatment_and_comparison_recompute():
    baseline = report("semantic_baseline_3trial.json")
    treatment = report("semantic_treatment_3trial.json")
    verify_report(treatment)
    assert treatment.totals.trials_attempted == 42
    assert treatment.trials_per_case == 3 and len(treatment.cases) == 14
    assert compare_reports(baseline, treatment) == json.loads(
        (DIRECTORY / "treatment_comparison.json").read_bytes()
    )
    assert treatment.provenance.git_dirty is False


def test_every_returned_soc_response_passes_complete_production_contract():
    cases = {c.test_id: c for c in load_suite().cases}
    for summary in report("semantic_treatment_3trial.json").cases:
        case = cases[summary.test_id]
        for trial in summary.trials:
            if case.mode == "soc_alert" and trial.response is not None:
                response, violations = validate_soc_output(trial.response, case.input)
                assert response is not None and not violations, (
                    case.test_id,
                    trial.trial,
                )
                assert any(
                    s["stage"] == "contract_accepted"
                    for s in trial.analysis_trace["stages"]
                )
            if trial.analysis_trace and trial.analysis_trace["repair_failed"]:
                assert trial.error and trial.response is None
            if case.mode == "soc_alert":
                assert (
                    max(
                        (s["generation"] for s in trial.analysis_trace["stages"]),
                        default=0,
                    )
                    <= 1
                )


def test_review_covers_all_trials_and_exact_evidence():
    treatment = report("semantic_treatment_3trial.json")
    review = json.loads((DIRECTORY / "treatment_manual_review.json").read_bytes())
    cases = {c.test_id: c for c in load_suite().cases}
    trials = {(c.test_id, t.trial): t for c in treatment.cases for t in c.trials}
    ids = [(r["case_id"], r["trial"]) for r in review["trials"]]
    assert len(ids) == len(set(ids)) == 42 and set(ids) == set(trials)
    for row in review["trials"]:
        case, trial = cases[row["case_id"]], trials[row["case_id"], row["trial"]]
        assert row["facts"] == [f.model_dump(mode="json") for f in case.facts]
        assert row["known_values"] == [
            v.model_dump(mode="json") for v in case.known_values
        ]
        assert row["official_outcome"] == (
            "error" if trial.error else "pass" if trial.passed else "fail"
        )
        assert row["assessment"] and row["confidence"] in {"high", "moderate", "low"}
        if trial.response is not None:
            assert row["evidence"]
            for e in row["evidence"]:
                assert e["quote"] and any(
                    e["quote"] in t for t in strings(trial.response[e["field"]])
                )
        else:
            assert row["classification"] == "application_error"
        for e in row["trace_evidence"]:
            stage = next(
                s
                for s in trial.analysis_trace["stages"]
                if s["stage"] == e["stage"] and s["generation"] == e["generation"]
            )
            assert any(e["quote"] in t for t in strings(stage["value"][e["field"]]))
            assert any(
                e["machine_violation"] in s["value"]
                for s in trial.analysis_trace["stages"]
                if s["stage"] == "policy_violations"
                and s["generation"] == e["generation"]
            )
        for k in (
            "validator_false_positives",
            "validator_false_negatives",
            "other_unscored_defects",
        ):
            assert k in row
            for issue in row[k]:
                assert issue["reason"] and issue["confidence"] in {
                    "high",
                    "moderate",
                    "low",
                }
    assert review["summary"]["classification_counts"] == dict(
        Counter(r["classification"] for r in review["trials"])
    )


def test_treatment_manifest_freeze_and_expectations():
    treatment = report("semantic_treatment_3trial.json")
    manifest = json.loads((DIRECTORY / "treatment_provenance.json").read_bytes())
    assert manifest["treatment_commit"] == treatment.provenance.git_commit
    assert manifest["file_sha256"] == treatment.file_sha256
    for name, expected in manifest["artifact_sha256"].items():
        assert byte_hash(ROOT / name) == expected, name
    for name, expected in manifest["behavior_git_blob_sha1"].items():
        from historical_identity import expansion_blob

        actual = expansion_blob(name)
        original = subprocess.check_output(
            ["git", "rev-parse", f"{manifest['treatment_commit']}:{name}"],
            cwd=ROOT,
            text=True,
        ).strip()
        assert actual == original == expected, name
    ledger = json.loads((DIRECTORY / "treatment_expectation_check.json").read_bytes())
    assert [x["hypothesis"] for x in ledger["hypotheses"]] == list(range(1, 10))
    for row in ledger["hypotheses"]:
        assert all(
            row[k]
            for k in ("expected", "actual", "assessment", "likely_reason", "confidence")
        )
    for path in [
        ROOT / "Documentation/18_semantic_production_hardening.md",
        ROOT / "Documentation/19_semantic_hardening_sprint_report.md",
        DIRECTORY / "treatment_manual_review.md",
        DIRECTORY / "treatment_failure_triage.md",
    ]:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if not target.startswith(("https://", "http://", "#")):
                assert (path.parent / target.split("#", 1)[0]).is_file(), (path, target)
