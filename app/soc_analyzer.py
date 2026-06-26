from app.ollama_client import call_model_json
from app.prompts import build_soc_prompt
from app.reference_loader import (
    format_references_for_prompt,
    get_relevant_references,
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

    return SocAlertResponse.model_validate(raw_result)