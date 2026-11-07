"""Prospective lifecycle acceptance with clocks/transports only; no model sends."""

import json
from copy import deepcopy
from uuid import uuid4

import pytest
import requests
from fastapi.testclient import TestClient
from test_schemas import (
    GOVERNANCE_INPUT,
    GOVERNANCE_RESPONSE,
    SOC_INPUT,
    SOC_RESPONSE,
)

from app import governance_analyzer, lifecycle_api, main, ollama_client, soc_analyzer
from app.inference_context import EvidenceBudgetError, microsoft_model_context
from app.inference_lifecycle import (
    ATTEMPT_HEADER,
    PREFIX,
    AttemptReused,
    BudgetConfig,
    Execution,
    ExecutionRegistry,
    InferenceLifecycleError,
    RegistryFull,
    current_execution,
    execution_scope,
    load_config,
)
from app.model_metrics import local_model_metrics
from app.schemas import SocAlertRequest
from app.ui_schemas import ProductTrace


def attempt():
    return str(uuid4())


@pytest.fixture
def clock():
    return [0.0]


@pytest.fixture
def execution(clock):
    return Execution(attempt(), BudgetConfig(), 2, clock=lambda: clock[0])


@pytest.fixture
def transport(monkeypatch, clock):
    state = {
        "gets": [],
        "posts": [],
        "closed": [],
        "version": "0.40.13",
        "status": 200,
        "elapsed_get": 0,
        "elapsed_post": 0,
        "failure": None,
        "body": {
            "done": True,
            "done_reason": "stop",
            "message": {"content": json.dumps(SOC_RESPONSE)},
            "prompt_eval_count": 40,
            "eval_count": 20,
        },
    }

    class Response:
        def __init__(self, status, data):
            self.status_code = status
            self.data = data

        def iter_content(self, chunk_size):
            assert chunk_size == 8192
            yield (
                self.data
                if isinstance(self.data, bytes)
                else json.dumps(self.data).encode()
            )

        def close(self):
            state["closed"].append(self)

    class Session:
        trust_env = True

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, **kwargs):
            assert not self.trust_env and not kwargs["allow_redirects"]
            assert kwargs["stream"] is True
            state["gets"].append((url, kwargs))
            clock[0] += state["elapsed_get"]
            if state["failure"] == "get":
                raise requests.Timeout("PRIVATE PREFLIGHT")
            return Response(200, {"version": state["version"]})

        def post(self, url, **kwargs):
            assert not self.trust_env and not kwargs["allow_redirects"]
            assert kwargs["stream"] is True
            state["posts"].append((url, kwargs))
            clock[0] += state["elapsed_post"]
            if state["failure"] == "post":
                raise requests.ConnectionError("PRIVATE POST")
            body = state["body"]
            if callable(body):
                body = body(len(state["posts"]))
            return Response(state["status"], deepcopy(body))

    monkeypatch.setattr(ollama_client.requests, "Session", Session)
    monkeypatch.setattr(
        ollama_client.client,
        "chat",
        lambda **kw: pytest.fail("Lifecycle must never fall back to legacy SDK"),
    )
    return state


@pytest.mark.parametrize(
    "field,value",
    [
        ("ANALYSIS_BUDGET_SECONDS", "29"),
        ("ANALYSIS_BUDGET_SECONDS", "1201"),
        ("ANALYSIS_CONNECT_SECONDS", "0"),
        ("ANALYSIS_READ_SECONDS", "1201"),
        ("ANALYSIS_UI_MARGIN_SECONDS", "4"),
        ("ANALYSIS_CONNECT_SECONDS", "true"),
        ("ANALYSIS_READ_SECONDS", "900.0"),
    ],
)
def test_operator_budget_validation(monkeypatch, field, value):
    monkeypatch.setenv(field, value)
    with pytest.raises(ValueError):
        load_config()


def test_budget_configuration_is_coordinated_and_strict(monkeypatch):
    assert load_config().ui_timeout == 930
    with pytest.raises(ValueError):
        BudgetConfig(total_seconds=30, read_seconds=31)
    with pytest.raises(ValueError):
        BudgetConfig(connect_seconds=True)
    monkeypatch.setenv("ANALYSIS_BUDGET_SECONDS", "1200")
    assert load_config().total_seconds == 1200


