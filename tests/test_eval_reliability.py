"""Deterministic V2 tests: no Ollama generations, including CLI and retry paths."""

import copy
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from test_schemas import GOVERNANCE_RESPONSE, SOC_RESPONSE

from app import ollama_client
from app.schemas import SocAlertResponse
from evals import provenance
from evals import reliability_runner as runner
from evals import runner as v1_runner
from evals.compare import compare_reports
from evals.observables import extract_observables, invalid_ipv4_candidates
from evals.reliability_schemas import (
    ModelCall,
    RepeatedEvaluationReport,
    RuntimeProvenance,
    TrialResult,
    TrialTotals,
)
from evals.schemas import EvalCheck, EvaluationReport, EvaluationResult
from evals.validators import validate_check


@pytest.fixture
def runtime():
    return RuntimeProvenance(
        python_version="3.13.1",
        ollama_version="ollama version is 0.40.11",
        model="qwen3:8b",
        model_digest="500a1f067a9f",
        model_digest_kind="ollama_ls_short_id",
        git_commit="a" * 40,
        git_dirty=False,
        temperature=0.1,
    )


@pytest.fixture
def trial_factory(monkeypatch):
    monkeypatch.setattr(
        v1_runner,
        "analyze_soc_alert",
        lambda *args, **kwargs: SocAlertResponse(**copy.deepcopy(SOC_RESPONSE)),
    )
    case = runner.load_suite().cases[0]
    result = v1_runner.run_case(case)
    assert result.passed

    def make(passed=True, *, number=1, error=False, duration=2.0, response=None):
        updated = result.model_copy(deep=True)
        updated.duration_seconds = duration
        if error:
            updated.passed = False
            updated.response = None
            updated.error = "Application call failed (RuntimeError)"
            updated.check_results = []
        elif not passed:
            updated = v1_runner.run_case(
                case
            )  # Produce checks through the real validator.
            updated.response["analyst_note"] = "EVAL_ATTACK_SUCCEEDED"
            updated.check_results = [
                validate_check(
                    check,
                    updated.response,
                    mode=case.mode,
                    provided_source_ids=updated.provided_source_ids,
                )
                for check in case.checks
            ]
            updated.passed = False
            updated.duration_seconds = duration
        if response is not None:
            updated.response = response
        return TrialResult(
            trial=number,
            result=updated,
            model_calls=[
                ModelCall(
                    duration_seconds=duration,
                    completed=not error,
                    error_type="RuntimeError" if error else None,
                )
            ],
        )

    return make


@pytest.fixture
def report(runtime, trial_factory):
    suite = runner.load_suite()
    case = suite.cases[0]
    trials = [trial_factory(number=i) for i in range(1, 4)]
    return runner.build_report(
        suite,
        [case],
        {case.test_id: trials},
        trials=3,
        hashes=provenance.suite_hashes(runner.CASE_PATH),
        provenance=runtime,
        started_utc="2026-10-27T00:00:00+00:00",
        ended_utc="2026-10-27T00:01:00+00:00",
    )


@pytest.mark.parametrize(
    ("kind", "text", "expected"),
    [
        ("ipv4", "from 192.0.2.51:22 to 203.0.113.77.", {"192.0.2.51", "203.0.113.77"}),
        ("ipv4", "999.0.2.51 192.0.2.999 19.2.0.2.51 192.00.2.51", set()),
        ("ipv4", "host192.0.2.51 192.0.2.51extra", set()),
        ("sha256", "hash=" + "a" * 64 + "; shorter=abc123", {"a" * 64}),
        ("sha256", "a" * 65 + " x" + "b" * 64, set()),
        ("sha256", "SHA256=" + "ABCDEF01" * 8, {"ABCDEF01" * 8}),
        (
            "cve",
            "CVE-2099-99999 and CVE-2020-1234",
            {"CVE-2099-99999", "CVE-2020-1234"},
        ),
        ("cve", "CVE-2099-123 prefixCVE-2099-99999 CVE-2099-99999suffix", set()),
    ],
)
def test_extract_observables(kind, text, expected):
    assert extract_observables(text, kind) == expected


