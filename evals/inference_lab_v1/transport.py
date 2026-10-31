"""Sequential, durable Sprint 9 accounting shared by both provider HTTP stacks.

No provider is contacted by importing this module. A reservation is fsynced before
send; an unresolved send prevents further generation. Old evaluation code/data
remain unchanged. Full hidden thinking is never retained.
"""

import hashlib
import json
import os
import re
import threading
import time
from pathlib import Path

from app.inference_context import EvidenceBudgetError
from evals.cross_pillar_v1.transport import (
    HOST,
    CountedHttpx,
    checked_url,
    counted_session_class,
    safe_bytes,
)

MODEL = "qwen3:8b"
DIGEST = "500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41"
CAPS = {"lab": 24, "acceptance": 12}
DEADLINE = 14_400
REQUEST_SECONDS = 180
MAX_BYTES = 12_000_000
MAX_PROMPT_BYTES = 180_000


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


class BudgetStop(EvidenceBudgetError):
    """No automatic provider retry after accounting/operational refusal."""

    def __init__(self):
        super().__init__("request_rejected")


def safe_output(data: bytes) -> None:
    safe_bytes(data)
    if re.search(rb"(?i)[a-z]:\\users\\|/home/[^/\s]+/|/Users/[^/\s]+/", data):
        raise BudgetStop()


