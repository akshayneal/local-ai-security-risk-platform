"""Small, rebuildable SQLite evidence snapshot; separate from document registry."""

import hashlib
import json
import sqlite3
from collections.abc import Iterable
from contextlib import closing
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from app.retrieval.contracts import EvidenceRecord, RetrievalError
from app.retrieval.filtering import unique_records

FORMAT_VERSION = "retrieval-evidence-v1"


def canonical_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return canonical_value(value.model_dump(mode="python"))
    if isinstance(value, dict):
        return {key: canonical_value(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted(canonical_value(item) for item in value)
    if isinstance(value, (tuple, list)):
        return [canonical_value(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, date):
        return value.isoformat()
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        canonical_value(value),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def write_snapshot(path: Path | str, records: Iterable[EvidenceRecord]) -> dict:
    """Atomic transaction preserves an existing valid snapshot on failure."""
    records = unique_records(records)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS evidence (ordinal INTEGER PRIMARY KEY, payload TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS manifest (version TEXT, digest TEXT)"
            )
            connection.execute("DELETE FROM evidence")
            connection.execute("DELETE FROM manifest")
            connection.executemany(
                "INSERT INTO evidence VALUES (?, ?)",
                enumerate(canonical_json(record) for record in records),
            )
            connection.execute(
                "INSERT INTO manifest VALUES (?, ?)",
                (FORMAT_VERSION, fingerprint(records)),
            )
    except sqlite3.Error as exc:
        raise RetrievalError("Could not build evidence snapshot") from exc
    return {
        "format": FORMAT_VERSION,
        "records": len(records),
        "corpus_sha256": fingerprint(records),
        "bytes": path.stat().st_size,
    }


def read_snapshot(path: Path | str) -> tuple[EvidenceRecord, ...]:
    try:
        with closing(
            sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
        ) as connection:
            manifest = connection.execute(
                "SELECT version, digest FROM manifest"
            ).fetchall()
            if len(manifest) != 1 or manifest[0][0] != FORMAT_VERSION:
                raise RetrievalError(
                    "Evidence snapshot format is incompatible; rebuild it"
                )
            records = unique_records(
                EvidenceRecord.model_validate_json(row[0])
                for row in connection.execute(
                    "SELECT payload FROM evidence ORDER BY ordinal"
                )
            )
            if fingerprint(records) != manifest[0][1]:
                raise RetrievalError(
                    "Evidence snapshot integrity check failed; rebuild it"
                )
            return records
    except (sqlite3.Error, ValidationError, ValueError) as exc:
        raise RetrievalError(
            "Evidence snapshot unavailable or corrupt; rebuild it"
        ) from exc
