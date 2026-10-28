"""Opt-in, in-memory analyzer diagnostics. Never attached to API/audit models."""

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnalysisTrace:
    stages: list[dict[str, Any]] = field(default_factory=list)
    repair_attempted: bool = False
    repair_failed: bool = False

    def capture(self, stage: str, value: Any, *, generation: int = 0) -> None:
        self.stages.append(
            {"stage": stage, "generation": generation, "value": deepcopy(value)}
        )
