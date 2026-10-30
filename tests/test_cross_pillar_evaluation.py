"""Budget/transport/freeze contracts, all offline. Never run the live matrix in CI."""

import io
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import requests
from sprint8_history import historical_call

from evals.cross_pillar_v1 import runner
from evals.cross_pillar_v1.transport import (
    HOST,
    MAX_CALLS,
    Budget,
    CountedHttpx,
    checked_url,
    counted_session_class,
    safe_bytes,
)


@pytest.mark.parametrize(
    "url,method",
    [
        ("https://127.0.0.1:11434/api/chat", "POST"),
        ("http://external.example/api/chat", "POST"),
        (HOST + "/api/pull", "POST"),
        (HOST + "/api/embed", "POST"),
        (HOST + "/api/chat?redirect=1", "POST"),
        ("http://user:pass@127.0.0.1:11434/api/chat", "POST"),
        (HOST + "/api/tags", "POST"),
    ],
)
def test_transport_network_boundary(url, method):
    with pytest.raises(RuntimeError, match="network boundary"):
        checked_url(url, method)


def test_attempt_cap_is_shared_durable_and_precedes_transport(tmp_path):
    budget = Budget(tmp_path)
    budget.case_id = "synthetic"
    sends = []

    def send(request):
        lines = (tmp_path / "journal.jsonl").read_text().splitlines()
        assert json.loads(lines[-1])["event"] == "provider_reserved"
        assert request.extensions["timeout"]["read"] <= 180
        sends.append(request)
        return httpx.Response(200, json={"message": {"content": "{}"}})

    with httpx.Client(
        transport=CountedHttpx(budget, httpx.MockTransport(send))
    ) as client:
        for _ in range(MAX_CALLS):
            client.post(HOST + "/api/chat", json={"model": "qwen3:8b"})
        with pytest.raises(RuntimeError, match="budget reached"):
            client.post(HOST + "/api/chat")
        with pytest.raises(RuntimeError, match="network boundary"):
            client.post("http://external.example/api/chat")
    assert len(sends) == budget.count == 32
    assert len(list(tmp_path.glob("provider-*.json"))) == 32
    # Both stacks share this counter, including a request that would retry.
    with (
        counted_session_class(budget)() as session,
        pytest.raises(RuntimeError, match="budget reached"),
    ):
        session.post(HOST + "/api/chat")
    budget.close()
    with pytest.raises(FileExistsError):
        Budget(tmp_path)


def test_requests_stack_counts_failures_and_disables_transport_retries(tmp_path):
    budget = Budget(tmp_path)
    budget.case_id = "synthetic"
    observed = []

    def send(adapter, request, **kwargs):
        assert adapter.max_retries.total == 0
        observed.append(kwargs)
        assert budget.count == len(observed)
        if len(observed) == 1:
            raise requests.Timeout("synthetic timeout")
        response = requests.Response()
        response.status_code = 200
        response.raw = io.BytesIO(b'{"done":true}')
        response.url = request.url
        return response

    with (
        patch.object(requests.adapters.HTTPAdapter, "send", send),
        counted_session_class(budget)() as session,
    ):
        with pytest.raises(requests.Timeout):
            session.post(HOST + "/api/chat")
        assert session.post(HOST + "/api/chat").json() == {"done": True}
    budget.close()
    assert budget.count == 2
    assert all(0 < k["timeout"] <= 180 and not k["proxies"] for k in observed)
    events = [
        json.loads(l)["event"]
        for l in (tmp_path / "journal.jsonl").read_text().splitlines()
    ]
    assert events == [
        "provider_reserved",
        "provider_failure",
        "provider_reserved",
        "provider_response",
    ]


def test_deadline_and_output_storage_fail_closed(tmp_path):
    clock = [0]
    budget = Budget(tmp_path, clock=lambda: clock[0])
    budget.case_id = "synthetic"
    clock[0] = 6501
    with pytest.raises(RuntimeError, match="deadline"):
        budget.reserve(HOST + "/api/chat", "POST")
    assert budget.count == 0
    with pytest.raises(RuntimeError):
        safe_bytes(b"x" * 256001)
    with pytest.raises(RuntimeError):
        safe_bytes(b"-----BEGIN RSA PRIVATE KEY-----")
    runner.write_new(tmp_path / "result.json", {"synthetic": True})
    with pytest.raises(FileExistsError):
        runner.write_new(tmp_path / "result.json", {"synthetic": False})
    budget.close()


def test_frozen_matrix_and_fresh_reviewed_workspace(
    tmp_path, monkeypatch, tmp_path_factory
):
    from app import knowledge_workspace as kw
    from app.ai_security_contracts import AiSecurityRequest
    from app.ui_schemas import UiGovernanceRequest, UiSocRequest

    historical_call(runner.verify_freeze, tmp_path_factory)
    cases = runner.read("cases.json")
    assert len(cases) == len({c["id"] for c in cases}) == 12
    assert runner.read("plan.json")["order"] == [c["id"] for c in cases]
    models = {
        "soc": UiSocRequest,
        "ai_safety": UiGovernanceRequest,
        "ai_security": AiSecurityRequest,
    }
    for case in cases:
        models[case["pillar"]].model_validate(case["input"])
        assert case["expected_facts"] and case["forbidden_inferences"]
    monkeypatch.setattr(kw, "WORKSPACE_ROOT", tmp_path / "workspaces")
    runner.create_workspace(tmp_path)
    workspace = kw.load_workspace("sprint7-evaluation")
    assert len(workspace.records) == 4
    assert all(r.approved for r in workspace.reviews.documents)
    assert all(r.synthetic for r in workspace.records)
    assert "northstar-sprint5" not in str(workspace.path)
    with pytest.raises(FileExistsError):
        runner.create_workspace(tmp_path)
    # Freeze must reject modified frozen data, without touching repository files.
    frozen = runner.read("freeze.json")
    frozen["sha256"]["evals/cross_pillar_v1/cases.json"] = "0" * 64
    original = runner.read
    monkeypatch.setattr(
        runner, "read", lambda n: frozen if n == "freeze.json" else original(n)
    )
    with pytest.raises(ValueError, match="Frozen evaluation bytes"):
        runner.verify_freeze()


