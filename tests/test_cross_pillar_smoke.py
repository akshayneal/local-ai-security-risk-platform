"""Reproducible software acceptance: UI -> gateway -> real analyzers -> stub -> export.

Run: python -B -m pytest -q -p no:cacheprovider tests/test_cross_pillar_smoke.py
No service, browser, provider or user workspace is involved.
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests
from fastapi.testclient import TestClient
from sprint9_history import historical_test as sprint9_historical_test
from streamlit.testing.v1 import AppTest

from app import (
    ai_security_analyzer,
    ai_security_api,
    governance_analyzer,
    main,
    soc_analyzer,
)
from app.ai_security_contracts import AiSecurityEnvelope
from app.ui_schemas import GovernanceAnalysisEnvelope, SocAnalysisEnvelope
from dashboard.sample_loader import load_governance_samples, load_soc_samples

ROOT = Path(__file__).resolve().parents[1]


def test_composed_gateway_routes_are_a_compatible_superset():
    with TestClient(ai_security_api.app) as gateway, TestClient(main.app) as old:
        original = old.get("/openapi.json").json()["paths"]
        combined = gateway.get("/openapi.json").json()["paths"]
        assert {
            "/analyze/soc-alert",
            "/analyze/governance",
            "/ui/analyze/soc-alert",
            "/ui/analyze/governance",
        } <= original.keys()
        assert all(combined[path] == methods for path, methods in original.items())
        assert "/ui/analyze/ai-security" in combined
        assert old.post("/ui/analyze/ai-security", json={}).status_code == 404
        assert gateway.get("/health").json() == old.get("/health").json()


def test_contradictory_model_coverage_is_withheld_without_error_disclosure(monkeypatch):
    """Observed live failure shape; preserve rejection rather than invent success."""
    from app.ai_security_sources import load_guidance

    hits, categories = load_guidance()
    source = hits[0].record.evidence_id
    raw = {
        "application_id": "SYN-RAG",
        "coverage_status": "insufficient_information",
        "summary": "Synthetic inconsistent coverage",
        "human_review_requirements": ["Human review required."],
        "evidence_gaps": ["Implementation is unverified."],
        "findings": [
            {
                "finding_id": "F1",
                "category": categories[source],
                "component_ids": ["C_MODEL"],
                "hypothesis": "Synthetic candidate.",
                "prerequisites": ["Review declared input path."],
                "possible_impact": "Unverified impact.",
                "proposed_mitigations": ["Review controls."],
                "validation_recommendations": ["Use synthetic controls."],
                "missing_evidence": ["No control test supplied."],
                "source_references": [source],
            }
        ],
    }
    audits = []
    monkeypatch.setattr(ai_security_analyzer, "call_model_json", lambda **kwargs: raw)
    monkeypatch.setattr(
        ai_security_api, "write_audit_log", lambda **row: audits.append(row)
    )
    sample = json.loads(
        (ROOT / "sample_data/ai_security_demo_v1/rag.json").read_bytes()
    )
    with TestClient(ai_security_api.app) as client:
        result = client.post("/ui/analyze/ai-security", json=sample)
    assert result.status_code == 500
    assert result.json() == {"detail": ai_security_api.WITHHELD}
    assert "analysis" not in result.json() and "Synthetic candidate" not in result.text
    assert len(audits) == 1 and audits[0]["success"] is False


@pytest.mark.parametrize(
    "pillar,page,button,endpoint",
    [
        ("soc", "soc_investigation", "Analyze SOC alert", "/ui/analyze/soc-alert"),
        (
            "ai_safety",
            "ai_system_risk_review",
            "Review AI system",
            "/ui/analyze/governance",
        ),
        (
            "ai_security",
            "ai_security_assessment",
            "Assess AI security",
            "/ui/analyze/ai-security",
        ),
    ],
)
@sprint9_historical_test
def test_three_frontend_backend_paths(monkeypatch, pillar, page, button, endpoint):
    audits, calls = [], []
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:8235")
    monkeypatch.setenv("RETRIEVAL_BACKEND", "legacy")
    monkeypatch.delenv("RETRIEVAL_SHADOW_BACKEND", raising=False)
    monkeypatch.delenv("LOCAL_KNOWLEDGE_WORKSPACE", raising=False)
    monkeypatch.setattr(main, "write_audit_log", lambda **row: audits.append(row))
    monkeypatch.setattr(
        ai_security_api, "write_audit_log", lambda **row: audits.append(row)
    )

    def stub(**kwargs):
        assert "user_prompt" in kwargs and "response_schema" in kwargs
        if pillar == "soc":
            sample = load_soc_samples()[0]
            return {
                "alert_id": sample.alert_id,
                "severity": "medium",
                "likely_incident_type": "Unverified authentication anomaly",
                "summary": sample.raw_log,
                "observed_evidence": [sample.raw_log],
                "analyst_inferences": [
                    "Credential misuse is a hypothesis requiring investigation."
                ],
                "evidence_gaps": ["MFA and approval evidence are missing."],
                "recommended_containment": [
                    "Seek owner approval before any containment."
                ],
                "recommended_investigation_steps": ["Verify source ownership."],
                "false_positive_considerations": ["Authorized user retry is possible."],
                "mitre_mapping": [],
                "analyst_note": "Human review required.",
                "source_references": [],
            }
        if pillar == "ai_safety":
            return {
                "system_name": load_governance_samples()[0].system_name,
                "risk_level": "medium",
                "decision": "needs_review",
                "summary": "Synthetic draft support; no deployment approval.",
                "key_risks": ["Drafts can be unsupported."],
                "required_controls": ["Check drafts against evidence."],
                "human_review_requirements": ["Reviewer decides."],
                "logging_requirements": ["Determine retention policy."],
                "evidence_gaps": ["No implementation test supplied."],
                "recommended_next_steps": ["Review before deployment."],
                "source_references": [],
            }
        sample = json.loads(
            (ROOT / "sample_data/ai_security_demo_v1/rag.json").read_bytes()
        )
        return {
            "application_id": sample["application_id"],
            "coverage_status": "advisory_returned",
            "summary": "Synthetic software stub; all claims remain unverified.",
            "findings": [],
            "evidence_gaps": ["No control verification was performed."],
            "human_review_requirements": ["Review declared design."],
        }

    for module in (soc_analyzer, governance_analyzer, ai_security_analyzer):
        monkeypatch.setattr(module, "call_model_json", stub)

    def post(url, *, json, timeout):
        assert url == "http://127.0.0.1:8235" + endpoint
        assert timeout == 300
        calls.append(json)
        with TestClient(ai_security_api.app) as client:
            response = client.post(endpoint, json=json)
        model = {
            "soc": SocAnalysisEnvelope,
            "ai_safety": GovernanceAnalysisEnvelope,
            "ai_security": AiSecurityEnvelope,
        }[pillar]
        assert response.status_code == 200, response.json()
        model.model_validate(response.json())
        return SimpleNamespace(ok=True, status_code=200, json=response.json)

    monkeypatch.setattr(requests, "post", post)
    app = AppTest.from_file(
        ROOT / "dashboard/streamlit_app.py", default_timeout=15
    ).run()
    app.switch_page(f"pages/{page}.py").run()
    next(b for b in app.button if b.label == button).click().run()
    assert not app.exception
    assert len(calls) == len(audits) == 1 and audits[0]["success"]
    assert len(app.get("download_button")) == 2
    assert calls[0].get("local_knowledge", False) is False