@pytest.mark.parametrize("complete", [False, True])
def test_active_transport_uses_one_send_and_preserves_metrics(
    transport, execution, complete
):
    with (
        execution_scope(execution),
        microsoft_model_context(complete),
        local_model_metrics() as metrics,
    ):
        assert ollama_client.call_model_json("PRIVATE TELEMETRY", {}) == SOC_RESPONSE
    assert execution.raw_sends == len(transport["posts"]) == len(metrics.attempts) == 1
    assert len(transport["gets"]) == int(complete)
    body = transport["posts"][0][1]["json"]
    assert body["stream"] is False
    if complete:
        assert body["truncate"] is body["shift"] is False
        assert body["options"]["num_ctx"] == 8192
    else:
        assert "truncate" not in body and "num_ctx" not in body["options"]
    assert metrics.attempts[0]["prompt_eval_count"] == 40
    assert "PRIVATE" not in json.dumps(metrics.attempts)
    assert current_execution() is None


@pytest.mark.parametrize("complete", [False, True])
def test_post_disconnect_never_retries_and_remains_unknown(
    transport, execution, complete
):
    transport["failure"] = "post"
    with (
        execution_scope(execution),
        microsoft_model_context(complete),
        pytest.raises(InferenceLifecycleError) as exc,
    ):
        ollama_client.call_model_json("PRIVATE", {})
    assert isinstance(exc.value, EvidenceBudgetError)
    assert execution.state == "unknown_post_dispatch"
    assert execution.raw_sends == len(transport["posts"]) == 1
    assert "PRIVATE" not in str(exc.value) + execution.snapshot().model_dump_json()
    assert current_execution() is None


def test_preflight_timeout_is_rejected_before_dispatch_without_retry(
    transport, execution
):
    transport["failure"] = "get"
    with (
        execution_scope(execution),
        microsoft_model_context(True),
        pytest.raises(InferenceLifecycleError),
    ):
        ollama_client.call_model_json("synthetic", {})
    assert execution.state == "rejected_before_dispatch"
    assert not transport["posts"] and len(transport["gets"]) == 1


def test_elapsed_preflight_cannot_dispatch_or_fall_back(transport, execution):
    transport["elapsed_get"] = 901
    with (
        execution_scope(execution),
        microsoft_model_context(True),
        pytest.raises(InferenceLifecycleError),
    ):
        ollama_client.call_model_json("synthetic", {})
    assert execution.reason_code == "elapsed_budget_exhausted"
    assert execution.raw_sends == 0 and not transport["posts"]
    assert len(transport["closed"]) == 1


def test_slow_responsive_send_can_complete_within_remaining_budget(
    transport, execution, clock
):
    transport.update(elapsed_get=9, elapsed_post=880)
    with execution_scope(execution), microsoft_model_context(True):
        ollama_client.call_model_json("synthetic", {})
        execution.complete()
    assert execution.state == "completed_validated"
    assert execution.snapshot().elapsed_seconds == 889
    assert transport["posts"][0][1]["timeout"] == (5, 891)
    clock[0] += 100
    assert execution.snapshot().elapsed_seconds == 889


def test_elapsed_socket_wait_withholds_late_response_without_cancellation_claim(
    transport, execution
):
    transport["elapsed_post"] = 901
    with execution_scope(execution), pytest.raises(InferenceLifecycleError):
        ollama_client.call_model_json("synthetic", {})
    assert execution.raw_sends == 1
    assert execution.state == "unknown_post_dispatch"
    assert execution.snapshot().completion_guarantee == "none"


@pytest.mark.parametrize(
    "host",
    [
        "https://127.0.0.1:11434",
        "http://example.invalid:11434",
        "http://user:secret@localhost:11434",
        "http://localhost:11434/path",
        "http://localhost:11434?scope=all",
        "http://localhost:99999",
    ],
)
def test_no_remote_redirect_proxy_or_credentialed_provider(
    transport, execution, monkeypatch, host
):
    monkeypatch.setattr(ollama_client, "OLLAMA_HOST", host)
    with execution_scope(execution), pytest.raises(InferenceLifecycleError):
        ollama_client.call_model_json("synthetic", {})
    assert execution.state == "rejected_before_dispatch"
    assert not transport["gets"] and not transport["posts"]


@pytest.mark.parametrize(
    "status,expected",
    [
        (301, "unknown_post_dispatch"),
        (500, "unknown_post_dispatch"),
        (400, "failed_known"),
        (413, "failed_known"),
    ],
)
def test_provider_error_response_never_retries(transport, execution, status, expected):
    transport["status"] = status
    with execution_scope(execution), pytest.raises(InferenceLifecycleError):
        ollama_client.call_model_json("synthetic", {})
    assert execution.state == expected and execution.raw_sends == 1
    assert len(transport["closed"]) == 1