def test_no_live_entry_point_in_deterministic_suite():
    source = Path(runner.__file__).read_text()
    assert 'if __name__ == "__main__":' in source
    assert "call_model_json" not in source  # Actual app functions supply inference.


def test_new_suite_literal_hashes_survive_windows_checkout():
    paths = list(runner.read("freeze.json")["sha256"])
    attributes = subprocess.check_output(
        ["git", "check-attr", "eol", "text", "--", *paths], cwd=runner.ROOT, text=True
    ).splitlines()
    for row in attributes:
        if row.startswith(
            ("evals/cross_pillar_v1/cases.json:", "evals/cross_pillar_v1/corpus.json:")
        ):
            assert row.endswith(": unset")  # Original frozen CRLF bytes, no filter.
        elif ": eol:" in row:
            assert row.endswith(": eol: lf")
    assert (runner.SUITE / ".gitattributes").read_text() == (
        "* text eol=lf\n"
        "cases.json -text -eol whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n"
        "corpus.json -text -eol whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol\n"
    )


def test_committed_evaluation_bytes_match_original_frozen_hashes():
    """A passing working-tree check must not hide Git transport normalization."""
    for name, digest in runner.read("freeze.json")["sha256"].items():
        committed = subprocess.check_output(
            ["git", "show", "HEAD:" + name], cwd=runner.ROOT
        )
        assert runner.sha(committed) == digest, name


def test_recorded_live_denominators_and_optional_local_artifact_identity():
    """Consistency/provenance checks only, never independent semantic validation."""
    from collections import Counter

    readout = json.loads(
        (runner.ROOT / "Documentation/cross_pillar_v1/live_readout.json").read_bytes()
    )
    counts = readout["counts"]
    assert counts["scheduled_submissions"] == counts["completed_http_submissions"] == 12
    assert (
        counts["raw_provider_http_attempts"]
        == 12
        <= runner.read("plan.json")["max_raw_generation_attempts"]
    )
    assert counts["returned_advisories"] + counts["withheld_advisories"] == 12
    assert [r["case_id"] for r in readout["results"]] == runner.read("plan.json")[
        "order"
    ]
    actual = Counter(
        j["judgment"] for r in readout["results"] for j in r["expected_fact_judgments"]
    )
    assert dict(actual) == readout["qualitative_metrics"]["fact_judgments"]
    assert sum(actual.values()) == 26
    # Fresh clones have no private ignored local run; absence is not verification.
    directory = runner.ROOT / readout["ignored_run_root"]
    if directory.exists():
        for name, digest in readout["artifact_sha256"].items():
            assert runner.sha((directory / name).read_bytes()) == digest, name
        events = [
            json.loads(line)
            for line in (directory / "journal.jsonl").read_text().splitlines()
        ]
        assert (
            sum(e["event"] == "provider_reserved" for e in events)
            == counts["raw_provider_http_attempts"]
        )
        assert events[-1]["event"] == "run_finished"


@pytest.mark.parametrize("complete", [False, True])
def test_actual_inference_retry_is_counted_on_both_http_stacks(
    tmp_path, monkeypatch, complete
):
    from ollama import Client

    from app import ollama_client as provider
    from app.inference_context import microsoft_model_context
    from app.model_metrics import local_model_metrics

    budget = Budget(tmp_path)
    budget.case_id = "synthetic-retry"
    sent = []

    def response(method, url):
        if url.endswith("/api/version"):
            return 200, {"version": "0.40.13"}
        sent.append(url)
        if len(sent) == 1:
            return 500, {"error": "synthetic provider failure"}
        return 200, {
            "model": "qwen3:8b",
            "done": True,
            "message": {"role": "assistant", "content": "{}"},
        }

    def httpx_send(request):
        status, body = response(request.method, str(request.url))
        return httpx.Response(status, json=body)

    def requests_send(adapter, request, **kwargs):
        status, body = response(request.method, request.url)
        result = requests.Response()
        result.status_code, result.url = status, request.url
        result.raw = io.BytesIO(json.dumps(body).encode())
        return result

    client = Client(
        host=HOST, transport=CountedHttpx(budget, httpx.MockTransport(httpx_send))
    )
    monkeypatch.setattr(provider, "client", client)
    monkeypatch.setattr(provider, "OLLAMA_HOST", HOST)
    monkeypatch.setattr(requests, "Session", counted_session_class(budget))
    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", requests_send)
    with microsoft_model_context(complete), local_model_metrics() as metrics:
        assert (
            provider.call_model_json("Synthetic retry test", {"type": "object"}) == {}
        )
    assert len(sent) == budget.count == len(metrics.attempts) == 2
    client._client.close()
    budget.close()
