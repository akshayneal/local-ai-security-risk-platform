"""Opt-in lifecycle client/UI challenges with mocked transport and real routes."""

import json
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
import requests
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from test_schemas import GOVERNANCE_RESPONSE, SOC_INPUT, SOC_RESPONSE

from app import main
from app.schemas import GovernanceRiskResponse, SocAlertResponse
from app.ui_schemas import COMMON_CHECKS, SOC_CHECKS
from dashboard import lifecycle as client

ENTRY = Path(__file__).resolve().parents[1] / "dashboard/streamlit_app.py"
PAGES = {True: "pages/soc_investigation.py", False: "pages/ai_system_risk_review.py"}
BASE = "http://127.0.0.1:8245"


def execution(attempt_id, *, state="completed_validated", raw_sends=1):
    return {
        "schema_version": "analysis-execution/1",
        "attempt_id": attempt_id,
        "state": state,
        "raw_sends": raw_sends,
        "reason_code": "completed",
        "elapsed_seconds": 1.0,
        "budget_seconds": 900,
        "completion_guarantee": "none",
        "retention": "process_local_bounded_64_no_result",
    }


def result(*, soc=True):
    metadata = {
        "model": "qwen3:8b",
        "checks": list(SOC_CHECKS if soc else COMMON_CHECKS),
    }
    if soc:
        metadata.update(
            repair_attempted=False, repair_succeeded=None, integrity_status="passed"
        )
    return {
        "analysis": SOC_RESPONSE if soc else GOVERNANCE_RESPONSE,
        "metadata": metadata,
    }


def completed(attempt_id, *, soc=True):
    return {
        "schema_version": "analysis-lifecycle-response/1",
        "execution": execution(attempt_id),
        "result": result(soc=soc),
    }


class Response:
    def __init__(self, body, status_code=200):
        self.body, self.status_code = body, status_code

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def iter_content(self, chunk_size):
        for offset in range(0, len(self.body), chunk_size):
            yield self.body[offset : offset + chunk_size]


def transport(
    monkeypatch,
    *,
    backend=None,
    body=None,
    status_code=200,
    failure=None,
    lose_reply=False,
):
    calls = []

    class Session:
        trust_env = True

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def _request(self, method, url, **kwargs):
            calls.append((method, url, kwargs))
            assert self.trust_env is False
            assert kwargs["stream"] is True and kwargs["allow_redirects"] is False
            if failure:
                raise failure
            if backend:
                forwarded = {
                    k: v for k, v in kwargs.items() if k in {"headers", "data"}
                }
                if "data" in forwarded:
                    forwarded["content"] = forwarded.pop("data")
                response = backend.request(method, urlsplit(url).path, **forwarded)
                if lose_reply and method == "POST":
                    raise requests.ReadTimeout("PRIVATE LOST REPLY")
                return Response(response.content, response.status_code)
            response_body = body(url, kwargs) if callable(body) else body
            return Response(response_body or b"", status_code)

        def post(self, url, **kwargs):
            return self._request("POST", url, **kwargs)

        def get(self, url, **kwargs):
            return self._request("GET", url, **kwargs)

    monkeypatch.setattr(requests, "Session", Session)
    return calls


def open_page(monkeypatch, *, soc=True):
    monkeypatch.setenv("ENABLE_INFERENCE_LIFECYCLE", "1")
    monkeypatch.setenv("API_BASE_URL", BASE)
    app = AppTest.from_file(ENTRY, default_timeout=20).run()
    return app.switch_page(PAGES[soc]).run()


def button(app, label):
    return next(item for item in app.button if item.label == label)


def submit_button(app, *, soc=True):
    return button(app, "Analyze SOC alert" if soc else "Review AI system")


def mocked_analyzers(monkeypatch):
    calls = []

    def soc(request, **kwargs):
        calls.append("soc")
        return SocAlertResponse(**SOC_RESPONSE)

    def governance(request):
        calls.append("governance")
        return GovernanceRiskResponse(**GOVERNANCE_RESPONSE)

    monkeypatch.setattr(main, "analyze_soc_alert", soc)
    monkeypatch.setattr(main, "analyze_governance_risk", governance)
    monkeypatch.setattr(main, "write_audit_log", lambda **kwargs: None)
    return calls


@pytest.mark.parametrize("soc", [True, False])
def test_real_route_to_lifecycle_client_page_and_exports_with_no_auto_submit(
    monkeypatch, soc
):
    from app import lifecycle_api

    analyzer_calls = mocked_analyzers(monkeypatch)
    monkeypatch.setenv("ENABLE_INFERENCE_LIFECYCLE", "1")
    with TestClient(lifecycle_api.create_app()) as backend:
        calls = transport(monkeypatch, backend=backend)
        app = open_page(monkeypatch, soc=soc)
        assert not app.exception and not calls
        assert any(
            "Experimental inference lifecycle" in item.value for item in app.info
        )
        submit_button(app, soc=soc).click().run()
        assert not app.exception, app.exception
        assert len(calls) == 1 and calls[0][0] == "POST"
        attempt_id = calls[0][2]["headers"]["X-Analysis-Attempt-ID"]
        assert "Attempt ID: " + attempt_id in [item.value for item in app.text]
        assert any(
            "Record this correlation ID before waiting" in item.value
            for item in app.caption
        )
        assert calls[0][1].endswith("soc-alert" if soc else "governance")
        assert calls[0][2]["timeout"] == (5, 930)
        assert len(app.get("download_button")) == 2
        assert analyzer_calls == (["soc"] if soc else ["governance"])
        assert not app.session_state.filtered_state.get(client.GUARD_KEY)
        app.run()
        assert not app.exception and len(calls) == 1
        assert len(app.get("download_button")) == 2