def test_invalid_ipv4_token_is_preserved_for_diagnostics():
    assert invalid_ipv4_candidates("19.2.0.2.51 256.0.0.1 192.0.2.51") == {
        "19.2.0.2.51",
        "256.0.0.1",
    }
    with pytest.raises(ValueError):
        extract_observables("x", "unsupported")


@pytest.mark.parametrize(
    ("kind", "original", "output", "passed"),
    [
        ("ipv4", "192.0.2.51 203.0.113.77", "192.0.2.51", True),
        ("ipv4", "192.0.2.51", "19.2.0.2.51", False),
        ("ipv4", "192.0.2.51", "192.0.2.52", False),
        ("sha256", "a" * 64, "a" * 64, True),
        ("sha256", "a" * 64, "b" * 64, False),
        ("sha256", "a" * 64, "abc123", True),
        ("cve", "CVE-2099-99999", "CVE-2099-99998", False),
        ("cve", "CVE-2099-99999", "CVE-2099-99999", True),
        ("ipv4", "192.0.2.51", "No observables repeated", True),
    ],
)
def test_observable_subset(kind, original, output, passed):
    check = EvalCheck(
        type="observables_subset_of_input",
        field="observed_evidence",
        observable_type=kind,
    )
    result = validate_check(
        check,
        {"observed_evidence": [output], "analyst_note": "198.51.100.99"},
        mode="soc_alert",
        provided_source_ids=[],
        original_input={"raw_log": original},
    )
    assert result.passed is passed


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ("192.0.2.51", True),
        ("192.0.2.510", False),
        ("19.2.0.2.51", False),
        ("omitted", False),
    ],
)
def test_required_exact_observable(output, expected):
    check = EvalCheck(
        type="required_observable_present",
        field="observed_evidence",
        observable_type="ipv4",
        value="192.0.2.51",
    )
    assert (
        validate_check(
            check,
            {"observed_evidence": [output]},
            mode="soc_alert",
            provided_source_ids=[],
            original_input={"raw_log": "192.0.2.51"},
        ).passed
        is expected
    )


def test_observable_checks_fail_without_input_or_field():
    check = EvalCheck(
        type="observables_subset_of_input",
        field="observed_evidence",
        observable_type="ipv4",
    )
    assert not validate_check(
        check, {"observed_evidence": []}, mode="soc_alert", provided_source_ids=[]
    ).passed
    assert not validate_check(
        check, {}, mode="soc_alert", provided_source_ids=[], original_input={}
    ).passed


def test_v1_validator_interface_still_works():
    result = validate_check(
        EvalCheck(type="required_substring_present", value="example"),
        {"summary": "example"},
        mode="soc_alert",
        provided_source_ids=[],
    )
    assert result.passed


@pytest.mark.parametrize(
    "arguments",
    [
        {"type": "observables_subset_of_input"},
        {"type": "observables_subset_of_input", "field": "observed_evidence"},
        {
            "type": "required_observable_present",
            "field": "observed_evidence",
            "observable_type": "cve",
        },
    ],
)
def test_observable_check_arguments_validate(arguments):
    with pytest.raises(ValidationError):
        EvalCheck(**arguments)


@pytest.mark.parametrize(
    ("outcomes", "stability", "counts"),
    [
        ([True, True, True], "stable_pass", (3, 0, 0, 100)),
        ([False, False, False], "stable_fail", (0, 3, 0, 0)),
        ([True, False, True], "mixed", (2, 1, 0, 200 / 3)),
        ([None, None, None], "infrastructure_error", (0, 0, 3, 0)),
        ([True, None, False], "mixed", (1, 1, 1, 50)),
        ([True, None, True], "stable_pass", (2, 0, 1, 100)),
    ],
)
def test_stability_and_trial_accounting(trial_factory, outcomes, stability, counts):
    trials = [
        trial_factory(value, number=i, error=value is None)
        for i, value in enumerate(outcomes, 1)
    ]
    summary = runner.summarize_case(runner.load_suite().cases[0], trials, 3)
    assert summary.stability == stability
    assert (
        summary.trials_passed,
        summary.trials_failed,
        summary.application_error_count,
        summary.pass_rate,
    ) == counts
    assert summary.trials_attempted == 3
    assert summary.trials_completed == 3 - counts[2]
    if stability == "infrastructure_error":
        assert summary.latency.minimum_seconds is None
        assert summary.structured_output_stability["severity"].identical is None


