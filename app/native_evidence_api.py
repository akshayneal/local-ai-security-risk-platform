"""Explicit ASGI composition; original gateway and launchers remain unchanged."""

import json

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app import native_investigation
from app.ai_security_api import app as original_gateway
from app.native_evidence_config import (
    ENDPOINT,
    INVALID_INPUT,
    MAX_WIRE_BYTES,
    WITHHELD,
    native_evidence_enabled,
)
from app.native_observations import (
    MAX_RESPONSE_BYTES,
    NativeObservationEnvelope,
    NativeObservationError,
    NativeObservationRequest,
    build_response,
    validate_response,
)


def _unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate_request_key")
        value[key] = item
    return value


def _reject_constant(_):
    raise ValueError("nonfinite_request_value")


def _request_json(body):
    text = bytes(body).decode("utf-8", errors="strict")
    depth, quoted, escaped = 0, False, False
    for character in text:
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
        elif character in "[{":
            depth += 1
            if depth > 8:
                raise ValueError("request_depth_budget")
        elif character in "]}":
            depth -= 1
    return json.loads(
        text, object_pairs_hook=_unique_pairs, parse_constant=_reject_constant
    )


class BoundedNativeRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def bounded(request: Request):
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > MAX_WIRE_BYTES:
                    raise HTTPException(413, detail=INVALID_INPUT)
                body.extend(chunk)
            try:
                _request_json(body)
            except (ValueError, UnicodeError, RecursionError):
                raise HTTPException(422, detail=INVALID_INPUT) from None
            consumed = False

            async def receive():
                nonlocal consumed
                if consumed:
                    return {"type": "http.disconnect"}
                consumed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}

            try:
                return await original(Request(request.scope, receive=receive))
            except RequestValidationError:
                return JSONResponse(status_code=422, content={"detail": INVALID_INPUT})

        return bounded


router = APIRouter(route_class=BoundedNativeRoute)


@router.post(ENDPOINT, response_model=NativeObservationEnvelope)
def native_observations(request: NativeObservationRequest):
    try:
        result = build_response(request)
    except NativeObservationError:
        raise HTTPException(422, detail=INVALID_INPUT) from None
    except Exception:  # noqa: BLE001 -- fixed API boundary, no source/error bodies
        raise HTTPException(500, detail=WITHHELD) from None
    try:
        result = validate_response(request, result)
        response = JSONResponse(result.model_dump(mode="json"))
        if len(response.body) > MAX_RESPONSE_BYTES:
            raise ValueError("response_byte_budget")
        return response
    except Exception:  # noqa: BLE001 -- unvalidated result must never escape
        raise HTTPException(500, detail=WITHHELD) from None


@router.post(
    native_investigation.ENDPOINT,
    response_model=native_investigation.NativeInvestigationEnvelope,
)
def native_investigation_report(
    request: native_investigation.NativeInvestigationRequest,
):
    try:
        result = native_investigation.build_response(request)
    except NativeObservationError:
        raise HTTPException(422, detail=INVALID_INPUT) from None
    except Exception:  # noqa: BLE001 -- fixed boundary; never echo source/errors
        raise HTTPException(500, detail=WITHHELD) from None
    try:
        result = native_investigation.validate_response(request, result)
        response = JSONResponse(result.model_dump(mode="json"))
        if len(response.body) > native_investigation.MAX_RESPONSE_BYTES:
            raise ValueError("response_byte_budget")
        return response
    except Exception:  # noqa: BLE001 -- reject mutated reports and either export
        raise HTTPException(500, detail=WITHHELD) from None


def create_app() -> FastAPI:
    # Preserve the mounted gateway's existing /docs and /openapi.json. The new
    # route is documented separately and never changes that gateway's schema.
    application = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    if native_evidence_enabled():
        application.include_router(router)
    application.mount("/", original_gateway)
    return application


app = create_app()
