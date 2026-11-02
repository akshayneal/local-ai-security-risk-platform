"""No provider contact: wire deadlines, completion, redaction, and durable caps."""

import hashlib
import io
import json
import os
from pathlib import Path

import pytest

from evals.adaptive_security_reasoning_v1 import transport as t

MESSAGES = [{"role": "user", "content": "Synthetic public test input."}]
SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
OPTIONS = {"temperature": 0.1, "num_ctx": 32768}


class Umbrella(t.CampaignLedger):
    def __init__(self, parent):
        super().__init__(
            parent / t.ROOT_NAMES["campaign"],
            lab_journal=parent / t.ROOT_NAMES["lab"] / "journal.jsonl",
            acceptance_journal=parent / t.ROOT_NAMES["acceptance"] / "journal.jsonl",
        )
        self.rows = []

    def reserve(self, **row):
        super().reserve(**row)
        self.rows.append(("reserve", row))

    def finish(self, **row):
        super().finish(**row)
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


def install(monkeypatch, budget, chunks, *, status=200, before_send=None):
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
            if isinstance(budget.umbrella, Umbrella):
                assert budget.umbrella.rows[-1][0] == "reserve"
            else:
                campaign_rows = [
                    json.loads(line)
                    for line in (budget.umbrella.root / "journal.jsonl")
                    .read_bytes()
                    .splitlines()
                ]
                assert campaign_rows[-1]["event"] == "reserved"
                assert budget.umbrella.pending == (budget.track, budget.pending)
            if before_send is not None:
                before_send()
            calls.append((method, path, json.loads(body), headers))

        def getresponse(self):
            return response

        def close(self):
            pass

    monkeypatch.setattr(t, "_Connection", Connection)
    return calls, response


def budget(tmp_path):
    umbrella = Umbrella(tmp_path)
    try:
        value = t.DiagnosticBudget(tmp_path / t.ROOT_NAMES["lab"], umbrella=umbrella)
    except BaseException:
        umbrella.close()
        raise
    original_close = value.close

    def close():
        original_close()
        umbrella.close()

    value.close = close
    value.begin("DEV-01", trial="d1-test", contrast="D0", input_sha256="f" * 64)
    return value


