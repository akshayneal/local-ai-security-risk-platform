"""Explicit Sprint 6 ASGI gateway: old routes unchanged plus one technical workflow."""

import json

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.ai_security_analyzer import analyze_ai_security
from app.ai_security_contracts import (
    MAX_WIRE_BYTES,
    AiSecurityEnvelope,
    AiSecurityRequest,
)
from app.audit_logger import write_audit_log
from app.inference_context import EvidenceBudgetError
from app.main import app as original_app
from app.retrieval.storage import fingerprint
from app.version import APPLICATION_VERSION

INVALID = "Invalid or oversized AI Security threat model. Review its bounded IDs and references."
WITHHELD = "AI Security assessment withheld. Check the local runtime and reviewed guidance; no result or action was returned."


def unique_json(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValueError("Duplicate JSON key")
        data[key] = value
    return data


def reject_constant(value):
    raise ValueError("Nonfinite JSON is unsupported")


class BoundedAiSecurityRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def bounded(request: Request):
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > MAX_WIRE_BYTES:
                    raise HTTPException(413, detail=INVALID)
                body.extend(chunk)
            try:
                json.loads(
                    body, object_pairs_hook=unique_json, parse_constant=reject_constant
                )
            except (ValueError, RecursionError):
                raise HTTPException(422, detail=INVALID) from None
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
                return JSONResponse(status_code=422, content={"detail": INVALID})

        return bounded


router = APIRouter(route_class=BoundedAiSecurityRoute)


@router.post("/ui/analyze/ai-security", response_model=AiSecurityEnvelope)
def ai_security_endpoint(request: AiSecurityRequest) -> AiSecurityEnvelope:
    identity = fingerprint(request)
    try:
        result = analyze_ai_security(request)
    except Exception as exc:  # noqa: BLE001 -- API boundary returns fixed errors, never model/design text.
        write_audit_log(
            mode="ai_security",
            input_summary="request-sha256:" + identity,
            result_summary="assessment_withheld",
            success=False,
            error="ai_security_boundary_or_runtime_failure",
        )
        if isinstance(exc, EvidenceBudgetError):
            raise HTTPException(
                422,
                detail={"code": "complete_context_unavailable", "message": WITHHELD},
            ) from None
        raise HTTPException(500, detail=WITHHELD) from None
    write_audit_log(
        mode="ai_security",
        input_summary="request-sha256:" + identity,
        result_summary=result.analysis.coverage_status,
        success=True,
        source_ids=[
            s.provenance.evidence_id
            for s in result.metadata.sources
            if s.cited_by_finding_ids
        ],
    )
    return result


# Compose rather than edit app/main.py, whose bytes are frozen by the Sprint 5 replay.
# Legacy launchers keep app.main:app. This gateway is an explicit foreground opt-in.
app = FastAPI(
    title="Local AI Security Platform — Experimental Gateway",
    version=APPLICATION_VERSION,
)
app.include_router(original_app.router)
app.include_router(router)
