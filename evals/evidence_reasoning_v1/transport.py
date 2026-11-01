"""Sprint 12 accounting adapter; the audited historical transport stays unchanged.

Internal legacy names/prefixes describe accounting only. H1 is a diagnostic
holdout, never release acceptance. No new socket or retry implementation.
"""

from evals.deterministic_evidence_v1.transport import (  # noqa: F401
    DIGEST,
    MODEL,
    OPTIONS,
    CampaignLedger,
    DiagnosticBudget,
    DiagnosticStop,
    encoded,
    sha,
)

PHASES = {"D1": "D0", "D2": "D1", "D3": "D3", "H1": "A"}


def track(phase: str) -> str:
    if phase not in PHASES:
        raise ValueError("Unknown Sprint 12 phase")
    return "acceptance" if phase == "H1" else "lab"