def test_phase_cap_counts_repairs_and_refuses_before_wire(tmp_path, monkeypatch):
    with budget(tmp_path) as b:
        b.begin("DEV-01", trial="d3-test", contrast="D3")
        for _ in range(36):
            install(monkeypatch, b, [frame(done=True, content='{"ok":true}')])
            b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        install(monkeypatch, b, [AssertionError("phase cap must prevent send")])
        with pytest.raises(t.DiagnosticStop):
            b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        assert b.count == 36
    with budget(tmp_path) as reopened:
        reopened.begin("DEV-02", trial="d3-next", contrast="D3")
        install(
            monkeypatch, reopened, [AssertionError("replay must preserve phase cap")]
        )
        with pytest.raises(t.DiagnosticStop):
            reopened.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        assert reopened.count == 36


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
            json.loads((b.directory / "s13-d-0001-request.json").read_bytes())
            == request
        )
        assert calls[0][:2] == ("POST", "/api/chat")
        assert len(calls) == 1 and response.closed
        assert answer["message"]["content"] == '{"ok":true}'
        assert b.snapshot() == {
            "raw_attempts": 1,
            "phase_counts": {"D0": 1, "D1": 0, "D3": 0, "A": 0},
            "pending": None,
            "blocked": False,
            "remaining": 83,
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
        hidden = b"HIDDEN_ALPHAHIDDEN_GAMMA<think>HIDDEN_BETA</think>"
        assert row["thinking_bytes"] == len(hidden)
        assert row["thinking_sha256"] == hashlib.sha256(hidden).hexdigest()
        assert row["raw_response_sha256"] == hashlib.sha256(wire).hexdigest()


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
    with pytest.raises((t.DiagnosticStop, t.CampaignStop)):
        budget(tmp_path)


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
            t.DiagnosticBudget(b.root, umbrella=b.umbrella)
        for phase in ("D0", "D1", "D3"):
            b.begin("DEV-01", trial="all-" + phase, contrast=phase)
            for _ in range(t.PHASE_CAPS[phase]):
                install(monkeypatch, b, [frame(done=True, content='{"ok":true}')])
                b.chat(MESSAGES, SCHEMA, OPTIONS)
        with pytest.raises(t.DiagnosticStop):
            b.chat(MESSAGES, SCHEMA, OPTIONS)
        with pytest.raises(FileExistsError):
            b.store("s13-d-0084.json", {})
    with budget(tmp_path) as resumed:
        assert resumed.count == 84
        resumed.begin("DEV-02", trial="d2-test")
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
            options = {"temperature": 0.8, "num_ctx": 32768}
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
    with pytest.raises((t.DiagnosticStop, t.CampaignStop)):
        budget(tmp_path)


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
    assert socket.timeouts[-1] == 120
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


def campaign(tmp_path, **options):
    return t.CampaignLedger(
        tmp_path / t.ROOT_NAMES["campaign"],
        lab_journal=tmp_path / t.ROOT_NAMES["lab"] / "journal.jsonl",
        acceptance_journal=tmp_path / t.ROOT_NAMES["acceptance"] / "journal.jsonl",
        **options,
    )


def test_shared_caps_are_84_development_24_diagnostic_and_108_total(
    tmp_path, monkeypatch
):
    assert t.LAB_CAP == 84
    assert t.PHASE_CAPS == {"D0": 24, "D1": 24, "D3": 36, "A": 24}
    assert t.CAPS == {"lab": 84, "acceptance": 24}
    assert t.MAX_ATTEMPTS == 108
    with campaign(tmp_path) as c:
        for track, maximum in t.CAPS.items():
            with t.DiagnosticBudget(
                tmp_path / t.ROOT_NAMES[track], umbrella=c, track=track
            ) as b:
                phases = ("D0", "D1", "D3") if track == "lab" else ("A",)
                for phase in phases:
                    b.begin("DEV-04", trial="full-" + phase, contrast=phase)
                    for _ in range(t.PHASE_CAPS[phase]):
                        install(monkeypatch, b, [frame(done=True, content="{}")])
                        b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
                assert b.count == maximum
            with pytest.raises(t.CampaignStop, match="exhausted"):
                c.reserve(track=track, attempt="overflow")
        result = c.snapshot()
        assert result["counts"] == t.CAPS and result["reserved"] == 108
        assert result["remaining"] == {"lab": 0, "acceptance": 0}
        assert result["pending"] is None and not result["blocked"]
    with campaign(tmp_path) as resumed:
        assert resumed.snapshot()["reserved"] == 108
        with pytest.raises(t.CampaignStop):
            resumed.reserve(track="lab", attempt="overflow")


def test_real_track_and_campaign_journals_are_fsynced_before_raw_send(
    tmp_path, monkeypatch
):
    syncs = []
    original_fsync = os.fsync
    with (
        campaign(tmp_path) as c,
        t.DiagnosticBudget(tmp_path / t.ROOT_NAMES["lab"], umbrella=c) as b,
    ):
        b.begin("DEV-02", trial="durable", contrast="D0")

        def fsync(fd):
            original_fsync(fd)
            identity = os.fstat(fd).st_ino
            syncs.append(identity)

        monkeypatch.setattr(t.os, "fsync", fsync)

        def durable_before_send():
            assert (b.root / "journal.jsonl").stat().st_ino in syncs
            assert (c.root / "journal.jsonl").stat().st_ino in syncs

        calls, _ = install(
            monkeypatch,
            b,
            [frame(done=True, content="{}")],
            before_send=durable_before_send,
        )
        b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        assert len(calls) == 1
        assert (b.root / "journal.jsonl").stat().st_ino in syncs
        assert (c.root / "journal.jsonl").stat().st_ino in syncs
        rows = [
            json.loads(line)
            for line in (c.root / "journal.jsonl").read_bytes().splitlines()
        ]
        assert [row["event"] for row in rows] == ["reserved", "finished"]
        assert c.snapshot()["reserved"] == b.snapshot()["raw_attempts"] == 1


def test_campaign_persistence_failure_prevents_wire_without_retry(
    tmp_path, monkeypatch
):
    with (
        campaign(tmp_path) as c,
        t.DiagnosticBudget(tmp_path / t.ROOT_NAMES["lab"], umbrella=c) as b,
    ):
        b.begin("DEV-03", trial="durability-failure", contrast="D0")
        calls, _ = install(monkeypatch, b, [frame(done=True, content="{}")])
        original_fsync = os.fsync

        def fail_campaign_reservation(fd):
            if os.fstat(fd).st_ino == (c.root / "journal.jsonl").stat().st_ino:
                raise OSError("synthetic persistence failure")
            original_fsync(fd)

        monkeypatch.setattr(t.os, "fsync", fail_campaign_reservation)
        with pytest.raises(OSError, match="synthetic"):
            b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        assert not calls
        assert b.pending == "s13-d-0001" and b.count == 1
        assert c.pending == ("lab", "s13-d-0001")
        with pytest.raises(t.DiagnosticStop):
            b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
    with pytest.raises(t.CampaignStop, match="Outstanding"):
        campaign(tmp_path)


def test_aggregate_clock_is_first_start_across_tracks_and_reopening(
    tmp_path, monkeypatch
):
    now, wall = [100.0], [1000.0]
    clocks = {"clock": lambda: now[0], "wall_clock": lambda: wall[0]}
    with campaign(tmp_path, **clocks) as c:
        manifest = (c.root / "manifest.json").read_bytes()
        with t.DiagnosticBudget(tmp_path / t.ROOT_NAMES["lab"], umbrella=c) as b:
            b.begin("DEV-05", trial="first", contrast="D0")
            install(monkeypatch, b, [frame(done=True, content="{}")])
            b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        increment = t.CAMPAIGN_SECONDS - t.REQUEST_SECONDS - 1
        now[0] += increment
        wall[0] += increment
        with t.DiagnosticBudget(
            tmp_path / t.ROOT_NAMES["acceptance"], umbrella=c, track="acceptance"
        ) as b:
            b.begin("DEV-06", trial="first", contrast="A")
            install(monkeypatch, b, [frame(done=True, content="{}")])
            b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        assert c.snapshot()["remaining_campaign_seconds"] == 601
    now[0] += 2
    wall[0] += 2
    with campaign(tmp_path, **clocks) as resumed:
        assert (resumed.root / "manifest.json").read_bytes() == manifest
        assert resumed.started == 100 and resumed.started_wall == 1000
        assert resumed.snapshot()["elapsed_seconds"] == increment + 2
        with pytest.raises(t.CampaignStop, match="wall-time"):
            resumed.reserve(track="lab", attempt="second")
        assert resumed.snapshot()["reserved"] == 2


@pytest.mark.parametrize("changed_clock", ["monotonic", "wall"])
def test_rollback_reboot_or_nonfinite_clock_refuses_dispatch_and_replay(
    tmp_path, changed_clock
):
    now, wall = [100.0], [1000.0]
    clocks = {"clock": lambda: now[0], "wall_clock": lambda: wall[0]}
    with campaign(tmp_path, **clocks) as c:
        if changed_clock == "monotonic":
            now[0] -= 1
        else:
            wall[0] -= 1
        with pytest.raises(t.CampaignStop, match="clock changed"):
            c.check_dispatch()
    with pytest.raises(t.CampaignStop, match="clock changed"):
        campaign(tmp_path, **clocks)


def test_exhausted_shared_clock_prevents_track_reservation_and_raw_send(
    tmp_path, monkeypatch
):
    now, wall = [100.0], [1000.0]
    clocks = {"clock": lambda: now[0], "wall_clock": lambda: wall[0]}
    with (
        campaign(tmp_path, **clocks) as c,
        t.DiagnosticBudget(
            tmp_path / t.ROOT_NAMES["acceptance"], umbrella=c, track="acceptance"
        ) as b,
    ):
        b.begin("J7K9", trial="h1", contrast="A")
        calls, _ = install(monkeypatch, b, [frame(done=True, content="{}")])
        now[0] += t.CAMPAIGN_SECONDS
        wall[0] += t.CAMPAIGN_SECONDS
        with pytest.raises(t.CampaignStop, match="wall-time"):
            b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        assert not calls
        assert b.count == c.snapshot()["reserved"] == 0


def test_unknown_blocks_all_tracks_and_cannot_be_replayed_as_completion(tmp_path):
    with campaign(tmp_path) as c:
        c.reserve(track="lab", attempt="first")
        c.finish(track="lab", attempt="first", outcome="UNKNOWN")
        assert c.snapshot()["blocked"]
        with pytest.raises(t.CampaignStop):
            c.reserve(track="acceptance", attempt="diagnostic")
    with pytest.raises(t.CampaignStop, match="Outstanding"):
        campaign(tmp_path)


def test_conservative_context_upper_bound_rejects_before_reservation(tmp_path):
    with budget(tmp_path) as b:
        with pytest.raises(t.DiagnosticStop):
            b.chat([{"role": "user", "content": "x" * 30_000}], SCHEMA, OPTIONS)
        assert b.count == 0 and not b.umbrella.rows
    assert t.MAX_PROMPT_BYTES == 48_000 and t.MAX_RESPONSE_BYTES == 1_000_000
    assert t.MAX_RETAINED_BYTES == 64_000_000
    assert (t.REQUEST_SECONDS, t.CONNECT_SECONDS, t.IDLE_SECONDS) == (600, 10, 120)


def test_foreign_phase_in_replayed_lab_journal_is_rejected(tmp_path, monkeypatch):
    with budget(tmp_path) as b:
        install(monkeypatch, b, [frame(done=True, content="{}")])
        b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
    path = tmp_path / t.ROOT_NAMES["lab"] / "journal.jsonl"
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    for row in rows:
        if row["event"] == "provider_reserved":
            row["contrast"] = "A"
    path.write_bytes(b"".join(t.encoded(row) + b"\n" for row in rows))
    with pytest.raises((t.DiagnosticStop, t.CampaignStop)):
        budget(tmp_path)


def test_low_level_stream_request_and_socket_code_matches_audited_original():
    import ast

    new = ast.parse(Path(t.__file__).read_text())
    old = ast.parse(Path("evals/deterministic_evidence_v1/transport.py").read_text())
    preserved = {
        "_DeadlineReader",
        "_DeadlineSocket",
        "_Connection",
        "StreamAnswer",
        "screened",
        "plain_path",
    }
    old_nodes = {node.name: node for node in old.body if hasattr(node, "name")}
    new_nodes = {node.name: node for node in new.body if hasattr(node, "name")}
    for name in preserved:
        assert ast.dump(old_nodes[name]) == ast.dump(new_nodes[name])
    old_request = next(
        node
        for node in old_nodes["DiagnosticBudget"].body
        if isinstance(node, ast.FunctionDef) and node.name == "_request"
    )
    new_request = next(
        node
        for node in new_nodes["DiagnosticBudget"].body
        if isinstance(node, ast.FunctionDef) and node.name == "_request"
    )
    assert ast.dump(old_request) == ast.dump(new_request)


@pytest.mark.parametrize(
    "changed",
    ["campaign", "development", "diagnostic", "different_parent", "wrong_journal"],
)
def test_foreign_namespace_rejected_before_any_filesystem_access(
    tmp_path, monkeypatch, changed
):
    campaign_root = tmp_path / t.ROOT_NAMES["campaign"]
    lab = tmp_path / t.ROOT_NAMES["lab"] / "journal.jsonl"
    diagnostic = tmp_path / t.ROOT_NAMES["acceptance"] / "journal.jsonl"
    if changed == "campaign":
        campaign_root = tmp_path / "spruce-sprint12-campaign"
    elif changed == "development":
        lab = tmp_path / "birch-sprint9-lab" / "journal.jsonl"
    elif changed == "diagnostic":
        diagnostic = tmp_path / "spruce-sprint12-diagnostic" / "journal.jsonl"
    elif changed == "different_parent":
        diagnostic = tmp_path / "foreign" / t.ROOT_NAMES["acceptance"] / "journal.jsonl"
    else:
        lab = lab.with_name("old.jsonl")

    def forbidden(*_args, **_kwargs):
        pytest.fail("Rejected namespace must not perform filesystem access")

    for method in ("mkdir", "open", "read_bytes", "stat", "is_symlink", "is_junction"):
        monkeypatch.setattr(Path, method, forbidden)
    with pytest.raises(t.CampaignStop, match="Sprint 13"):
        t.CampaignLedger(campaign_root, lab_journal=lab, acceptance_journal=diagnostic)


@pytest.mark.parametrize("mode", ["old_root", "other_parent", "wrong_track"])
def test_budget_namespace_and_manifest_track_match_precede_filesystem_access(
    tmp_path, monkeypatch, mode
):
    with campaign(tmp_path) as c:
        root, track = tmp_path / t.ROOT_NAMES["lab"], "lab"
        if mode == "old_root":
            root = tmp_path / "spruce-sprint12-development"
        elif mode == "other_parent":
            root = tmp_path / "elsewhere" / t.ROOT_NAMES["lab"]
        else:
            track = "acceptance"

        def forbidden(*_args, **_kwargs):
            pytest.fail("Mismatched track must not perform filesystem access")

        with monkeypatch.context() as patch:
            for method in (
                "mkdir",
                "open",
                "read_bytes",
                "stat",
                "is_symlink",
                "is_junction",
            ):
                patch.setattr(Path, method, forbidden)
            with pytest.raises((t.DiagnosticStop, t.CampaignStop)):
                t.DiagnosticBudget(root, umbrella=c, track=track)


def test_local_reservation_crash_gap_blocks_other_track_on_campaign_reopen(tmp_path):
    with (
        campaign(tmp_path) as c,
        t.DiagnosticBudget(tmp_path / t.ROOT_NAMES["lab"], umbrella=c) as b,
    ):
        b.begin("DEV-07", trial="interrupted", contrast="D0")
        # Simulate the durable local reservation immediately before the global
        # reservation. No provider request occurred and no completion is invented.
        b.event(event="provider_reserved", attempt="s13-d-0001", contrast="D0")
        assert c.snapshot()["reserved"] == 0
    with pytest.raises(t.CampaignStop, match="accounting mismatch"):
        campaign(tmp_path)
    assert not (tmp_path / t.ROOT_NAMES["acceptance"]).exists()


@pytest.mark.parametrize(
    "change",
    [
        "missing_track",
        "changed_outcome",
        "missing_artifact",
        "same_length_artifact",
        "duplicate_artifact",
        "unsafe_path",
    ],
)
def test_track_or_artifact_replay_mismatch_prevents_any_fresh_campaign(
    tmp_path, monkeypatch, change
):
    with budget(tmp_path) as b:
        calls, _ = install(monkeypatch, b, [frame(done=True, content="{}")])
        b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
        journal, reply = b.root / "journal.jsonl", b.directory / "s13-d-0001.json"
        assert len(calls) == 1
    if change == "missing_track":
        journal.unlink()
    elif change == "changed_outcome":
        journal.write_bytes(
            journal.read_bytes().replace(
                b'"outcome":"COMPLETED"', b'"outcome":"KNOWN_WITHHELD"'
            )
        )
    elif change == "missing_artifact":
        reply.unlink()
    elif change == "same_length_artifact":
        original = reply.read_bytes()
        altered = original.replace(b'"content":"{}"', b'"content":"[]"')
        assert original != altered and len(original) == len(altered)
        reply.write_bytes(altered)
    else:
        rows = [json.loads(line) for line in journal.read_bytes().splitlines()]
        stored = next(row for row in rows if row["event"] == "artifact_stored")
        if change == "duplicate_artifact":
            rows.append(dict(stored))
        else:
            stored["path"] = "../outside.json"
        journal.write_bytes(b"".join(t.encoded(row) + b"\n" for row in rows))
    with pytest.raises(t.CampaignStop):
        campaign(tmp_path)
    assert len(calls) == 1  # A mismatch cannot be turned into another raw send.


def test_budget_replay_checks_same_length_reply_tamper_even_with_open_campaign(
    tmp_path, monkeypatch
):
    with campaign(tmp_path) as c:
        root = tmp_path / t.ROOT_NAMES["lab"]
        with t.DiagnosticBudget(root, umbrella=c) as b:
            b.begin("DEV-08", trial="tamper", contrast="D0")
            calls, _ = install(monkeypatch, b, [frame(done=True, content="{}")])
            b.chat(MESSAGES, SCHEMA, OPTIONS, think=False)
            reply = b.directory / "s13-d-0001.json"
        original = reply.read_bytes()
        reply.write_bytes(original.replace(b'"content":"{}"', b'"content":"[]"'))
        assert reply.stat().st_size == len(original)
        with pytest.raises(t.DiagnosticStop):
            t.DiagnosticBudget(root, umbrella=c)
        assert len(calls) == 1
