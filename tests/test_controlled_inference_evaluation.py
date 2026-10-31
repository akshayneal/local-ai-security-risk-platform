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
    budget.response(
        attempt,
        200,
        b'{"model":"qwen3:8b","message":{"content":"{}"},"done":true}',
        0.01,
    )


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
                "model": "qwen3:8b",
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
            json={"model": "qwen3:8b", "message": {"content": "{}"}, "done": True},
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
        assert adapter.max_retries.total == 0 and not kwargs["proxies"]
        sends.append("strict")
        response = requests.Response()
        response.status_code, response.url = 200, request.url
        response.raw = io.BytesIO(
            b'{"model":"qwen3:8b","message":{"content":"{}"},"done":true}'
        )
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


def test_actual_provider_retry_and_soc_repair_consume_same_counter(
    tmp_path, monkeypatch
):
    from app import ollama_client, soc_analyzer
    from app.analysis_trace import AnalysisTrace
    from app.model_metrics import local_model_metrics
    from app.schemas import SocAlertRequest

    budget = SprintBudget(tmp_path / "accounting")
    begin(budget, tmp_path)
    generations = []
    response_body = {
        "alert_id": "OFFLINE-S9",
        "severity": "low",
        "likely_incident_type": "Uncertain observation",
        "summary": "A synthetic authentication observation was supplied for lab-host-9.",
        "mitre_mapping": [],
        "recommended_containment": [],
        "recommended_investigation_steps": [
            "Review the supplied record with its owner."
        ],
        "false_positive_considerations": ["Routine access is possible."],
        "evidence_gaps": ["Business purpose unknown."],
        "analyst_note": "Human review required; no action executed.",
        "observed_evidence": [
            "A synthetic authentication observation concerns lab-host-9."
        ],
        "analyst_inferences": [],
        "source_references": [],
    }

    def send(adapter, request, **kwargs):
        response = requests.Response()
        response.url, response.status_code = request.url, 200
        if request.url.endswith("/api/version"):
            body = {"version": "0.40.13"}
        else:
            generations.append(json.loads(request.body))
            if len(generations) == 1:
                response.status_code, body = (
                    500,
                    {"error": "Synthetic provider failure"},
                )
            else:
                raw = response_body.copy()
                if len(generations) == 3:
                    raw["observed_evidence"] = []  # Forces the real bounded SOC repair.
                body = {
                    "model": "qwen3:8b",
                    "done": True,
                    "message": {"content": json.dumps(raw)},
                }
        response.raw = io.BytesIO(encoded(body))
        return response

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", send)
    monkeypatch.setattr(requests, "Session", fingerprinted_session_class(budget))
    monkeypatch.setattr(ollama_client, "OLLAMA_HOST", HOST)
    monkeypatch.setattr(ollama_client, "complete_context_required", lambda: True)
    with local_model_metrics(num_ctx=8192):
        assert (
            ollama_client.call_model_json(
                "Synthetic transport retry", {"type": "object"}
            )["alert_id"]
            == "OFFLINE-S9"
        )
        trace = AnalysisTrace()
        output = soc_analyzer.analyze_soc_alert(
            SocAlertRequest(
                alert_id="OFFLINE-S9",
                alert_type="Synthetic observation",
                source_system="Offline test",
                affected_asset="lab-host-9",
                raw_log="Synthetic authentication observation concerns lab-host-9.",
            ),
            references=[],
            trace=trace,
        )
    assert output.alert_id == "OFFLINE-S9"
    assert trace.repair_attempted and trace.repair_failed is False
    assert len(generations) == budget.count == 4
    assert "APPLICATION OUTPUT REPAIR" in generations[-1]["messages"][-1]["content"]
    budget.close()


def test_ordinary_sdk_route_is_refused_before_any_raw_send(tmp_path, monkeypatch):
    from ollama import Client

    from app import ollama_client

    budget = SprintBudget(tmp_path / "accounting")
    begin(budget, tmp_path)
    provider = Client(
        host=HOST,
        transport=FingerprintedHttpx(
            budget, httpx.MockTransport(lambda r: pytest.fail("non-strict SDK send"))
        ),
    )
    monkeypatch.setattr(ollama_client, "client", provider)
    monkeypatch.setattr(ollama_client, "complete_context_required", lambda: False)
    with pytest.raises(BudgetStop):
        ollama_client.call_model_json(
            "Synthetic non-strict SDK denial", {"type": "object"}
        )
    assert budget.count == 0
    provider._client.close()
    budget.close()


