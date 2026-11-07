"""Opt-in, cooperative analysis budgets; never cancellation or durable idempotency.

Only the versioned gateway enters this context. Legacy SDK/HTTP retry behavior
and historical runners retain their existing default execution seam.
"""

import json
import os
import re
import time
from collections import OrderedDict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from threading import Lock
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

import requests
from pydantic import Field, StrictInt, StrictStr, field_validator, model_validator

from app.inference_context import (
    EvidenceBudgetError,
    complete_context_required,
    generation_system_prompt,
)
from app.model_metrics import configured_context, finish_attempt, start_attempt
from app.prompts import SYSTEM_PROMPT
from app.support_contracts import SupportModel

ENABLE_FLAG = "ENABLE_INFERENCE_LIFECYCLE"
PREFIX = "/experimental/analysis-lifecycle/v1"
ATTEMPT_HEADER = "X-Analysis-Attempt-ID"
MAX_RESPONSE_BYTES = 256_000
REGISTRY_CAPACITY = 64
State = Literal[
    "running",
    "completed_validated",
    "rejected_before_dispatch",
    "failed_known",
    "unknown_post_dispatch",
]


class BudgetConfig(SupportModel):
    """Local-process configuration only; never accepted from an analysis body."""

    total_seconds: StrictInt = Field(default=900, ge=30, le=1200)
    connect_seconds: StrictInt = Field(default=5, ge=1, le=30)
    read_seconds: StrictInt = Field(default=900, ge=1, le=1200)
    ui_margin_seconds: StrictInt = Field(default=30, ge=5, le=120)

    @model_validator(mode="after")
    def coordinated_limits(self):
        if max(self.connect_seconds, self.read_seconds) > self.total_seconds:
            raise ValueError("transport_limits_exceed_analysis_budget")
        return self

    @property
    def ui_timeout(self) -> int:
        return self.total_seconds + self.ui_margin_seconds


def lifecycle_enabled() -> bool:
    return os.getenv(ENABLE_FLAG, "") == "1"


def load_config() -> BudgetConfig:
    values = {}
    for name, environment in (
        ("total_seconds", "ANALYSIS_BUDGET_SECONDS"),
        ("connect_seconds", "ANALYSIS_CONNECT_SECONDS"),
        ("read_seconds", "ANALYSIS_READ_SECONDS"),
        ("ui_margin_seconds", "ANALYSIS_UI_MARGIN_SECONDS"),
    ):
        value = os.getenv(environment)
        if value is not None:
            if not re.fullmatch(r"[0-9]{1,4}", value):
                raise ValueError("invalid_analysis_budget_configuration")
            values[name] = int(value)
    return BudgetConfig(**values)


class ExecutionStatus(SupportModel):
    schema_version: Literal["analysis-execution/1"] = "analysis-execution/1"
    attempt_id: StrictStr = Field(pattern=r"^[a-f0-9-]{36}$")
    state: State
    raw_sends: StrictInt = Field(ge=0, le=2)
    reason_code: StrictStr = Field(pattern=r"^[a-z_]{1,64}$")
    elapsed_seconds: float = Field(ge=0, allow_inf_nan=False)
    budget_seconds: StrictInt = Field(ge=30, le=1200)
    completion_guarantee: Literal["none"] = "none"
    retention: Literal["process_local_bounded_64_no_result"] = (
        "process_local_bounded_64_no_result"
    )

    @field_validator("attempt_id")
    @classmethod
    def canonical_uuid(cls, value):
        return valid_attempt_id(value)


class LifecycleResponse(SupportModel):
    schema_version: Literal["analysis-lifecycle-response/1"] = (
        "analysis-lifecycle-response/1"
    )
    execution: ExecutionStatus
    result: dict


class InferenceLifecycleError(EvidenceBudgetError):
    """Fixed safe error; subtype also prevents the legacy Tenacity retry."""

    def __init__(self, reason: str):
        super().__init__("request_rejected")
        self.code = reason
        self.args = ("Analysis withheld by the experimental execution lifecycle.",)


def valid_attempt_id(value: str) -> str:
    if not isinstance(value, str) or len(value) != 36 or str(UUID(value)) != value:
        raise ValueError("invalid_analysis_attempt_id")
    return value


