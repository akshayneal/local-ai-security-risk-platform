"""No-provider Sprint 9 accounting, operational boundaries and literal bytes."""

import io
import json
import subprocess

import httpx
import pytest
import requests

from evals.inference_lab_v1 import runner
from evals.inference_lab_v1.transport import (
    CAPS,
    HOST,
    BudgetStop,
    FingerprintedHttpx,
    SprintBudget,
    encoded,
    fingerprinted_session_class,
    sha,
)


def payload():
    return {
        "model": "qwen3:8b",
        "stream": False,
        "truncate": False,
        "shift": False,
        "messages": [{"role": "user", "content": "Synthetic test only"}],
        "format": {"type": "object"},
        "options": {"temperature": 0.1, "num_ctx": 8192},
    }


def begin(budget, tmp_path, track="lab"):
    budget.begin(
        track,
        "SYNTHETIC",
        tmp_path,
        treatment="offline",
        input_sha256="0" * 64,
        commit="offline",
    )
    budget.prepare(encoded(payload()))


def complete(budget, attempt):
    budget.response(attempt, 200, b'{"message":{"content":"{}"},"done":true}', 0.01)


def test_fresh_twelve_contracts_controls_and_sealed_literal_bytes():
    from app.ai_security_contracts import AiSecurityRequest
    from app.ui_schemas import UiGovernanceRequest, UiSocRequest

    suite = runner.ROOT / "evals/controlled_acceptance_v1"
    cases = runner.read(suite / "cases.json")
    assert len(cases) == len({c["id"] for c in cases}) == 12
    models = {
        "ai_security": AiSecurityRequest,
        "soc": UiSocRequest,
        "ai_safety": UiGovernanceRequest,
    }
    assert {p: sum(c["pillar"] == p for c in cases) for p in models} == dict.fromkeys(
        models, 4
    )
    for case in cases:
        models[case["pillar"]].model_validate(case["input"])
        assert len(case["expected_facts"]) == 3 and case["forbidden_inferences"]
        assert case["source_scope"]["authority"] == "caller_supplied_unverified"
    frozen = runner.read(suite / "freeze.json")
    for name, digest in frozen["sha256"].items():
        assert sha((runner.ROOT / name).read_bytes()) == digest
    lab = runner.read(runner.ROOT / "evals/inference_lab_v1/cases.json")
    assert not {sha(encoded(c["input"])) for c in cases} & {
        sha(encoded(c["input"])) for c in lab
    }
    assert not {c["id"] for c in cases} & {c["id"] for c in lab}


def test_committed_and_working_acceptance_bytes_are_identical():
    # Initial authoring is checked after the freeze checkpoint commits these files.
    if subprocess.run(
        ["git", "cat-file", "-e", "HEAD:evals/controlled_acceptance_v1/freeze.json"],
        cwd=runner.ROOT,
        capture_output=True,
        check=False,
    ).returncode:
        pytest.skip("Initial freeze checkpoint is not committed yet")
    runner.verify_freeze()


def test_global_tracks_cannot_borrow_and_reservations_precede_send(tmp_path):
    budget = SprintBudget(tmp_path / "accounting")
    begin(budget, tmp_path)
    for _ in range(CAPS["lab"]):
        attempt = budget.reserve(HOST + "/api/chat", "POST")
        rows = [
            json.loads(x)
            for x in (budget.root / "journal.jsonl").read_text().splitlines()
        ]
        assert (
            rows[-1]["attempt"] == attempt and rows[-1]["event"] == "provider_reserved"
        )
        complete(budget, attempt)
    with pytest.raises(BudgetStop):
        budget.reserve(HOST + "/api/chat", "POST")
    begin(budget, tmp_path, "acceptance")
    for _ in range(CAPS["acceptance"]):
        complete(budget, budget.reserve(HOST + "/api/chat", "POST"))
    with pytest.raises(BudgetStop):
        budget.reserve(HOST + "/api/chat", "POST")
    assert budget.count == 36 and budget.counts == {"lab": 24, "acceptance": 12}
    budget.close()
    reopened = SprintBudget(tmp_path / "accounting")
    assert reopened.count == 36
    reopened.close()


def test_incomplete_reservation_and_uncertain_timeout_prevent_future_sends(tmp_path):
    root = tmp_path / "accounting"
    budget = SprintBudget(root)
    begin(budget, tmp_path)
    budget.reserve(HOST + "/api/chat", "POST")
    with pytest.raises(BudgetStop):
        budget.reserve(HOST + "/api/chat", "POST")
    budget.close()
    with pytest.raises(BudgetStop):
        SprintBudget(root)
    assert not (root / "active.lock").exists()


def test_timeout_no_hidden_retry_and_no_thinking_retention(tmp_path):
    budget = SprintBudget(tmp_path / "accounting")
    begin(budget, tmp_path)
    calls = []

    def send(request):
        calls.append(request)
        raise httpx.ReadTimeout("synthetic timeout")

    with httpx.Client(
        transport=FingerprintedHttpx(budget, httpx.MockTransport(send))
    ) as client:
        with pytest.raises(httpx.ReadTimeout):
            client.post(HOST + "/api/chat", json=payload())
        with pytest.raises(BudgetStop):
            client.post(HOST + "/api/chat", json=payload())
    assert len(calls) == budget.count == 1
    budget.close()
    with pytest.raises(BudgetStop):
        SprintBudget(tmp_path / "accounting")


