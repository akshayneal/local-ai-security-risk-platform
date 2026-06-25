from app.ollama_client import call_model_json
from app.prompts import build_governance_prompt
from app.schemas import GovernanceRiskRequest, GovernanceRiskResponse


def analyze_governance_risk(request: GovernanceRiskRequest) -> GovernanceRiskResponse:
    prompt = build_governance_prompt(request)

    raw_result = call_model_json(
        user_prompt=prompt,
        response_schema=GovernanceRiskResponse.model_json_schema(),
    )

    return GovernanceRiskResponse.model_validate(raw_result)