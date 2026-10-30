from copy import deepcopy
from types import SimpleNamespace

import pytest
import requests
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from test_dashboard import button, open_page
from test_evidence_inspector import report_for
from test_schemas import GOVERNANCE_RESPONSE, SOC_RESPONSE

from app import governance_analyzer, main, soc_analyzer

SCRIPT = """
import streamlit as st
from test_evidence_inspector import report_for
from app.evidence_inspector import inspector_export
from dashboard.evidence_inspector import display_evidence_inspector
request,_,report=report_for(True,st.session_state.get('case_name','INSPECTOR-SYNTHETIC'))
parsed,reviews=display_evidence_inspector(report.model_dump(mode='json'),prefix='test',submitted_input=request.model_dump(mode='json'))
st.session_state['test_export']=inspector_export(parsed,reviews)
"""


def test_expandable_inspector_records_human_judgment_and_clears_on_new_result():
    app = AppTest.from_string(SCRIPT).run()
    assert not app.exception
    assert any(e.label == "Evidence Inspector" for e in app.expander)
    assert not app.success
    _, _, report = report_for()
    judgment = next(s for s in app.selectbox if s.label == "Analyst support judgment")
    judgment.select("Supports within stated scope — analyst judgment")
    app.multiselect[0].set_value([report.sources[0].provenance.evidence_id])
    app.text_area[0].input("Synthetic user review; not an independent adjudication")
    next(b for b in app.button if b.label == "Record analyst judgment").click().run()
    assert not app.exception
    reviews = app.session_state["test_export"]["analyst_reviews"]
    assert len(reviews) == 1 and reviews[0]["provenance"] == "analyst_recorded"
    assert reviews[0]["verification_status"] == "not_verified"
    assert "PRIVATE-INPUT-VALUE" not in str(app.session_state["test_export"])
    app.session_state["case_name"] = "ANOTHER-SUBMITTED-CASE"
    app.run()
    assert not app.exception
    assert app.session_state["test_export"]["analyst_reviews"] == []


def test_support_judgment_without_evidence_stays_unrecorded():
    app = AppTest.from_string(SCRIPT).run()
    next(s for s in app.selectbox if s.label == "Analyst support judgment").select(
        "Supports within stated scope — analyst judgment"
    )
    next(b for b in app.button if b.label == "Record analyst judgment").click().run()
    assert not app.exception
    assert app.warning
    assert app.session_state["test_export"]["analyst_reviews"] == []


def test_private_value_requires_explicit_selection_and_stays_out_of_export():
    app = AppTest.from_string(SCRIPT).run()
    assert not any("PRIVATE-INPUT-VALUE" in t.value for t in app.text)
    next(
        c for c in app.checkbox if c.label == "Inspect a selected submitted value"
    ).check().run()
    selected = next(s for s in app.selectbox if s.label == "Submitted field to inspect")
    selected.select("DeviceProcessEvents[0].ProcessCommandLine").run()
    assert not app.exception
    assert any("PRIVATE-INPUT-VALUE" in t.value for t in app.text)
    assert "PRIVATE-INPUT-VALUE" not in str(app.session_state["test_export"])


def test_valid_empty_telemetry_row_has_no_value_picker_crash():
    script = """
from app.soc_inputs import MicrosoftSocAdapter
from app.schemas import SocAlertResponse
from test_schemas import SOC_RESPONSE
from app.evidence_inspector import collect_evidence,build_inspector
from dashboard.evidence_inspector import display_evidence_inspector
request=MicrosoftSocAdapter().normalize({'case_id':'EMPTY-ROW','tables':{'DeviceProcessEvents':[{}]}}).request
result=SocAlertResponse(**SOC_RESPONSE)
with collect_evidence('soc_alert') as capture:
    pass
report=build_inspector(capture,request,result)
display_evidence_inspector(report.model_dump(mode='json'),prefix='empty',submitted_input=request.model_dump(mode='json'))
"""
    app = AppTest.from_string(script).run()
    assert not app.exception
    next(
        c for c in app.checkbox if c.label == "Inspect a selected submitted value"
    ).check().run()
    assert not app.exception
    assert next(
        s for s in app.selectbox if s.label == "Submitted field to inspect"
    ).disabled


@pytest.mark.parametrize("workflow", ["soc", "governance", "microsoft"])
def test_real_ui_api_envelope_reaches_active_workspaces_and_safe_export(
    monkeypatch, workflow
):
    audits, requests_seen = [], []
    monkeypatch.setattr(main, "write_audit_log", lambda **kw: audits.append(kw))
    client = TestClient(main.app)

    def post(url, *, json, timeout):
        requests_seen.append(json)
        soc = url.endswith("soc-alert")
        result = deepcopy(SOC_RESPONSE if soc else GOVERNANCE_RESPONSE)
        result["alert_id" if soc else "system_name"] = json[
            "alert_id" if soc else "system_name"
        ]
        result["source_references"] = []
        if soc:
            result["observed_evidence"] = ["Supplied event requires analyst review."]
        module = soc_analyzer if soc else governance_analyzer
        monkeypatch.setattr(module, "call_model_json", lambda **kw: deepcopy(result))
        response = client.post(
            "/ui/analyze/soc-alert" if soc else "/ui/analyze/governance", json=json
        )
        return SimpleNamespace(ok=response.is_success, json=response.json)

    monkeypatch.setattr(requests, "post", post)
    monkeypatch.setattr(
        requests,
        "get",
        lambda *a, **kw: SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"status": "ok", "model": "qwen3:8b", "version": "synthetic"},
        ),
    )
    app = open_page(
        "AI System Risk Review" if workflow == "governance" else "SOC Investigation"
    )
    if workflow == "microsoft":
        app.selectbox(key="soc_input_profile").select(
            "Microsoft Security telemetry"
        ).run()
        button(app, "Load Microsoft sample").click().run()
        submit = "Analyze Microsoft telemetry"
    else:
        submit = "Review AI system" if workflow == "governance" else "Analyze SOC alert"
    button(app, submit).click().run()
    assert not app.exception
    assert len(requests_seen) == len(audits) == 1
    assert any(e.label == "Evidence Inspector" for e in app.expander)
    prefix = (
        "gov"
        if workflow == "governance"
        else "ms"
        if workflow == "microsoft"
        else "soc"
    )
    saved = app.session_state[f"{prefix}_result"]
    inspector = saved["document"]["evidence_inspector"]
    assert inspector["retrieval_status"] == "captured" and inspector["sources"]
    assert all(c["verification_status"] == "not_verified" for c in inspector["claims"])
    assert len(app.get("download_button")) == 2
    if workflow == "microsoft":
        app.text_area(key="ms_json").set_value("{}").run()
        assert not app.get("download_button")
        assert not any(e.label == "Evidence Inspector" for e in app.expander)
