"""Inert Sprint 10 entrypoint for the untouched, conditional Aster acceptance.

Only this process receives output-root redirects and additional conservative
accounting guards. The inherited runner and transport files remain immutable.
"""

import json
import os
import threading
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from evals.controlled_acceptance_v1 import runner as acceptance_runner
from evals.inference_lab_v1 import runner as inherited
from evals.inference_lab_v1.transport import BudgetStop, SprintBudget
from evals.model_task_diagnostic_v1.umbrella import (
    CampaignLedger,
    CampaignStop,
    reject_linked_path,
)

ROOT = Path(__file__).resolve().parents[2]
WORKSPACES = ROOT / "knowledge_base/workspaces"
CAMPAIGN_ROOT = WORKSPACES / "elm-sprint10-campaign"
LAB_JOURNAL = WORKSPACES / "elm-sprint10-lab/accounting/journal.jsonl"
ACCEPTANCE_ROOT = WORKSPACES / "elm-sprint10-acceptance"
_RUN_LOCK = threading.Lock()
_ORIGINAL_RUN = inherited.run


def _budget_type(umbrella):
    class AcceptanceBudget(SprintBudget):
        """Retain inherited accounting; forbid repair sends and add shared cap."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.sent_cases = set()
            self.umbrella_pending = None

        def reserve(self, url, method):
            if self.track != "acceptance" or self.case_id in self.sent_cases:
                raise BudgetStop()
            attempt = super().reserve(url, method)
            if attempt is not None:
                self.sent_cases.add(self.case_id)
                try:
                    umbrella.reserve(track="acceptance", attempt=attempt)
                except Exception as exc:
                    self.blocked = True
                    raise BudgetStop() from exc
                self.umbrella_pending = attempt
            return attempt

        def prepare(self, body):
            if "think" in json.loads(body):
                raise BudgetStop()
            return super().prepare(body)

        def response(self, attempt, status, data, elapsed):
            if attempt is not None:
                value = json.loads(data)
                if value.get("done") is not True:
                    raise BudgetStop()
            super().response(attempt, status, data, elapsed)
            if attempt is not None:
                content = value.get("message", {}).get("content")
                outcome = (
                    "COMPLETED"
                    if status == 200 and isinstance(content, str) and content.strip()
                    else "KNOWN_WITHHELD"
                )
                umbrella.finish(track="acceptance", attempt=attempt, outcome=outcome)
                self.umbrella_pending = None

        def failure(self, attempt, exc):
            super().failure(attempt, exc)
            if attempt is not None and self.umbrella_pending == attempt:
                umbrella.finish(track="acceptance", attempt=attempt, outcome="UNKNOWN")
                self.umbrella_pending = None

    return AcceptanceBudget


def run_acceptance(*, readiness):
    """Run once only after external viability review and committed source freeze.

    The booleans document the operator's gate decision; they cannot establish
    semantic truth, independent review, provider quiescence or authorization.
    No model variant, subset, trial ID, or output-root argument is accepted.
    """
    required = {
        "development_viable",
        "ledger_activation_supported",
        "provider_quiescent",
        "frozen_method_compatible",
        "lab_closed",
    }
    if not isinstance(readiness, dict) or any(
        readiness.get(k) is not True for k in required
    ):
        raise CampaignStop("Acceptance viability gates have not passed")
    commit = inherited.git("rev-parse", "HEAD")
    if readiness.get("implementation_commit") != commit:
        raise CampaignStop("Acceptance implementation is not the selected commit")
    if acceptance_runner.run is not _ORIGINAL_RUN or inherited.run is not _ORIGINAL_RUN:
        raise CampaignStop("Inherited acceptance function identity changed")
    if not _RUN_LOCK.acquire(blocking=False):
        raise CampaignStop("Acceptance is already active in this process")
    try:
        reject_linked_path(ACCEPTANCE_ROOT)
        if ACCEPTANCE_ROOT.exists():
            raise FileExistsError("Sprint 10 acceptance already attempted")
        inherited.verify_freeze()
        ACCEPTANCE_ROOT.mkdir(parents=True, exist_ok=False)
        # The exclusive root is a permanent one-run seal, including preflight
        # failure, unknown generation, or a crash before a report is written.
        record = {
            "implementation_commit": commit,
            "gates": sorted(required),
            "method": "inherited Aster compact/ledger-on/default instructions",
            "raw_cap": 12,
            "one_generation_per_submission": True,
        }
        with (ACCEPTANCE_ROOT / "entry.json").open("x", encoding="utf-8") as output:
            output.write(json.dumps(record, sort_keys=True) + "\n")
            output.flush()
            os.fsync(output.fileno())
        accounting = ACCEPTANCE_ROOT / "accounting"
        with CampaignLedger(
            CAMPAIGN_ROOT,
            lab_journal=LAB_JOURNAL,
            acceptance_journal=accounting / "journal.jsonl",
        ) as umbrella, ExitStack() as stack:
            stack.enter_context(
                patch.object(
                    inherited, "WORKSPACES", ACCEPTANCE_ROOT / "isolated-workspaces"
                )
            )
            stack.enter_context(patch.object(inherited, "ACCOUNTING", accounting))
            stack.enter_context(
                patch.object(inherited, "SprintBudget", _budget_type(umbrella))
            )
            return acceptance_runner.main()
    finally:
        _RUN_LOCK.release()
