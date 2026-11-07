"""Bounded loopback-only observation client; no inference retries or redirects."""

import ipaddress
import json
from urllib.parse import urlsplit

import requests

from app.native_evidence_config import ENDPOINT, INVALID_INPUT, WITHHELD
from app.native_observations import (
    MAX_RESPONSE_BYTES,
    NativeObservationEnvelope,
    NativeObservationRequest,
    validate_response,
)

UNAVAILABLE = (
    "The experimental observation endpoint is unavailable. Enable the workflow flag "
    "and use the documented app.native_evidence_api:app backend."
)
LOCAL_ONLY = "Use an HTTP(S) loopback IP address, such as http://127.0.0.1:8000, for this local upload workflow."


def _local_base(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
        or parsed.hostname is None
        or not ipaddress.ip_address(parsed.hostname).is_loopback
    ):
        raise ValueError("loopback_url_required")
    _ = parsed.port  # Validate a supplied port before opening a connection.
    return value.rstrip("/")


def _unique_pairs(pairs):
    result = {}
    for key, item in pairs:
        if key in result:
            raise ValueError("duplicate_response_key")
        result[key] = item
    return result


def _reject_constant(_):
    raise ValueError("nonfinite_response_value")


def post_native_observations(
    base_url: str, request: NativeObservationRequest
) -> tuple[NativeObservationEnvelope | None, str | None]:
    try:
        base = _local_base(base_url)
    except (ValueError, TypeError, AttributeError):
        return None, LOCAL_ONLY
    try:
        request = NativeObservationRequest.model_validate(
            request.model_dump(mode="json", warnings=False)
        )
    except (ValueError, TypeError, AttributeError):
        return None, INVALID_INPUT
    try:
        with requests.Session() as transport:
            # Ignore proxy and netrc environment configuration: raw telemetry
            # must not be forwarded away from the explicitly selected loopback IP.
            transport.trust_env = False
            with transport.post(
                base + ENDPOINT,
                json=request.model_dump(mode="json"),
                timeout=(3, 15),
                stream=True,
                allow_redirects=False,
            ) as response:
                if response.status_code in {404, 405}:
                    return None, UNAVAILABLE
                if response.status_code in {413, 422}:
                    return None, INVALID_INPUT
                if response.status_code != 200:
                    return None, WITHHELD
                body = bytearray()
                for chunk in response.iter_content(chunk_size=8192):
                    if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                        return None, WITHHELD
                    body.extend(chunk)
        decoded = json.loads(
            body.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_pairs,
            parse_constant=_reject_constant,
        )
        return validate_response(request, decoded), None
    except requests.exceptions.Timeout:
        return (
            None,
            "The observation request timed out. This workflow dispatches no model or security action; build again when the local endpoint is available.",
        )
    except requests.exceptions.RequestException:
        return None, UNAVAILABLE
    except (ValueError, TypeError, AttributeError, RecursionError, UnicodeError):
        return None, WITHHELD
