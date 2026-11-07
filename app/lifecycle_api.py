"""Default-off foreground gateway; no worker, queue, result store or cancellation."""

import json
from collections.abc import Callable

from fastapi import APIRouter, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel

from app import main
from app.inference_lifecycle import (
    ATTEMPT_HEADER,
    PREFIX,
    AttemptReused,
    ExecutionRegistry,
    ExecutionStatus,
    LifecycleResponse,
    RegistryFull,
    execution_scope,
    lifecycle_enabled,
    load_config,
    valid_attempt_id,
)
from app.native_evidence_api import _request_json
from app.native_evidence_api import app as native_gateway
from app.ui_schemas import (
    GovernanceAnalysisEnvelope,
    SocAnalysisEnvelope,
    UiGovernanceRequest,
    UiSocRequest,
)

INVALID = "Invalid or oversized analysis lifecycle request."
MAX_RESULT_BYTES = 4_000_000
REGISTRY = ExecutionRegistry()


class BoundedLifecycleRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def bounded(request: Request):
            if request.method != "POST":
                return await original(request)
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > 400_000:
                    raise HTTPException(413, detail=INVALID)
                body.extend(chunk)
            try:
                _request_json(body)
            except (ValueError, UnicodeError, RecursionError):
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


router = APIRouter(route_class=BoundedLifecycleRoute)


def _withheld(status: ExecutionStatus, *, code="analysis_lifecycle_withheld"):
    return HTTPException(
        409
        if status.state == "unknown_post_dispatch" or code == "analysis_attempt_reused"
        else 422
        if status.state == "rejected_before_dispatch"
        else 500,
        detail={"code": code, "execution": status.model_dump(mode="json")},
    )


def _run(attempt_id: str, max_sends: int, operation: Callable, envelope_type):
    try:
        valid_attempt_id(attempt_id)
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(422, detail=INVALID) from None
    try:
        config = load_config()
        execution = REGISTRY.reserve(attempt_id, config, max_sends)
    except AttemptReused as exc:
        raise _withheld(exc.status, code="analysis_attempt_reused") from None
    except RegistryFull:
        raise HTTPException(
            503,
            detail="Analysis lifecycle registry is full; no new request was dispatched.",
        ) from None
    except ValueError:
        raise HTTPException(
            503,
            detail="Analysis lifecycle configuration is invalid; no request was dispatched.",
        ) from None
    try:
        with execution_scope(execution):
            raw = operation()
            if isinstance(raw, BaseModel):
                raw = raw.model_dump(mode="json", warnings=False)
            result = envelope_type.model_validate(raw)
            result_data = result.model_dump(mode="json")
            if (
                len(
                    json.dumps(result_data, ensure_ascii=True, allow_nan=False).encode(
                        "utf-8"
                    )
                )
                > MAX_RESULT_BYTES
            ):
                execution.reject("api_result_byte_budget")
            execution.complete()
            return LifecycleResponse(
                execution=execution.snapshot(),
                result=result_data,
            )
    except Exception:  # noqa: BLE001 -- original safe exceptions cannot leak runtime/source bodies
        execution.fail("analysis_or_validation_failed")
        raise _withheld(execution.snapshot()) from None
    except BaseException:  # interruption leaves uncertain metadata; never re-dispatch
        execution.fail("analysis_interrupted")
        raise


@router.post(PREFIX + "/analyze/soc-alert", response_model=LifecycleResponse)
def lifecycle_soc(
    request: UiSocRequest,
    attempt_id: str = Header(alias=ATTEMPT_HEADER, min_length=36, max_length=36),
):
    return _run(
        attempt_id,
        2,
        lambda: main.ui_soc_endpoint(request),
        SocAnalysisEnvelope,
    )


@router.post(PREFIX + "/analyze/governance", response_model=LifecycleResponse)
def lifecycle_governance(
    request: UiGovernanceRequest,
    attempt_id: str = Header(alias=ATTEMPT_HEADER, min_length=36, max_length=36),
):
    return _run(
        attempt_id,
        1,
        lambda: main.ui_governance_endpoint(request),
        GovernanceAnalysisEnvelope,
    )


@router.get(PREFIX + "/status/{attempt_id}", response_model=ExecutionStatus)
def execution_status(attempt_id: str):
    try:
        status = REGISTRY.status(attempt_id)
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(422, detail=INVALID) from None
    if status is None:
        raise HTTPException(
            404, detail="Attempt status unavailable; prior dispatch remains unknown."
        )
    return status


def create_app() -> FastAPI:
    application = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    if lifecycle_enabled():
        load_config()  # Fail before serving if operator configuration is invalid.
        application.include_router(router)
    application.mount("/", native_gateway)
    return application


app = create_app()
