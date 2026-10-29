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
    return _COMPLETE.get()


@contextmanager
def microsoft_model_context(enabled: bool) -> Iterator[None]:
    token = _COMPLETE.set(enabled)
    try:
        yield
    finally:
        _COMPLETE.reset(token)
