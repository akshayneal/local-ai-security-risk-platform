from app.ollama_client import call_model_json
from app.prompts import build_soc_prompt
from app.reference_loader import (
    clean_inline_source_citations,
    format_references_for_prompt,
    get_reference_ids,
    get_relevant_references,
    sanitize_source_references,
)
from app.schemas import SocAlertRequest, SocAlertResponse


def analyze_soc_alert(request: SocAlertRequest) -> SocAlertResponse:
    query = request.model_dump_json()

    references = get_relevant_references(
        mode="soc_alert",
        query=query,
        limit=5,
    )

    reference_context = format_references_for_prompt(references)

    prompt = build_soc_prompt(
        request=request,
        reference_context=reference_context,
    )

    raw_result = call_model_json(
        user_prompt=prompt,
        response_schema=SocAlertResponse.model_json_schema(),
    )

    source_ids = get_reference_ids(references)

    raw_result = clean_inline_source_citations(
        raw_result=raw_result,
        source_ids=source_ids,
        fields_to_clean=[
            "summary",
            "mitre_mapping",
            "recommended_containment",
            "recommended_investigation_steps",
            "false_positive_considerations",
            "evidence_gaps",
            "analyst_note",
        ],
    )

    raw_result["source_references"] = sanitize_source_references(
        returned_sources=raw_result.get("source_references", []),
        retrieved_references=references,
    )
    return SocAlertResponse.model_validate(raw_result)