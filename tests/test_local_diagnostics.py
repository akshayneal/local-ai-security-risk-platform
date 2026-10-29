import json
from copy import deepcopy

import pytest
from test_schemas import SOC_INPUT, SOC_RESPONSE

from app import soc_analyzer
from app.local_diagnostics import LocalDiagnosticTrace, violation_code
from app.output_policy import OutputPolicyError
from app.schemas import SocAlertRequest
from app.ui_schemas import ProductTrace


@pytest.mark.parametrize(
    "outcomes,repair_failed",
    [([False, False], True), ([False, True], False), ([True], False)],
)
def test_bounded_safe_diagnostics(monkeypatch, outcomes, repair_failed):
    marker = "SECRET-TENANT-CREDENTIAL-INJECTION-C:\\private"
    outputs = []
    for valid in outcomes:
        payload = deepcopy(SOC_RESPONSE)
        payload["summary"] = marker
        if not valid:
            payload["observed_evidence"] = []
        outputs.append(payload)
    monkeypatch.setattr(soc_analyzer, "call_model_json", lambda **kw: outputs.pop(0))
    trace = LocalDiagnosticTrace(marker)
    try:
        result = soc_analyzer.analyze_soc_alert(
            SocAlertRequest(**SOC_INPUT), references=[], trace=trace
        )
        assert not repair_failed
        assert "diagnostic" not in result.model_dump_json()
    except OutputPolicyError:
        assert repair_failed
    report = trace.report()
    assert marker not in json.dumps(report)
    assert trace.repair_attempted == (len(outcomes) == 2)
    assert trace.repair_failed == repair_failed
    assert trace.stages[-1]["status"] == ("withheld" if repair_failed else "accepted")
    validations = [e for e in trace.stages if e["stage"] == "validation"]
    assert len(validations) == len(outcomes)
    assert validations[0]["observations"] == ("passed" if outcomes[0] else "failed")


@pytest.mark.parametrize(
    "payload,code",
    [(None, "SOURCE_PROCESSING"), ({}, "SCHEMA"), ([], "SOURCE_PROCESSING")],
)
def test_malformed_output(monkeypatch, payload, code):
    monkeypatch.setattr(soc_analyzer, "call_model_json", lambda **kw: deepcopy(payload))
    trace = LocalDiagnosticTrace("synthetic")
    with pytest.raises(OutputPolicyError):
        soc_analyzer.analyze_soc_alert(
            SocAlertRequest(**SOC_INPUT), references=[], trace=trace
        )
    assert code in {v["code"] for e in trace.stages for v in e.get("violations", [])}


def test_generation_failure_has_no_exception_payload(monkeypatch):
    def fail(**kw):
        raise ValueError("sensitive raw output")

    monkeypatch.setattr(soc_analyzer, "call_model_json", fail)
    trace = LocalDiagnosticTrace("synthetic")
    with pytest.raises(ValueError):
        soc_analyzer.analyze_soc_alert(
            SocAlertRequest(**SOC_INPUT), references=[], trace=trace
        )
    assert trace.stages[-1]["status"] == "withheld"
    assert "sensitive" not in json.dumps(trace.report())


def test_allowlisted_codes_and_ignored_payloads():
    assert violation_code(
        "summary contains an endpoint relationship absent from the original request"
    ) == {"code": "ENDPOINT_PAIR", "field": "summary"}
    assert (
        violation_code(
            "SECRET contains an endpoint relationship absent from the original request"
        )["code"]
        == "UNCLASSIFIED"
    )
    trace = LocalDiagnosticTrace("secret")
    for stage in ("raw_model", "final_response", "citation_cleaned", "secret"):
        trace.capture(stage, {"secret": "secret"})
    assert trace.stages == []
    for _ in range(50):
        trace.capture("generation_started", None)
    assert len(trace.stages) == 16
    product = ProductTrace()
    product.capture("policy_violations", ["secret"])
    assert product.stages == []


def test_disabled_by_default(monkeypatch):
    monkeypatch.setattr(
        LocalDiagnosticTrace,
        "capture",
        lambda *a, **kw: pytest.fail("unexpected diagnostics"),
    )
    monkeypatch.setattr(
        soc_analyzer, "call_model_json", lambda **kw: deepcopy(SOC_RESPONSE)
    )
    soc_analyzer.analyze_soc_alert(SocAlertRequest(**SOC_INPUT), references=[])