class SprintBudget:
    def __init__(self, root: Path, *, clock=time.monotonic):
        self.root, self.clock = root, clock
        if root.is_symlink() or root.is_junction():
            raise BudgetStop()
        root.mkdir(parents=True, exist_ok=True)
        self.lock_path = root / "active.lock"
        self.lock_file = self.lock_path.open("x", encoding="utf-8")
        self.journal = None
        try:
            self.counts = dict.fromkeys(CAPS, 0)
            self.count = 0
            self.retained_bytes = 0
            self.started = clock()
            self.started_wall = time.time()
            self.pending = None
            self.blocked = False
            self.track = self.case_id = self.directory = None
            self.context = {}
            self.request_metadata = {}
            self.mutex = threading.Lock()
            path = root / "journal.jsonl"
            self.journal_bytes = path.stat().st_size if path.exists() else 0
            if path.exists():
                if path.stat().st_size > MAX_BYTES:
                    raise BudgetStop()
                for line in path.read_text(encoding="utf-8").splitlines():
                    row = json.loads(line)
                    if row["event"] == "sprint_started":
                        self.started_wall = row["unix_seconds"]
                    elif row["event"] == "provider_reserved":
                        if self.pending or row["global_index"] != self.count + 1:
                            raise BudgetStop()
                        self.count += 1
                        self.counts[row["track"]] += 1
                        self.pending = row["attempt"]
                    elif row["event"] in {"provider_response", "provider_failure"}:
                        if row["attempt"] != self.pending:
                            raise BudgetStop()
                        self.pending = None
                        self.blocked |= row["event"] == "provider_failure"
                    elif row["event"] == "artifact_stored":
                        self.retained_bytes += row["bytes"]
                if (
                    self.pending
                    or self.blocked
                    or self.count > 36
                    or any(self.counts[k] > CAPS[k] for k in CAPS)
                ):
                    raise BudgetStop()
            self.journal = path.open("a", encoding="utf-8", newline="\n")
            if not self.journal_bytes:
                self.event(event="sprint_started", unix_seconds=self.started_wall)
        except BaseException:
            self.lock_file.close()
            self.lock_path.unlink()
            raise

    def event(self, **row):
        line = encoded(row) + b"\n"
        if self.retained_bytes + self.journal_bytes + len(line) > MAX_BYTES:
            raise BudgetStop()
        self.journal.write(line.decode())
        self.journal.flush()
        os.fsync(self.journal.fileno())
        self.journal_bytes += len(line)

    def begin(self, track, case, directory, **context):
        if track not in CAPS or self.pending or self.blocked:
            raise BudgetStop()
        self.track, self.case_id, self.directory = track, case, directory
        self.context = context

    def remaining(self):
        seconds = DEADLINE - max(
            self.clock() - self.started, time.time() - self.started_wall
        )
        if seconds < REQUEST_SECONDS:
            raise BudgetStop()
        return REQUEST_SECONDS

    def prepare(self, body):
        """Validate actual provider request, rather than an intended configuration."""
        if len(body) > MAX_PROMPT_BYTES:
            raise BudgetStop()
        value = json.loads(body)
        if (
            set(value)
            - {
                "model",
                "messages",
                "format",
                "options",
                "stream",
                "truncate",
                "shift",
                "think",
            }
            or not isinstance(value.get("messages"), list)
            or any(
                set(message) != {"role", "content"}
                or message["role"] not in {"system", "user"}
                or not isinstance(message["content"], str)
                for message in value.get("messages", [])
            )
            or not isinstance(value.get("format"), dict)
            or ("think" in value and type(value["think"]) is not bool)
            or value.get("model") != MODEL
            or value.get("stream") is not False
            or value.get("truncate") is not False
            or value.get("shift") is not False
            or value.get("options") != {"temperature": 0.1, "num_ctx": 8192}
        ):
            raise BudgetStop()
        self.request_metadata = {
            "request_sha256": sha(body),
            "prompt_sha256": sha(encoded(value["messages"])),
            "schema_sha256": sha(encoded(value["format"])),
            "prompt_bytes": len(encoded(value["messages"])),
            "schema_bytes": len(encoded(value["format"])),
            "model": MODEL,
            "model_digest": DIGEST,
            "options": value["options"],
            "think": value.get("think", "provider_default"),
            "truncate": False,
            "shift": False,
        }

    def reserve(self, url, method):
        with self.mutex:
            path = checked_url(url, method)
            self.remaining()
            if path != "/api/chat":
                return None
            if (
                self.pending
                or self.blocked
                or not self.case_id
                or not self.request_metadata
                or self.count >= 36
                or self.counts[self.track] >= CAPS[self.track]
            ):
                raise BudgetStop()
            attempt = f"s9-{self.count + 1:04d}"
            self.event(
                event="provider_reserved",
                attempt=attempt,
                global_index=self.count + 1,
                track=self.track,
                track_index=self.counts[self.track] + 1,
                case_id=self.case_id,
                **self.context,
                **self.request_metadata,
            )
            self.count += 1
            self.counts[self.track] += 1
            self.pending = attempt
            return attempt

    def allow_storage(self, length):
        if self.retained_bytes + self.journal_bytes + length > MAX_BYTES:
            raise BudgetStop()

    def store(self, path, data):
        safe_output(data)
        self.allow_storage(len(data))
        with path.open("xb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        self.retained_bytes += len(data)
        self.event(event="artifact_stored", bytes=len(data), sha256=sha(data))

    def response(self, attempt, status, data, elapsed):
        if attempt is None:
            return
        safe_output(data)
        value = json.loads(data)
        message = value.get("message", {})
        thinking = message.pop("thinking", None)
        if "thinking" in value:
            thinking = value.pop("thinking")
        content = message.get("content")
        inline = []
        if isinstance(content, str):
            inline = re.findall(r"<think>.*?</think>", content, flags=re.DOTALL)
            if "<think>" in content and not inline:
                raise BudgetStop()
            message["content"] = re.sub(
                r"<think>.*?</think>", "", content, flags=re.DOTALL
            )
        sanitized = encoded(value)
        name = attempt + ".json"
        self.store(self.directory / name, sanitized)
        self.event(
            event="provider_response",
            attempt=attempt,
            case_id=self.case_id,
            http_status=status,
            raw_response_sha256=sha(data),
            artifact_sha256=sha(sanitized),
            artifact=name,
            thinking_present=bool(thinking or inline),
            thinking_bytes=len(str(thinking or "").encode())
            + sum(len(v.encode()) for v in inline),
            wall_seconds=round(elapsed, 6),
            usage={
                k: value.get(k)
                for k in (
                    "prompt_eval_count",
                    "eval_count",
                    "total_duration",
                    "load_duration",
                    "prompt_eval_duration",
                    "eval_duration",
                )
            },
        )
        self.pending = None

    def failure(self, attempt, exc):
        if attempt and self.pending == attempt:
            self.event(
                event="provider_failure",
                attempt=attempt,
                exception_type=type(exc).__name__,
                outcome="unknown_no_retry",
            )
            self.pending = None
            self.blocked = True

    def close(self):
        if self.journal:
            self.journal.close()
        self.lock_file.close()
        self.lock_path.unlink()


class FingerprintedHttpx(CountedHttpx):
    def handle_request(self, request):
        if checked_url(str(request.url), request.method) == "/api/chat":
            self.budget.prepare(request.read())
        return super().handle_request(request)


def fingerprinted_session_class(budget):
    class FingerprintedSession(counted_session_class(budget)):
        def send(self, request, **kwargs):
            if checked_url(request.url, request.method) == "/api/chat":
                body = request.body
                budget.prepare(body.encode() if isinstance(body, str) else body)
            return super().send(request, **kwargs)

    return FingerprintedSession


def provider_client(budget):
    from ollama import Client

    return Client(
        host=HOST,
        transport=FingerprintedHttpx(budget),
        timeout=REQUEST_SECONDS,
        trust_env=False,
        follow_redirects=False,
    )
