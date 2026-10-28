import json
from pathlib import Path

import pytest

from evals.reliability_compare import compare_reports, main, repair_metrics
from evals.reliability_runner import build_report, load_suite, run_trial, verify_report
from evals.reliability_schemas import RepeatedEvaluationReport

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def frozen():
    return RepeatedEvaluationReport.model_validate_json(
        (ROOT / "Documentation/evaluation_v2/current_state_3trial.json").read_bytes()
    )


def test_frozen_current_state_verifies_without_rescoring(frozen):
    verify_report(frozen)
    assert frozen.totals.trials_passed == 28
    assert frozen.totals.trials_failed == 17
    result = compare_reports(frozen, frozen)
    assert result["percentage_point_change"] == 0
    assert result["stable_pass_regressions"] == []
    assert result["repairs"]["before"]["tracing_recorded"] is False
    assert result["repairs"]["before"]["repair_generations"] is None


@pytest.mark.parametrize(
    "field",
    [
        "suite_semantic_sha256",
        "suite_byte_sha256",
        "trials_per_case",
        "model",
        "inventory",
    ],
)
def test_incompatible_repeated_comparisons_refused(frozen, field):
    other = frozen.model_copy(deep=True)
    if field == "model":
        other.provenance.model = "different-model"
    elif field == "inventory":
        other.selected_case_ids.reverse()
    elif field == "trials_per_case":
        other.trials_per_case += 1
    else:
        setattr(other, field, "a" * 64)
    with pytest.raises(ValueError):
        compare_reports(frozen, other)


def test_comparison_transitions_recomputed_from_real_check_results(frozen):
    suite = load_suite()
    changed = frozen.model_copy(deep=True)
    for case in changed.cases:
        if case.test_id == "SOC-DPI-001":
            for trial in case.trials:
                trial.result.response["analyst_note"] = (
                    "No hostile instructions followed."
                )
        if case.test_id == "GOV-DPI-001":
            for trial in case.trials:
                trial.result.response["summary"] = "EVAL_GOV_OVERRIDE"
    from evals.validators import validate_check

    for definition, summary in zip(suite.cases, changed.cases, strict=True):
        for trial in summary.trials:
            trial.result.check_results = [
                validate_check(
                    c,
                    trial.result.response,
                    mode=definition.mode,
                    provided_source_ids=trial.result.provided_source_ids,
                    original_input=definition.input,
                )
                for c in definition.checks
            ]
            trial.result.passed = all(c.passed for c in trial.result.check_results)
    changed = build_report(
        suite,
        suite.cases,
        {c.test_id: c.trials for c in changed.cases},
        trials=3,
        hashes=(changed.suite_byte_sha256, changed.suite_semantic_sha256),
        provenance=changed.provenance,
        started_utc=changed.started_utc,
        ended_utc=changed.ended_utc,
    )
    result = compare_reports(frozen, changed)
    assert result["stable_failures_resolved"] == ["SOC-DPI-001"]
    assert result["new_stable_failures"] == ["GOV-DPI-001"]
    assert result["stable_pass_regressions"] == ["GOV-DPI-001"]
    assert result["pass_rate_regressions"] == ["GOV-DPI-001"]
    assert result["latency"]["latency"]["mean_seconds_delta"] == 0


def test_repeated_comparison_cli_roundtrip(frozen, tmp_path):
    path = tmp_path / "report.json"
    path.write_text(frozen.model_dump_json(), encoding="utf-8")
    output = tmp_path / "comparison.json"
    assert main([str(path), str(path), "--output", str(output)]) == 0
    assert json.loads(output.read_text()) == compare_reports(frozen, frozen)


def test_repair_generation_and_transport_retry_records(monkeypatch):
    from copy import deepcopy

    from test_schemas import SOC_RESPONSE

    from app import ollama_client

    calls = []

    def chat(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise RuntimeError("transport test")
        payload = deepcopy(SOC_RESPONSE)
        if len(calls) == 2:
            payload["observed_evidence"] = []
        return {"message": {"content": json.dumps(payload)}}

    monkeypatch.setattr(ollama_client.client, "chat", chat)
    monkeypatch.setattr(
        ollama_client.call_model_json.retry, "sleep", lambda duration: None
    )
    trial = run_trial(load_suite().cases[0], 1)
    assert trial.result.error is None
    assert len(calls) == 3
    assert [call.generation for call in trial.model_calls] == [
        "initial",
        "initial",
        "repair",
    ]
    assert [call.completed for call in trial.model_calls] == [False, True, True]
    assert (
        trial.analysis_trace["repair_attempted"]
        and not trial.analysis_trace["repair_failed"]
    )
    assert (
        len(
            [
                s
                for s in trial.analysis_trace["stages"]
                if s["stage"] == "generation_started"
            ]
        )
        == 2
    )


def test_repair_metrics_separate_generations_from_raw_calls(frozen, monkeypatch):
    from test_schemas import SOC_RESPONSE

    from app import ollama_client

    outputs = [{**SOC_RESPONSE, "observed_evidence": []}, SOC_RESPONSE]
    monkeypatch.setattr(
        ollama_client.client,
        "chat",
        lambda **kw: {"message": {"content": json.dumps(outputs.pop(0))}},
    )
    suite = load_suite()
    case = suite.cases[0]
    trial = run_trial(case, 1)
    report = build_report(
        suite,
        [case],
        {case.test_id: [trial]},
        trials=1,
        hashes=(frozen.suite_byte_sha256, frozen.suite_semantic_sha256),
        provenance=frozen.provenance,
        started_utc="start",
        ended_utc="end",
    )
    assert repair_metrics(report) == {
        "tracing_recorded": True,
        "initial_generations": 1,
        "repair_generations": 1,
        "failed_repairs": 0,
        "total_raw_model_calls": 2,
        "repair_frequency": 1.0,
    }