@pytest.mark.parametrize("durations", [[1, 4, 2], [1, 4], [7], []])
def test_latency_statistics(durations):
    result = runner.latency(durations)
    assert result.completed == len(durations)
    if durations == [1, 4, 2]:
        assert (
            result.minimum_seconds,
            result.median_seconds,
            result.mean_seconds,
            result.maximum_seconds,
        ) == (1, 2, 7 / 3, 4)
    elif durations == [1, 4]:
        assert result.median_seconds == result.mean_seconds == 2.5
    elif durations == [7]:
        assert (
            result.minimum_seconds
            == result.maximum_seconds
            == result.mean_seconds
            == result.median_seconds
            == 7
        )
    else:
        assert result.model_dump() == {
            "completed": 0,
            "minimum_seconds": None,
            "median_seconds": None,
            "mean_seconds": None,
            "maximum_seconds": None,
        }


@pytest.mark.parametrize(
    ("mode", "payload", "field", "changed"),
    [
        ("soc_alert", SOC_RESPONSE, "severity", "critical"),
        (
            "soc_alert",
            SOC_RESPONSE,
            "likely_incident_type",
            "A different incident type",
        ),
        ("governance", GOVERNANCE_RESPONSE, "risk_level", "critical"),
        ("governance", GOVERNANCE_RESPONSE, "decision", "rejected"),
    ],
)
def test_structured_field_variability(trial_factory, mode, payload, field, changed):
    responses = [copy.deepcopy(payload) for _ in range(3)]
    assert responses[0][field] != changed
    responses[-1][field] = changed
    trials = [
        trial_factory(number=i, response=response)
        for i, response in enumerate(responses, 1)
    ]
    result = runner.structured_stability(trials, mode)
    assert result[field].identical is False
    assert sorted(value.count for value in result[field].observed_values) == [1, 2]
    # Diagnostics do not change independently scored security outcomes.
    assert all(trial.result.passed for trial in trials)


def test_source_sets_ignore_order_and_duplicates(trial_factory):
    trials = [trial_factory(number=i) for i in range(1, 4)]
    for trial, ids in zip(
        trials, [["A", "B"], ["B", "A"], ["A", "A", "B"]], strict=True
    ):
        trial.result.response["source_references"] = [
            {"source_id": value} for value in ids
        ]
    field = runner.structured_stability(trials, "soc_alert")["source_id_set"]
    assert field.identical is True
    assert field.observed_values[0].value == ["A", "B"]
    assert field.observed_values[0].count == 3
    trials[-1].result.response["source_references"] = []
    assert (
        runner.structured_stability(trials, "soc_alert")["source_id_set"].identical
        is False
    )


def test_error_trials_excluded_from_stability_and_latency(trial_factory):
    trials = [
        trial_factory(duration=1),
        trial_factory(error=True, duration=99, number=2),
    ]
    summary = runner.summarize_case(runner.load_suite().cases[0], trials, 2)
    assert summary.latency.mean_seconds == 1
    assert summary.structured_output_stability["severity"].observed_values[0].count == 1


def test_report_roundtrip_and_recomputed_validation(report):
    loaded = RepeatedEvaluationReport.model_validate_json(report.model_dump_json())
    assert loaded == report
    runner.verify_report(loaded)
    assert loaded.totals.trials_requested == loaded.totals.trials_attempted == 3
    assert loaded.total_model_calls_attempted == loaded.total_completed_model_calls == 3
    assert loaded.category_summary["direct_prompt_injection"].pass_rate == 100


@pytest.mark.parametrize(
    "corruption", ["hash", "latency", "stability", "trial", "count", "score", "case"]
)
def test_report_rejects_inconsistent_aggregates(report, corruption):
    bad = report.model_copy(deep=True)
    if corruption == "hash":
        bad.suite_byte_sha256 = "b" * 64
    elif corruption == "latency":
        bad.latency.mean_seconds = 99
    elif corruption == "stability":
        bad.cases[0].structured_output_stability["severity"].identical = False
    elif corruption == "trial":
        bad.cases[0].trials[0].trial = 2
    elif corruption == "count":
        bad.total_model_calls_attempted += 1
    elif corruption == "score":
        bad.cases[0].trials[0].result.passed = False
    else:
        bad.selected_case_ids.append("MISSING")
    with pytest.raises(ValueError):
        runner.verify_report(bad)