@dataclass
class Execution:
    attempt_id: str
    config: BudgetConfig
    max_sends: int
    clock: Callable[[], float] = field(default_factory=lambda: time.monotonic)
    state: State = "running"
    raw_sends: int = 0
    reason_code: str = "analysis_started"
    response_complete: bool = False
    started: float = field(init=False)
    finished_elapsed: float | None = None

    def __post_init__(self):
        valid_attempt_id(self.attempt_id)
        if type(self.max_sends) is not int or self.max_sends not in (1, 2):
            raise ValueError("invalid_analysis_send_cap")
        self.started = self.clock()

    def elapsed(self) -> float:
        return max(0.0, self.clock() - self.started)

    def snapshot(self) -> ExecutionStatus:
        return ExecutionStatus(
            attempt_id=self.attempt_id,
            state=self.state,
            raw_sends=self.raw_sends,
            reason_code=self.reason_code,
            elapsed_seconds=round(
                self.elapsed()
                if self.finished_elapsed is None
                else self.finished_elapsed,
                3,
            ),
            budget_seconds=self.config.total_seconds,
        )

    def fail(self, reason: str) -> None:
        if self.state == "running":
            self.state = (
                "rejected_before_dispatch"
                if self.raw_sends == 0
                else "failed_known"
                if self.response_complete
                else "unknown_post_dispatch"
            )
            self.reason_code = reason
            self.finished_elapsed = self.elapsed()

    def reject(self, reason: str):
        self.fail(reason)
        raise InferenceLifecycleError(reason)

    def remaining(self) -> float:
        if self.state != "running":
            raise InferenceLifecycleError(self.reason_code)
        remaining = self.config.total_seconds - self.elapsed()
        if remaining <= 0:
            self.reject("elapsed_budget_exhausted")
        return remaining

    def timeouts(self, *, preflight: bool = False) -> tuple[float, float]:
        remaining = self.remaining()
        return (
            min(self.config.connect_seconds, remaining),
            min(self.config.read_seconds, remaining, 10 if preflight else remaining),
        )

    def dispatch(self) -> None:
        self.remaining()
        if self.raw_sends >= self.max_sends:
            self.reject("raw_send_cap_reached")
        self.raw_sends += 1
        self.response_complete = False
        self.reason_code = "provider_dispatch_attempted"

    def complete(self) -> None:
        self.remaining()
        self.state = "completed_validated"
        self.reason_code = "validated_result_returned"
        self.finished_elapsed = self.elapsed()


_ACTIVE: ContextVar[Execution | None] = ContextVar("analysis_execution", default=None)


def current_execution() -> Execution | None:
    return _ACTIVE.get()


@contextmanager
def execution_scope(execution: Execution) -> Iterator[Execution]:
    token = _ACTIVE.set(execution)
    try:
        yield execution
    finally:
        _ACTIVE.reset(token)


class AttemptReused(ValueError):
    def __init__(self, status: ExecutionStatus):
        self.status = status
        super().__init__("analysis_attempt_reused")


class RegistryFull(ValueError):
    pass


class ExecutionRegistry:
    """At most 64 metadata entries; protect running/uncertain attempts from eviction.

    Terminal entries may be evicted. A missing entry, a new registry or restart
    proves nothing about previous dispatch. No result/prompt/telemetry is stored.
    """

    def __init__(self, *, clock: Callable[[], float] | None = None):
        self._clock = clock
        self._entries: OrderedDict[str, Execution] = OrderedDict()
        self._lock = Lock()

    def reserve(
        self, attempt_id: str, config: BudgetConfig, max_sends: int
    ) -> Execution:
        valid_attempt_id(attempt_id)
        with self._lock:
            if attempt_id in self._entries:
                raise AttemptReused(self._entries[attempt_id].snapshot())
            if len(self._entries) >= REGISTRY_CAPACITY:
                evictable = next(
                    (
                        key
                        for key, value in self._entries.items()
                        if value.state not in {"running", "unknown_post_dispatch"}
                    ),
                    None,
                )
                if evictable is None:
                    raise RegistryFull("analysis_registry_full")
                del self._entries[evictable]
            execution = Execution(
                attempt_id,
                config,
                max_sends,
                clock=self._clock or time.monotonic,
            )
            self._entries[attempt_id] = execution
            return execution

    def status(self, attempt_id: str) -> ExecutionStatus | None:
        valid_attempt_id(attempt_id)
        with self._lock:
            execution = self._entries.get(attempt_id)
            return None if execution is None else execution.snapshot()


def _local_host(host: str) -> str:
    parsed = urlsplit(host)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or (parsed.port is not None and not 1 <= parsed.port <= 65535)
    ):
        raise ValueError("unsupported_local_provider_address")
    return host.rstrip("/")


