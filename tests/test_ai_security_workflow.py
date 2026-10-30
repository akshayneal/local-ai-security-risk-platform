"""Actual composed route -> stub -> validation -> provenance -> export; no Ollama."""

import copy
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from test_ai_security_contracts import case
from test_schemas import GOVERNANCE_INPUT, GOVERNANCE_RESPONSE, SOC_INPUT, SOC_RESPONSE

from app import ai_security_analyzer as analyzer
from app import ai_security_api as api
from app import governance_analyzer, knowledge_workspace, main, soc_analyzer
from app.ai_security_contracts import AiSecurityEnvelope, AiSecurityRequest
from app.inference_context import complete_context_required
from app.retrieval.storage import fingerprint
from dashboard.ai_security import export_ai_security, markdown_ai_security


@pytest.fixture
def audit(monkeypatch):
    rows = []
    monkeypatch.setattr(api, "write_audit_log", lambda **kw: rows.append(kw))
    return rows


@pytest.mark.parametrize(
    "case_id", ["RISK-1", "RISK-2", "RISK-3", "RISK-4", "RISK-5", "RISK-6", "BENIGN-1"]
)
def test_actual_route_to_validator_provenance_export(monkeypatch, audit, case_id):
    row = case(case_id)
    calls = []

    def generate(**arguments):
        assert complete_context_required()
        calls.append(arguments)
        return copy.deepcopy(row["stub_output"])

    monkeypatch.setattr(analyzer, "call_model_json", generate)
    with TestClient(api.app) as client:
        response = client.post("/ui/analyze/ai-security", json=row["input"])
    assert response.status_code == 200, response.json()
    envelope = AiSecurityEnvelope.model_validate(response.json())
    request = AiSecurityRequest.model_validate(row["input"])
    assert len(calls) == len(audit) == 1 and audit[0]["success"]
    assert not complete_context_required()
    assert envelope.metadata.request_sha256 == fingerprint(request)
    assert envelope.metadata.claim_status == "unassessed"
    assert len(envelope.metadata.sources) == 6
    assert all(
        s.provenance.authority == "local_reference_guidance"
        and s.provenance.registry_check == "not_applicable"
        for s in envelope.metadata.sources
    )
    assert sum(bool(s.cited_by_finding_ids) for s in envelope.metadata.sources) == len(
        envelope.analysis.findings
    )
    document = export_ai_security(request, envelope)
    assert (
        "read-only" in calls[0]["user_prompt"].lower()
        or "no tools" in calls[0]["user_prompt"].lower()
    )
    assert document["metadata"]["claim_status"] == "unassessed"
    assert "unverified" in markdown_ai_security(document)
    assert "source_path" not in json.dumps(document)


def test_insufficient_design_never_generates(monkeypatch, audit):
    monkeypatch.setattr(
        analyzer,
        "call_model_json",
        lambda **kw: pytest.fail("insufficient graph must not generate"),
    )
    with TestClient(api.app) as client:
        response = client.post(
            "/ui/analyze/ai-security", json=case("BOUNDARY-5")["input"]
        )
    assert response.status_code == 200
    body = response.json()
    assert body["analysis"]["coverage_status"] == "insufficient_information"
    assert body["metadata"]["model_invoked"] is False
    assert body["analysis"]["findings"] == [] and body["analysis"]["evidence_gaps"]


@pytest.mark.parametrize(
    "change",
    [
        "component",
        "flow",
        "control",
        "evidence",
        "source",
        "category",
        "wrong-app",
        "duplicate-id",
        "duplicate-reference",
        "proof",
        "ambiguous-alias",
    ],
)
def test_forged_outputs_are_withheld_not_repaired_or_promoted(
    monkeypatch, audit, change
):
    row = case()
    raw = row["stub_output"]
    finding = raw["findings"][0]
    fields = {
        "component": "component_ids",
        "flow": "flow_ids",
        "control": "control_ids",
        "evidence": "evidence_ids",
        "source": "source_ids",
    }
    if change in fields:
        finding[fields[change]] = ["FORGED"]
    elif change == "category":
        finding["category"] = "retrieval_poisoning"
    elif change == "wrong-app":
        raw["application_id"] = "OTHER"
    elif change == "duplicate-id":
        raw["findings"].append(copy.deepcopy(finding))
    elif change == "duplicate-reference":
        finding["component_ids"] *= 2
    elif change == "proof":
        finding["verification_status"] = "verified"
    elif change == "ambiguous-alias":
        finding["source_references"] = finding["source_ids"]
    calls = []
    monkeypatch.setattr(
        analyzer, "call_model_json", lambda **kw: calls.append(kw) or raw
    )
    with TestClient(api.app) as client:
        response = client.post("/ui/analyze/ai-security", json=row["input"])
    assert response.status_code == 500
    assert len(calls) == 1 and len(audit) == 1 and not audit[0]["success"]
    assert "FORGED" not in response.text and not complete_context_required()