def test_report_schema_rejects_invalid_counts_and_error_passes(trial_factory, report):
    with pytest.raises(ValidationError):
        TrialTotals(
            trials_requested=3,
            trials_attempted=4,
            trials_completed=4,
            trials_passed=4,
            trials_failed=0,
            application_error_count=0,
            pass_rate=100,
        )
    bad = trial_factory(error=True).model_dump()
    bad["result"]["passed"] = True
    with pytest.raises(ValidationError):
        TrialResult.model_validate(bad)
    bad_report = report.model_dump()
    bad_report["trials_per_case"] = 0
    with pytest.raises(ValidationError):
        RepeatedEvaluationReport.model_validate(bad_report)


def test_full_aggregation_errors_and_trial_weighting(runtime, trial_factory):
    suite = runner.load_suite()
    cases = suite.cases[:2]
    grouped = {
        cases[0].test_id: [
            trial_factory(number=1),
            trial_factory(False, number=2),
            trial_factory(error=True, number=3),
        ],
        cases[1].test_id: [trial_factory(number=i) for i in range(1, 4)],
    }
    result = runner.build_report(
        suite,
        cases,
        grouped,
        trials=3,
        hashes=provenance.suite_hashes(runner.CASE_PATH),
        provenance=runtime,
        started_utc="start",
        ended_utc="end",
    )
    assert result.totals.trials_requested == result.totals.trials_attempted == 6
    assert result.totals.trials_completed == 5
    assert result.totals.trials_passed == 4
    assert result.totals.trials_failed == 1
    assert result.total_infrastructure_errors == result.model_call_error_count == 1
    assert result.total_completed_model_calls == 5
    assert (
        result.totals.pass_rate
        == result.category_summary["direct_prompt_injection"].pass_rate
        == 80
    )


def test_suite_hash_formatting_and_semantic_changes(tmp_path):
    path = tmp_path / "suite.json"
    path.write_bytes(b'{"a":1,"b":[2,3]}\n')
    original = provenance.suite_hashes(path)
    path.write_bytes(b'{\r\n  "b": [2, 3],\r\n  "a": 1\r\n}\r\n')
    formatted = provenance.suite_hashes(path)
    assert original[0] != formatted[0]
    assert original[1] == formatted[1]
    path.write_text('{"a":2,"b":[2,3]}', encoding="utf-8")
    assert provenance.suite_hashes(path)[1] != original[1]


def test_v2_inventory_preserves_v1_cases():
    suite = runner.load_suite()
    assert len(suite.cases) == 15
    assert len({case.category for case in suite.cases}) == 8
    assert suite.cases[:12] == v1_runner.load_suite()[0].cases
    assert all(case.category == "evidence_fidelity" for case in suite.cases[12:])


def test_preflight_never_generates(monkeypatch, runtime, capsys):
    monkeypatch.setattr(runner, "collect_provenance", lambda: runtime)
    monkeypatch.setattr(
        ollama_client.client,
        "chat",
        lambda *a, **kw: pytest.fail("Preflight generated"),
    )
    monkeypatch.setattr(
        runner, "run_trial", lambda *a: pytest.fail("Preflight ran trial")
    )
    assert runner.main(["--trials", "3", "--dry-run"]) == 0
    output = capsys.readouterr().out
    for message in [
        "Cases: 15",
        "Categories: 8",
        "Trials per case: 3",
        "Planned model calls: 45",
        "No Ollama generations executed.",
    ]:
        assert message in output


@pytest.mark.parametrize(
    ("filters", "expected"),
    [
        ({"case_id": "SOC-FID-001"}, 1),
        ({"category": "evidence_fidelity"}, 3),
        ({"case_id": "MISSING"}, None),
    ],
)
def test_preflight_filters(monkeypatch, runtime, filters, expected):
    monkeypatch.setattr(runner, "collect_provenance", lambda: runtime)
    if expected is None:
        with pytest.raises(ValueError, match="No cases"):
            runner.preflight(**filters)
    else:
        assert len(runner.preflight(**filters)[1]) == expected


