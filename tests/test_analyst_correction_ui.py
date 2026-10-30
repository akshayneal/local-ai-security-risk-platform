from copy import deepcopy
from types import SimpleNamespace

import pytest
import requests
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from test_dashboard import button, open_page
from test_evidence_inspector import report_for
from test_schemas import GOVERNANCE_RESPONSE, SOC_INPUT, SOC_RESPONSE

from app import governance_analyzer, main, soc_analyzer
from app.evidence_inspector import build_inspector, collect_evidence
from app.schemas import SocAlertRequest, SocAlertResponse


def correction_fixture(profile="soc", case="CORRECTION-CASE"):
    if profile == "microsoft":
        return report_for(True, case)
    if profile == "governance":
        request, analysis, _ = report_for(False, case)
        analysis = type(analysis).model_validate(
            {
                **analysis.model_dump(),
                "summary": "The quarterly review requirement has already been implemented.",
            }
        )
        with collect_evidence("governance") as capture:
            pass
        return request, analysis, build_inspector(capture, request, analysis)
    request = SocAlertRequest(
        **{**SOC_INPUT, "alert_id": case, "raw_log": "PRIVATE-TELEMETRY-SENTINEL"}
    )
    analysis = SocAlertResponse(
        **{
            **SOC_RESPONSE,
            "alert_id": case,
            "likely_incident_type": "Command and Control",
        }
    )
    with collect_evidence("soc_alert") as capture:
        pass
    return request, analysis, build_inspector(capture, request, analysis)


SCRIPT = """
import streamlit as st
from test_analyst_correction_ui import correction_fixture
from app.evidence_inspector import inspector_export
from dashboard.evidence_inspector import display_evidence_inspector,correction_history
request,analysis,report=correction_fixture(st.session_state.get('profile','soc'),st.session_state.get('case','CORRECTION-CASE'))
parsed,reviews=display_evidence_inspector(report.model_dump(mode='json'),prefix='test',submitted_input=request.model_dump(mode='json'))
st.session_state['export']=inspector_export(parsed,reviews,corrections=correction_history(parsed,prefix='test'))
st.session_state['original']=analysis.model_dump(mode='json')
"""


def widget(app, kind, label):
    return next(w for w in getattr(app, kind) if w.label == label)


def save(app, text="A connection does not establish Command and Control."):
    widget(app, "text_area", "Proposed correction wording").input(text)
    widget(app, "text_area", "Correction rationale").input("Synthetic analyst review.")
    button(app, "Save correction revision").click().run()
    assert not app.exception


@pytest.mark.parametrize("profile", ["soc", "microsoft", "governance"])
def test_editor_preserves_original_appends_revision_and_does_not_call_services(
    monkeypatch, profile
):
    def forbidden(*args, **kwargs):
        pytest.fail("Editing corrections must not call an API or model")

    monkeypatch.setattr(requests, "post", forbidden)
    monkeypatch.setattr(soc_analyzer, "call_model_json", forbidden)
    monkeypatch.setattr(governance_analyzer, "call_model_json", forbidden)
    app = AppTest.from_string(SCRIPT)
    app.session_state["profile"] = profile
    app.run()
    _, _, report = correction_fixture(profile)
    target = next(
        c
        for c in report.claims
        if c.response_field
        == ("summary" if profile == "governance" else "likely_incident_type")
    )
    widget(app, "selectbox", "Claim to review").set_value(target.claim_id).run()
    original = deepcopy(app.session_state["original"])
    save(app)
    first = app.session_state["export"]["correction_history"]["revisions"][0]
    assert first["revision"] == 1 and first["evidence_ids"] == []
    assert any("No linked support selected" in c.value for c in app.caption)
    widget(app, "multiselect", "Correction evidence").set_value(
        [report.input_inventory[0].observation_id]
    )
    save(app, "The stated requirement does not establish implementation.")
    revisions = app.session_state["export"]["correction_history"]["revisions"]
    assert len(revisions) == 2 and revisions[0] == first
    assert revisions[1]["supersedes_revision_id"] == first["revision_id"]
    assert revisions[1]["verification_status"] == "not_verified"
    assert revisions[1]["evidence_ids"] == [report.input_inventory[0].observation_id]
    assert app.session_state["original"] == original
    assert any(e.label == "Correction revision history" for e in app.expander)
    assert "PRIVATE-TELEMETRY-SENTINEL" not in str(app.session_state["export"])


def test_blank_correction_rejected_and_new_case_or_workflow_clears_history():
    app = AppTest.from_string(SCRIPT).run()
    button(app, "Save correction revision").click().run()
    assert app.warning and "correction_history" not in app.session_state["export"]
    save(app)
    app.session_state["case"] = "NEW-SUBMITTED-INPUT"
    app.run()
    assert "correction_history" not in app.session_state["export"]
    save(app)
    app.session_state["profile"] = "governance"
    app.run()
    assert not app.exception
    assert "correction_history" not in app.session_state["export"]
    assert app.session_state["export"]["analyst_reviews"] == []


@pytest.mark.parametrize("profile", ["soc", "microsoft", "governance"])
def test_active_workspaces_export_corrections_without_reanalysis(monkeypatch, profile):
    calls, generations, audits = [], [], []
    client = TestClient(main.app)
    monkeypatch.setattr(main, "write_audit_log", lambda **kw: audits.append(kw))

    def post(url, *, json, timeout):
        calls.append(json)
        soc = url.endswith("soc-alert")
        raw = deepcopy(SOC_RESPONSE if soc else GOVERNANCE_RESPONSE)
        raw["alert_id" if soc else "system_name"] = json[
            "alert_id" if soc else "system_name"
        ]
        raw["source_references"] = []
        if soc:
            raw["observed_evidence"] = ["Supplied observation requires analyst review."]
        module = soc_analyzer if soc else governance_analyzer
        monkeypatch.setattr(
            module,
            "call_model_json",
            lambda **kw: generations.append(kw) or deepcopy(raw),
        )
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
            json=lambda: {"status": "ok", "model": "fixture", "version": "fixture"},
        ),
    )
    app = open_page(
        "AI System Risk Review" if profile == "governance" else "SOC Investigation"
    )
    if profile == "microsoft":
        app.selectbox(key="soc_input_profile").select(
            "Microsoft Security telemetry"
        ).run()
        button(app, "Load Microsoft sample").click().run()
    submit = {
        "soc": "Analyze SOC alert",
        "microsoft": "Analyze Microsoft telemetry",
        "governance": "Review AI system",
    }[profile]
    button(app, submit).click().run()
    assert not app.exception
    prefix = {"soc": "soc", "microsoft": "ms", "governance": "gov"}[profile]
    original = deepcopy(app.session_state[f"{prefix}_result"]["document"]["analysis"])
    save(app)
    document = app.session_state[f"{prefix}_result"]["document"]
    assert document["analysis"] == original
    assert len(document["evidence_inspector"]["correction_history"]["revisions"]) == 1
    assert len(calls) == len(generations) == len(audits) == 1
    # A new submission clears corrections even if a deterministic model repeats output.
    button(app, submit).click().run()
    assert (
        "correction_history"
        not in app.session_state[f"{prefix}_result"]["document"]["evidence_inspector"]
    )
    if profile == "microsoft":
        save(app)
        app.text_area(key="ms_json").input("{}").run()
        assert "ms_evidence_reviews" not in app.session_state
        assert not app.get("download_button")
