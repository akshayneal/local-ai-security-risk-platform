"""Offline evaluation integrity. No real provider requests or old artifact writes."""

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from evals.cross_pillar_v1.transport import HOST, CountedHttpx, counted_session_class
from evals.reliability_v1 import runner
from evals.reliability_v1.transport import BudgetStop, SixAttemptBudget


def test_fresh_frozen_cases_and_exact_git_bytes():
    from app.ai_security_contracts import AiSecurityRequest
    from app.ui_schemas import UiGovernanceRequest, UiSocRequest

    freeze = runner.verify_freeze()
    cases = runner.read("cases.json")
    assert len(cases) == len({c["id"] for c in cases}) == 6
    assert runner.read("plan.json")["case_order"] == [c["id"] for c in cases]
    assert [c["pillar"] for c in cases] == ["ai_security"] * 2 + ["soc"] * 2 + [
        "ai_safety"
    ] * 2
    models = {
        "ai_security": AiSecurityRequest,
        "soc": UiSocRequest,
        "ai_safety": UiGovernanceRequest,
    }
    for case in cases:
        models[case["pillar"]].model_validate(case["input"])
        assert len(case["expected_facts"]) == 3 and case["forbidden_inferences"]
    for name, digest in freeze["sha256"].items():
        assert (
            runner.hashlib.sha256(
                subprocess.check_output(
                    ["git", "show", "HEAD:" + name], cwd=runner.ROOT
                )
            ).hexdigest()
            == digest
        )


def test_six_attempt_cap_is_atomic_and_durable(tmp_path):
    budget = SixAttemptBudget(tmp_path)
    budget.case_id = "synthetic"

    def reserve(_):
        try:
            return budget.reserve(HOST + "/api/chat", "POST")
        except BudgetStop:
            return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(reserve, range(8)))
    budget.close()
    assert len({v for v in ids if v}) == budget.count == 6
    events = [
        json.loads(line)
        for line in (tmp_path / "journal.jsonl").read_text().splitlines()
    ]
    assert sum(e["event"] == "provider_reserved" for e in events) == 6
    assert sum(e["event"] == "budget_refused" for e in events) == 2
    with pytest.raises(FileExistsError):
        SixAttemptBudget(tmp_path)


def test_both_stacks_and_production_retry_cannot_exceed_global_cap(
    tmp_path, monkeypatch
):
    from ollama import Client

    from app import ollama_client
    from app.inference_context import microsoft_model_context

    budget = SixAttemptBudget(tmp_path)
    budget.case_id = "synthetic"
    for _ in range(6):
        budget.reserve(HOST + "/api/chat", "POST")
    transport = CountedHttpx(
        budget, httpx.MockTransport(lambda r: pytest.fail("over-cap send"))
    )
    client = Client(host=HOST, transport=transport)
    monkeypatch.setattr(ollama_client, "client", client)
    with microsoft_model_context(False), pytest.raises(BudgetStop):
        ollama_client.call_model_json("Synthetic budget denial", {"type": "object"})
    with counted_session_class(budget)() as session, pytest.raises(BudgetStop):
        session.post(HOST + "/api/chat")
    client._client.close()
    budget.close()
    assert budget.count == 6
    events = [
        json.loads(line)
        for line in (tmp_path / "journal.jsonl").read_text().splitlines()
    ]
    assert (
        sum(e["event"] == "budget_refused" for e in events) == 2
    )  # No tenacity retry.


def test_deadline_and_storage_fail_closed(tmp_path):
    now = [0]
    budget = SixAttemptBudget(tmp_path, clock=lambda: now[0])
    budget.case_id = "synthetic"
    now[0] = 1501
    with pytest.raises(BudgetStop):
        budget.reserve(HOST + "/api/chat", "POST")
    assert budget.count == 0
    with pytest.raises(BudgetStop):
        budget.allow_storage(4_000_001)
    budget.close()


def test_unavailable_is_not_run_and_existing_run_cannot_be_overwritten(
    tmp_path, monkeypatch
):
    for key in ("PYTHON_DOTENV_DISABLED", "OLLAMA_HOST", "OLLAMA_MODEL"):
        monkeypatch.setenv(key, "test-local")
    monkeypatch.setattr(runner, "RESULTS", tmp_path / "new-run")
    monkeypatch.setattr(
        runner, "preflight", lambda: (_ for _ in ()).throw(ValueError("unavailable"))
    )
    runner.main()
    report = json.loads((runner.RESULTS / "report.json").read_bytes())
    assert report["status"] == "LIVE NOT RUN" and report["raw_attempts"] == 0
    assert len(report["results"]) == 6
    assert all(r["state"] == "NOT RUN" for r in report["results"])
    original = (runner.RESULTS / "journal.jsonl").read_bytes()
    with pytest.raises(FileExistsError):
        runner.main()
    assert (runner.RESULTS / "journal.jsonl").read_bytes() == original
