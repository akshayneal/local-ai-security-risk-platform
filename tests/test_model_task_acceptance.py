"""Mock-only acceptance isolation and aggregate accounting, without holdout gold."""

import hashlib
import json
from pathlib import Path

import pytest

from evals.controlled_acceptance_v1 import runner as sealed
from evals.inference_lab_v1 import runner as inherited
from evals.inference_lab_v1 import transport as old_transport
from evals.model_task_diagnostic_v1 import acceptance
from evals.model_task_diagnostic_v1.umbrella import CampaignLedger, CampaignStop


def paths(tmp_path):
    return {
        "root": tmp_path / "elm-sprint10-campaign",
        "lab_journal": tmp_path / "elm-sprint10-lab/accounting/journal.jsonl",
        "acceptance_journal": tmp_path
        / "elm-sprint10-acceptance/accounting/journal.jsonl",
    }


def readiness():
    return {
        "implementation_commit": "c" * 40,
        "development_viable": True,
        "ledger_activation_supported": True,
        "provider_quiescent": True,
        "frozen_method_compatible": True,
        "lab_closed": True,
    }


def wire_body(**changes):
    body = {
        "model": "qwen3:8b",
        "messages": [{"role": "user", "content": "synthetic"}],
        "format": {"type": "object"},
        "stream": False,
        "truncate": False,
        "shift": False,
        "options": {"temperature": 0.1, "num_ctx": 8192},
    }
    body.update(changes)
    return old_transport.encoded(body)


def complete(budget, attempt, *, done=True):
    body = old_transport.encoded(
        {
            "model": "qwen3:8b",
            "done": done,
            "message": {"role": "assistant", "content": "{}"},
        }
    )
    budget.response(attempt, 200, body, 0.01)


def isolated(monkeypatch, tmp_path):
    p = paths(tmp_path)
    monkeypatch.setattr(acceptance, "CAMPAIGN_ROOT", p["root"])
    monkeypatch.setattr(acceptance, "LAB_JOURNAL", p["lab_journal"])
    monkeypatch.setattr(
        acceptance, "ACCEPTANCE_ROOT", p["acceptance_journal"].parents[1]
    )
    monkeypatch.setattr(
        inherited, "git", lambda *args: "c" * 40 if args[0] == "rev-parse" else ""
    )
    plan = json.loads(
        (inherited.ROOT / "evals/controlled_acceptance_v1/plan.json").read_bytes()
    )
    original_read = inherited.read

    def read(path):
        if path.name == "cases.json":
            # Only the frozen plan's identifiers/order are read. Holdout input,
            # expected facts, and judgments are never used by these mock tests.
            return [{"id": case, "input": {}} for case in plan["case_order"]]
        return original_read(path)

    monkeypatch.setattr(inherited, "read", read)
    monkeypatch.setattr(inherited, "preflight", lambda: {"mock_only": True})
    return p, plan


def frozen_hashes():
    names = ["evals/inference_lab_v1/runner.py", "evals/inference_lab_v1/transport.py"]
    names += [
        "evals/controlled_acceptance_v1/" + name
        for name in (
            "runner.py",
            "plan.json",
            "cases.json",
            "rubric.md",
            "freeze.json",
            ".gitattributes",
        )
    ]
    return {
        name: hashlib.sha256((inherited.ROOT / name).read_bytes()).hexdigest()
        for name in names
    }


def test_untouched_imported_run_exact_order_roots_caps_and_reuse(monkeypatch, tmp_path):
    p, plan = isolated(monkeypatch, tmp_path)
    before = frozen_hashes()
    original = (inherited.WORKSPACES, inherited.ACCOUNTING, inherited.SprintBudget)
    seen = []

    def execute(cases, budget, directory, variant):
        assert sealed.run is inherited.run is acceptance._ORIGINAL_RUN
        assert variant == {"protocol": "compact", "ledger": "on", "system": "default"}
        assert directory.is_relative_to(acceptance.ACCEPTANCE_ROOT)
        assert budget.root == p["acceptance_journal"].parent
        assert old_transport.CAPS == {"lab": 24, "acceptance": 12}
        assert old_transport.REQUEST_SECONDS == budget.remaining() == 180
        for case in cases:
            seen.append(case["id"])
            budget.begin("acceptance", case["id"], directory)
            budget.prepare(wire_body())
            assert budget.request_metadata["think"] == "provider_default"
            attempt = budget.reserve(old_transport.HOST + "/api/chat", "POST")
            complete(budget, attempt)
            with pytest.raises(old_transport.BudgetStop):
                budget.reserve(old_transport.HOST + "/api/chat", "POST")
        return [{"id": case["id"], "state": "MOCK"} for case in cases]

    monkeypatch.setattr(inherited, "execute", execute)
    result = acceptance.run_acceptance(readiness=readiness())
    assert result["global_raw_attempts"] == 12
    assert seen == plan["case_order"]
    assert (
        inherited.WORKSPACES,
        inherited.ACCOUNTING,
        inherited.SprintBudget,
    ) == original
    assert frozen_hashes() == before
    with pytest.raises(FileExistsError, match="already attempted"):
        acceptance.run_acceptance(readiness=readiness())
    with CampaignLedger(**p) as ledger:
        assert ledger.counts == {"lab": 0, "acceptance": 12}
        with pytest.raises(CampaignStop):
            ledger.reserve(track="acceptance", attempt="s9-0013")


