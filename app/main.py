from fastapi import FastAPI, HTTPException

from app.audit_logger import read_audit_logs, write_audit_log
from app.evidence_inspector import build_inspector, collect_evidence
from app.governance_analyzer import analyze_governance_risk
from app.inference_context import EVIDENCE_BUDGET_MESSAGE, EvidenceBudgetError
from app.knowledge_contracts import knowledge_enabled, local_knowledge_request
from app.knowledge_workspace import KNOWLEDGE_ERROR, workspace_status
from app.ollama_client import OLLAMA_MODEL
from app.output_policy import OutputPolicyError
from app.retrieval.contracts import RetrievalError
from app.schemas import (
    GovernanceRiskRequest,
    GovernanceRiskResponse,
    SocAlertRequest,
    SocAlertResponse,
)
from app.soc_analyzer import analyze_soc_alert
from app.ui_schemas import (
    INTEGRITY_FAILURE_MESSAGE,
    GovernanceAnalysisEnvelope,
    GovernanceMetadata,
    ProductTrace,
    SocAnalysisEnvelope,
    SocMetadata,
    UiGovernanceRequest,
    UiSocRequest,
)
from app.version import APPLICATION_VERSION

app = FastAPI(
    title="Local AI Security Risk Platform",
    description="Local AI security and governance workflow platform using Ollama.",
    version=APPLICATION_VERSION,
)


@app.get("/")
def root() -> dict:
    return {
        "message": "Local AI Security Risk Platform",
        "version": APPLICATION_VERSION,
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "local-ai-security-risk-platform",
    }


@app.post("/analyze/governance", response_model=GovernanceRiskResponse)
def governance_endpoint(request: GovernanceRiskRequest) -> GovernanceRiskResponse:
    return _run_governance(request)


def _run_governance(request: GovernanceRiskRequest) -> GovernanceRiskResponse:
    try:
        result = analyze_governance_risk(request)

        write_audit_log(
            mode="governance",
            input_summary=request.system_name,
            result_summary=f"{result.risk_level} / {result.decision}",
            success=True,
            source_ids=[source.source_id for source in result.source_references],
        )

        return result

    except Exception as exc:
        write_audit_log(
            mode="governance",
            input_summary=request.system_name,
            result_summary="analysis_failed",
            success=False,
            error=str(exc),
        )

        if knowledge_enabled() and isinstance(exc, RetrievalError):
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "local_knowledge_unavailable",
                    "message": KNOWLEDGE_ERROR,
                },
            ) from exc
        if knowledge_enabled() and isinstance(exc, EvidenceBudgetError):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "complete_context_unavailable",
                    "message": EVIDENCE_BUDGET_MESSAGE,
                },
            ) from exc
        raise HTTPException(
            status_code=500, detail="Analysis failed. See local logs for details."
        ) from exc


@app.post("/analyze/soc-alert", response_model=SocAlertResponse)
def soc_alert_endpoint(request: SocAlertRequest) -> SocAlertResponse:
    return _run_soc(request)


def _run_soc(
    request: SocAlertRequest, *, trace: ProductTrace | None = None
) -> SocAlertResponse:
    try:
        result = (
            analyze_soc_alert(request)
            if trace is None
            else analyze_soc_alert(request, trace=trace)
        )
        # The routing ID belongs to the submitted case, not the model or vendor.
        # Rebuild only after the analyzer's complete factual validation succeeds.
        result = SocAlertResponse.model_validate(
            {**result.model_dump(mode="json"), "alert_id": request.alert_id}
        )

        write_audit_log(
            mode="soc_alert",
            input_summary=f"{request.alert_id}: {request.alert_type}",
            result_summary=f"{result.severity} / {result.likely_incident_type}",
            success=True,
            source_ids=[source.source_id for source in result.source_references],
        )

        return result

    except Exception as exc:
        write_audit_log(
            mode="soc_alert",
            input_summary=f"{request.alert_id}: {request.alert_type}",
            result_summary="analysis_failed",
            success=False,
            error=str(exc),
        )

        if knowledge_enabled() and isinstance(exc, RetrievalError):
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "local_knowledge_unavailable",
                    "message": KNOWLEDGE_ERROR,
                },
            ) from exc
        if trace is not None and isinstance(exc, OutputPolicyError):
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "integrity_validation_failed",
                    "message": INTEGRITY_FAILURE_MESSAGE,
                },
            ) from exc
        if isinstance(exc, EvidenceBudgetError):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "complete_context_unavailable",
                    "message": EVIDENCE_BUDGET_MESSAGE,
                },
            ) from exc
        raise HTTPException(
            status_code=500, detail="Analysis failed. See local logs for details."
        ) from exc


@app.post("/ui/analyze/governance", response_model=GovernanceAnalysisEnvelope)
def ui_governance_endpoint(
    request: UiGovernanceRequest,
) -> GovernanceAnalysisEnvelope:
    enabled = request.local_knowledge
    request = GovernanceRiskRequest.model_validate(
        request.model_dump(exclude={"local_knowledge"})
    )
    with local_knowledge_request(enabled), collect_evidence("governance") as capture:
        result = _run_governance(request)
    return GovernanceAnalysisEnvelope(
        analysis=result,
        metadata=GovernanceMetadata(
            model=OLLAMA_MODEL,
            evidence_inspector=build_inspector(capture, request, result),
        ),
    )


@app.post("/ui/analyze/soc-alert", response_model=SocAnalysisEnvelope)
def ui_soc_endpoint(request: UiSocRequest) -> SocAnalysisEnvelope:
    enabled = request.local_knowledge
    request = SocAlertRequest.model_validate(
        request.model_dump(exclude={"local_knowledge"})
    )
    trace = ProductTrace()
    with local_knowledge_request(enabled), collect_evidence("soc_alert") as capture:
        result = _run_soc(request, trace=trace)
    return SocAnalysisEnvelope(
        analysis=result,
        metadata=SocMetadata(
            model=OLLAMA_MODEL,
            repair_attempted=trace.repair_attempted,
            repair_succeeded=(not trace.repair_failed)
            if trace.repair_attempted
            else None,
            evidence_inspector=build_inspector(capture, request, result),
        ),
    )


@app.get("/ui/status")
def ui_status() -> dict:
    """Backend readiness only; deliberately does not call Ollama."""
    return {"status": "ok", "version": app.version, "model": OLLAMA_MODEL}


@app.get("/ui/knowledge/status")
def knowledge_status() -> dict:
    """Allowlisted aggregate metadata only; no path, payload or request grants."""
    return workspace_status()


@app.get("/logs")
def logs_endpoint(limit: int = 50) -> dict:
    return {
        "logs": read_audit_logs(limit=limit),
    }


@app.get("/schemas")
def schemas_endpoint() -> dict:
    return {
        "governance_request": GovernanceRiskRequest.model_json_schema(),
        "governance_response": GovernanceRiskResponse.model_json_schema(),
        "soc_alert_request": SocAlertRequest.model_json_schema(),
        "soc_alert_response": SocAlertResponse.model_json_schema(),
    }
