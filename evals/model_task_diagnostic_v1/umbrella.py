"""Experimental append-only accounting across the two isolated Sprint 10 tracks.

Reservations are conservative: a failure between local and umbrella persistence
must stop sending. A reservation is not evidence that a provider completed work.
"""

import json
import os
import re
import threading
from pathlib import Path

CAPS = {"lab": 16, "acceptance": 12}
MAX_ATTEMPTS = 28
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
    """An exclusive file lock, durable reservations, and disjoint 16/12 caps."""

    def __init__(self, root: Path, *, lab_journal: Path, acceptance_journal: Path):
        root = Path(root).absolute()
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
            "format": "model-task-diagnostic-v1-campaign",
            "caps": CAPS,
            "aggregate_cap": MAX_ATTEMPTS,
            "journals": journals,
            "reservation_is_not_completion": True,
        }
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
        try:
            manifest = root / "manifest.json"
            existing = manifest.exists()
            if manifest.exists():
                if (
                    manifest.stat().st_size > 4096
                    or json.loads(manifest.read_bytes()) != self.identity
                ):
                    raise CampaignStop("Campaign identity changed")
            else:
                with manifest.open("xb") as output:
                    output.write(_encoded(self.identity))
                    output.flush()
                    os.fsync(output.fileno())
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
            self.pending = None
        else:
            raise CampaignStop("Unrecognized campaign record")

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
        return {
            "counts": dict(self.counts),
            "reserved": sum(self.counts.values()),
            "pending": self.pending,
            "blocked": self.blocked,
            "remaining": {name: CAPS[name] - self.counts[name] for name in CAPS},
        }

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
