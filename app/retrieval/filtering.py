"""Eligibility happens before ranking for every backend, including fusion."""

import sqlite3
from collections.abc import Callable, Iterable
from pathlib import Path

from app.retrieval.contracts import EvidenceRecord, RetrievalError, RetrievalQuery

VersionGate = Callable[[EvidenceRecord], bool]


def eligible(record: EvidenceRecord, query: RetrievalQuery) -> bool:
    return (
        query.workflow in record.workflows
        and record.required_scopes <= query.access_scopes
        and (not record.policy_scope or record.policy_scope in query.policy_scopes)
        and (not query.source_types or record.source_type in query.source_types)
        and (not query.authorities or record.authority in query.authorities)
        and query.applicability <= record.applicability
        and record.status != "failed"
        and (query.include_inactive or record.status == "current")
        and (not query.version_ids or record.document_version_id in query.version_ids)
        and (record.effective_date is None or record.effective_date <= query.as_of)
        and (record.expiration_date is None or query.as_of < record.expiration_date)
    )


def unique_records(records: Iterable[EvidenceRecord]) -> tuple[EvidenceRecord, ...]:
    """Collapse identical duplicates; conflicting identities fail closed."""
    unique: dict[str, EvidenceRecord] = {}
    for record in records:
        if record.evidence_id in unique and unique[record.evidence_id] != record:
            raise ValueError(f"Conflicting evidence identity: {record.evidence_id}")
        unique[record.evidence_id] = record
    return tuple(unique.values())


def filter_records(
    records: Iterable[EvidenceRecord],
    query: RetrievalQuery,
    version_gate: VersionGate | None = None,
) -> list[EvidenceRecord]:
    return [
        record
        for record in records
        if eligible(record, query) and (version_gate is None or version_gate(record))
    ]


def registry_version_gate(database_path: Path | str) -> VersionGate:
    """Recheck live registry without creating/migrating it or trusting an old index.

    Historical queries never reactivate registry versions: this gate is current-only.
    An unavailable/corrupt registry raises, rather than silently admitting evidence.
    """
    path = Path(database_path).resolve()

    def is_current(record: EvidenceRecord) -> bool:
        if record.document_id is None:
            return True
        try:
            with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as connection:
                row = connection.execute(
                    "SELECT v.content_hash, v.status FROM documents d "
                    "JOIN document_versions v ON d.current_version_id=v.document_version_id "
                    "WHERE d.document_id=? AND v.document_version_id=?",
                    (record.document_id, record.document_version_id),
                ).fetchone()
                return (
                    row is not None
                    and row[0] == record.content_hash
                    and row[1] == "chunked"
                )
        except sqlite3.Error as exc:
            raise RetrievalError(
                "Document registry unavailable; retrieval refused"
            ) from exc

    return is_current
