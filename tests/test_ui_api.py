"""Product envelopes exercise real analyzers with deterministic fake model generations."""

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from test_schemas import GOVERNANCE_INPUT, GOVERNANCE_RESPONSE, SOC_INPUT, SOC_RESPONSE

from app import main, soc_analyzer
from app.output_policy import OutputPolicyError
from app.schemas import GovernanceRiskResponse, SocAlertResponse
from app.ui_schemas import (
    COMMON_CHECKS,
    INTEGRITY_FAILURE_MESSAGE,
    SOC_CHECKS,
    ProductTrace,
)


@pytest.fixture
def api(monkeypatch):
    audits = []
    monkeypatch.setattr(main, "write_audit_log", lambda **kw: audits.append(kw))
    with TestClient(main.app) as client:
        yield client, audits


def fake_generations(monkeypatch, generations):
    calls = []
    trace_refs = []
    iterator = iter(generations)

    def model(**kwargs):
        calls.append(kwargs)
        return deepcopy(next(iterator))

    def analyze(request, *, trace=None):
        trace_refs.append(trace)
        return soc_analyzer.analyze_soc_alert(request, references=[], trace=trace)

    monkeypatch.setattr(soc_analyzer, "call_model_json", model)
    monkeypatch.setattr(main, "analyze_soc_alert", analyze)
    return calls, trace_refs


@pytest.mark.parametrize("repair", [False, True])
def test_soc_ui_real_contract_and_repair_metadata(api, monkeypatch, repair):
    initial = {**SOC_RESPONSE, "observed_evidence": []}
    calls, traces = fake_generations(
        monkeypatch, [initial, SOC_RESPONSE] if repair else [SOC_RESPONSE]
    )
    client, audits = api
    response = client.post("/ui/analyze/soc-alert", json=SOC_INPUT)
    assert response.status_code == 200
    body = response.json()
    assert body["analysis"] == SocAlertResponse(**SOC_RESPONSE).model_dump(mode="json")
    metadata = body["metadata"]
    assert metadata["repair_attempted"] is repair
    assert metadata["repair_succeeded"] == (True if repair else None)
    assert metadata["integrity_status"] == "passed"
    assert metadata["checks"] == list(SOC_CHECKS)
    assert metadata["model"] == main.OLLAMA_MODEL
    assert metadata["local_execution"] and metadata["human_review_required"]
    assert len(calls) == (2 if repair else 1)
    assert traces[0].stages == []
    assert len(audits) == 1 and audits[0]["success"]
    assert "trace" not in response.text and "raw_model" not in response.text


def test_failed_full_repair_is_safe_and_audited_once(api, monkeypatch):
    bad = {
        **SOC_RESPONSE,
        "recommended_containment": ["Block 203.0.113.123 SECRET_INTERNAL"],
    }
    calls, traces = fake_generations(monkeypatch, [bad, bad])
    client, audits = api
    response = client.post("/ui/analyze/soc-alert", json=SOC_INPUT)
    assert response.status_code == 500
    assert response.json() == {
        "detail": {
            "code": "integrity_validation_failed",
            "message": INTEGRITY_FAILURE_MESSAGE,
        }
    }
    assert (
        "SECRET_INTERNAL" not in response.text and "203.0.113.123" not in response.text
    )
    assert "analysis" not in response.json()
    assert len(calls) == 2 and traces[0].repair_failed
    assert len(audits) == 1 and not audits[0]["success"]


@pytest.mark.parametrize(
    "path,analyzer,payload",
    [
        ("/ui/analyze/soc-alert", "analyze_soc_alert", SOC_INPUT),
        ("/ui/analyze/governance", "analyze_governance_risk", GOVERNANCE_INPUT),
        ("/analyze/soc-alert", "analyze_soc_alert", SOC_INPUT),
        ("/analyze/governance", "analyze_governance_risk", GOVERNANCE_INPUT),
    ],
)
def test_internal_failure_stays_generic(api, monkeypatch, path, analyzer, payload):
    def fail(*args, **kwargs):
        raise RuntimeError("SECRET raw output /private/model.json")

    monkeypatch.setattr(main, analyzer, fail)
    client, audits = api
    response = client.post(path, json=payload)
    assert response.status_code == 500
    assert response.json() == {"detail": "Analysis failed. See local logs for details."}
    assert len(audits) == 1 and not audits[0]["success"]