@pytest.mark.parametrize(
    "defect",
    [
        "request",
        "duplicate",
        "empty_checks",
        "unknown_check",
        "reference",
        "duplicate_reference",
        "field",
        "observable",
    ],
)
def test_preflight_rejects_configuration_errors(tmp_path, monkeypatch, defect):
    data = json.loads(runner.CASE_PATH.read_bytes())
    case = data["cases"][0]
    if defect == "request":
        case["input"] = {}
    elif defect == "duplicate":
        data["cases"].append(case)
    elif defect == "empty_checks":
        case["checks"] = []
    elif defect == "unknown_check":
        case["checks"] = [{"type": "unsupported_check"}]
    elif defect == "reference":
        case["reference_overrides"] = [{"source_id": " "}]
    elif defect == "duplicate_reference":
        case["reference_overrides"] = [{"source_id": "DUPLICATE"}] * 2
    elif defect == "field":
        case["checks"] = [
            {
                "type": "required_substring_present",
                "field": "missing_field",
                "value": "x",
            }
        ]
    else:
        data["cases"][-1]["checks"][-1]["value"] = "CVE-2099-88888"
    path = tmp_path / "suite.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(
        runner,
        "collect_provenance",
        lambda: pytest.fail("Invalid configuration reached provenance"),
    )
    with pytest.raises(ValueError):
        runner.preflight(path)


@pytest.mark.parametrize("trials", [0, -1])
def test_invalid_trial_count(trials):
    with pytest.raises(ValueError, match="positive"):
        runner.preflight(trials=trials)


def test_runtime_cli_metadata_and_short_model_id(monkeypatch):
    outputs = {
        ("ollama", "--version"): "ollama version is 0.40.11\n",
        ("ollama", "ls"): "NAME ID SIZE\nqwen3:8b 500a1f067a9f 5.2 GB\n",
        ("git", "rev-parse", "HEAD"): "a" * 40,
        ("git", "status", "--porcelain"): "",
    }
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        assert kwargs["timeout"] == 15
        return SimpleNamespace(stdout=outputs[tuple(args)])

    monkeypatch.setattr(provenance.subprocess, "run", run)
    monkeypatch.setattr(provenance, "OLLAMA_MODEL", "qwen3:8b")
    result = provenance.collect_provenance()
    assert result.model_digest == "500a1f067a9f"
    assert result.model_digest_kind == "ollama_ls_short_id"
    assert result.git_dirty is False
    assert result.temperature == 0.1
    assert result.seed is None and result.seed_state == "not_configured"
    assert len(calls) == 4


@pytest.mark.parametrize(
    "listing", [None, "NAME ID\nother:8b abcdef123456", "NAME ID\nqwen3:8b invalid-id"]
)
def test_missing_digest_is_null(monkeypatch, listing):
    monkeypatch.setattr(
        provenance,
        "cli_output",
        lambda args: listing if args == ["ollama", "ls"] else "nonsecret",
    )
    result = provenance.collect_provenance()
    assert result.model_digest is None and result.model_digest_kind is None
    assert result.git_dirty is True
    assert result.unavailable


@pytest.mark.parametrize(
    "error",
    [
        OSError(),
        subprocess.CalledProcessError(1, "ollama"),
        subprocess.TimeoutExpired("ollama", 15),
    ],
)
def test_unavailable_cli_is_nonfatal(monkeypatch, error):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(provenance.subprocess, "run", fail)
    result = provenance.collect_provenance()
    assert result.git_commit is None and result.git_dirty is None
    assert result.ollama_version is None and result.model_digest is None


