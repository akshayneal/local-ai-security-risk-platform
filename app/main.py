from fastapi import FastAPI, HTTPException

from app.audit_logger import read_audit_logs, write_audit_log
from app.governance_analyzer import analyze_governance_risk
from app.ollama_client import OLLAMA_MODEL
from app.output_policy import OutputPolicyError
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
)

app = FastAPI(
    title="Local AI Security Risk & SOC Triage Platform",
    description="Local AI security and governance workflow platform using Ollama.",
    version="2.2.0",
)


@app.get("/")
def root() -> dict:
    return {
        "message": "Local AI Security Risk & SOC Triage Platform",
        "version": "2.2.0",
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

        if trace is not None and isinstance(exc, OutputPolicyError):
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "integrity_validation_failed",
                    "message": INTEGRITY_FAILURE_MESSAGE,
                },
            ) from exc
        raise HTTPException(
            status_code=500, detail="Analysis failed. See local logs for details."
        ) from exc


@app.post("/ui/analyze/governance", response_model=GovernanceAnalysisEnvelope)
def ui_governance_endpoint(
    request: GovernanceRiskRequest,
) -> GovernanceAnalysisEnvelope:
    return GovernanceAnalysisEnvelope(
        analysis=_run_governance(request),
        metadata=GovernanceMetadata(model=OLLAMA_MODEL),
    )


@app.post("/ui/analyze/soc-alert", response_model=SocAnalysisEnvelope)
def ui_soc_endpoint(request: SocAlertRequest) -> SocAnalysisEnvelope:
    trace = ProductTrace()
    result = _run_soc(request, trace=trace)
    return SocAnalysisEnvelope(
        analysis=result,
        metadata=SocMetadata(
            model=OLLAMA_MODEL,
            repair_attempted=trace.repair_attempted,
            repair_succeeded=(not trace.repair_failed)
            if trace.repair_attempted
            else None,
        ),
    )


@app.get("/ui/status")
def ui_status() -> dict:
    """Backend readiness only; deliberately does not call Ollama."""
    return {"status": "ok", "version": app.version, "model": OLLAMA_MODEL}


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
