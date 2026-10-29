import json
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from test_schemas import SOC_INPUT, SOC_RESPONSE

from app import main, ollama_client
from app.inference_context import EvidenceBudgetError, microsoft_model_context
from app.model_metrics import configured_context, local_model_metrics
from dashboard.api_client import CONTEXT_ERROR, safe_error


@pytest.fixture
def transport(monkeypatch):
    state = {
        "version": "0.40.12",
        "status": 200,
        "body": {
            "done": True,
            "done_reason": "stop",
            "message": {"content": '{"ok":true}'},
            "prompt_eval_count": 2400,
            "eval_count": 40,
        },
        "calls": [],
    }

    class Response:
        def __init__(self, status, data):
            self.status_code, self.data = status, data

        def json(self):
            return self.data

    class Session:
        trust_env = True

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, url, **kw):
            assert not self.trust_env and not kw["allow_redirects"]
            return Response(200, {"version": state["version"]})

        def post(self, url, **kw):
            assert not self.trust_env and not kw["allow_redirects"]
            state["calls"].append(kw)
            return Response(state["status"], deepcopy(state["body"]))

    monkeypatch.setattr(ollama_client.requests, "Session", Session)
    return state


def test_protected_request_and_usage_without_content_retention(transport):
    with local_model_metrics() as metrics, microsoft_model_context(True):
        assert ollama_client.call_model_json("PRIVATE TELEMETRY", {}) == {"ok": True}
    body = transport["calls"][0]["json"]
    assert body["truncate"] is body["shift"] is False
    assert body["options"] == {"temperature": 0.1, "num_ctx": 8192}
    assert metrics.attempts[0]["configured_num_ctx"] == 8192
    assert metrics.attempts[0]["prompt_eval_count"] == 2400
    assert "PRIVATE" not in json.dumps(metrics.attempts)
    assert configured_context() is None


@pytest.mark.parametrize("status", [400, 413])
def test_rejected_full_input_has_one_attempt_no_raw_body_or_retry(transport, status):
    transport.update(status=status, body={"error": "PRIVATE RAW INPUT /private/path"})
    with (
        local_model_metrics() as metrics,
        microsoft_model_context(True),
        pytest.raises(EvidenceBudgetError) as exc,
    ):
        ollama_client.call_model_json("secret", {})
    assert len(transport["calls"]) == len(metrics.attempts) == 1
    assert metrics.attempts[0]["context_status"] == "request_rejected"
    assert "PRIVATE" not in str(exc.value) + json.dumps(metrics.attempts)


@pytest.mark.parametrize(
    "done,reason,code",
    [
        (True, "length", "generation_limit"),
        (False, "stop", "incomplete_generation"),
        (None, None, "incomplete_generation"),
    ],
)
def test_incomplete_or_capacity_stop_never_returns_partial_json(
    transport, done, reason, code
):
    transport["body"].update(done=done, done_reason=reason)
    with microsoft_model_context(True), pytest.raises(EvidenceBudgetError) as exc:
        ollama_client.call_model_json("x", {})
    assert exc.value.code == code
    assert len(transport["calls"]) == 1


@pytest.mark.parametrize("version", ["0.40.11", "0.6.2", None, "PRIVATE"])
def test_unsupported_runtime_has_no_inference_or_fallback(transport, version):
    transport["version"] = version
    with microsoft_model_context(True), pytest.raises(EvidenceBudgetError) as exc:
        ollama_client.call_model_json("x", {})
    assert exc.value.code == "runtime_unsupported" and not transport["calls"]


@pytest.mark.parametrize(
    "host",
    [
        "https://example.invalid",
        "http://user:secret@localhost:11434",
        "http://localhost:11434/private",
    ],
)
def test_protected_transport_never_sends_to_remote_or_credentialed_host(
    monkeypatch, transport, host
):
    monkeypatch.setattr(ollama_client, "OLLAMA_HOST", host)
    with microsoft_model_context(True), pytest.raises(EvidenceBudgetError):
        ollama_client.call_model_json("x", {})
    assert not transport["calls"]


@pytest.mark.parametrize("ui", [False, True])
def test_capacity_failure_is_explicit_safe_and_has_no_analysis(monkeypatch, ui):
    audits = []
    monkeypatch.setattr(main, "write_audit_log", lambda **kw: audits.append(kw))

    def reject(*a, **kw):
        raise EvidenceBudgetError("request_rejected")

    monkeypatch.setattr(main, "analyze_soc_alert", reject)
    with TestClient(main.app) as client:
        response = client.post(
            ("/ui" if ui else "") + "/analyze/soc-alert", json=SOC_INPUT
        )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "complete_context_unavailable"
    assert "analysis" not in response.json()
    assert len(audits) == 1 and not audits[0]["success"]
    assert (
        safe_error(
            422,
            {"detail": {"code": "complete_context_unavailable", "message": "PRIVATE"}},
        )
        == CONTEXT_ERROR
    )


def test_generic_transport_remains_sdk_default(monkeypatch, transport):
    calls = []
    monkeypatch.setattr(
        ollama_client.client,
        "chat",
        lambda **kw: (
            calls.append(kw) or {"message": {"content": json.dumps(SOC_RESPONSE)}}
        ),
    )
    assert ollama_client.call_model_json("generic", {}) == SOC_RESPONSE
    assert calls[0]["options"] == {"temperature": 0.1}
    assert not transport["calls"]
