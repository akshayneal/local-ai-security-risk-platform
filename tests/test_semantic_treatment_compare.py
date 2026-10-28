"""Comparison is derived from frozen scores; no model or new scoring rules."""

import json

import pytest
from historical_identity import productization_blob

from evals.provenance import ROOT
from evals.semantic_runner_v32 import build_report, load_suite
from evals.semantic_schemas_v32 import SemanticReport
from evals.semantic_treatment_compare import compare_reports


@pytest.fixture
def baseline():
    return SemanticReport.model_validate_json(
        (
            ROOT / "Documentation/evaluation_v3_2/semantic_baseline_3trial.json"
        ).read_bytes()
    )


def test_same_report_has_zero_changes(baseline):
    result = compare_reports(baseline, baseline)
    assert result["pass_rate_percentage_point_change"] == 0
    assert result["before"]["repair_generations"] == 4
    assert result["mean_trial_seconds_change"] == 0
    assert len(result["case_transitions"]) == 14


@pytest.mark.parametrize(
    "key",
    [
        "suite_byte_sha256",
        "suite_semantic_sha256",
        "trials_per_case",
        "scorer_version",
        "model",
        "model_digest",
        "temperature",
        "seed_state",
    ],
)
def test_incompatible_experiments_refused(baseline, key):
    after = baseline.model_copy(deep=True)
    target = after.provenance if hasattr(after.provenance, key) else after
    setattr(
        target, key, "different" if key not in {"temperature", "trials_per_case"} else 9
    )
    with pytest.raises(ValueError):
        compare_reports(baseline, after)


def test_application_errors_remain_separate(baseline):
    records = {
        c.test_id: [t.model_copy(deep=True) for t in c.trials] for c in baseline.cases
    }
    t = records[baseline.cases[0].test_id][0]
    t.error = "OutputPolicyError"
    t.response = None
    t.checks = []
    t.passed = False
    after = build_report(
        load_suite(),
        records,
        trials=3,
        hashes=(baseline.suite_byte_sha256, baseline.suite_semantic_sha256),
        provenance=baseline.provenance,
        file_hashes=baseline.file_sha256,
        started=baseline.started_utc,
        ended=baseline.ended_utc,
    )
    result = compare_reports(baseline, after)
    assert result["after"]["totals"]["application_error_count"] == 1
    assert result["after"]["totals"]["trials_completed"] == 41
    assert result["case_transitions"][0]["after_outcomes"][0] == "error"


def test_frozen_artifacts_scorers_and_unrelated_production_preserved():
    data = json.loads(
        (
            ROOT / "Documentation/evaluation_v3_2/semantic_hardening_preservation.json"
        ).read_bytes()
    )
    for name, expected in data["frozen_git_blob_sha1"].items():
        actual = productization_blob(name)
        assert actual == expected, name
