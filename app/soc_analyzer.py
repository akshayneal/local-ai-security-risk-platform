from app.ollama_client import call_model_json
from app.prompts import build_soc_prompt
from app.schemas import SocAlertRequest, SocAlertResponse


def analyze_soc_alert(request: SocAlertRequest) -> SocAlertResponse:
    prompt = build_soc_prompt(request)

    raw_result = call_model_json(
        user_prompt=prompt,
        response_schema=SocAlertResponse.model_json_schema(),
    )

    return SocAlertResponse.model_validate(raw_result)