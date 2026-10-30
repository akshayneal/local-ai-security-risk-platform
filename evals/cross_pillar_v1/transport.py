"""Evaluation-only loopback transports: reserve durably before every generation.

Both HTTP stacks use zero transport retries. Application retries still pass here.
No application inference function is stubbed or replaced in the live run.
"""

import hashlib
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import requests

HOST = "http://127.0.0.1:11434"
MAX_CALLS = 32
MAX_SECONDS = 6500
CALL_SECONDS = 180
MAX_RESPONSE_BYTES = 256_000
MAX_RETAINED_BYTES = 6_000_000  # Leaves room for the small fresh workspace below 10 MB.


def checked_url(url: str, method: str) -> str:
    parsed = urlsplit(str(url))
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.port != 11434
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or (method, parsed.path)
        not in {("GET", "/api/version"), ("GET", "/api/tags"), ("POST", "/api/chat")}
    ):
        raise RuntimeError("Evaluation network boundary refused")
    return parsed.path


def safe_bytes(data: bytes) -> None:
    if len(data) > MAX_RESPONSE_BYTES or re.search(
        rb"-----BEGIN .*PRIVATE KEY|sk-[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{24,}",
        data,
    ):
        raise RuntimeError("Response size or sensitive-pattern check failed; withheld")


class Budget:
    def __init__(self, directory: Path, *, clock=time.monotonic):
        self.directory = directory
        self.clock = clock
        self.started = clock()
        self.count = 0
        self.case_id = None
        self.retained_bytes = 0
        self.journal = (directory / "journal.jsonl").open("x", encoding="utf-8")

    def event(self, **row):
        line = json.dumps(row, sort_keys=True) + "\n"
        self.allow_storage(len(line.encode()))
        self.journal.write(line)
        self.journal.flush()
        os.fsync(self.journal.fileno())

    def allow_storage(self, length):
        if self.retained_bytes + length > MAX_RETAINED_BYTES:
            raise RuntimeError("Frozen retained-output budget reached")
        self.retained_bytes += length

    def store(self, path, data):
        safe_bytes(data)
        self.allow_storage(len(data))
        with path.open("xb") as output:
            output.write(data)

    def remaining(self):
        seconds = MAX_SECONDS - (self.clock() - self.started)
        if seconds <= 0:
            raise RuntimeError("Frozen whole-run deadline reached")
        return min(CALL_SECONDS, seconds)

    def reserve(self, url, method):
        path = checked_url(url, method)
        self.remaining()
        if path != "/api/chat":
            return None
        if not self.case_id or self.count >= MAX_CALLS:
            raise RuntimeError("Frozen provider-attempt budget reached")
        self.count += 1
        attempt = f"provider-{self.count:04d}"
        self.event(event="provider_reserved", attempt=attempt, case_id=self.case_id)
        return attempt

    def response(self, attempt, status, data, elapsed):
        if attempt is None:
            return
        name = attempt + ".json"
        self.store(self.directory / name, data)
        self.event(
            event="provider_response",
            attempt=attempt,
            case_id=self.case_id,
            http_status=status,
            sha256=hashlib.sha256(data).hexdigest(),
            bytes=len(data),
            wall_seconds=round(elapsed, 6),
            artifact=name,
        )

    def failure(self, attempt, exc):
        if attempt:
            self.event(
                event="provider_failure",
                attempt=attempt,
                case_id=self.case_id,
                exception_type=type(exc).__name__,
            )

    def close(self):
        self.journal.close()


class CountedHttpx(httpx.BaseTransport):
    def __init__(self, budget, inner=None):
        self.budget = budget
        self.inner = inner or httpx.HTTPTransport(retries=0, trust_env=False)

    def handle_request(self, request):
        attempt = self.budget.reserve(str(request.url), request.method)
        timeout = self.budget.remaining()
        request.extensions["timeout"] = dict.fromkeys(
            ("connect", "read", "write", "pool"), timeout
        )
        started = time.monotonic()
        try:
            response = self.inner.handle_request(request)
            # Bound storage and transport read before decoding untrusted JSON.
            body = bytearray()
            try:
                for chunk in response.iter_bytes():
                    if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                        raise RuntimeError("Provider response exceeds frozen limit")
                    body.extend(chunk)
            finally:
                response.close()
            self.budget.response(
                attempt, response.status_code, bytes(body), time.monotonic() - started
            )
            return httpx.Response(
                response.status_code,
                headers=response.headers,
                content=bytes(body),
                request=request,
            )
        except Exception as exc:
            self.budget.failure(attempt, exc)
            raise

    def close(self):
        self.inner.close()


def counted_session_class(budget, base=requests.Session):
    class CountedSession(base):
        def __init__(self):
            super().__init__()
            self.trust_env = False
            self.mount(HOST, requests.adapters.HTTPAdapter(max_retries=0))

        def send(self, request, **kwargs):
            attempt = budget.reserve(request.url, request.method)
            kwargs.update(
                timeout=budget.remaining(),
                allow_redirects=False,
                proxies={},
                stream=True,
            )
            started = time.monotonic()
            try:
                response = super().send(request, **kwargs)
                body = bytearray()
                try:
                    for chunk in response.iter_content(chunk_size=8192):
                        if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                            raise RuntimeError("Provider response exceeds frozen limit")
                        body.extend(chunk)
                finally:
                    response.close()
                response._content = bytes(body)
                response._content_consumed = True
                budget.response(
                    attempt,
                    response.status_code,
                    bytes(body),
                    time.monotonic() - started,
                )
                return response
            except Exception as exc:
                budget.failure(attempt, exc)
                raise

    return CountedSession
