"""Sprint 13 foreground transport, copied from the audited Sprint 11 transport.

The socket deadline applies to every send/read, including HTTP headers and chunk
framing. No watchdog, thread, retry, proxy, redirect, or service operation is used.
Only an answer and usage survive; thinking is counted/hashed then discarded.
Legacy track name ``acceptance`` means this sprint's diagnostic holdout only;
it confers no release acceptance. The caller must use new isolated output roots
and perform read-only provider/model-identity preflight before every raw send.
"""

import hashlib
import http.client
import io
import json
import math
import os
import re
import socket
import threading
import time
from pathlib import Path

from app.inference_context import EvidenceBudgetError

MODEL = "qwen3:8b"
DIGEST = "500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41"
HOST = "http://127.0.0.1:11434"
LAB_CAP = 84
PHASE_CAPS = {"D0": 24, "D1": 24, "D3": 36, "A": 24}
REQUEST_SECONDS = 600
CONNECT_SECONDS = 10
IDLE_SECONDS = 120
CAMPAIGN_SECONDS = 14_400
MAX_RESPONSE_BYTES = 1_000_000
MAX_RETAINED_BYTES = 64_000_000
MAX_PROMPT_BYTES = 48_000
# Ordinary answer cap and independent 1 MB NDJSON wire bound.
# The same token ceiling applies to every arm; length completion is withheld.
OPTIONS = {"temperature": 0.1, "num_ctx": 32768, "num_predict": 4096}
USAGE_FIELDS = (
    "total_duration",
    "load_duration",
    "prompt_eval_count",
    "prompt_eval_duration",
    "eval_count",
    "eval_duration",
)
ROOT_NAMES = {
    "lab": "willow-sprint13-development",
    "acceptance": "willow-sprint13-diagnostic",
    "campaign": "willow-sprint13-campaign",
}


def named_root(path, kind):
    """Lexical namespace gate; do not touch any candidate path before this check."""
    path = Path(path)
    if path.name != ROOT_NAMES[kind] or ".." in path.parts:
        raise CampaignStop("Sprint 13 namespace required")
    return path.absolute()


def artifact_bytes(root, row, seen):
    """Replay only exact, bounded, unique artifacts inside the new track root."""
    name = row.get("path")
    if (
        not isinstance(name, str)
        or not re.fullmatch(r"trials/[a-zA-Z0-9_-]{1,100}/[a-zA-Z0-9_.-]{1,120}", name)
        or name.rsplit("/", 1)[1] in {".", ".."}
        or name in seen
        or type(row.get("bytes")) is not int
        or not 0 <= row["bytes"] <= MAX_RESPONSE_BYTES
        or not isinstance(row.get("sha256"), str)
        or not re.fullmatch(r"[a-f0-9]{64}", row["sha256"])
    ):
        raise DiagnosticStop("artifact_identity")
    path = root.joinpath(*name.split("/"))
    plain_path(path)
    if not path.is_file() or path.stat().st_size != row["bytes"]:
        raise DiagnosticStop("artifact_missing_or_changed")
    with path.open("rb") as source:
        data = source.read(MAX_RESPONSE_BYTES + 1)
    if len(data) != row["bytes"] or sha(data) != row["sha256"]:
        raise DiagnosticStop("artifact_missing_or_changed")
    seen.add(name)
    return len(data)


