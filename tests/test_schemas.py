from app.schemas import (
    GovernanceRiskRequest,
    GovernanceRiskResponse,
    SocAlertRequest,
    SocAlertResponse,
    SourceReference,
)


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