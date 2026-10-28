from typing import Any

from app.analysis_trace import AnalysisTrace
from app.ollama_client import call_model_json
from app.output_policy import replace_untrusted_source_ids, untrusted_source_ids
from app.prompts import build_governance_prompt
from app.reference_loader import (
    clean_inline_source_citations,
    format_references_for_prompt,
    get_reference_ids,
    get_relevant_references,
    sanitize_source_references,
)
from app.schemas import GovernanceRiskRequest, GovernanceRiskResponse


def analyze_governance_risk(
    request: GovernanceRiskRequest,
    *,
    references: list[dict[str, Any]] | None = None,
    trace: AnalysisTrace | None = None,
) -> GovernanceRiskResponse:
    query = request.model_dump_json()

    if references is None:
        references = get_relevant_references(mode="governance", query=query, limit=6)

    reference_context = format_references_for_prompt(references)

    prompt = build_governance_prompt(
        request=request,
        reference_context=reference_context,
    )

    if trace is not None:
        trace.capture("generation_started", None)
    raw_result = call_model_json(
        user_prompt=prompt,
        response_schema=GovernanceRiskResponse.model_json_schema(),
    )

    if trace is not None:
        trace.capture("raw_model", raw_result)

    source_ids = get_reference_ids(references) | get_reference_ids(
        raw_result.get("source_references", [])
    )

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

    if trace is not None:
        trace.capture("citation_cleaned", raw_result)

    raw_result["source_references"] = sanitize_source_references(
        returned_sources=raw_result.get("source_references", []),
        retrieved_references=references,
    )

    if trace is not None:
        trace.capture("source_sanitized", raw_result)

    blocked = untrusted_source_ids(
        request.model_dump(mode="json"), get_reference_ids(references)
    )
    raw_result = replace_untrusted_source_ids(raw_result, blocked)
    if trace is not None:
        trace.capture("output_policy", raw_result)

    response = GovernanceRiskResponse.model_validate(raw_result)
    if trace is not None:
        trace.capture("final_response", response.model_dump(mode="json"))
    return response