def test_workflow_system_context_nested_exception_resets():
    from app.inference_context import generation_system_prompt, workflow_model_context

    assert generation_system_prompt() is None
    with workflow_model_context("Outer synthetic instruction"):
        assert generation_system_prompt() == "Outer synthetic instruction"
        with (
            pytest.raises(ValueError),
            workflow_model_context("Inner synthetic instruction"),
        ):
            assert generation_system_prompt() == "Inner synthetic instruction"
            raise ValueError("synthetic")
        assert generation_system_prompt() == "Outer synthetic instruction"
    assert generation_system_prompt() is None


@pytest.mark.parametrize(
    "content",
    [
        "<think>complete secret</think>{}<think>unclosed secret",
        "<THINK>unclosed secret",
        "{} </think>unmatched secret",
    ],
)
def test_malformed_hidden_markers_withhold_without_retention(tmp_path, content):
    budget = SprintBudget(tmp_path / "accounting")
    begin(budget, tmp_path)

    def send(request):
        return httpx.Response(
            200, json={"model": "qwen3:8b", "message": {"content": content}}
        )

    with (
        httpx.Client(
            transport=FingerprintedHttpx(budget, httpx.MockTransport(send))
        ) as client,
        pytest.raises(BudgetStop),
    ):
        client.post(HOST + "/api/chat", json=payload())
    assert budget.count == 1 and budget.blocked
    budget.close()
    assert not list(tmp_path.glob("s9-*.json"))
    assert "secret" not in (tmp_path / "accounting/journal.jsonl").read_text()


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_header",
        "duplicate_header",
        "unknown_event",
        "negative_storage",
        "wrong_attempt_id",
    ],
)
def test_corrupt_accounting_cannot_reset_budget_or_deadline(tmp_path, mutation):
    root = tmp_path / "accounting"
    budget = SprintBudget(root)
    begin(budget, tmp_path)
    complete(budget, budget.reserve(HOST + "/api/chat", "POST"))
    budget.close()
    path = root / "journal.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if mutation == "missing_header":
        rows.pop(0)
    elif mutation == "duplicate_header":
        rows.append(rows[0])
    elif mutation == "unknown_event":
        rows.append({"event": "silently_reset"})
    elif mutation == "negative_storage":
        next(row for row in rows if row["event"] == "artifact_stored")["bytes"] = -1
    else:
        next(row for row in rows if row["event"] == "provider_reserved")["attempt"] = (
            "s9-9999"
        )
    path.write_bytes(b"\n".join(encoded(row) for row in rows) + b"\n")
    with pytest.raises(BudgetStop):
        SprintBudget(root)


def test_deadline_persists_across_separate_budget_instances(tmp_path):
    clock = [0]
    root = tmp_path / "accounting"
    first = SprintBudget(root, clock=lambda: clock[0])
    first.close()
    clock[0] = 14_300
    second = SprintBudget(root, clock=lambda: clock[0])
    begin(second, tmp_path)
    with pytest.raises(BudgetStop):
        second.reserve(HOST + "/api/chat", "POST")
    assert second.count == 0
    second.close()


def test_unexpected_returned_model_stops_without_retry(tmp_path):
    budget = SprintBudget(tmp_path / "accounting")
    begin(budget, tmp_path)

    def send(request):
        return httpx.Response(
            200, json={"model": "different-model", "message": {"content": "{}"}}
        )

    with (
        httpx.Client(
            transport=FingerprintedHttpx(budget, httpx.MockTransport(send))
        ) as client,
        pytest.raises(BudgetStop),
    ):
        client.post(HOST + "/api/chat", json=payload())
    assert budget.count == 1 and budget.blocked
    budget.close()


def test_metadata_preflight_is_bounded_before_json_decode(monkeypatch):
    responses = []

    class Response:
        status_code = 200
        closed = False

        def iter_content(self, chunk_size):
            assert chunk_size == 8192
            for _ in range(33):
                yield b"x" * 8192

        def close(self):
            self.closed = True

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, **kwargs):
            assert url == HOST + "/api/version"
            assert kwargs == {"timeout": 5, "allow_redirects": False, "stream": True}
            response = Response()
            responses.append(response)
            return response

    monkeypatch.setattr(requests, "Session", Session)
    with pytest.raises(ValueError, match="oversized"):
        runner.preflight()
    assert len(responses) == 1 and responses[0].closed
