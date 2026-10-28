from copy import deepcopy

import pytest
from test_schemas import GOVERNANCE_INPUT, GOVERNANCE_RESPONSE, SOC_INPUT, SOC_RESPONSE

from app import governance_analyzer, soc_analyzer
from app.analysis_trace import AnalysisTrace
from app.schemas import GovernanceRiskRequest, SocAlertRequest


@pytest.mark.parametrize("mode", ["soc", "governance"])
def test_trace_snapshots_are_optional_independent_and_behavior_preserving(
    monkeypatch, mode
):
    module, analyzer, request, payload = (
        (
            soc_analyzer,
            soc_analyzer.analyze_soc_alert,
            SocAlertRequest(**SOC_INPUT),
            SOC_RESPONSE,
        )
        if mode == "soc"
        else (
            governance_analyzer,
            governance_analyzer.analyze_governance_risk,
            GovernanceRiskRequest(**GOVERNANCE_INPUT),
            GOVERNANCE_RESPONSE,
        )
    )
    raw = {
        **payload,
        "summary": "Review LOCAL-REF.",
        "source_references": [
            {
                "source_id": "UNKNOWN-ID",
                "title": "Fake",
                "framework": "Fake",
                "relevance": "Fake",
            }
        ],
    }
    monkeypatch.setattr(module, "call_model_json", lambda **kw: deepcopy(raw))
    references = [{"source_id": "LOCAL-REF", "title": "Trusted", "framework": "Local"}]
    trace = AnalysisTrace()
    traced = analyzer(request, references=references, trace=trace)
    ordinary = analyzer(request, references=references)
    assert traced == ordinary
    stages = {s["stage"]: s["value"] for s in trace.stages}
    assert stages["raw_model"] == raw
    assert stages["citation_cleaned"]["summary"] == "Review."
    assert stages["citation_cleaned"]["source_references"] == raw["source_references"]
    assert stages["source_sanitized"]["source_references"] == []
    assert stages["final_response"] == traced.model_dump(mode="json")
    assert "trace" not in traced.model_dump()
    traced.summary = "Changed later"
    assert stages["final_response"]["summary"] == "Review."


def test_disabled_trace_does_not_capture(monkeypatch):
    monkeypatch.setattr(
        soc_analyzer, "call_model_json", lambda **kw: deepcopy(SOC_RESPONSE)
    )
    monkeypatch.setattr(
        AnalysisTrace, "capture", lambda *a, **kw: pytest.fail("Trace enabled")
    )
    soc_analyzer.analyze_soc_alert(SocAlertRequest(**SOC_INPUT), references=[])
