from app.prompts import build_governance_prompt, build_soc_prompt
from app.reference_loader import format_references_for_prompt, get_relevant_references
from app.schemas import GovernanceRiskRequest, SocAlertRequest


def test_governance_prompt_includes_reference_context():
    request = GovernanceRiskRequest(
        system_name="Internal Resume Screening Assistant",
        system_purpose="Rank job candidates for initial recruiter review.",
        data_types=["candidate resumes", "employment history", "education history"],
        users=["recruiters", "hiring managers"],
        external_integrations=["applicant tracking system"],
        human_review_process="Recruiters review all AI recommendations before decisions.",
        business_impact="High impact because the system may affect hiring opportunities.",
    )

    references = get_relevant_references(
        mode="governance",
        query=request.model_dump_json(),
        limit=6,
    )

    reference_context = format_references_for_prompt(references)

    prompt = build_governance_prompt(
        request=request,
        reference_context=reference_context,
    )

    assert "Local reference context:" in prompt
    assert "Source ID:" in prompt
    assert "Internal Resume Screening Assistant" in prompt
    assert "candidate resumes" in prompt


def test_soc_prompt_includes_reference_context():
    request = SocAlertRequest(
        alert_id="SOC-001",
        alert_type="SSH brute force followed by successful login",
        source_system="Linux auth logs",
        affected_asset="ubuntu-web-01",
        raw_log="Multiple failed password attempts followed by accepted password.",
        known_indicators=["185.22.10.4", "root", "admin"],
        observed_behavior="Foreign IP attempted failed logins and then successfully authenticated.",
    )

    references = get_relevant_references(
        mode="soc_alert",
        query=request.model_dump_json(),
        limit=5,
    )

    reference_context = format_references_for_prompt(references)

    prompt = build_soc_prompt(
        request=request,
        reference_context=reference_context,
    )

    assert "Local reference context:" in prompt
    assert "Source ID:" in prompt
    assert "SSH brute force followed by successful login" in prompt
    assert "185.22.10.4" in prompt