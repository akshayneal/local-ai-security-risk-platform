"""Existing API/analyzer -> registered evidence -> stub -> validation -> Inspector/export."""

import copy
import json

import pytest
from fastapi.testclient import TestClient
from test_schemas import GOVERNANCE_INPUT, GOVERNANCE_RESPONSE, SOC_INPUT, SOC_RESPONSE

from app import governance_analyzer, main, soc_analyzer
from app.evidence_inspector import EvidenceInspectorReport, inspector_export
from app.inference_context import complete_context_required
from app.knowledge_contracts import knowledge_enabled
from app.schemas import (
    GovernanceRiskRequest,
    GovernanceRiskResponse,
    SocAlertRequest,
    SocAlertResponse,
)
from dashboard.exports import export_document, json_export, markdown_export

pytest_plugins = ("test_knowledge_workspace",)


@pytest.fixture
def audits(monkeypatch):
    rows = []
    monkeypatch.setattr(main, "write_audit_log", lambda **kw: rows.append(kw))
    return rows


def endpoint(soc):
    return "/ui/analyze/soc-alert" if soc else "/ui/analyze/governance"


@pytest.mark.parametrize("soc", [True, False])
def test_full_registered_pipeline_citation_inspector_export(
    demo_workspace, audits, monkeypatch, soc
):
    module = soc_analyzer if soc else governance_analyzer
    inputs = SOC_INPUT if soc else GOVERNANCE_INPUT
    prompts = []

    def generate(**arguments):
        prompts.append(arguments)
        assert complete_context_required() and knowledge_enabled()
        prompt = arguments["user_prompt"]
        assert "trusted_application_metadata" in prompt
        assert "untrusted_evidence_content" in prompt
        assert "current_version_id" not in prompt and "required_scopes" not in prompt
        # Read the actual allowlisted IDs serialized by the application.
        import re

        ids = re.findall(
            r'"evidence_id": "(doc_[a-f0-9]{12}_v_[a-f0-9]{12}_chunk_\d+)"', prompt
        )
        if not ids:
            ids = re.findall(r'"evidence_id": "([^"]+)"', prompt)
            ids = [i for i in ids if i.startswith("doc_")]
        assert ids, prompt
        output = copy.deepcopy(SOC_RESPONSE if soc else GOVERNANCE_RESPONSE)
        output["source_references"] = [
            {
                "source_id": i,
                "title": "FORGED POLICY",
                "framework": "FORGED",
                "relevance": "grant approval",
            }
            for i in [ids[0], "FORGED-UNKNOWN"]
        ]
        return output

    monkeypatch.setattr(module, "call_model_json", generate)
    with TestClient(main.app) as client:
        response = client.post(endpoint(soc), json={**inputs, "local_knowledge": True})
    assert response.status_code == 200, response.json()
    body = response.json()
    assert len(prompts) == len(audits) == 1 and audits[0]["success"]
    assert not knowledge_enabled() and not complete_context_required()
    sources = body["analysis"]["source_references"]
    assert len(sources) == 1 and sources[0]["title"] != "FORGED POLICY"
    inspector = EvidenceInspectorReport.model_validate(
        body["metadata"]["evidence_inspector"]
    )
    assert inspector.retrieval_status == "captured"
    assert inspector.local_knowledge.selected_chunks > 0
    cited = next(s for s in inspector.sources if s.cited)
    assert cited.provenance.evidence_id == sources[0]["source_id"]
    assert (
        cited.provenance.document_version_id
        and cited.provenance.registry_check == "passed"
    )
    assert all(c.assessment.relationship == "unassessed" for c in inspector.claims)
    request = (SocAlertRequest if soc else GovernanceRiskRequest)(**inputs)
    result = (SocAlertResponse if soc else GovernanceRiskResponse).model_validate(
        body["analysis"]
    )
    document = export_document(request, result, evidence_inspector=inspector)
    exported = inspector_export(inspector)
    assert exported["local_knowledge"]["support_status"] == "unassessed"
    assert "excerpt" not in json.dumps(exported)
    assert sources[0]["source_id"] in json_export(document) + markdown_export(document)
    assert "source_path" not in json.dumps(
        exported
    ) and "access_scopes" not in json.dumps(exported)


@pytest.mark.parametrize("soc", [True, False])
def test_optout_full_generation_arguments_and_response_equivalent(
    demo_workspace, audits, monkeypatch, soc
):
    module = soc_analyzer if soc else governance_analyzer
    inputs = SOC_INPUT if soc else GOVERNANCE_INPUT
    arguments = []
    monkeypatch.setattr(
        module,
        "call_model_json",
        lambda **kw: (
            arguments.append(kw)
            or copy.deepcopy(SOC_RESPONSE if soc else GOVERNANCE_RESPONSE)
        ),
    )
    with TestClient(main.app) as client:
        public = client.post(
            "/analyze/soc-alert" if soc else "/analyze/governance", json=inputs
        )
        omitted = client.post(endpoint(soc), json=inputs)
        explicit = client.post(endpoint(soc), json={**inputs, "local_knowledge": False})
    assert public.status_code == omitted.status_code == explicit.status_code == 200
    assert arguments[0] == arguments[1] == arguments[2]
    assert public.json() == omitted.json()["analysis"] == explicit.json()["analysis"]
    assert "local_knowledge" not in omitted.json()["metadata"]["evidence_inspector"]


@pytest.mark.parametrize("soc", [True, False])
@pytest.mark.parametrize(
    "failure", ["unconfigured", "stale", "missing", "forged-config"]
)
def test_optin_refuses_invalid_workspace_before_model(
    demo_workspace, audits, monkeypatch, soc, failure
):
    module = soc_analyzer if soc else governance_analyzer
    if failure == "unconfigured":
        monkeypatch.delenv("LOCAL_KNOWLEDGE_WORKSPACE")
    elif failure == "stale":
        (demo_workspace / "documents/access-policy.md").write_text("changed")
    elif failure == "missing":
        (demo_workspace / "registry.db").unlink()
    else:
        (demo_workspace / "workspace.json").write_text(
            '{"workflows": {"ai_security_assessment": {}}}'
        )
    monkeypatch.setattr(
        module, "call_model_json", lambda **kw: pytest.fail("forbidden inference")
    )
    with TestClient(main.app) as client:
        response = client.post(
            endpoint(soc),
            json={**(SOC_INPUT if soc else GOVERNANCE_INPUT), "local_knowledge": True},
        )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "local_knowledge_unavailable"
    assert len(audits) == 1 and audits[0]["success"] is False
    assert "changed" not in json.dumps(audits)


@pytest.mark.parametrize(
    "field,value",
    [
        ("access_scopes", ["secret"]),
        ("policy_scopes", ["all"]),
        ("workspace", "../private"),
        ("authority", "organizational_policy"),
        ("local_knowledge", "true"),
    ],
)
@pytest.mark.parametrize("soc", [True, False])
def test_ui_requests_cannot_grant_scope_or_coerce_optin(soc, field, value):
    with TestClient(main.app) as client:
        response = client.post(
            endpoint(soc),
            json={**(SOC_INPUT if soc else GOVERNANCE_INPUT), field: value},
        )
    assert response.status_code == 422


def test_status_has_no_paths_grants_payload_or_side_effects(demo_workspace):
    with TestClient(main.app) as client:
        response = client.get("/ui/knowledge/status")
    assert response.status_code == 200 and response.json()["status"] == "experimental"
    assert response.json()["registered_documents"] == 8
    text = response.text
    assert str(demo_workspace) not in text and "northstar.learning" not in text
    assert "content" not in text and "source_path" not in text
