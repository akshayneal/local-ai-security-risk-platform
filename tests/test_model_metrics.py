import json

import pytest

from app import ollama_client
from app.model_metrics import configured_context, local_model_metrics


def test_usage_is_allowlisted_and_opt_in(monkeypatch):
    calls = []

    def chat(**kw):
        calls.append(kw)
        return {
            "message": {"content": '{"ok":true}'},
            "prompt_eval_count": 3123,
            "eval_count": 52,
            "total_duration": 123,
            "raw": "secret",
            "done_reason": "length",
        }

    monkeypatch.setattr(ollama_client.client, "chat", chat)
    assert ollama_client.call_model_json("secret", {}) == {"ok": True}
    assert calls[-1]["options"] == {"temperature": 0.1}
    with local_model_metrics(num_ctx=8192) as metrics:
        ollama_client.call_model_json("secret", {})
    record = metrics.attempts[0]
    assert record["prompt_eval_count"] == 3123
    assert record["load_duration"] is None
    assert record["context_status"] == "generation_limit"
    assert record["prompt_retention"] == "not_proven"
    assert "secret" not in json.dumps(record)
    assert calls[-1]["options"]["num_ctx"] == 8192
    assert configured_context() is None


def test_missing_or_hostile_metadata(monkeypatch):
    monkeypatch.setattr(
        ollama_client.client,
        "chat",
        lambda **kw: {
            "message": {"content": "{}"},
            "eval_count": "sensitive",
            "load_duration": -1,
            "prompt_eval_count": True,
        },
    )
    with local_model_metrics() as metrics:
        ollama_client.call_model_json("x", {})
    assert metrics.attempts[0]["eval_count"] is None
    assert metrics.attempts[0]["prompt_eval_count"] is None
    assert metrics.attempts[0]["load_duration"] is None


@pytest.mark.parametrize("value", [0, -1, 32768, "8192", True])
def test_unsupported_context(value):
    with (
        pytest.raises(ValueError, match="Unsupported"),
        local_model_metrics(num_ctx=value),
    ):
        pass


def test_retries_and_json_failure_are_safe(monkeypatch):
    monkeypatch.setattr(
        ollama_client.client,
        "chat",
        lambda **kw: {"message": {"content": "PRIVATE TELEMETRY"}},
    )
    with local_model_metrics() as metrics, pytest.raises(Exception) as error:
        ollama_client.call_model_json("secret", {})
    assert len(metrics.attempts) == 2
    assert all(a["status"] == "invalid_json" for a in metrics.attempts)
    assert "PRIVATE" not in str(error.value)
