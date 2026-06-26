from app.ollama_client import call_model_json
from app.prompts import build_governance_prompt
from app.reference_loader import (
    format_references_for_prompt,
    get_relevant_references,
)
from app.schemas import GovernanceRiskRequest, GovernanceRiskResponse


def analyze_governance_risk(request: GovernanceRiskRequest) -> GovernanceRiskResponse:
    query = request.model_dump_json()

    references = get_relevant_references(
        mode="governance",
        query=query,
        limit=6,
    )

    reference_context = format_references_for_prompt(references)

    prompt = build_governance_prompt(
        request=request,
        reference_context=reference_context,
    )

    raw_result = call_model_json(
        user_prompt=prompt,
        response_schema=GovernanceRiskResponse.model_json_schema(),
    )

    return GovernanceRiskResponse.model_validate(raw_result)