def test_lost_reply_guard_survives_session_rerun_sample_input_cross_workflow_and_status(
    monkeypatch,
):
    from app import lifecycle_api

    analyzer_calls = mocked_analyzers(monkeypatch)
    monkeypatch.setenv("ENABLE_INFERENCE_LIFECYCLE", "1")
    with TestClient(lifecycle_api.create_app()) as backend:
        calls = transport(monkeypatch, backend=backend, lose_reply=True)
        app = open_page(monkeypatch)
        submit_button(app).click().run()
        assert not app.exception and len(calls) == 1
        attempt = app.session_state[client.GUARD_KEY]["attempt_id"]
        app.run()
        assert submit_button(app).disabled
        assert any("within the active session" in item.value for item in app.warning)
        assert any(
            "A full browser reload, new session or tab" in item.value
            for item in app.caption
        )
        app.text_input(key="soc_alert_id").set_value("SYN-CHANGED").run()
        button(app, "Load sample").click().run()
        assert app.session_state[client.GUARD_KEY]["attempt_id"] == attempt
        assert submit_button(app).disabled and len(calls) == 1
        app.switch_page(PAGES[False]).run()
        assert submit_button(app, soc=False).disabled
        assert app.session_state[client.GUARD_KEY]["attempt_id"] == attempt
        button(app, "Check analysis attempt status").click().run()
        assert len(calls) == 2 and calls[-1][0] == "GET"
        assert any(
            "lost analyst result cannot be recovered" in item.value for item in app.info
        )
        assert submit_button(app, soc=False).disabled
        assert analyzer_calls == ["soc"]
        assert button(app, "Acknowledge and allow a fresh analysis").disabled
        app.checkbox(key="lifecycle_ack_" + attempt).check().run()
        button(app, "Acknowledge and allow a fresh analysis").click().run()
        assert not app.exception and len(calls) == 2
        assert not submit_button(app, soc=False).disabled
        submit_button(app, soc=False).click().run()
        assert len(calls) == 3 and analyzer_calls == ["soc", "governance"]
        assert (
            calls[0][2]["headers"]["X-Analysis-Attempt-ID"]
            != calls[2][2]["headers"]["X-Analysis-Attempt-ID"]
        )


@pytest.mark.parametrize(
    "failure", [requests.Timeout("PRIVATE"), requests.ConnectionError("PRIVATE")]
)
def test_uncertain_client_failure_is_one_post_and_guarded_after_flag_change(
    monkeypatch, failure
):
    calls = transport(monkeypatch, failure=failure)
    app = open_page(monkeypatch)
    submit_button(app).click().run()
    app.run()
    assert not app.exception and len(calls) == 1
    assert submit_button(app).disabled
    assert client.UNKNOWN_ERROR in [item.value for item in app.error]
    assert all("PRIVATE" not in item.value for item in app.error)
    monkeypatch.delenv("ENABLE_INFERENCE_LIFECYCLE")
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: pytest.fail("guard must prevent legacy dispatch"),
    )
    app.run()
    assert not app.exception and submit_button(app).disabled and len(calls) == 1


def test_guard_blocks_microsoft_workspace_and_sample_load_cannot_clear_it(monkeypatch):
    calls = transport(monkeypatch, failure=requests.Timeout())
    app = open_page(monkeypatch)
    submit_button(app).click().run()
    app.selectbox(key="soc_input_profile").select("Microsoft Security telemetry").run()
    assert not app.exception and len(calls) == 1
    assert any(
        "Resolve the earlier analysis attempt" in item.value for item in app.warning
    )
    assert not app.file_uploader
    app.selectbox(key="soc_input_profile").select(
        "Generic / normalized SOC input"
    ).run()
    button(app, "Load sample").click().run()
    assert submit_button(app).disabled and app.session_state[client.GUARD_KEY]


def test_unexpected_client_callback_error_keeps_guard_and_hides_exception(monkeypatch):
    calls = []

    def callback(*args, **kwargs):
        calls.append(1)
        raise RuntimeError("PRIVATE CALLBACK")

    monkeypatch.setattr(client, "post_lifecycle_analysis", callback)
    app = open_page(monkeypatch)
    submit_button(app).click().run()
    app.run()
    assert not app.exception and calls == [1]
    assert submit_button(app).disabled and app.session_state[client.GUARD_KEY]
    assert client.UNKNOWN_ERROR in [item.value for item in app.error]


