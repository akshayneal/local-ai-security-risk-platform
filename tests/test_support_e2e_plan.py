import json
from types import SimpleNamespace

from evals.evidence_support_e2e import runner


def test_live_diagnostic_frozen_eight_cases_and_no_generation_treatment():
    assert runner.identity() == json.loads(
        (runner.DIRECTORY / "freeze.json").read_bytes()
    )
    assert len(runner.cases()) == 8
    for case in runner.cases():
        request = runner.request_for(case)
        assert (
            request and case["supported"] and case["unsupported"] and case["positive"]
        )
        for rows in case.get("bundle", {}).get("tables", {}).values():
            for row in rows:
                if "SHA256" in row:
                    assert len(row["SHA256"]) == 64


def test_ui_route_trial_is_bounded_and_audits_are_counted_not_persisted(monkeypatch):
    calls = []

    def endpoint(request):
        calls.append(request)
        runner.main.write_audit_log(success=True, source_ids=[])
        body = {
            "analysis": {"alert_id": request.alert_id, "source_references": []},
            "metadata": {
                "evidence_inspector": {
                    "sources": [],
                    "claims": [],
                    "retrieval_status": "captured",
                }
            },
        }
        return SimpleNamespace(model_dump=lambda **kwargs: body)

    monkeypatch.setattr(runner.main, "ui_soc_endpoint", endpoint)
    row = runner.trial(runner.cases()[0])
    assert len(calls) == 1 and len(row["audit_outcomes"]) == 1
    assert row["model_attempts"] == [] and all(row["checks"].values())


def test_unexpected_route_failure_is_recorded_without_sensitive_error(monkeypatch):
    def failure(request):
        raise ValueError("SECRET-ERROR-PAYLOAD")

    monkeypatch.setattr(runner.main, "ui_soc_endpoint", failure)
    row = runner.trial(runner.cases()[0])
    assert row["error"] == "analysis_failed" and row["response"] is None
    assert "SECRET-ERROR-PAYLOAD" not in json.dumps(row)