@pytest.mark.parametrize(
    "body,expected",
    [
        ({"done": False, "message": {"content": "{}"}}, "unknown_post_dispatch"),
        (
            {"done": True, "done_reason": "length", "message": {"content": "{}"}},
            "failed_known",
        ),
        (
            {"done": True, "message": {"content": "PRIVATE INVALID JSON"}},
            "failed_known",
        ),
        ({"done": True, "message": {"content": "[]"}}, "failed_known"),
        (b"PRIVATE INVALID RESPONSE", "unknown_post_dispatch"),
        (b"x" * 256001, "unknown_post_dispatch"),
    ],
    ids=[
        "incomplete",
        "generation_limit",
        "invalid_model_json",
        "wrong_model_shape",
        "invalid_response",
        "oversized_response",
    ],
)
def test_incomplete_malformed_or_oversized_output_cannot_retry(
    transport, execution, body, expected
):
    transport["body"] = body
    with execution_scope(execution), pytest.raises(InferenceLifecycleError):
        ollama_client.call_model_json("synthetic", {})
    assert execution.raw_sends == 1 and execution.state == expected


@pytest.mark.parametrize(
    "body",
    [
        b'{"done":false,"done":true,"message":{"content":"{}"}}',
        b'{"done":true,"unknown":NaN,"message":{"content":"{}"}}',
    ],
    ids=["duplicate_completion", "nonfinite"],
)
def test_ambiguous_provider_json_cannot_confirm_completion(transport, execution, body):
    transport["body"] = body
    with execution_scope(execution), pytest.raises(InferenceLifecycleError):
        ollama_client.call_model_json("synthetic", {})
    assert execution.state == "unknown_post_dispatch" and execution.raw_sends == 1


def test_callback_failure_is_wrapped_and_never_retries(
    transport, execution, monkeypatch
):
    def fail(*args):
        raise ValueError("PRIVATE CALLBACK")

    monkeypatch.setattr("app.inference_lifecycle.finish_attempt", fail)
    with execution_scope(execution), pytest.raises(InferenceLifecycleError):
        ollama_client.call_model_json("synthetic", {})
    assert execution.state == "failed_known" and len(transport["posts"]) == 1


@pytest.mark.parametrize("callback", ["start_attempt", "cleaner"])
def test_callback_failures_before_and_after_dispatch_are_distinct(
    transport, execution, monkeypatch, callback
):
    def fail(*args):
        raise ValueError("PRIVATE CALLBACK")

    if callback == "start_attempt":
        monkeypatch.setattr("app.inference_lifecycle.start_attempt", fail)
    else:
        monkeypatch.setattr(ollama_client, "_clean_model_json", fail)
    with execution_scope(execution), pytest.raises(InferenceLifecycleError):
        ollama_client.call_model_json("synthetic", {})
    assert execution.state == (
        "rejected_before_dispatch" if callback == "start_attempt" else "failed_known"
    )
    assert len(transport["posts"]) == int(callback == "cleaner")
    assert current_execution() is None


def test_cap_prevents_third_send_and_context_restores_outer_execution(
    transport, execution
):
    outer = Execution(attempt(), BudgetConfig(), 1)
    with execution_scope(outer):
        with execution_scope(execution):
            ollama_client.call_model_json("synthetic", {})
            ollama_client.call_model_json("synthetic", {})
            with pytest.raises(InferenceLifecycleError):
                ollama_client.call_model_json("synthetic", {})
        assert current_execution() is outer
    assert current_execution() is None
    assert execution.raw_sends == len(transport["posts"]) == 2
    assert execution.reason_code == "raw_send_cap_reached"


def test_unsupported_version_has_no_send_or_retry(transport, execution):
    transport["version"] = "0.40.11"
    with (
        execution_scope(execution),
        microsoft_model_context(True),
        pytest.raises(InferenceLifecycleError),
    ):
        ollama_client.call_model_json("synthetic", {})
    assert not transport["posts"] and len(transport["gets"]) == 1
    assert execution.state == "rejected_before_dispatch"