def _unique_keys(pairs):
    value = {}
    for key, child in pairs:
        if key in value:
            raise ValueError("duplicate_provider_key")
        value[key] = child
    return value


def _reject_nonfinite(_):
    raise ValueError("nonfinite_provider_value")


def _strict_json(value):
    return json.loads(
        value, object_pairs_hook=_unique_keys, parse_constant=_reject_nonfinite
    )


def _read_json(response, execution: Execution, limit: int) -> dict:
    """Bound response bytes and check elapsed time between transport reads.

    These checks cannot interrupt a blocked socket read or cancel Ollama.
    """
    body = bytearray()
    try:
        for chunk in response.iter_content(chunk_size=8192):
            execution.remaining()
            if len(body) + len(chunk) > limit:
                execution.reject("provider_response_byte_budget")
            body.extend(chunk)
        execution.remaining()
        value = _strict_json(body)
        if not isinstance(value, dict):
            execution.reject("invalid_provider_response")
        return value
    finally:
        response.close()


def _transport(messages, response_schema, options, *, host, model, execution):
    complete = complete_context_required()
    host = _local_host(host)
    with requests.Session() as session:
        session.trust_env = False
        if complete:
            response = session.get(
                host + "/api/version",
                timeout=execution.timeouts(preflight=True),
                allow_redirects=False,
                stream=True,
            )
            status = response.status_code
            data = _read_json(response, execution, 4096)
            version = data.get("version")
            if (
                status != 200
                or not isinstance(version, str)
                or not re.fullmatch(r"\d+\.\d+\.\d+", version)
                or tuple(map(int, version.split("."))) < (0, 40, 12)
            ):
                execution.reject("runtime_unsupported")
        payload = {
            "model": model,
            "messages": messages,
            "format": response_schema,
            "options": options,
            "stream": False,
        }
        if complete:
            payload.update(truncate=False, shift=False)
        timeout = execution.timeouts()
        execution.dispatch()
        response = session.post(
            host + "/api/chat",
            json=payload,
            timeout=timeout,
            allow_redirects=False,
            stream=True,
        )
        status = response.status_code
        if status != 200:
            response.close()
            if status in {400, 413}:
                execution.response_complete = True
                execution.reject("provider_request_rejected")
            execution.reject("provider_status_uncertain")
        data = _read_json(response, execution, MAX_RESPONSE_BYTES)
        if data.get("done") is not True or "error" in data:
            execution.reject("provider_completion_unconfirmed")
        execution.response_complete = True
        execution.remaining()
        if data.get("done_reason") == "length":
            execution.reject("generation_limit")
        return data


def bounded_model_json(
    user_prompt: str,
    response_schema: dict,
    *,
    host: str,
    model: str,
    temperature: float,
    cleaner: Callable[[str], str],
) -> dict:
    """One transport send per generation; every error suppresses legacy retry.

    The original analyzer retains ownership of validation and its one SOC repair.
    Generic lifecycle requests deliberately use this HTTP path instead of SDK.
    """
    execution = current_execution()
    if execution is None:
        raise InferenceLifecycleError("missing_execution_context")
    record = None
    started = time.perf_counter()
    try:
        execution.remaining()
        record = start_attempt(user_prompt, response_schema)
        system_prompt = generation_system_prompt() or SYSTEM_PROMPT
        if record is not None:
            record["system_utf8_bytes"] = len(system_prompt.encode("utf-8"))
        options = {"temperature": temperature}
        if configured_context() is not None:
            options["num_ctx"] = configured_context()
        response = _transport(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_schema,
            options,
            host=host,
            model=model,
            execution=execution,
        )
        finish_attempt(record, response, started)
        content = response["message"]["content"]
        value = _strict_json(cleaner(content))
        if not isinstance(value, dict):
            execution.reject("invalid_model_json_shape")
        execution.remaining()
        return value
    except InferenceLifecycleError as exc:
        if record is not None:
            record.update(context_status=exc.code, lifecycle_state=execution.state)
        raise
    except Exception as exc:  # noqa: BLE001 -- no callback/transport error may reach Tenacity
        reason = (
            "provider_transport_uncertain"
            if isinstance(exc, requests.RequestException) and execution.raw_sends
            else "provider_preflight_failed"
            if isinstance(exc, requests.RequestException)
            else "local_runtime_or_output_failure"
        )
        execution.fail(reason)
        if record is not None:
            record.update(context_status=reason, lifecycle_state=execution.state)
        raise InferenceLifecycleError(reason) from None
