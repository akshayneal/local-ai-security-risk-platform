"""Provider contract, trust boundary and prompt regressions; no semantic oracle."""

import copy
import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import ai_security_analyzer as analyzer
from app import ai_security_api as api
from app.ai_security_contracts import AiSecurityRequest, AiSecurityResponse
from app.inference_context import complete_context_required
from app.prompts import SYSTEM_PROMPT, build_governance_prompt, build_soc_prompt
from app.schemas import GovernanceRiskRequest, SocAlertRequest

pytest_plugins = ("test_knowledge_workspace",)


def design():
    return AiSecurityRequest(
        application_id="UNIT-S8",
        application_name="Synthetic unit design",
        purpose="Test declared boundaries only.",
        components=(
            {"id": "INPUT", "kind": "user_interface", "description": "Untrusted input"},
            {"id": "MODEL", "kind": "model", "description": "Draft model"},
        ),
        flows=(
            {
                "id": "FLOW",
                "source_id": "INPUT",
                "target_id": "MODEL",
                "classification": "public",
                "boundary_crossing": "unknown",
                "description": "Submitted text enters model",
            },
        ),
    )


def output(kind="candidate"):
    findings = [
        {
            "finding_id": "F1",
            "category": "prompt_injection",
            "component_ids": ["INPUT", "MODEL"],
            "flow_ids": ["FLOW"],
            "hypothesis": "Untrusted text may influence generation if separation fails.",
            "prerequisites": ["Instruction separation fails."],
            "possible_impact": "Incorrect drafts.",
            "proposed_mitigations": ["Separate instructions and text."],
            "validation_recommendations": ["Test synthetic role claims."],
            "missing_evidence": ["Separation tests."],
            "source_references": ["AISEC-V1-PROMPT-INJECTION"],
        }
    ]
    return {
        "application_id": "UNIT-S8",
        "coverage_status": "insufficient_information"
        if kind == "insufficient"
        else "advisory_returned",
        "summary": "Unverified synthetic design review.",
        "findings": findings if kind == "candidate" else [],
        "evidence_gaps": ["No control verification supplied."],
        "human_review_requirements": ["Human review required."],
    }


def test_decoder_schema_encodes_both_publicly_valid_variants():
    from app.ai_security_contracts import generation_schema, validate_generation

    schema = generation_schema()
    variants = [schema["$defs"][s["$ref"].split("/")[-1]] for s in schema["anyOf"]]
    by_status = {v["properties"]["coverage_status"]["const"]: v for v in variants}
    assert set(by_status) == {"advisory_returned", "insufficient_information"}
    assert (
        by_status["insufficient_information"]["properties"]["findings"]["maxItems"] == 0
    )
    assert (
        by_status["insufficient_information"]["properties"]["evidence_gaps"]["minItems"]
        == 1
    )
    assert by_status["advisory_returned"]["properties"]["findings"]["maxItems"] == 12
    for kind in ("candidate", "benign", "insufficient"):
        raw = output(kind)
        assert validate_generation(raw) == AiSecurityResponse.model_validate(raw)
    bad = output()
    bad["coverage_status"] = "insufficient_information"
    with pytest.raises(ValidationError):
        validate_generation(bad)
    with pytest.raises(ValidationError):
        AiSecurityResponse.model_validate(
            bad
        )  # Original public boundary remains strict.


@pytest.mark.parametrize("kind", ["candidate", "benign", "insufficient"])
def test_real_api_uses_visible_variant_contract_and_preserves_raw_status(
    monkeypatch, kind
):
    calls, audits = [], []
    raw = output(kind)

    def generate(**kwargs):
        assert complete_context_required()
        assert "anyOf" in kwargs["response_schema"]
        assert "Missing implementation proof" in kwargs["user_prompt"]
        calls.append(kwargs)
        return copy.deepcopy(raw)

    monkeypatch.setattr(analyzer, "call_model_json", generate)
    monkeypatch.setattr(api, "write_audit_log", lambda **row: audits.append(row))
    with TestClient(api.app) as client:
        response = client.post(
            "/ui/analyze/ai-security", json=design().model_dump(mode="json")
        )
    assert response.status_code == 200
    body = response.json()
    assert body["analysis"]["coverage_status"] == raw["coverage_status"]
    expected = [
        f.model_dump(mode="json")
        for f in AiSecurityResponse.model_validate(raw).findings
    ]
    assert body["analysis"]["findings"] == expected
    assert len(calls) == len(audits) == 1 and audits[0]["success"]
    assert body["metadata"]["claim_status"] == "unassessed"
    assert not complete_context_required()


