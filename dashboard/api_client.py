"""Small API boundary; never display server bodies or exception strings."""

import requests

GENERIC_ERROR = (
    "Analysis failed. Check the local services and Activity, then try again."
)
POLICY_ERROR = (
    "Analysis withheld. The generated response failed required checks after one repair attempt. "
    "No analyst result was returned."
)
CONTEXT_ERROR = (
    "Complete analysis withheld by the local runtime's context or generation limits. "
    "No analyst result was returned. Use a smaller, clearly scoped bundle and check the supported local runtime."
)
UNAVAILABLE = (
    "FastAPI is unavailable. Start the local backend to analyze cases or view Activity."
)


def safe_error(status: int, body: object) -> str:
    if isinstance(body, dict):
        detail = body.get("detail")
        if (
            isinstance(detail, dict)
            and detail.get("code") == "local_knowledge_unavailable"
        ):
            return "Reviewed local knowledge unavailable or invalid; analysis withheld. Check Knowledge Workspace and the operator CLI."
        if (
            isinstance(detail, dict)
            and detail.get("code") == "complete_context_unavailable"
        ):
            return CONTEXT_ERROR
        if (
            isinstance(detail, dict)
            and detail.get("code") == "integrity_validation_failed"
        ):
            return POLICY_ERROR
    if status == 422:
        return "Some input fields are invalid or too long. Review the form and submit again."
    return GENERIC_ERROR


def post_analysis(
    base_url: str, endpoint: str, payload: dict
) -> tuple[dict | None, str | None]:
    try:
        response = requests.post(
            f"{base_url.rstrip('/')}{endpoint}", json=payload, timeout=300
        )
        try:
            body = response.json()
        except ValueError:
            return None, GENERIC_ERROR
        if not response.ok:
            return None, safe_error(response.status_code, body)
        if (
            not isinstance(body, dict)
            or not isinstance(body.get("analysis"), dict)
            or not isinstance(body.get("metadata"), dict)
        ):
            return None, GENERIC_ERROR
        return body, None
    except requests.exceptions.Timeout:
        return (
            None,
            "The request timed out. The backend may still finish and audit it. Check Activity before resubmitting.",
        )
    except requests.exceptions.RequestException:
        return None, UNAVAILABLE


def get_data(base_url: str, endpoint: str) -> tuple[dict | None, str | None]:
    try:
        response = requests.get(f"{base_url.rstrip('/')}{endpoint}", timeout=5)
        response.raise_for_status()
        body = response.json()
        return (body, None) if isinstance(body, dict) else (None, UNAVAILABLE)
    except (requests.exceptions.RequestException, ValueError):
        return None, UNAVAILABLE
