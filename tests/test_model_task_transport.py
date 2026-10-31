"""No provider contact: wire deadlines, completion, redaction, and durable caps."""

import io
import json
from pathlib import Path

import pytest

from evals.model_task_diagnostic_v1 import transport as t

MESSAGES = [{"role": "user", "content": "Synthetic public test input."}]
SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
OPTIONS = {"temperature": 0.1, "num_ctx": 8192}


class Umbrella:
    def __init__(self):
        self.rows = []

    def reserve(self, **row):
        self.rows.append(("reserve", row))

    def finish(self, **row):
        self.rows.append(("finish", row))


def frame(*, done=False, content="", **changes):
    row = {
        "model": t.MODEL,
        "done": done,
        "message": {"role": "assistant", "content": content},
    }
    if done:
        row.update(done_reason="stop", eval_count=9, prompt_eval_count=40)
    row.update(changes)
    return t.encoded(row) + b"\n"


class Response:
    status = 200

    def __init__(self, chunks):
        self.chunks = iter(chunks)
        self.closed = False

    def read1(self, size):
        value = next(self.chunks, b"")
        if isinstance(value, BaseException):
            raise value
        return value

    def close(self):
        self.closed = True


def install(monkeypatch, budget, chunks, *, status=200):
    response = Response(chunks)
    response.status = status
    calls = []

    class Connection:
        def __init__(self, deadline, clock):
            assert t.REQUEST_SECONDS - 1 < deadline - clock() <= t.REQUEST_SECONDS

        def request(self, method, path, *, body, headers):
            rows = [
                json.loads(line)
                for line in (budget.root / "journal.jsonl").read_bytes().splitlines()
            ]
            assert rows[-1]["event"] == "provider_reserved"
            assert budget.pending == rows[-1]["attempt"]
            assert budget.umbrella.rows[-1][0] == "reserve"
            calls.append((method, path, json.loads(body), headers))

        def getresponse(self):
            return response

        def close(self):
            pass

    monkeypatch.setattr(t, "_Connection", Connection)
    return calls, response


def budget(tmp_path):
    value = t.DiagnosticBudget(tmp_path / "accounting", umbrella=Umbrella())
    value.begin("ELM-01", trial="d1-test", input_sha256="f" * 64)
    return value


def test_phase_cap_counts_repairs_and_refuses_before_wire(tmp_path, monkeypatch):
    with budget(tmp_path) as b:
        b.begin("ELM-01", trial="d3-test", contrast="D3")
        for _ in range(4):
            install(monkeypatch, b, [frame(done=True, content='{"ok":true}')])
            b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        install(monkeypatch, b, [AssertionError("phase cap must prevent send")])
        with pytest.raises(t.DiagnosticStop):
            b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        assert b.count == 4
    with t.DiagnosticBudget(tmp_path / "accounting", umbrella=Umbrella()) as reopened:
        reopened.begin("ELM-02", trial="d3-next", contrast="D3")
        install(
            monkeypatch, reopened, [AssertionError("replay must preserve phase cap")]
        )
        with pytest.raises(t.DiagnosticStop):
            reopened.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        assert reopened.count == 4


@pytest.mark.parametrize("mode", [None, False, True])
def test_actual_wire_mode_schema_options_and_durable_reservation(
    tmp_path, monkeypatch, mode
):
    with budget(tmp_path) as b:
        calls, response = install(
            monkeypatch, b, [frame(content='{"ok":'), frame(done=True, content="true}")]
        )
        answer = b.chat(MESSAGES, SCHEMA, OPTIONS, think=mode)
        request = calls[0][2]
        assert ("think" in request) is (mode is not None)
        if mode is not None:
            assert request["think"] is mode
        assert request["format"] == SCHEMA
        assert request["options"] == t.OPTIONS
        assert request["stream"] is True
        assert request["truncate"] is request["shift"] is False
        assert (
            json.loads((b.directory / "s10-d-0001-request.json").read_bytes())
            == request
        )
        assert calls[0][:2] == ("POST", "/api/chat")
        assert len(calls) == 1 and response.closed
        assert answer["message"]["content"] == '{"ok":true}'
        assert b.snapshot() == {
            "raw_attempts": 1,
            "phase_counts": {"D1": 0, "D2": 0, "D3": 0, "D4": 0},
            "pending": None,
            "blocked": False,
            "remaining": 15,
        }
        assert b.umbrella.rows[-1][1]["outcome"] == "COMPLETED"