@pytest.mark.parametrize(
    "fault",
    [
        "contradiction",
        "component",
        "flow",
        "source",
        "category",
        "alias",
        "identity",
        "approval",
    ],
)
def test_hostile_or_contradictory_external_outputs_still_withheld(monkeypatch, fault):
    raw = output()
    if fault == "contradiction":
        raw["coverage_status"] = "insufficient_information"
    elif fault == "identity":
        raw["application_id"] = "OTHER"
    elif fault == "approval":
        raw["verification_status"] = "verified"
    elif fault == "component":
        raw["findings"][0]["component_ids"] = ["UNKNOWN"]
    elif fault == "flow":
        raw["findings"][0]["component_ids"] = ["MODEL"]
    elif fault == "source":
        raw["findings"][0]["source_references"] = ["FORGED"]
    elif fault == "category":
        raw["findings"][0]["category"] = "retrieval_poisoning"
    else:
        raw["findings"][0]["source_ids"] = ["FORGED"]
    audits = []
    monkeypatch.setattr(analyzer, "call_model_json", lambda **kwargs: raw)
    monkeypatch.setattr(api, "write_audit_log", lambda **row: audits.append(row))
    with TestClient(api.app) as client:
        response = client.post(
            "/ui/analyze/ai-security", json=design().model_dump(mode="json")
        )
    assert response.status_code == 500 and response.json() == {"detail": api.WITHHELD}
    assert len(audits) == 1 and not audits[0]["success"]
    assert "FORGED" not in json.dumps(audits) and "hypothesis" not in response.text
    assert not complete_context_required()


def test_three_workflows_and_task_rules_preserve_unknown_and_positive_inputs():
    assert "3. Technical AI Security" in SYSTEM_PROMPT
    soc = SocAlertRequest(
        alert_id="UNIT-SOC",
        alert_type="Synthetic observation",
        source_system="Lab record",
        affected_asset="unit-host",
        raw_log="Inventory match established within lab record; containment approval absent.",
    )
    gov = GovernanceRiskRequest(
        system_name="Unit draft",
        system_purpose="Low-impact public drafts.",
        human_review_process="Review proposed; logging reported implemented; gate explicitly absent.",
    )
    soc_prompt, gov_prompt = build_soc_prompt(soc, ""), build_governance_prompt(gov, "")
    assert "Unknown inventory does not establish a mismatch" in soc_prompt
    assert "An observed pattern is not established attacker intent" in soc_prompt
    assert (
        "Missing implementation evidence does not establish control absence"
        in gov_prompt
    )
    for prompt, request in [(soc_prompt, soc), (gov_prompt, gov)]:
        serialized = prompt.split("BEGIN UNTRUSTED USER INPUT\n")[1].split(
            "\nEND UNTRUSTED USER INPUT"
        )[0]
        assert json.loads(serialized) == request.model_dump(mode="json")
        assert "exact envelope evidence_id" in prompt
    # This proves instruction/input framing, NOT arbitrary model adherence.


@pytest.mark.parametrize("logical_id", [False, True])
def test_relevant_registered_chunk_citation_is_version_bound(
    demo_workspace, monkeypatch, logical_id
):
    from app import governance_analyzer, knowledge_workspace, main

    workspace = knowledge_workspace.load_workspace("demo")
    record = next(r for r in workspace.records if r.source_path == "access-policy.md")
    request = GovernanceRiskRequest(
        system_name="Synthetic Northstar catalog RAG unit test",
        system_purpose="Review learning-unit document eligibility before retrieval and human review before operational use.",
    )

    def generate(**kwargs):
        assert f'"evidence_id": "{record.evidence_id}"' in kwargs["user_prompt"]
        assert "learning-unit document eligibility" in record.content
        return {
            "system_name": request.system_name,
            "risk_level": "medium",
            "decision": "needs_review",
            "summary": "The supplied policy requires eligible retrieval and human review; implementation and approval remain unverified.",
            "key_risks": [],
            "required_controls": ["Review eligible retrieval and human oversight."],
            "human_review_requirements": ["Human review before operational use."],
            "logging_requirements": [],
            "evidence_gaps": ["No implementation or approval evidence supplied."],
            "recommended_next_steps": [],
            "source_references": [
                {
                    "source_id": record.source_id if logical_id else record.evidence_id,
                    "title": "FORGED",
                    "framework": "FORGED",
                    "relevance": "untrusted",
                }
            ],
        }

    monkeypatch.setattr(governance_analyzer, "call_model_json", generate)
    monkeypatch.setattr(main, "write_audit_log", lambda **row: None)
    with TestClient(api.app) as client:
        response = client.post(
            "/ui/analyze/governance",
            json={**request.model_dump(), "local_knowledge": True},
        )
    assert response.status_code == 200
    body = response.json()
    sources = body["analysis"]["source_references"]
    assert len(sources) == (0 if logical_id else 1)
    if sources:
        assert sources[0]["source_id"] == record.evidence_id
        assert sources[0]["title"] != "FORGED"
        assert record.document_version_id in sources[0]["relevance"]
    inspector = body["metadata"]["evidence_inspector"]
    assert inspector["local_knowledge"]["support_status"] == "unassessed"
    assert sum(s["cited"] for s in inspector["sources"]) == len(sources)


def test_incomplete_design_does_not_invoke_provider(monkeypatch):
    monkeypatch.setattr(
        analyzer,
        "call_model_json",
        lambda **kwargs: pytest.fail("incomplete graph generated"),
    )
    request = AiSecurityRequest(
        application_id="UNIT-EMPTY",
        application_name="Synthetic missing design",
        purpose="No architecture supplied.",
    )
    result = analyzer.analyze_ai_security(request)
    assert not result.metadata.model_invoked
    assert result.analysis.coverage_status == "insufficient_information"
    assert not result.analysis.findings and result.analysis.evidence_gaps
