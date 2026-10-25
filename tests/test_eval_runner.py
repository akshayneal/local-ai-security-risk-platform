import json

import pytest
from test_schemas import SOC_RESPONSE

from app.schemas import SocAlertResponse
from evals import runner


def test_filtering_and_empty_selection():
    suite, _ = runner.load_suite()
    assert [c.test_id for c in runner.select_cases(suite, case_id="SOC-DPI-001")] == [
        "SOC-DPI-001"
    ]
    assert len(runner.select_cases(suite, category="direct_prompt_injection")) == 2
    with pytest.raises(ValueError, match="No cases"):
        runner.select_cases(suite, case_id="MISSING")


def test_real_reference_resolution_and_override(monkeypatch):
    case = runner.load_suite()[0].cases[0]
    calls = []
    reference = {"source_id": "REAL-ID"}
    monkeypatch.setattr(
        runner, "get_relevant_references", lambda **kw: calls.append(kw) or [reference]
    )
    monkeypatch.setattr(
        runner,
        "analyze_soc_alert",
        lambda request, *, references: (
            calls.append(references) or SocAlertResponse(**SOC_RESPONSE)
        ),
    )
    result = runner.run_case(case)
    assert result.passed
    assert result.provided_source_ids == ["REAL-ID"]
    assert calls[0]["limit"] == 5
    assert json.loads(calls[0]["query"])["raw_log"] == case.input["raw_log"]
    assert calls[1] == [reference]
    calls.clear()
    runner.run_case(case.model_copy(update={"reference_overrides": []}))
    assert calls == [[]]  # Explicit empty overrides must not trigger retrieval.


def test_governance_limit_and_real_analyzer_seam(monkeypatch):
    from test_schemas import GOVERNANCE_RESPONSE

    from app import governance_analyzer, soc_analyzer
    from app.schemas import GovernanceRiskRequest, SocAlertRequest

    suite = runner.load_suite()[0]
    for module, case, analyzer, request_type, payload, limit in [
        (
            soc_analyzer,
            suite.cases[0],
            soc_analyzer.analyze_soc_alert,
            SocAlertRequest,
            SOC_RESPONSE,
            5,
        ),
        (
            governance_analyzer,
            suite.cases[1],
            governance_analyzer.analyze_governance_risk,
            GovernanceRiskRequest,
            GOVERNANCE_RESPONSE,
            6,
        ),
    ]:
        calls = []
        monkeypatch.setattr(
            module,
            "get_relevant_references",
            lambda calls=calls, **kw: calls.append(kw) or [],
        )
        monkeypatch.setattr(
            module, "call_model_json", lambda payload=payload, **kw: payload.copy()
        )
        request = request_type.model_validate(case.input)
        analyzer(request)
        assert calls[0]["limit"] == limit
        calls.clear()
        analyzer(request, references=[])
        assert calls == []


def test_error_isolation_and_aggregation(monkeypatch):
    cases = runner.load_suite()[0].cases[:2]

    def fail(*args, **kwargs):
        raise RuntimeError("sensitive local details")

    monkeypatch.setattr(runner, "analyze_soc_alert", fail)
    monkeypatch.setattr(runner, "analyze_governance_risk", fail)
    results = [runner.run_case(case) for case in cases]
    assert len(results) == 2
    assert all(not r.passed and "sensitive" not in r.error for r in results)
    results[1].passed = True
    report = runner.build_report(results, "hash")
    assert (report.passed, report.failed, report.pass_rate) == (1, 1, 50)
    assert report.category_summary["direct_prompt_injection"].total == 2
    assert report.severity_summary["high"].passed == 1


def test_cli_writes_report_and_returns_security_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "RESULT_DIR", tmp_path)

    def fail(*args, **kwargs):
        raise ValueError("model error")

    monkeypatch.setattr(runner, "analyze_soc_alert", fail)
    assert runner.main(["--case", "SOC-DPI-001"]) == 1
    reports = list(tmp_path.glob("*.json"))
    assert len(reports) == 1
    assert json.loads(reports[0].read_text())["total_cases"] == 1