def test_reasoning_extensions_and_split_inline_thought_never_stored(
    tmp_path, monkeypatch
):
    with budget(tmp_path) as b:
        wire = frame(
            message={
                "role": "assistant",
                "content": "<thi",
                "thinking": "HIDDEN_ALPHA",
            },
            extension="HIDDEN_OTHER",
        )
        wire += frame(content="nk>HIDDEN_BETA</think>{")
        wire += frame(done=True, content='"ok":true}', thinking="HIDDEN_GAMMA")
        install(monkeypatch, b, [wire[:27], wire[27:70], wire[70:]])
        answer = b.chat(MESSAGES, SCHEMA, OPTIONS)
        assert json.loads(answer["message"]["content"]) == {"ok": True}
        files = [p.read_bytes() for p in b.root.rglob("*") if p.is_file()]
        assert all(b"HIDDEN" not in data for data in files)
        row = json.loads((b.root / "journal.jsonl").read_bytes().splitlines()[-1])
        assert row["thinking_present"] and row["thinking_bytes"] > 20


@pytest.mark.parametrize(
    "chunks",
    [
        [frame(content='{"ok":true}')],
        [TimeoutError()],
        [frame(content="{"), TimeoutError()],
        [b"x" * (t.MAX_RESPONSE_BYTES + 1)],
        [b"not json\n"],
        [frame(done=True, model="different-model")],
        [frame(done=True, done_reason="unknown")],
        [frame(done=True, eval_count="HIDDEN_EXTENSION")],
        [frame(done=True, content="<think>unclosed")],
        [frame(done=True, content='{"ok":true}') + frame()],
    ],
)
def test_unknown_partial_timeout_or_hostile_frame_stops_without_retry(
    tmp_path, monkeypatch, chunks
):
    with budget(tmp_path) as b:
        calls, _ = install(monkeypatch, b, chunks)
        with pytest.raises(t.DiagnosticStop):
            b.chat(MESSAGES, SCHEMA, OPTIONS)
        assert b.blocked and b.count == 1
        with pytest.raises(t.DiagnosticStop):
            b.chat(MESSAGES, SCHEMA, OPTIONS)
        assert len(calls) == 1
        assert b.umbrella.rows[-1][1]["outcome"] == "UNKNOWN"
    with pytest.raises(t.DiagnosticStop):
        t.DiagnosticBudget(tmp_path / "accounting", umbrella=Umbrella())


def test_known_token_cap_completion_is_withheld_without_unknown(tmp_path, monkeypatch):
    with budget(tmp_path) as b:
        calls, _ = install(
            monkeypatch, b, [frame(done=True, content="{", done_reason="length")]
        )
        with pytest.raises(t.DiagnosticStop) as err:
            b.chat(MESSAGES, SCHEMA, OPTIONS)
        assert err.value.code == "generation_limit"
        assert b.count == len(calls) == 1 and not b.blocked and b.pending is None
        assert b.umbrella.rows[-1][1]["outcome"] == "KNOWN_WITHHELD"


@pytest.mark.parametrize("status", [301, 400, 413, 500])
def test_error_redirect_is_not_followed_or_retried(tmp_path, monkeypatch, status):
    with budget(tmp_path) as b:
        calls, _ = install(monkeypatch, b, [], status=status)
        with pytest.raises(t.DiagnosticStop):
            b.chat(MESSAGES, SCHEMA, OPTIONS)
        assert len(calls) == 1 and b.blocked


def test_cap_reopen_lock_and_exclusive_artifacts(tmp_path, monkeypatch):
    with budget(tmp_path) as b:
        with pytest.raises(FileExistsError):
            t.DiagnosticBudget(b.root, umbrella=Umbrella())
        for _ in range(16):
            install(monkeypatch, b, [frame(done=True, content='{"ok":true}')])
            b.chat(MESSAGES, SCHEMA, OPTIONS)
        with pytest.raises(t.DiagnosticStop):
            b.chat(MESSAGES, SCHEMA, OPTIONS)
        with pytest.raises(FileExistsError):
            b.store("s10-d-0001.json", {})
    with t.DiagnosticBudget(tmp_path / "accounting", umbrella=Umbrella()) as resumed:
        assert resumed.count == 16
        resumed.begin("ELM-02", trial="d2-test")
        with pytest.raises(t.DiagnosticStop):
            resumed.chat(MESSAGES, SCHEMA, OPTIONS)


