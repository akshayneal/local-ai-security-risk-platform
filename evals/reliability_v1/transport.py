"""Reuse frozen transports, with a stricter GLOBAL sprint budget; no old file edits."""

import threading

from app.inference_context import EvidenceBudgetError
from evals.cross_pillar_v1.transport import Budget, checked_url

MAX_CALLS = 6
MAX_SECONDS = 1500
MAX_BYTES = 4_000_000


class BudgetStop(EvidenceBudgetError):
    """Prevent production retries when the evaluation, not the provider, stops."""

    def __init__(self):
        super().__init__("request_rejected")


class SixAttemptBudget(Budget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = threading.Lock()

    def reserve(self, url: str, method: str) -> str | None:
        with self.lock:
            path = checked_url(url, method)
            if path == "/api/chat" and self.count >= MAX_CALLS:
                self.event(event="budget_refused", case_id=self.case_id)
                raise BudgetStop()
            return super().reserve(url, method)

    def remaining(self) -> float:
        remaining = MAX_SECONDS - (self.clock() - self.started)
        if remaining <= 0:
            raise BudgetStop()
        return min(180, remaining)

    def allow_storage(self, length: int) -> None:
        if self.retained_bytes + length > MAX_BYTES:
            raise BudgetStop()
        super().allow_storage(length)