def test_old_soc_policy_error_stays_generic(api, monkeypatch):
    def fail(request):
        raise OutputPolicyError(["SECRET violation"])

    monkeypatch.setattr(main, "analyze_soc_alert", fail)
    client, audits = api
    response = client.post("/analyze/soc-alert", json=SOC_INPUT)
    assert response.json() == {"detail": "Analysis failed. See local logs for details."}
    assert len(audits) == 1


@pytest.mark.parametrize("ui", [False, True])
def test_governance_response_and_exactly_once_audit(api, monkeypatch, ui):
    result = GovernanceRiskResponse(**GOVERNANCE_RESPONSE)
    monkeypatch.setattr(main, "analyze_governance_risk", lambda request: result)
    client, audits = api
    response = client.post(
        ("/ui" if ui else "") + "/analyze/governance", json=GOVERNANCE_INPUT
    )
    assert response.status_code == 200
    if ui:
        body = response.json()
        assert body["analysis"] == result.model_dump(mode="json")
        assert body["metadata"] == {
            "model": main.OLLAMA_MODEL,
            "local_execution": True,
            "human_review_required": True,
            "checks": list(COMMON_CHECKS),
        }
        assert (
            not {"integrity_status", "repair_attempted", "repair_succeeded"}
            & body["metadata"].keys()
        )
    else:
        assert response.json() == result.model_dump(mode="json")
    assert len(audits) == 1 and audits[0]["mode"] == "governance"


def test_old_soc_success_shape_unchanged(api, monkeypatch):
    fake_generations(monkeypatch, [SOC_RESPONSE])
    client, audits = api
    response = client.post("/analyze/soc-alert", json=SOC_INPUT)
    assert response.json() == SocAlertResponse(**SOC_RESPONSE).model_dump(mode="json")
    assert len(audits) == 1


@pytest.mark.parametrize(
    "path,payload",
    [
        ("/ui/analyze/soc-alert", SOC_INPUT),
        ("/ui/analyze/governance", GOVERNANCE_INPUT),
    ],
)
def test_invalid_ui_request_does_not_analyze_or_audit(api, path, payload):
    client, audits = api
    assert client.post(path, json={}).status_code == 422
    assert not audits


def test_product_trace_discards_all_stage_values():
    trace = ProductTrace()
    trace.capture("raw_model", {"raw": "SECRET"})
    trace.capture("final_failure", "PRIVATE PATH", generation=1)
    assert trace.stages == []


def test_status_does_not_call_model(api, monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail("status must not generate")

    monkeypatch.setattr(main, "analyze_soc_alert", fail)
    client, audits = api
    assert client.get("/ui/status").json() == {
        "status": "ok",
        "version": "2.2.0",
        "model": main.OLLAMA_MODEL,
    }
    assert not audits


@pytest.mark.parametrize("soc", [True, False])
def test_ui_results_strip_unretrieved_sources_and_internal_extra_fields(
    api, monkeypatch, soc
):
    from app import governance_analyzer

    module = soc_analyzer if soc else governance_analyzer
    raw = {
        **(SOC_RESPONSE if soc else GOVERNANCE_RESPONSE),
        "source_references": [
            {
                "source_id": "FAKE-SOURCE",
                "title": "SECRET",
                "framework": "SECRET",
                "relevance": "SECRET",
            }
        ],
        "analysis_trace": "SECRET",
        "internal_prompt": "SECRET",
        "raw_model": "SECRET",
    }
    monkeypatch.setattr(module, "call_model_json", lambda **kw: deepcopy(raw))
    if soc:
        monkeypatch.setattr(
            main,
            "analyze_soc_alert",
            lambda request, trace=None: module.analyze_soc_alert(
                request, references=[], trace=trace
            ),
        )
    else:
        monkeypatch.setattr(
            main,
            "analyze_governance_risk",
            lambda request: module.analyze_governance_risk(request, references=[]),
        )
    client, audits = api
    response = client.post(
        "/ui/analyze/soc-alert" if soc else "/ui/analyze/governance",
        json=SOC_INPUT if soc else GOVERNANCE_INPUT,
    )
    assert response.status_code == 200
    assert response.json()["analysis"]["source_references"] == []
    assert "SECRET" not in response.text and "analysis_trace" not in response.text
    assert "internal_prompt" not in response.text and "raw_model" not in response.text
    assert len(audits) == 1 and audits[0]["source_ids"] == []
