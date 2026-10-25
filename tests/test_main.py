import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import main
from app.schemas import GovernanceRiskRequest, SocAlertRequest


@pytest.mark.parametrize(
    "path,analyzer,endpoint,payload,mode",
    [
        (
            "/analyze/governance",
            "analyze_governance_risk",
            main.governance_endpoint,
            GovernanceRiskRequest(
                system_name="Synthetic assistant", system_purpose="Draft answers"
            ),
            "governance",
        ),
        (
            "/analyze/soc-alert",
            "analyze_soc_alert",
            main.soc_alert_endpoint,
            SocAlertRequest(
                alert_id="SYNTHETIC-001",
                alert_type="Authentication",
                source_system="Demo",
                affected_asset="demo-host",
                raw_log="Synthetic failed authentication",
            ),
            "soc_alert",
        ),
    ],
)
def test_analysis_failure_is_generic_and_audited(
    monkeypatch, path, analyzer, endpoint, payload, mode
):
    internal_error = RuntimeError(
        "Internal model failure at /private/synthetic/model.json"
    )
    audit_calls = []

    def fail_analysis(_request):
        raise internal_error

    monkeypatch.setattr(main, analyzer, fail_analysis)
    monkeypatch.setattr(
        main, "write_audit_log", lambda **kwargs: audit_calls.append(kwargs)
    )

    with TestClient(main.app) as client:
        response = client.post(path, json=payload.model_dump())

    assert response.status_code == 500
    assert response.json() == {"detail": "Analysis failed. See local logs for details."}
    assert str(internal_error) not in response.text
    assert len(audit_calls) == 1
    assert audit_calls[0]["error"] == str(internal_error)
    assert audit_calls[0]["success"] is False
    assert audit_calls[0]["mode"] == mode
    assert audit_calls[0]["result_summary"] == "analysis_failed"

    with pytest.raises(HTTPException) as exc_info:
        endpoint(payload)
    assert exc_info.value.__cause__ is internal_error
