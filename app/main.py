from fastapi import FastAPI, HTTPException

from app.audit_logger import read_audit_logs, write_audit_log
from app.governance_analyzer import analyze_governance_risk
from app.schemas import (
    GovernanceRiskRequest,
    GovernanceRiskResponse,
    SocAlertRequest,
    SocAlertResponse,
)
from app.soc_analyzer import analyze_soc_alert


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
    try:
        result = analyze_governance_risk(request)

        write_audit_log(
            mode="governance",
            input_summary=request.system_name,
            result_summary=f"{result.risk_level} / {result.decision}",
            success=True,
            source_ids=[
                source.source_id for source in result.source_references
            ],
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

        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/analyze/soc-alert", response_model=SocAlertResponse)
def soc_alert_endpoint(request: SocAlertRequest) -> SocAlertResponse:
    try:
        result = analyze_soc_alert(request)

        write_audit_log(
            mode="soc_alert",
            input_summary=f"{request.alert_id}: {request.alert_type}",
            result_summary=f"{result.severity} / {result.likely_incident_type}",
            success=True,
            source_ids=[
                source.source_id for source in result.source_references
            ],
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

        raise HTTPException(status_code=500, detail=str(exc)) from exc


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