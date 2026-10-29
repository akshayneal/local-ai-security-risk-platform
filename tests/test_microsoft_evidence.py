import json
from copy import deepcopy

import pytest
from test_schemas import SOC_INPUT, SOC_RESPONSE

from app import soc_analyzer
from app.microsoft_evidence import microsoft_evidence, port_number
from app.observables import endpoint_violations
from app.output_policy import (
    SOC_FACTUAL_FIELDS,
    OutputPolicyError,
    soc_contract_violations,
)
from app.soc_inputs import MicrosoftSocAdapter, SocInputError


@pytest.fixture
def original():
    return (
        MicrosoftSocAdapter()
        .normalize(
            {
                "case_id": "SYN-ENDPOINT",
                "tables": {
                    "DeviceNetworkEvents": [
                        {
                            "LocalIP": "192.0.2.31",
                            "LocalPort": 50131,
                            "RemoteIP": "203.0.113.31",
                            "RemotePort": "00443",
                        },
                        {
                            "LocalIP": "192.0.2.32",
                            "LocalPort": 50132,
                            "RemoteIP": "203.0.113.32",
                            "RemotePort": 8443,
                            "Protocol": "Tcp",
                        },
                    ]
                },
            }
        )
        .request.model_dump(mode="json")
    )


@pytest.mark.parametrize("field", SOC_FACTUAL_FIELDS)
@pytest.mark.parametrize(
    "text",
    [
        "203.0.113.31:443",
        "192.0.2.31:50131",
        "RemoteIP=203.0.113.31 RemotePort=443",
        '{"RemotePort":443,"RemoteIP":"203.0.113.31"}',
    ],
)
def test_valid_representations_now_succeed_in_all_protected_fields(
    original, field, text
):
    response = deepcopy(SOC_RESPONSE)
    response[field] = [text] if isinstance(response.get(field, []), list) else text
    assert not soc_contract_violations(response, original)
    if text == "203.0.113.31:443":
        assert endpoint_violations(text, original["raw_log"], field=field)


@pytest.mark.parametrize(
    "text",
    [
        "203.0.113.31:8443",
        "203.0.113.31:50131",
        "203.0.113.99:443",
        "remote IP 192.0.2.31",
        "192.0.2.31 (remote)",
        "LocalIP=192.0.2.31 LocalPort=443",
        '{"RemoteIP":"192.0.2.31","RemotePort":50131}',
        '{"LocalIP":"192.0.2.31","LocalPort":50131,"RemoteIP":"203.0.113.32","RemotePort":8443}',
        '{"RemoteIP":"203.0.113.31","RemotePort":8443}',
        '{"RemoteIP":"203.0.113.31","RemotePort":443,"RemotePort":8443}',
    ],
)
def test_role_pair_and_row_mutations_reject(original, text):
    response = {**SOC_RESPONSE, "observed_evidence": [text]}
    assert soc_contract_violations(response, original)


def test_inventory_exact_values_missing_protocol_and_no_selection(original):
    evidence = microsoft_evidence(original)
    inventory = evidence.inventory()
    assert inventory["original_rows"] == len(inventory["records"]) == 2
    assert inventory["selection"].startswith("none")
    first, second = inventory["records"]
    assert first["observed_fields"]["RemotePort"] == "00443"
    assert "Protocol" not in first["observed_fields"]
    assert second["observed_fields"]["Protocol"] == "Tcp"
    assert json.loads(original["raw_log"]) == evidence.bundle
    assert evidence.pairs("remote") == {("203.0.113.31", 443), ("203.0.113.32", 8443)}
    assert evidence.pairs("local") == {("192.0.2.31", 50131), ("192.0.2.32", 50132)}


@pytest.mark.parametrize(
    "value", [True, False, 443.0, -1, 65536, " 443", "443 ", "-1", None, {}, []]
)
def test_malformed_port_never_authorizes_pair(value):
    assert port_number(value) is None


@pytest.mark.parametrize(
    "value,expected", [(0, 0), (65535, 65535), ("00443", 443), ("0", 0)]
)
def test_observed_numeric_port_formats(value, expected):
    assert port_number(value) == expected


def test_malformed_or_mismatched_profile_fails_closed(original):
    with pytest.raises(SocInputError):
        microsoft_evidence({**original, "raw_log": '{"case_id":"X","tables":{}}'})
    with pytest.raises(ValueError, match="identity"):
        microsoft_evidence({**original, "alert_id": "different"})
    assert microsoft_evidence(SOC_INPUT) is None


def test_full_validation_after_one_repair_and_source_identity_fidelity(
    monkeypatch, original
):
    from app.analysis_trace import AnalysisTrace
    from app.schemas import SocAlertRequest

    initial = {**SOC_RESPONSE, "observed_evidence": ["203.0.113.31:8443"]}
    repair = {
        **SOC_RESPONSE,
        "observed_evidence": ["203.0.113.31:443"],
        "analyst_note": "Investigate 203.0.113.31:8443",
    }
    calls = []

    def model(**kw):
        calls.append(kw)
        return deepcopy(initial if len(calls) == 1 else repair)

    monkeypatch.setattr(soc_analyzer, "call_model_json", model)
    trace = AnalysisTrace()
    with pytest.raises(OutputPolicyError):
        soc_analyzer.analyze_soc_alert(
            SocAlertRequest(**original), references=[], trace=trace
        )
    assert len(calls) == 2 and trace.repair_failed
    assert '["203.0.113.31", 443]' in calls[1]["user_prompt"]
    assert not any(s["stage"] == "final_response" for s in trace.stages)


def test_previously_rejected_valid_pair_returns_without_repair(monkeypatch, original):
    from app.analysis_trace import AnalysisTrace
    from app.schemas import SocAlertRequest

    payload = {
        **SOC_RESPONSE,
        "summary": "Remote endpoint 203.0.113.31:443; protocol unknown",
        "observed_evidence": ['{"RemoteIP":"203.0.113.31","RemotePort":443}'],
    }
    monkeypatch.setattr(soc_analyzer, "call_model_json", lambda **kw: deepcopy(payload))
    trace = AnalysisTrace()
    response = soc_analyzer.analyze_soc_alert(
        SocAlertRequest(**original), references=[], trace=trace
    )
    assert response.summary == payload["summary"]
    assert not trace.repair_attempted


def test_microsoft_path_preserves_critical_identity_checks(original):
    bundle = json.loads(original["raw_log"])
    bundle["tables"]["DeviceProcessEvents"] = [
        {"SHA256": "a9" * 32, "ActionType": "ProcessCreated"}
    ]
    request = MicrosoftSocAdapter().normalize(bundle).request.model_dump(mode="json")
    valid = {**SOC_RESPONSE, "observed_evidence": ["a9" * 32, "203.0.113.31:443"]}
    assert not soc_contract_violations(valid, request)
    for bad in ("b9" * 32, "203.0.113.131:443"):
        assert soc_contract_violations(
            {**valid, "recommended_investigation_steps": [bad]}, request
        )