def test_real_soc_repair_has_two_raw_sends_with_shared_budget(transport, execution):
    transport["body"] = lambda n: {
        "done": True,
        "message": {
            "content": json.dumps(
                {**SOC_RESPONSE, "observed_evidence": []} if n == 1 else SOC_RESPONSE
            )
        },
    }
    trace = ProductTrace()
    with execution_scope(execution), local_model_metrics() as metrics:
        result = soc_analyzer.analyze_soc_alert(
            SocAlertRequest(**SOC_INPUT), references=[], trace=trace
        )
        execution.complete()
    assert (
        result.observed_evidence and trace.repair_attempted and not trace.repair_failed
    )
    assert execution.raw_sends == len(transport["posts"]) == len(metrics.attempts) == 2


def test_budget_exhausted_after_first_completed_output_prevents_repair(
    transport, execution, clock, monkeypatch
):
    transport["body"]["message"]["content"] = json.dumps(
        {**SOC_RESPONSE, "observed_evidence": []}
    )
    original = soc_analyzer._validate_generation

    def slow_validation(*args):
        clock[0] = 901
        return original(*args)

    monkeypatch.setattr(soc_analyzer, "_validate_generation", slow_validation)
    with execution_scope(execution), pytest.raises(InferenceLifecycleError):
        soc_analyzer.analyze_soc_alert(SocAlertRequest(**SOC_INPUT), references=[])
    assert execution.raw_sends == len(transport["posts"]) == 1
    assert execution.state == "failed_known"


def test_registry_duplicate_eviction_restart_and_no_result_retention(clock):
    registry = ExecutionRegistry(clock=lambda: clock[0])
    first_id = attempt()
    first = registry.reserve(first_id, BudgetConfig(), 1)
    with pytest.raises(AttemptReused):
        registry.reserve(first_id, BudgetConfig(), 1)
    first.complete()
    for _ in range(64):
        item = registry.reserve(attempt(), BudgetConfig(), 1)
        item.complete()
    assert registry.status(first_id) is None
    assert len(registry._entries) == 64
    # Eviction/restart removes the suppression guarantee; neither is no-dispatch proof.
    assert registry.reserve(first_id, BudgetConfig(), 1).raw_sends == 0
    assert ExecutionRegistry().status(first_id) is None
    assert set(first.snapshot().model_dump()) == {
        "schema_version",
        "attempt_id",
        "state",
        "raw_sends",
        "reason_code",
        "elapsed_seconds",
        "budget_seconds",
        "completion_guarantee",
        "retention",
    }
    assert not {"result", "prompt", "telemetry", "source_text"} & set(vars(first))


def test_registry_never_evicts_running_or_unknown_attempts():
    registry = ExecutionRegistry()
    for index in range(64):
        execution = registry.reserve(attempt(), BudgetConfig(), 1)
        if index % 2:
            execution.dispatch()
            execution.fail("provider_transport_uncertain")
    with pytest.raises(RegistryFull):
        registry.reserve(attempt(), BudgetConfig(), 1)
    assert len(registry._entries) == 64


@pytest.fixture
def api(monkeypatch, clock):
    monkeypatch.setenv("ENABLE_INFERENCE_LIFECYCLE", "1")
    monkeypatch.setattr(
        lifecycle_api, "REGISTRY", ExecutionRegistry(clock=lambda: clock[0])
    )
    monkeypatch.setattr(main, "write_audit_log", lambda **kw: None)
    monkeypatch.setattr(soc_analyzer, "get_relevant_references", lambda **kw: [])
    monkeypatch.setattr(governance_analyzer, "get_relevant_references", lambda **kw: [])
    return TestClient(lifecycle_api.create_app())


@pytest.mark.parametrize("soc", [True, False])
def test_actual_route_original_analyzer_status_and_duplicate_suppression(
    api, transport, soc
):
    attempt_id = attempt()
    endpoint = PREFIX + "/analyze/" + ("soc-alert" if soc else "governance")
    payload = SOC_INPUT if soc else GOVERNANCE_INPUT
    transport["body"]["message"]["content"] = json.dumps(
        SOC_RESPONSE if soc else GOVERNANCE_RESPONSE
    )
    response = api.post(endpoint, json=payload, headers={ATTEMPT_HEADER: attempt_id})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["execution"]["state"] == "completed_validated"
    assert body["execution"]["raw_sends"] == len(transport["posts"]) == 1
    assert "analysis" in body["result"] and "metadata" in body["result"]
    status = api.get(PREFIX + "/status/" + attempt_id)
    assert status.status_code == 200 and status.json() == body["execution"]
    repeat = api.post(endpoint, json=payload, headers={ATTEMPT_HEADER: attempt_id})
    assert repeat.status_code == 409
    assert repeat.json()["detail"]["code"] == "analysis_attempt_reused"
    assert len(transport["posts"]) == 1
    assert current_execution() is None


