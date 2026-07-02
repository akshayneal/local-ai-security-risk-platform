from app.ollama_client import call_model_json
from app.prompts import build_governance_prompt
from app.reference_loader import (
    clean_inline_source_citations,
    format_references_for_prompt,
    get_reference_ids,
    get_relevant_references,
    sanitize_source_references,
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

    source_ids = get_reference_ids(references)

    raw_result = clean_inline_source_citations(
        raw_result=raw_result,
        source_ids=source_ids,
        fields_to_clean=[
            "summary",
            "key_risks",
            "required_controls",
            "human_review_requirements",
            "logging_requirements",
            "evidence_gaps",
            "recommended_next_steps",
        ],
    )

    raw_result["source_references"] = sanitize_source_references(
        returned_sources=raw_result.get("source_references", []),
        retrieved_references=references,
    )

    return GovernanceRiskResponse.model_validate(raw_result)