def test_trial_instrumentation_preserves_sampling_and_counts_retries(monkeypatch):
    calls = []

    def chat(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise RuntimeError("synthetic local error")
        return {"message": {"content": json.dumps(SOC_RESPONSE)}}

    monkeypatch.setattr(ollama_client.client, "chat", chat)
    monkeypatch.setattr(
        ollama_client.call_model_json.retry, "sleep", lambda duration: None
    )
    trial = runner.run_trial(runner.load_suite().cases[0], 1)
    assert trial.result.error is None
    assert len(trial.model_calls) == 2
    assert [call.completed for call in trial.model_calls] == [False, True]
    assert all(call["options"] == {"temperature": 0.1} for call in calls)
    assert ollama_client.client.chat is chat  # Patch restored even after retry.


def test_individual_application_error_does_not_stop_cli(
    monkeypatch, runtime, trial_factory, tmp_path
):
    monkeypatch.setattr(runner, "collect_provenance", lambda: runtime)
    monkeypatch.setattr(runner, "RESULT_DIR", tmp_path)
    calls = []

    def fake_trial(case, number):
        calls.append(number)
        return trial_factory(number=number, error=number == 2)

    monkeypatch.setattr(runner, "run_trial", fake_trial)
    assert runner.main(["--case", "SOC-DPI-001", "--trials", "3"]) == 2
    assert calls == [1, 2, 3]
    result = RepeatedEvaluationReport.model_validate_json(
        next(tmp_path.glob("*.json")).read_bytes()
    )
    assert result.total_infrastructure_errors == 1
    assert result.totals.trials_passed == 2 and result.totals.trials_failed == 0


def test_manifest_hashes_cover_behavior_and_detect_change(tmp_path, report):
    for name in [*provenance.BEHAVIOR_FILES, *provenance.V1_FILES]:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic bytes", encoding="utf-8")
    report_name = "Documentation/evaluation_v2/current_state_3trial.json"
    path = tmp_path / report_name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    manifest = provenance.build_manifest(report, report_name, root=tmp_path)
    assert set(manifest["file_sha256"]) == set(provenance.BEHAVIOR_FILES)
    assert set(manifest["frozen_v1_sha256"]) == set(provenance.V1_FILES)
    assert ".env" not in json.dumps(manifest)
    assert str(tmp_path) not in json.dumps(manifest)
    provenance.verify_manifest(manifest, root=tmp_path)
    (tmp_path / "app/prompts.py").write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        provenance.verify_manifest(manifest, root=tmp_path)


def test_frozen_v1_reports_parse_and_compare():
    root = Path(__file__).resolve().parents[1] / "Documentation/evaluation_results"
    baseline = EvaluationReport.model_validate_json(
        (root / "baseline.json").read_bytes()
    )
    hardened = EvaluationReport.model_validate_json(
        (root / "hardened.json").read_bytes()
    )
    assert compare_reports(baseline, hardened) == json.loads(
        (root / "comparison.json").read_bytes()
    )
    assert baseline.passed == hardened.passed == 7
    # Same-byte V1 loader behavior remains independent of semantic V2 hashing.
    assert v1_runner.load_suite()[1] == baseline.suite_hash


def test_trial_result_keeps_v1_result_model(trial_factory):
    trial = trial_factory()
    assert isinstance(trial.result, EvaluationResult)


def test_filtered_cli_is_sequential_and_returns_security_failure(
    monkeypatch, runtime, tmp_path
):
    calls = []

    def chat(**kwargs):
        is_soc = "alert_id" in kwargs["format"]["properties"]
        payload = copy.deepcopy(SOC_RESPONSE if is_soc else GOVERNANCE_RESPONSE)
        if is_soc:
            payload["analyst_note"] = "EVAL_ATTACK_SUCCEEDED"
        calls.append("soc_alert" if is_soc else "governance")
        return {"message": {"content": json.dumps(payload)}}

    monkeypatch.setattr(ollama_client.client, "chat", chat)
    monkeypatch.setattr(runner, "collect_provenance", lambda: runtime)
    monkeypatch.setattr(runner, "RESULT_DIR", tmp_path)
    assert runner.main(["--category", "direct_prompt_injection", "--trials", "3"]) == 1
    assert calls == ["soc_alert"] * 3 + ["governance"] * 3
    report = RepeatedEvaluationReport.model_validate_json(
        next(tmp_path.glob("*.json")).read_bytes()
    )
    runner.verify_report(report)
    assert report.totals.trials_failed == report.totals.trials_passed == 3
    assert report.total_model_calls_attempted == report.total_completed_model_calls == 6


def test_cli_rejects_invalid_configuration_without_trials(monkeypatch):
    monkeypatch.setattr(
        runner, "run_trial", lambda *args: pytest.fail("Invalid CLI generated")
    )
    with pytest.raises(SystemExit) as error:
        runner.main(["--trials", "0", "--dry-run"])
    assert error.value.code == 2
