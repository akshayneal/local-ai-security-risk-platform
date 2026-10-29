"""Opt-in local experiment metrics and bounded context overrides, never prompts."""

import json
import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field

from app.prompts import SYSTEM_PROMPT

_USAGE = (
    "prompt_eval_count",
    "eval_count",
    "total_duration",
    "load_duration",
    "prompt_eval_duration",
    "eval_duration",
)


@dataclass
class ModelMetrics:
    num_ctx: int | None = None
    attempts: list[dict] = field(default_factory=list)


_ACTIVE: ContextVar[ModelMetrics | None] = ContextVar(
    "local_model_metrics", default=None
)


@contextmanager
def local_model_metrics(*, num_ctx: int | None = None) -> Iterator[ModelMetrics]:
    """Explicit evaluation scope; defaults never change server context settings."""
    if num_ctx is not None and (
        type(num_ctx) is not int or num_ctx not in (4096, 8192)
    ):
        raise ValueError("Unsupported experimental context size")
    metrics = ModelMetrics(num_ctx=num_ctx)
    token = _ACTIVE.set(metrics)
    try:
        yield metrics
    finally:
        _ACTIVE.reset(token)


def configured_context() -> int | None:
    metrics = _ACTIVE.get()
    return metrics.num_ctx if metrics else None


def start_attempt(user_prompt: str, schema: dict) -> dict | None:
    metrics = _ACTIVE.get()
    if metrics is None or len(metrics.attempts) >= 8:
        return None
    record = {
        "configured_num_ctx": metrics.num_ctx,
        "system_utf8_bytes": len(SYSTEM_PROMPT.encode()),
        "user_utf8_bytes": len(user_prompt.encode()),
        "schema_json_utf8_bytes": len(json.dumps(schema).encode()),
        "byte_counts_are_token_counts": False,
        "prompt_retention": "not_proven",
        "status": "request_failed",
    }
    metrics.attempts.append(record)
    return record


def finish_attempt(record: dict | None, response, started: float) -> None:
    if record is None:
        return
    for key in _USAGE:
        value = response.get(key)
        record[key] = value if type(value) is int and value >= 0 else None
    record["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
    record["context_status"] = (
        "generation_limit" if response.get("done_reason") == "length" else "unknown"
    )
    record["status"] = "response_received"
