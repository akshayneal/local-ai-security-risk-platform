"""Request-local complete-context mode for the structured Microsoft profile."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

MICROSOFT_CONTEXT = 8192
EVIDENCE_BUDGET_MESSAGE = (
    "The local runtime could not complete this analysis within the supported "
    "context or generation limits. No analyst result was returned. Use a smaller, "
    "clearly scoped bundle and check that the local runtime is supported."
)
_COMPLETE: ContextVar[bool] = ContextVar("complete_evidence_context", default=False)
_SYSTEM: ContextVar[str | None] = ContextVar(
    "workflow_system_instructions", default=None
)


def generation_system_prompt() -> str | None:
    """Application instructions only; callers must never pass supplied evidence here."""
    return _SYSTEM.get()


@contextmanager
def workflow_model_context(system_prompt: str) -> Iterator[None]:
    """Select trusted workflow instructions without changing the generation seam."""
    if not isinstance(system_prompt, str) or not system_prompt.strip():
        raise ValueError("Workflow instructions must be a nonblank string")
    if len(system_prompt.encode("utf-8")) > 12_000:
        raise ValueError("Workflow instructions exceed the application limit")
    token = _SYSTEM.set(system_prompt)
    try:
        yield
    finally:
        _SYSTEM.reset(token)


class EvidenceBudgetError(RuntimeError):
    """Safe failure: never substitute a partial-context result for the whole input."""

    def __init__(self, code: str) -> None:
        self.code = (
            code
            if code
            in {
                "runtime_unsupported",
                "request_rejected",
                "generation_limit",
                "incomplete_generation",
            }
            else "request_rejected"
        )
        super().__init__(EVIDENCE_BUDGET_MESSAGE)


def complete_context_required() -> bool:
    from app.knowledge_contracts import knowledge_enabled

    return _COMPLETE.get() or knowledge_enabled()


@contextmanager
def microsoft_model_context(enabled: bool) -> Iterator[None]:
    token = _COMPLETE.set(enabled)
    try:
        yield
    finally:
        _COMPLETE.reset(token)