@pytest.mark.parametrize(
    "change", ["model", "secret", "path", "schema", "mode", "options"]
)
def test_bad_requests_rejected_before_reservation(tmp_path, change):
    with budget(tmp_path) as b:
        messages, schema, options, mode = MESSAGES, SCHEMA, OPTIONS, None
        if change == "model":
            messages = [{"role": "assistant", "content": "x"}]
        if change == "secret":
            messages = [{"role": "user", "content": "sk-" + "x" * 30}]
        if change == "path":
            messages = [{"role": "user", "content": "C:/Users/private/name"}]
        if change == "schema":
            schema = "json"
        if change == "mode":
            mode = "false"
        if change == "options":
            options = {"temperature": 0.8, "num_ctx": 8192}
        with pytest.raises(t.DiagnosticStop):
            b.chat(messages, schema, options, think=mode)
        assert b.count == 0 and not b.umbrella.rows


def test_campaign_deadline_path_traversal_and_storage_budget(tmp_path):
    with budget(tmp_path) as b:
        for name in ("../escape.json", "a/b.json", ".."):
            with pytest.raises(t.DiagnosticStop):
                b.store(name, {})
        b.started -= t.CAMPAIGN_SECONDS
        with pytest.raises(t.DiagnosticStop):
            b.chat(MESSAGES, SCHEMA, OPTIONS)
        b.retained_bytes = t.MAX_RETAINED_BYTES
        with pytest.raises(t.DiagnosticStop):
            b.store("large.json", {})
        assert b.count == 0


def test_unresolved_reservation_and_umbrella_failure_cannot_resume(
    tmp_path, monkeypatch
):
    with budget(tmp_path) as b:

        def refuse(**kwargs):
            raise RuntimeError("umbrella refuses")

        monkeypatch.setattr(b.umbrella, "reserve", refuse)
        with pytest.raises(RuntimeError):
            b.chat(MESSAGES, SCHEMA, OPTIONS)
        assert b.pending and b.count == 1
    with pytest.raises(t.DiagnosticStop):
        t.DiagnosticBudget(tmp_path / "accounting", umbrella=Umbrella())


class Socket:
    def __init__(self, content=b""):
        self.source = io.BytesIO(content)
        self.timeouts, self.sent = [], []
        self.closed = False

    def settimeout(self, timeout):
        self.timeouts.append(timeout)

    def sendall(self, data):
        self.sent.append(data)

    def recv_into(self, buffer):
        assert not self.closed
        return self.source.readinto(buffer)

    def close(self):
        self.closed = True


def test_wall_deadline_applies_to_header_body_and_send_not_outer_timer():
    now = [0]
    socket = Socket(b"abc")
    owner = t._DeadlineSocket(socket, 360, lambda: now[0])
    owner.sendall(b"request")
    assert socket.timeouts[-1] == 90
    now[0] = 359
    reader = owner.makefile("rb")
    assert reader.read1(1) == b"a"
    assert socket.timeouts[-1] == 1
    now[0] = 360
    with pytest.raises(TimeoutError):
        owner.sendall(b"forbidden")
    owner.close()
    assert not socket.closed
    reader.close()
    assert socket.closed


def test_real_http_chunk_framing_fixed_loopback_no_proxy_or_retry(
    tmp_path, monkeypatch
):
    content = frame(content='{"ok":') + frame(done=True, content="true}")
    wire = (
        b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n"
        + format(len(content), "x").encode()
        + b"\r\n"
        + content
        + b"\r\n0\r\n\r\n"
    )
    raw = Socket(wire)
    addresses = []

    def connect(address, timeout):
        addresses.append((address, timeout))
        return raw

    monkeypatch.setattr(t.socket, "create_connection", connect)
    monkeypatch.setenv("HTTP_PROXY", "http://invalid.example:3128")
    with budget(tmp_path) as b:
        result = b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
    assert addresses == [(("127.0.0.1", 11434), 10)]
    assert json.loads(result["message"]["content"]) == {"ok": True}
    assert raw.closed
    assert b"POST /api/chat HTTP/1.1" in b"".join(raw.sent)
    assert b"invalid.example" not in b"".join(raw.sent)


def test_no_historical_output_root_is_a_transport_default():
    text = Path(t.__file__).read_text()
    assert "sprint9" not in text and "cedar" not in text and "birch" not in text