@pytest.mark.parametrize("failure", ["preflight", "execute", "unknown"])
def test_failure_keeps_one_run_seal_and_restores_original_roots(
    monkeypatch, tmp_path, failure
):
    p, _ = isolated(monkeypatch, tmp_path)
    original = (inherited.WORKSPACES, inherited.ACCOUNTING, inherited.SprintBudget)
    sentinel = tmp_path / "old-sprint9" / "accounting"
    sentinel.mkdir(parents=True)
    (sentinel / "journal.jsonl").write_bytes(b"preserved historical unknown\n")
    monkeypatch.setattr(inherited, "ACCOUNTING", sentinel)

    def fail(*_):
        raise ValueError("mock preflight unavailable")

    def execute(cases, budget, directory, _variant):
        if failure == "unknown":
            budget.begin("acceptance", cases[0]["id"], directory)
            budget.prepare(wire_body())
            attempt = budget.reserve(old_transport.HOST + "/api/chat", "POST")
            budget.failure(attempt, TimeoutError("synthetic unknown"))
        raise RuntimeError("mock stopped")

    monkeypatch.setattr(inherited, "execute", execute)
    if failure == "preflight":
        monkeypatch.setattr(inherited, "preflight", fail)
        assert (
            acceptance.run_acceptance(readiness=readiness())["status"] == "LIVE NOT RUN"
        )
    else:
        with pytest.raises(RuntimeError, match="mock stopped"):
            acceptance.run_acceptance(readiness=readiness())
    assert inherited.ACCOUNTING == sentinel
    assert inherited.WORKSPACES == original[0] and inherited.SprintBudget is original[2]
    assert (
        sentinel / "journal.jsonl"
    ).read_bytes() == b"preserved historical unknown\n"
    assert list(sentinel.iterdir()) == [sentinel / "journal.jsonl"]
    with pytest.raises(FileExistsError):
        acceptance.run_acceptance(readiness=readiness())
    if failure == "unknown":
        with pytest.raises(CampaignStop, match="Outstanding"):
            CampaignLedger(**p)


@pytest.mark.parametrize("key", list(readiness()))
def test_viability_or_pin_failure_creates_no_acceptance_directory(
    monkeypatch, tmp_path, key
):
    isolated(monkeypatch, tmp_path)
    decision = readiness()
    decision[key] = False
    with pytest.raises(CampaignStop):
        acceptance.run_acceptance(readiness=decision)
    assert not acceptance.ACCEPTANCE_ROOT.exists()


def test_aggregate_caps_are_disjoint_durable_and_never_borrow(tmp_path):
    with CampaignLedger(**paths(tmp_path)) as ledger:
        for track, count in (("lab", 16), ("acceptance", 12)):
            for index in range(count):
                attempt = f"mock-{index:04d}"
                ledger.reserve(track=track, attempt=attempt)
                rows = [
                    json.loads(line)
                    for line in (ledger.root / "journal.jsonl")
                    .read_bytes()
                    .splitlines()
                ]
                assert rows[-1]["event"] == "reserved"
                assert rows[-1]["ordinal"] == sum(ledger.counts.values())
                ledger.finish(track=track, attempt=attempt, outcome="COMPLETED")
            with pytest.raises(CampaignStop):
                ledger.reserve(track=track, attempt="one-too-many")
        assert ledger.snapshot()["reserved"] == 28
    with CampaignLedger(**paths(tmp_path)) as replay:
        assert replay.counts == {"lab": 16, "acceptance": 12}


@pytest.mark.parametrize("outcome", [None, "UNKNOWN"])
def test_cross_track_unknown_or_pending_refuses_send_and_reopen(tmp_path, outcome):
    with CampaignLedger(**paths(tmp_path)) as ledger:
        ledger.reserve(track="lab", attempt="s10-d-0001")
        if outcome:
            ledger.finish(track="lab", attempt="s10-d-0001", outcome=outcome)
        with pytest.raises(CampaignStop):
            ledger.reserve(track="acceptance", attempt="s9-0001")
    with pytest.raises(CampaignStop):
        CampaignLedger(**paths(tmp_path))


def test_concurrent_lock_and_missing_journal_refuse(tmp_path):
    p = paths(tmp_path)
    with CampaignLedger(**p), pytest.raises(FileExistsError):
        CampaignLedger(**p)
    (p["root"] / "journal.jsonl").unlink()
    with pytest.raises(CampaignStop, match="missing"):
        CampaignLedger(**p)


def test_acceptance_rejects_thinking_override_and_incomplete_provider_reply(tmp_path):
    with CampaignLedger(**paths(tmp_path)) as ledger:
        cls = acceptance._budget_type(ledger)
        budget = cls(tmp_path / "acceptance-accounting")
        try:
            budget.begin("acceptance", "synthetic", tmp_path)
            with pytest.raises(old_transport.BudgetStop):
                budget.prepare(wire_body(think=False))
            budget.prepare(wire_body())
            attempt = budget.reserve(old_transport.HOST + "/api/chat", "POST")
            with pytest.raises(old_transport.BudgetStop):
                complete(budget, attempt, done=False)
            budget.failure(attempt, ValueError("incomplete mock reply"))
            assert ledger.blocked and budget.blocked
        finally:
            budget.close()


def test_journal_identity_and_outside_workspace_rejected(tmp_path):
    p = paths(tmp_path)
    with CampaignLedger(**p):
        pass
    with pytest.raises(CampaignStop, match="identity"):
        CampaignLedger(**(p | {"lab_journal": tmp_path / "changed/journal.jsonl"}))
    with pytest.raises(CampaignStop, match="share"):
        CampaignLedger(
            **(p | {"lab_journal": Path(tmp_path.anchor) / "outside/journal.jsonl"})
        )