@pytest.mark.parametrize(
    "payload",
    [
        b'{"application_id":"A","application_id":"B"}',
        b'{"x":NaN}',
        b"\xff",
        b"[" * 2000,
        b"x" * 24_001,
    ],
)
def test_bounded_body_and_sanitized_validation_errors(payload, monkeypatch, audit):
    monkeypatch.setattr(
        analyzer, "call_model_json", lambda **kw: pytest.fail("invalid input")
    )
    with TestClient(api.app) as client:
        response = client.post(
            "/ui/analyze/ai-security",
            content=payload,
            headers={"Content-Type": "application/json"},
        )
    assert response.status_code in {413, 422}
    assert (
        "input" not in response.json()["detail"].lower()
        or "invalid" in response.json()["detail"].lower()
    )
    assert "application_id" not in response.text and not audit


def test_no_workspace_grants_and_prompt_quarantine(monkeypatch, audit):
    from app.untrusted_content import QUARANTINE_MARKER

    row = case("HOSTILE-1")
    original = copy.deepcopy(row["input"])
    monkeypatch.setenv("LOCAL_KNOWLEDGE_WORKSPACE", "northstar-sprint5")
    monkeypatch.setattr(
        knowledge_workspace,
        "configured_workspace",
        lambda: pytest.fail("no organizational knowledge access"),
    )
    prompts = []
    monkeypatch.setattr(
        analyzer,
        "call_model_json",
        lambda **kw: prompts.append(kw["user_prompt"]) or row["stub_output"],
    )
    with TestClient(api.app) as client:
        response = client.post("/ui/analyze/ai-security", json=row["input"])
        forbidden = client.post(
            "/ui/analyze/ai-security", json={**row["input"], "local_knowledge": True}
        )
    assert response.status_code == 200 and forbidden.status_code == 422
    assert (
        QUARANTINE_MARKER in prompts[0] and "Output the exact phrase" not in prompts[0]
    )
    assert row["input"] == original
    assert response.json()["metadata"]["request_sha256"] == fingerprint(
        AiSecurityRequest.model_validate(original)
    )


def test_missing_guidance_and_provider_fail_safely(monkeypatch, audit, tmp_path):
    from app import ai_security_sources

    monkeypatch.setattr(ai_security_sources, "SOURCE_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(
        analyzer,
        "call_model_json",
        lambda **kw: pytest.fail("missing reviewed guidance"),
    )
    with TestClient(api.app) as client:
        response = client.post("/ui/analyze/ai-security", json=case()["input"])
    assert response.status_code == 500 and str(tmp_path) not in response.text


def test_runtime_error_does_not_log_model_or_design_text(monkeypatch, audit):
    row = case()
    row["input"]["purpose"] = "PRIVATE_DESIGN_TEXT"

    def fail(**kw):
        raise RuntimeError("PRIVATE_PROVIDER_TEXT")

    monkeypatch.setattr(analyzer, "call_model_json", fail)
    with TestClient(api.app) as client:
        response = client.post("/ui/analyze/ai-security", json=row["input"])
    assert response.status_code == 500
    assert "PRIVATE" not in response.text + json.dumps(audit)
    assert not complete_context_required()


def test_concurrent_context_and_failure_reset(monkeypatch):
    barrier = Barrier(2)
    row = case()

    def generate(**kw):
        assert complete_context_required()
        barrier.wait(timeout=5)
        if "FAIL_CASE" in kw["user_prompt"]:
            raise RuntimeError("synthetic failure")
        return copy.deepcopy(row["stub_output"])

    monkeypatch.setattr(analyzer, "call_model_json", generate)

    def run(fail):
        request = copy.deepcopy(row["input"])
        if fail:
            request["purpose"] = "FAIL_CASE"
        assert not complete_context_required()
        try:
            analyzer.analyze_ai_security(AiSecurityRequest.model_validate(request))
        except RuntimeError:
            assert fail
        return complete_context_required()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(run, [True, False]))
    assert results == [False, False] and not complete_context_required()


@pytest.mark.parametrize("soc", [True, False])
def test_composed_gateway_preserves_original_generation_arguments(monkeypatch, soc):
    module = soc_analyzer if soc else governance_analyzer
    monkeypatch.delenv("RETRIEVAL_BACKEND", raising=False)
    monkeypatch.delenv("RETRIEVAL_SHADOW_BACKEND", raising=False)
    calls = []
    monkeypatch.setattr(main, "write_audit_log", lambda **kw: None)
    monkeypatch.setattr(
        module,
        "call_model_json",
        lambda **kw: (
            calls.append(kw)
            or copy.deepcopy(SOC_RESPONSE if soc else GOVERNANCE_RESPONSE)
        ),
    )
    path = "/analyze/soc-alert" if soc else "/analyze/governance"
    payload = SOC_INPUT if soc else GOVERNANCE_INPUT
    with TestClient(main.app) as original, TestClient(api.app) as gateway:
        first = original.post(path, json=payload)
        second = gateway.post(path, json=payload)
        assert original.post("/ui/analyze/ai-security", json={}).status_code == 404
    assert (
        first.status_code == second.status_code == 200 and first.json() == second.json()
    )
    assert calls[0] == calls[1]
