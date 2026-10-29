"""Reuse curated cards and existing loader/chunker/registry; no ingestion rewrite."""

import hashlib
import json
from pathlib import Path

from app.chunker import DocumentChunk, chunk_documents
from app.document_loader import load_documents
from app.reference_loader import load_references
from app.retrieval.contracts import Authority, EvidenceRecord, Workflow
from app.retrieval.filtering import registry_version_gate, unique_records

LEGACY_WORKFLOWS = {"soc_alert": Workflow.SOC, "governance": Workflow.AI_RISK}


def card_record(card: dict, workflows: frozenset[Workflow]) -> EvidenceRecord:
    digest = hashlib.sha256(json.dumps(card, sort_keys=True).encode()).hexdigest()
    return EvidenceRecord(
        evidence_id=card["source_id"],
        source_id=card["source_id"],
        title=card["title"],
        content=card["content"],
        source_type=card["reference_type"],
        source_family=card["framework"],
        tags=tuple(card.get("tags", [])),
        workflows=workflows,
        content_hash=digest,
        authority=Authority.LOCAL
        if card["framework"].startswith("Local")
        else Authority.EXTERNAL,
    )


def load_curated_records(mode: str | None = None) -> tuple[EvidenceRecord, ...]:
    """Preserve per-workflow card order for legacy score ties.

    Existing local checklists are shared only across the two released workflows;
    future workflows require explicit reviewed metadata before they consume cards.
    """
    cards: dict[str, dict] = {}
    scopes: dict[str, set[Workflow]] = {}
    for name, workflow in LEGACY_WORKFLOWS.items():
        for card in load_references(name):
            source_id = card["source_id"]
            if source_id in cards and cards[source_id] != card:
                raise ValueError(f"Conflicting curated source: {source_id}")
            cards[source_id] = card
            scopes.setdefault(source_id, set()).add(workflow)
    ordered = load_references(mode) if mode else list(cards.values())
    return unique_records(
        card_record(card, frozenset(scopes[card["source_id"]])) for card in ordered
    )


def chunk_record(chunk: DocumentChunk, metadata: dict) -> EvidenceRecord:
    """Trusted sidecar metadata may supply scope/authority, never chunk text."""
    reserved = {
        "evidence_id",
        "source_id",
        "document_id",
        "document_version_id",
        "chunk_id",
        "content_hash",
        "chunk_hash",
        "title",
        "content",
        "source_path",
    }
    if reserved & metadata.keys():
        raise ValueError("Sidecar cannot override chunk identity/content provenance")
    return EvidenceRecord(
        evidence_id=chunk.chunk_id,
        source_id=chunk.document_id,
        document_id=chunk.document_id,
        document_version_id=chunk.document_version_id,
        chunk_id=chunk.chunk_id,
        content_hash=chunk.content_hash,
        chunk_hash=hashlib.sha256(chunk.text.encode()).hexdigest(),
        source_path=chunk.source_path,
        title=chunk.title,
        content=chunk.text,
        **metadata,
    )


def load_registered_records(
    raw_docs: Path | str,
    registry_path: Path | str,
    metadata_by_document: dict[str, dict],
) -> tuple[EvidenceRecord, ...]:
    """Re-extract current registered files. Missing reviewed metadata is an error.

    The registry stores identities, not chunk payloads. Reuse its loader/chunker
    and admit only exact registered current content. No registry writes occur.
    """
    gate = registry_version_gate(registry_path)
    records = []
    for chunk in chunk_documents(load_documents(raw_docs)):
        if chunk.document_id not in metadata_by_document:
            raise ValueError(f"Missing trusted retrieval metadata: {chunk.document_id}")
        record = chunk_record(chunk, metadata_by_document[chunk.document_id])
        if gate(record):
            records.append(record)
    return unique_records(records)