def test_response_artifact_excludes_hidden_thinking(tmp_path):
    budget = SprintBudget(tmp_path / "accounting")
    begin(budget, tmp_path)
    attempt = budget.reserve(HOST + "/api/chat", "POST")
    budget.response(
        attempt,
        200,
        encoded(
            {
                "message": {
                    "content": "<think>hidden alpha</think>{}",
                    "thinking": "hidden beta",
                },
                "eval_count": 12,
            }
        ),
        1,
    )
    budget.close()
    raw = (tmp_path / (attempt + ".json")).read_bytes()
    assert b"hidden" not in raw and b"thinking" not in raw
    journal = (tmp_path / "accounting/journal.jsonl").read_text()
    assert "hidden alpha" not in journal and "hidden beta" not in journal
    row = json.loads(journal.splitlines()[-1])
    assert row["thinking_present"] and row["thinking_bytes"] > 0


@pytest.mark.parametrize(
    "mutation",
    [
        {"model": "other"},
        {"stream": True},
        {"truncate": True},
        {"shift": True},
        {"options": {"num_ctx": 4096}},
        {"think": "auto"},
    ],
)
def test_actual_wire_options_fail_closed_before_send(tmp_path, mutation):
    budget = SprintBudget(tmp_path / "accounting")
    begin(budget, tmp_path)
    with pytest.raises(BudgetStop):
        budget.prepare(encoded(payload() | mutation))
    assert budget.count == 0
    budget.close()


def test_requests_and_sdk_transport_share_retry_accounting(tmp_path, monkeypatch):
    from ollama import Client

    budget = SprintBudget(tmp_path / "accounting")
    begin(budget, tmp_path)
    sends = []

    def send_httpx(request):
        sends.append("sdk")
        return httpx.Response(
            500 if len(sends) == 1 else 200,
            json={"message": {"content": "{}"}, "done": True},
        )

    sdk = Client(
        host=HOST, transport=FingerprintedHttpx(budget, httpx.MockTransport(send_httpx))
    )
    # Use the SDK's actual transport with the strict raw body; ordinary SDK .chat
    # lacks truncate/shift and is intentionally refused in live Sprint 9 trials.
    for _ in range(2):
        sdk._client.post(HOST + "/api/chat", json=payload())
    sdk._client.close()

    def send_requests(adapter, request, **kwargs):
        assert (
            adapter.max_retries.total == 0
            and not kwargs["proxies"]
        )
        sends.append("strict")
        response = requests.Response()
        response.status_code, response.url = 200, request.url
        response.raw = io.BytesIO(b'{"message":{"content":"{}"},"done":true}')
        return response

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", send_requests)
    with fingerprinted_session_class(budget)() as session:
        session.post(HOST + "/api/chat", json=payload())
    assert sends == ["sdk", "sdk", "strict"] and budget.count == 3
    budget.close()


def test_exhaustion_denies_both_transports_without_send(tmp_path):
    budget = SprintBudget(tmp_path / "accounting")
    begin(budget, tmp_path)
    for _ in range(24):
        complete(budget, budget.reserve(HOST + "/api/chat", "POST"))
    with (
        httpx.Client(
            transport=FingerprintedHttpx(
                budget, httpx.MockTransport(lambda r: pytest.fail("over-cap send"))
            )
        ) as client,
        pytest.raises(BudgetStop),
    ):
        client.post(HOST + "/api/chat", json=payload())
    with fingerprinted_session_class(budget)() as session, pytest.raises(BudgetStop):
        session.post(HOST + "/api/chat", json=payload())
    budget.close()


def test_deadline_storage_lock_and_private_path_refusal(tmp_path):
    now = [0]
    budget = SprintBudget(tmp_path / "accounting", clock=lambda: now[0])
    begin(budget, tmp_path)
    with pytest.raises(FileExistsError):
        SprintBudget(tmp_path / "accounting")
    now[0] = 14_300
    with pytest.raises(BudgetStop):
        budget.reserve(HOST + "/api/chat", "POST")
    with pytest.raises(BudgetStop):
        budget.allow_storage(12_000_001)
    with pytest.raises(BudgetStop):
        budget.store(tmp_path / "bad.json", b"C:\\Users\\someone\\private.txt")
    budget.close()


def test_existing_trial_and_acceptance_cannot_be_reused(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "WORKSPACES", tmp_path)
    monkeypatch.setattr(runner, "ACCOUNTING", tmp_path / "cedar-sprint9-lab/accounting")
    monkeypatch.setattr(runner, "verify_freeze", dict)
    (tmp_path / "cedar-sprint9-lab/existing").mkdir(parents=True)
    with pytest.raises(FileExistsError):
        runner.run(track="lab", trial="existing")
    (tmp_path / "cedar-sprint9-acceptance").mkdir()
    with pytest.raises(FileExistsError):
        runner.run(track="acceptance", trial="different-id")