def test_api_unknown_is_lookupable_no_result_and_has_no_raw_data(api, transport):
    transport["failure"] = "post"
    attempt_id = attempt()
    response = api.post(
        PREFIX + "/analyze/soc-alert",
        json=SOC_INPUT,
        headers={ATTEMPT_HEADER: attempt_id},
    )
    assert response.status_code == 409
    status = response.json()["detail"]["execution"]
    assert status["state"] == "unknown_post_dispatch" and status["raw_sends"] == 1
    assert api.get(PREFIX + "/status/" + attempt_id).json() == status
    assert "PRIVATE" not in response.text and SOC_INPUT["raw_log"] not in response.text
    assert api.get(PREFIX + "/status/" + attempt()).status_code == 404


def test_gateway_revalidates_mutated_pydantic_result(api, monkeypatch):
    from app.ui_schemas import SocAnalysisEnvelope

    envelope = SocAnalysisEnvelope.model_validate(
        {
            "analysis": SOC_RESPONSE,
            "metadata": {
                "model": "synthetic",
                "repair_attempted": False,
                "repair_succeeded": None,
            },
        }
    )
    envelope.analysis.__dict__["severity"] = "forged"
    monkeypatch.setattr(main, "ui_soc_endpoint", lambda request: envelope)
    response = api.post(
        PREFIX + "/analyze/soc-alert",
        json=SOC_INPUT,
        headers={ATTEMPT_HEADER: attempt()},
    )
    assert response.status_code == 422 and "result" not in response.json()
    assert response.json()["detail"]["execution"]["state"] == "rejected_before_dispatch"


def test_gateway_withholds_validated_output_if_final_validation_runs_late(
    api, transport, monkeypatch, clock
):
    original = main.ui_soc_endpoint

    def late(request):
        result = original(request)
        clock[0] = 901
        return result

    monkeypatch.setattr(main, "ui_soc_endpoint", late)
    response = api.post(
        PREFIX + "/analyze/soc-alert",
        json=SOC_INPUT,
        headers={ATTEMPT_HEADER: attempt()},
    )
    assert response.status_code == 500
    status = response.json()["detail"]["execution"]
    assert status["state"] == "failed_known" and status["raw_sends"] == 1
    assert status["reason_code"] == "elapsed_budget_exhausted"


def test_gateway_result_budget_is_checked_before_completed_status(
    api, transport, monkeypatch
):
    monkeypatch.setattr(lifecycle_api, "MAX_RESULT_BYTES", 10)
    response = api.post(
        PREFIX + "/analyze/soc-alert",
        json=SOC_INPUT,
        headers={ATTEMPT_HEADER: attempt()},
    )
    assert response.status_code == 500
    status = response.json()["detail"]["execution"]
    assert status["state"] == "failed_known" and status["raw_sends"] == 1
    assert status["reason_code"] == "api_result_byte_budget"


@pytest.mark.parametrize(
    "mutation",
    ["missing_header", "invalid_id", "budget_body", "duplicate_keys", "oversized"],
)
def test_api_hostile_requests_never_dispatch(api, transport, mutation):
    payload, headers = deepcopy(SOC_INPUT), {ATTEMPT_HEADER: attempt()}
    kwargs = {"json": payload}
    if mutation == "missing_header":
        headers = {}
    elif mutation == "invalid_id":
        headers[ATTEMPT_HEADER] = "x" * 36
    elif mutation == "budget_body":
        payload["total_seconds"] = 1200
    elif mutation == "duplicate_keys":
        kwargs = {"content": '{"alert_id":"PRIVATE","alert_id":"forged"}'}
    else:
        kwargs = {"content": b"x" * 400001}
    response = api.post(PREFIX + "/analyze/soc-alert", headers=headers, **kwargs)
    assert response.status_code in {422, 413}
    assert not transport["posts"] and "PRIVATE" not in response.text


def test_default_off_route_absent_and_original_routes_still_composed(monkeypatch):
    monkeypatch.delenv("ENABLE_INFERENCE_LIFECYCLE", raising=False)
    client = TestClient(lifecycle_api.create_app())
    assert client.post(PREFIX + "/analyze/soc-alert", json=SOC_INPUT).status_code == 404
    assert client.get("/health").status_code == 200
    assert client.get("/ui/status").status_code == 200