def encoded(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class DiagnosticStop(EvidenceBudgetError):
    """Withhold safely; production's existing retry exclusion recognizes this."""

    def __init__(self, code="request_rejected"):
        super().__init__(code)


def screened(data: bytes) -> None:
    if len(data) > MAX_RESPONSE_BYTES or re.search(
        rb"(?i)-----BEGIN .*PRIVATE KEY|sk-[a-z0-9_-]{24,}|"
        rb"gh[pousr]_[a-z0-9]{24,}|[a-z]:[\\/]+users[\\/]|/home/[^/\s]+/|/Users/[^/\s]+/",
        data,
    ):
        raise DiagnosticStop()


def plain_path(path: Path) -> None:
    if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
        raise DiagnosticStop()


class _DeadlineReader(io.RawIOBase):
    def __init__(self, owner):
        self.owner = owner

    def readable(self):
        return True

    def readinto(self, buffer):
        self.owner.limit()
        return self.owner.socket.recv_into(buffer)

    def close(self):
        if not self.closed:
            self.owner.files -= 1
            if self.owner.closing and not self.owner.files:
                self.owner.socket.close()
        super().close()


class _DeadlineSocket:
    """http.client's buffered header/body reader still uses this bounded recv."""

    def __init__(self, connection, deadline, clock):
        self.socket, self.deadline, self.clock = connection, deadline, clock
        self.files, self.closing = 0, False

    def limit(self):
        remaining = self.deadline - self.clock()
        if remaining <= 0:
            raise TimeoutError("Laboratory wall deadline")
        self.socket.settimeout(min(IDLE_SECONDS, remaining))

    def sendall(self, data):
        self.limit()
        self.socket.sendall(data)

    def makefile(self, mode):
        if mode != "rb":
            raise DiagnosticStop()
        self.files += 1
        return io.BufferedReader(_DeadlineReader(self))

    def close(self):
        self.closing = True
        if not self.files:
            self.socket.close()


class _Connection(http.client.HTTPConnection):
    def __init__(self, deadline, clock):
        super().__init__("127.0.0.1", 11434, timeout=CONNECT_SECONDS)
        self.deadline, self.clock = deadline, clock

    def connect(self):
        remaining = self.deadline - self.clock()
        if remaining <= 0:
            raise TimeoutError("Laboratory connect deadline")
        raw = socket.create_connection(
            ("127.0.0.1", 11434), timeout=min(CONNECT_SECONDS, remaining)
        )
        self.sock = _DeadlineSocket(raw, self.deadline, self.clock)


class StreamAnswer:
    """Incremental NDJSON framing; only allowlisted final-answer fields survive."""

    def __init__(self):
        self.pending = bytearray()
        self.raw_bytes = self.thinking_bytes = 0
        self.raw_hash, self.thinking_hash = hashlib.sha256(), hashlib.sha256()
        self.content = []
        self.final = None
        self.frames = 0

    def feed(self, chunk):
        self.raw_bytes += len(chunk)
        if self.raw_bytes > MAX_RESPONSE_BYTES:
            raise DiagnosticStop()
        self.raw_hash.update(chunk)
        self.pending.extend(chunk)
        while b"\n" in self.pending:
            line, _, tail = self.pending.partition(b"\n")
            self.pending = bytearray(tail)
            if line.strip():
                self.frame(bytes(line))

    def frame(self, line):
        if self.final is not None:
            raise DiagnosticStop()
        value = json.loads(line)
        if (
            not isinstance(value, dict)
            or value.get("model") != MODEL
            or type(value.get("done")) is not bool
            or "error" in value
        ):
            raise DiagnosticStop()
        message = value.get("message", {})
        if not isinstance(message, dict) or message.get("role") != "assistant":
            raise DiagnosticStop()
        for hidden in (message.get("thinking", ""), value.get("thinking", "")):
            if not isinstance(hidden, str):
                raise DiagnosticStop()
            raw = hidden.encode()
            self.thinking_bytes += len(raw)
            self.thinking_hash.update(raw)
        content = message.get("content", "")
        if not isinstance(content, str):
            raise DiagnosticStop()
        self.content.append(content)
        self.frames += 1
        if value["done"]:
            if value.get("done_reason") not in {"stop", "length"}:
                raise DiagnosticStop()
            if any(
                type(value[k]) is not int or value[k] < 0
                for k in USAGE_FIELDS
                if k in value
            ):
                raise DiagnosticStop()
            self.final = {
                k: value[k]
                for k in ("model", "done", "done_reason", *USAGE_FIELDS)
                if k in value
            }

    def answer(self):
        if self.pending.strip():
            self.frame(bytes(self.pending))
            self.pending.clear()
        if self.final is None:
            raise DiagnosticStop("incomplete_generation")
        content = "".join(self.content)
        for hidden in re.findall(
            r"<think>.*?</think>", content, flags=re.IGNORECASE | re.DOTALL
        ):
            self.thinking_bytes += len(hidden.encode())
            self.thinking_hash.update(hidden.encode())
        content = re.sub(
            r"<think>.*?</think>", "", content, flags=re.IGNORECASE | re.DOTALL
        )
        if re.search(r"</?think\b", content, flags=re.IGNORECASE):
            raise DiagnosticStop()
        result = {**self.final, "message": {"role": "assistant", "content": content}}
        screened(encoded(result))
        return result

    def metadata(self):
        return {
            "raw_response_bytes": self.raw_bytes,
            "raw_response_sha256": self.raw_hash.hexdigest(),
            "frames": self.frames,
            "thinking_present": self.thinking_bytes > 0,
            "thinking_bytes": self.thinking_bytes,
            "thinking_sha256": self.thinking_hash.hexdigest(),
        }


class DiagnosticBudget:
    """Append-only, locked track-counted journal; unresolved sends permanently block it."""

    def __init__(self, root: Path, *, umbrella=None, clock=time.monotonic, track="lab"):
        if track not in {"lab", "acceptance"}:
            raise DiagnosticStop()
        root = named_root(root, track)
        if (
            not isinstance(umbrella, CampaignLedger)
            or umbrella.closed
            or root.parent != umbrella.root.parent
            or umbrella.identity["journals"][track] != (root.name + "/journal.jsonl")
        ):
            raise DiagnosticStop("campaign_track_root_mismatch")
        self.track, self.cap = track, LAB_CAP if track == "lab" else 24
        self.root, self.umbrella, self.clock = root, umbrella, clock
        plain_path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.root / "active.lock"
        self.lock = self.lock_path.open("x", encoding="utf-8")
        self.journal = None
        self.count = self.retained_bytes = self.journal_bytes = 0
        self.phase_counts = dict.fromkeys(PHASE_CAPS, 0)
        self.pending, self.blocked = None, False
        self.case_id, self.context, self.directory = None, {}, None
        self.started, self.started_wall = clock(), time.time()
        try:
            path = self.root / "journal.jsonl"
            plain_path(path)
            if path.exists():
                self._replay(path)
            self.journal = path.open("a", encoding="utf-8", newline="\n")
            if not self.journal_bytes:
                self.event(
                    event="campaign_started",
                    unix_seconds=self.started_wall,
                    monotonic_seconds=self.started,
                    lab_cap=self.cap,
                    track=self.track,
                )
        except BaseException:
            self.close()
            raise

    def _replay(self, path):
        self.journal_bytes = path.stat().st_size
        if self.journal_bytes > MAX_RETAINED_BYTES:
            raise DiagnosticStop()
        rows = [json.loads(line) for line in path.read_bytes().splitlines()]
        if (
            not rows
            or rows[0].get("event") != "campaign_started"
            or rows[0].get("lab_cap") != self.cap
            or rows[0].get("track") != self.track
        ):
            raise DiagnosticStop()
        self.started = rows[0]["monotonic_seconds"]
        self.started_wall = rows[0]["unix_seconds"]
        if self.clock() < self.started or time.time() < self.started_wall:
            raise DiagnosticStop()
        artifacts = set()
        for row in rows[1:]:
            if row["event"] == "provider_reserved":
                if self.pending or row["attempt"] != f"s13-d-{self.count + 1:04d}":
                    raise DiagnosticStop()
                self.count += 1
                phase = row.get("contrast")
                allowed = {"D0", "D1", "D3"} if self.track == "lab" else {"A"}
                if phase not in allowed:
                    raise DiagnosticStop()
                self.phase_counts[phase] += 1
                if self.phase_counts[phase] > PHASE_CAPS[phase]:
                    raise DiagnosticStop()
                self.pending = row["attempt"]
            elif row["event"] == "provider_finished":
                if row["attempt"] != self.pending or row["outcome"] not in {
                    "COMPLETED",
                    "KNOWN_WITHHELD",
                    "UNKNOWN",
                }:
                    raise DiagnosticStop()
                self.pending = None
                self.blocked |= row["outcome"] == "UNKNOWN"
            elif row["event"] == "artifact_stored":
                self.retained_bytes += artifact_bytes(self.root, row, artifacts)
            else:
                raise DiagnosticStop()
        if self.pending or self.blocked or self.count > self.cap:
            raise DiagnosticStop()
        self._space(0)

    def event(self, **row):
        data = encoded(row) + b"\n"
        screened(data)
        self._space(len(data))
        self.journal.write(data.decode())
        self.journal.flush()
        os.fsync(self.journal.fileno())
        self.journal_bytes += len(data)

    def _space(self, length):
        if self.retained_bytes + self.journal_bytes + length > MAX_RETAINED_BYTES:
            raise DiagnosticStop()

    def begin(self, case_id: str, *, trial: str, **metadata):
        if (
            self.pending
            or self.blocked
            or any(
                not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", value)
                for value in (case_id, trial)
            )
        ):
            raise DiagnosticStop()
        self.case_id, self.context = case_id, {"trial": trial, **metadata}
        self.directory = self.root / "trials" / trial
        plain_path(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def store(self, name: str, value):
        if not re.fullmatch(r"[a-zA-Z0-9_.-]{1,120}", name) or name in {".", ".."}:
            raise DiagnosticStop()
        if self.directory is None:
            raise DiagnosticStop()
        data = encoded(value) + b"\n"
        screened(data)
        self._space(len(data) + 1024)
        path = self.directory / name
        plain_path(path)
        with path.open("xb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        self.retained_bytes += len(data)
        self.event(
            event="artifact_stored",
            bytes=len(data),
            sha256=sha(data),
            path=path.relative_to(self.root).as_posix(),
        )
        return path

    def snapshot(self):
        return {
            "raw_attempts": self.count,
            "phase_counts": dict(self.phase_counts),
            "pending": self.pending,
            "blocked": self.blocked,
            "remaining": self.cap - self.count,
        }

    def _request(self, messages, schema, options, think):
        if (
            not isinstance(messages, list)
            or not messages
            or any(
                not isinstance(m, dict)
                or set(m) != {"role", "content"}
                or m["role"] not in {"system", "user"}
                or not isinstance(m["content"], str)
                for m in messages
            )
            or not isinstance(schema, dict)
            or not schema
            or options != {"temperature": 0.1, "num_ctx": 32768}
            or (think is not None and type(think) is not bool)
        ):
            raise DiagnosticStop()
        value = {
            "model": MODEL,
            "messages": messages,
            "format": schema,
            "options": OPTIONS,
            "stream": True,
            "truncate": False,
            "shift": False,
        }
        if think is not None:
            value["think"] = think
        body = encoded(value)
        # Conservative UTF8-byte token upper bound, including JSON schema and template.
        context_bound = (
            sum(len(m["content"].encode()) for m in messages)
            + len(encoded(schema))
            + 512
            + OPTIONS["num_predict"]
        )
        if context_bound > OPTIONS["num_ctx"]:
            raise DiagnosticStop("request_rejected")
        if len(body) > MAX_PROMPT_BYTES:
            raise DiagnosticStop()
        screened(body)
        return body

    def chat(self, messages, response_schema, options, *, think=None):
        body = self._request(messages, response_schema, options, think)
        phase = self.context.get("contrast")
        if phase not in ({"D0", "D1", "D3"} if self.track == "lab" else {"A"}):
            raise DiagnosticStop()
        if phase is not None and (
            phase not in PHASE_CAPS or self.phase_counts[phase] >= PHASE_CAPS[phase]
        ):
            raise DiagnosticStop()
        elapsed = max(self.clock() - self.started, time.time() - self.started_wall)
        if (
            self.pending
            or self.blocked
            or not self.case_id
            or self.count >= self.cap
            or elapsed + REQUEST_SECONDS > CAMPAIGN_SECONDS
            or self.umbrella is None
        ):
            raise DiagnosticStop()
        # The shared first-start clock prevents switching tracks/reopening a
        # process from granting a fresh campaign wall-time allowance.
        self.umbrella.check_dispatch()
        attempt = f"s13-d-{self.count + 1:04d}"
        # Reserve enough retention capacity before asking the shared provider to
        # work; actual synthetic wire prompts are retained for reproducibility.
        self._space(len(body) + MAX_RESPONSE_BYTES + 16_384)
        self.store(attempt + "-request.json", json.loads(body))
        self.event(
            event="provider_reserved",
            attempt=attempt,
            case_id=self.case_id,
            **self.context,
            request_sha256=sha(body),
            prompt_sha256=sha(encoded(messages)),
            schema_sha256=sha(encoded(response_schema)),
            model=MODEL,
            model_digest=DIGEST,
            options=OPTIONS,
            think="provider_default" if think is None else think,
            stream=True,
            truncate=False,
            shift=False,
            request_bytes=len(body),
            wall_seconds=REQUEST_SECONDS,
            connect_seconds=CONNECT_SECONDS,
            idle_seconds=IDLE_SECONDS,
        )
        self.pending, self.count = attempt, self.count + 1
        if phase is not None:
            self.phase_counts[phase] += 1
        self.umbrella.reserve(track=self.track, attempt=attempt)
        started = self.clock()
        parser, response = StreamAnswer(), None
        connection = _Connection(started + REQUEST_SECONDS, self.clock)
        outcome = "UNKNOWN"
        try:
            connection.request(
                "POST",
                "/api/chat",
                body=body,
                headers={"Content-Type": "application/json", "Connection": "close"},
            )
            response = connection.getresponse()
            if response.status != 200:
                raise DiagnosticStop()
            while True:
                chunk = response.read1(8192)
                if not chunk:
                    break
                parser.feed(chunk)
                if parser.final is not None:
                    break
            answer = parser.answer()
            outcome = "COMPLETED"
            if (
                answer["done_reason"] == "length"
                or not answer["message"]["content"].strip()
            ):
                outcome = "KNOWN_WITHHELD"
            self.store(attempt + ".json", answer)
            self._finish(attempt, outcome, started, parser, answer)
            if outcome == "KNOWN_WITHHELD":
                raise DiagnosticStop(
                    "generation_limit"
                    if answer["done_reason"] == "length"
                    else "incomplete_generation"
                )
            return answer
        except BaseException as exc:
            if self.pending == attempt:
                self._finish(
                    attempt,
                    "UNKNOWN",
                    started,
                    parser,
                    exception_type=type(exc).__name__,
                )
            if isinstance(exc, (KeyboardInterrupt, SystemExit, DiagnosticStop)):
                raise
            raise DiagnosticStop("incomplete_generation") from None
        finally:
            if response is not None:
                response.close()
            connection.close()

    def _finish(self, attempt, outcome, started, parser, answer=None, **extra):
        self.event(
            event="provider_finished",
            attempt=attempt,
            outcome=outcome,
            wall_seconds=round(self.clock() - started, 6),
            **parser.metadata(),
            usage={k: answer.get(k) for k in USAGE_FIELDS} if answer else {},
            **extra,
        )
        self.pending = None
        self.blocked |= outcome == "UNKNOWN"
        self.umbrella.finish(track=self.track, attempt=attempt, outcome=outcome)

    def close(self):
        if self.journal:
            self.journal.close()
        self.lock.close()
        self.lock_path.unlink(missing_ok=True)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


CAPS = {"lab": 84, "acceptance": 24}
MAX_ATTEMPTS = 108
MAX_JOURNAL_BYTES = 256_000


class CampaignStop(RuntimeError):
    """A closed, inconsistent or outstanding campaign cannot send again."""


def reject_linked_path(path: Path) -> None:
    """Inspect every existing ancestor; resolving first would hide a link."""
    for item in (path, *path.parents):
        if item.is_symlink() or item.is_junction():
            raise CampaignStop("Linked diagnostic output refused")


def _encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


class CampaignLedger:
    """Exclusive lock, durable reservations, disjoint 84/24 caps and one clock.

    ``acceptance`` is a legacy accounting name for the fresh diagnostic track.
    Neither passing the diagnostic nor a completed reservation is release acceptance.
    """

    def __init__(
        self,
        root: Path,
        *,
        lab_journal: Path,
        acceptance_journal: Path,
        clock=time.monotonic,
        wall_clock=time.time,
    ):
        # Check every supplied name and common parent before any file metadata,
        # resolution, directory creation or historical-root access is possible.
        root = named_root(root, "campaign")
        lab_journal, acceptance_journal = Path(lab_journal), Path(acceptance_journal)
        if (
            lab_journal.name != "journal.jsonl"
            or acceptance_journal.name != "journal.jsonl"
        ):
            raise CampaignStop("Sprint 13 journal name required")
        lab_root = named_root(lab_journal.parent, "lab")
        diagnostic_root = named_root(acceptance_journal.parent, "acceptance")
        if root.parent != lab_root.parent or root.parent != diagnostic_root.parent:
            raise CampaignStop("Sprint 13 roots must share one parent")
        lab_journal = lab_root / "journal.jsonl"
        acceptance_journal = diagnostic_root / "journal.jsonl"
        reject_linked_path(root)
        root = root.resolve()
        self.root = root
        for path in (lab_journal, acceptance_journal):
            reject_linked_path(path)
        try:
            journals = {
                "lab": Path(lab_journal).resolve().relative_to(root.parent).as_posix(),
                "acceptance": Path(acceptance_journal)
                .resolve()
                .relative_to(root.parent)
                .as_posix(),
            }
        except ValueError as exc:
            raise CampaignStop("Journals must share the campaign workspace") from exc
        if journals["lab"] == journals["acceptance"]:
            raise CampaignStop("Track journals must be separate")
        self.identity = {
            "format": "adaptive-security-reasoning-v1-campaign",
            "caps": CAPS,
            "aggregate_cap": MAX_ATTEMPTS,
            "journals": journals,
            "reservation_is_not_completion": True,
            "campaign_seconds": CAMPAIGN_SECONDS,
        }
        self.clock, self.wall_clock = clock, wall_clock
        self.started, self.started_wall = clock(), wall_clock()
        root.mkdir(parents=True, exist_ok=True)
        self.lock_path = root / "active.lock"
        for leaf in (self.lock_path, root / "manifest.json", root / "journal.jsonl"):
            reject_linked_path(leaf)
        self.lock = self.lock_path.open("xb")
        self.journal = None
        self.closed = False
        self.mutex = threading.Lock()
        self.counts = dict.fromkeys(CAPS, 0)
        self.pending = None
        self.blocked = False
        self.seen = set()
        self.outcomes = {}
        try:
            manifest = root / "manifest.json"
            existing = manifest.exists()
            if manifest.exists():
                if manifest.stat().st_size > 4096:
                    raise CampaignStop("Campaign identity changed")
                recorded = json.loads(manifest.read_bytes())
                start_fields = {"started_monotonic_seconds", "started_unix_seconds"}
                if (
                    not isinstance(recorded, dict)
                    or set(recorded) != set(self.identity) | start_fields
                    or {k: v for k, v in recorded.items() if k not in start_fields}
                    != self.identity
                    or any(
                        type(recorded[k]) not in {int, float}
                        or not math.isfinite(recorded[k])
                        for k in start_fields
                    )
                ):
                    raise CampaignStop("Campaign identity changed")
                self.started = recorded["started_monotonic_seconds"]
                self.started_wall = recorded["started_unix_seconds"]
                self.identity = recorded
            else:
                self.identity.update(
                    started_monotonic_seconds=self.started,
                    started_unix_seconds=self.started_wall,
                )
                with manifest.open("xb") as output:
                    output.write(_encoded(self.identity))
                    output.flush()
                    os.fsync(output.fileno())
            self.elapsed_seconds()
            path = root / "journal.jsonl"
            if existing and not path.exists():
                raise CampaignStop("Existing campaign journal is missing")
            self.journal_bytes = path.stat().st_size if path.exists() else 0
            if self.journal_bytes > MAX_JOURNAL_BYTES:
                raise CampaignStop("Oversized campaign journal")
            if path.exists():
                for line in path.read_bytes().splitlines():
                    self._apply(json.loads(line))
            if self.pending or self.blocked:
                raise CampaignStop("Outstanding or unknown provider work")
            self._reconcile_tracks()
            self.journal = path.open("ab")
        except BaseException:
            self.close()
            raise

    def _apply(self, row):
        if row.get("event") == "reserved":
            track, attempt = row.get("track"), row.get("attempt")
            key = (track, attempt)
            if (
                set(row) != {"event", "track", "attempt", "ordinal"}
                or not isinstance(track, str)
                or track not in CAPS
                or not isinstance(attempt, str)
                or not attempt
                or len(attempt) > 80
                or not re.fullmatch(r"[a-z0-9-]+", attempt)
                or key in self.seen
                or self.pending
                or self.blocked
                or self.counts[track] >= CAPS[track]
                or sum(self.counts.values()) >= MAX_ATTEMPTS
                or row["ordinal"] != sum(self.counts.values()) + 1
            ):
                raise CampaignStop("Invalid or exhausted campaign reservation")
            self.counts[track] += 1
            self.pending = key
            self.seen.add(key)
        elif row.get("event") == "finished":
            if (
                set(row) != {"event", "track", "attempt", "outcome"}
                or (row.get("track"), row.get("attempt")) != self.pending
                or row.get("outcome") not in {"COMPLETED", "KNOWN_WITHHELD", "UNKNOWN"}
            ):
                raise CampaignStop("Invalid campaign completion")
            self.blocked = row["outcome"] == "UNKNOWN"
            self.outcomes[self.pending] = row["outcome"]
            self.pending = None
        else:
            raise CampaignStop("Unrecognized campaign record")

    def _reconcile_tracks(self):
        """A local/global crash gap or altered artifact stops reopening, never repairs."""
        for track, relative in self.identity["journals"].items():
            path = self.root.parent / relative
            reject_linked_path(path)
            expected = {attempt for name, attempt in self.seen if name == track}
            if not path.exists():
                if expected:
                    raise CampaignStop("Declared track journal is missing")
                continue
            if path.stat().st_size > MAX_RETAINED_BYTES:
                raise CampaignStop("Oversized track journal")
            with path.open("rb") as source:
                raw = source.read(MAX_RETAINED_BYTES + 1)
            if len(raw) > MAX_RETAINED_BYTES:
                raise CampaignStop("Oversized track journal")
            try:
                rows = [json.loads(line) for line in raw.splitlines()]
                if (
                    not rows
                    or rows[0].get("event") != "campaign_started"
                    or rows[0].get("track") != track
                    or rows[0].get("lab_cap") != CAPS[track]
                ):
                    raise CampaignStop("Track journal identity changed")
                local, pending, artifacts, phases = (
                    {},
                    None,
                    set(),
                    dict.fromkeys(PHASE_CAPS, 0),
                )
                allowed = {"D0", "D1", "D3"} if track == "lab" else {"A"}
                for row in rows[1:]:
                    if row["event"] == "provider_reserved":
                        attempt, phase = row["attempt"], row.get("contrast")
                        if (
                            pending
                            or attempt != f"s13-d-{len(local) + 1:04d}"
                            or phase not in allowed
                            or phases[phase] >= PHASE_CAPS[phase]
                        ):
                            raise CampaignStop("Invalid track reservation")
                        phases[phase] += 1
                        local[attempt], pending = None, attempt
                    elif row["event"] == "provider_finished":
                        if row["attempt"] != pending or row["outcome"] not in {
                            "COMPLETED",
                            "KNOWN_WITHHELD",
                            "UNKNOWN",
                        }:
                            raise CampaignStop("Invalid track completion")
                        local[pending], pending = row["outcome"], None
                    elif row["event"] == "artifact_stored":
                        artifact_bytes(path.parent, row, artifacts)
                    else:
                        raise CampaignStop("Unrecognized track record")
                if (
                    pending
                    or set(local) != expected
                    or any(
                        outcome == "UNKNOWN"
                        or outcome != self.outcomes.get((track, attempt))
                        for attempt, outcome in local.items()
                    )
                ):
                    raise CampaignStop("Track/campaign accounting mismatch")
            except (ValueError, KeyError, TypeError, DiagnosticStop) as exc:
                raise CampaignStop("Invalid track journal or artifact") from exc

    def _append(self, row):
        if self.closed or self.journal is None:
            raise CampaignStop("Campaign is closed")
        data = _encoded(row)
        if self.journal_bytes + len(data) > MAX_JOURNAL_BYTES:
            raise CampaignStop("Campaign journal limit reached")
        # Validate before append; if persistence fails, in-memory state remains
        # conservative and the caller must not send.
        self._apply(row)
        self.journal.write(data)
        self.journal.flush()
        os.fsync(self.journal.fileno())
        self.journal_bytes += len(data)

    def reserve(self, *, track, attempt):
        with self.mutex:
            self.check_dispatch()
            self._append(
                {
                    "event": "reserved",
                    "track": track,
                    "attempt": attempt,
                    "ordinal": sum(self.counts.values()) + 1,
                }
            )

    def finish(self, *, track, attempt, outcome):
        with self.mutex:
            self._append(
                {
                    "event": "finished",
                    "track": track,
                    "attempt": attempt,
                    "outcome": outcome,
                }
            )

    def snapshot(self):
        elapsed = self.elapsed_seconds()
        return {
            "counts": dict(self.counts),
            "reserved": sum(self.counts.values()),
            "pending": self.pending,
            "blocked": self.blocked,
            "remaining": {name: CAPS[name] - self.counts[name] for name in CAPS},
            "campaign_started_unix_seconds": self.started_wall,
            "elapsed_seconds": elapsed,
            "remaining_campaign_seconds": max(0, CAMPAIGN_SECONDS - elapsed),
        }

    def elapsed_seconds(self):
        """Use the larger elapsed value; rollback/reboot fails closed."""
        elapsed = self.clock() - self.started
        wall_elapsed = self.wall_clock() - self.started_wall
        if (
            not math.isfinite(elapsed)
            or not math.isfinite(wall_elapsed)
            or elapsed < 0
            or wall_elapsed < 0
        ):
            raise CampaignStop("Campaign clock changed")
        return max(elapsed, wall_elapsed)

    def check_dispatch(self):
        if self.closed or self.elapsed_seconds() + REQUEST_SECONDS > CAMPAIGN_SECONDS:
            raise CampaignStop("Campaign wall-time allowance exhausted")

    def close(self):
        if not self.closed:
            if self.journal is not None:
                self.journal.close()
            self.lock.close()
            self.lock_path.unlink()
            self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