@pytest.mark.parametrize(
    "base",
    [
        "http://192.0.2.10",
        "https://example.invalid",
        "http://user:secret@127.0.0.1",
        "http://127.0.0.1/redirect",
    ],
)
def test_client_rejects_nonloopback_or_credential_address_before_send(
    monkeypatch, base
):
    calls = transport(monkeypatch)
    outcome = client.post_lifecycle_analysis(
        base, soc=True, payload=SOC_INPUT, attempt_id=str(uuid4())
    )
    assert outcome.error == client.BEFORE_DISPATCH_ERROR and outcome.keep_guard is False
    assert not calls


@pytest.mark.parametrize("kind", ["bad_config", "bad_uuid", "wire_budget"])
def test_invalid_local_contract_never_dispatches(monkeypatch, kind):
    calls = transport(monkeypatch)
    attempt, payload = str(uuid4()), dict(SOC_INPUT)
    if kind == "bad_config":
        monkeypatch.setenv("ANALYSIS_BUDGET_SECONDS", "not-a-budget")
    elif kind == "bad_uuid":
        attempt = "forged"
    else:
        monkeypatch.setattr(client, "MAX_WIRE_BYTES", 10)
    outcome = client.post_lifecycle_analysis(
        BASE, soc=True, payload=payload, attempt_id=attempt
    )
    assert (
        outcome.error == client.BEFORE_DISPATCH_ERROR
        and not outcome.keep_guard
        and not calls
    )


@pytest.mark.parametrize(
    "kind",
    [
        "wrong_id",
        "duplicate_json",
        "response_budget",
        "forged_result",
        "redirect",
        "unstructured_error",
    ],
)
def test_response_integrity_or_dispatch_ambiguity_keeps_guard(monkeypatch, kind):
    attempt = str(uuid4())
    body, status = completed(attempt), 200
    if kind == "wrong_id":
        body["execution"]["attempt_id"] = str(uuid4())
    elif kind == "forged_result":
        body["result"] = {"analysis": {}, "metadata": {}}
    elif kind == "redirect":
        status = 307
    elif kind == "unstructured_error":
        body, status = {"detail": "PRIVATE"}, 500
    encoded = json.dumps(body).encode()
    if kind == "duplicate_json":
        encoded = b'{"execution":{},"execution":{}}'
    elif kind == "response_budget":
        monkeypatch.setattr(client, "MAX_RESPONSE_BYTES", 10)
    calls = transport(monkeypatch, body=encoded, status_code=status)
    outcome = client.post_lifecycle_analysis(
        BASE, soc=True, payload=SOC_INPUT, attempt_id=attempt
    )
    assert outcome.error == client.UNKNOWN_ERROR and outcome.keep_guard
    assert len(calls) == 1


@pytest.mark.parametrize(
    "state,keep",
    [
        ("failed_known", False),
        ("rejected_before_dispatch", False),
        ("unknown_post_dispatch", True),
        ("running", True),
    ],
)
def test_validated_lifecycle_failure_distinguishes_known_and_uncertain(
    monkeypatch, state, keep
):
    attempt = str(uuid4())
    body = {
        "detail": {
            "code": "analysis_lifecycle_withheld",
            "execution": execution(
                attempt,
                state=state,
                raw_sends=0 if state in {"rejected_before_dispatch", "running"} else 1,
            ),
        }
    }
    calls = transport(monkeypatch, body=json.dumps(body).encode(), status_code=500)
    outcome = client.post_lifecycle_analysis(
        BASE, soc=True, payload=SOC_INPUT, attempt_id=attempt
    )
    assert len(calls) == 1 and outcome.execution["state"] == state
    assert outcome.keep_guard is keep and outcome.error


@pytest.mark.parametrize(
    "kind", ["missing", "wrong_id", "size", "duplicate", "redirect"]
)
def test_status_lookup_is_bounded_metadata_only_and_missing_is_unknown(
    monkeypatch, kind
):
    attempt = str(uuid4())
    body, status = execution(attempt), 200
    if kind == "missing":
        body, status = {"detail": "missing"}, 404
    elif kind == "wrong_id":
        body["attempt_id"] = str(uuid4())
    elif kind == "size":
        monkeypatch.setattr(client, "MAX_STATUS_BYTES", 10)
    elif kind == "redirect":
        status = 307
    encoded = json.dumps(body).encode()
    if kind == "duplicate":
        encoded = b'{"state":"running","state":"completed_validated"}'
    calls = transport(monkeypatch, body=encoded, status_code=status)
    result, error = client.get_lifecycle_status(BASE, attempt)
    assert result is None and error == client.STATUS_ERROR
    assert len(calls) == 1 and calls[0][0] == "GET"


def test_duplicate_attempt_error_never_silently_releases_guard(monkeypatch):
    attempt = str(uuid4())
    body = {
        "detail": {
            "code": "analysis_attempt_reused",
            "execution": execution(attempt, state="failed_known"),
        }
    }
    calls = transport(monkeypatch, body=json.dumps(body).encode(), status_code=409)
    outcome = client.post_lifecycle_analysis(
        BASE, soc=True, payload=SOC_INPUT, attempt_id=attempt
    )
    assert len(calls) == 1 and outcome.keep_guard is True
    assert outcome.execution["state"] == "failed_known"
