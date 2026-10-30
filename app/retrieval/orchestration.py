"""Legacy by default, optional lexical context, isolated best-effort shadow."""

import hashlib
import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.evidence_inspector import capture_selection
from app.knowledge_contracts import KnowledgeCoverage, knowledge_enabled
from app.retrieval.contracts import RetrievalError, RetrievalQuery, RetrievedEvidence
from app.retrieval.filtering import VersionGate
from app.retrieval.importers import LEGACY_WORKFLOWS, load_curated_records
from app.retrieval.lexical import LexicalRetriever
from app.retrieval.serialization import evidence_cards, serialize_evidence


@dataclass
class AnalysisReferences:
    cards: list[dict]
    evidence: list[RetrievedEvidence] | None = None
    context: str | None = None
    knowledge: KnowledgeCoverage | None = None
    eligibility: RetrievalQuery | None = None
    version_gate: VersionGate | None = None


def _observed(
    mode: str, query: str, selection: AnalysisReferences
) -> AnalysisReferences:
    capture_selection(mode, query, selection)
    return selection


def lexical_search(mode: str, query: str, limit: int) -> list[RetrievedEvidence]:
    # Curated public cards only. Never accept access/policy grants from request text.
    # Bound only the ranking query; never truncate the actual model evidence/request.
    request = RetrievalQuery(
        text=query[:20_000], workflow=LEGACY_WORKFLOWS[mode], top_k=limit
    )
    return LexicalRetriever(load_curated_records(mode)).search(request)


def write_shadow(record: dict) -> None:
    path = Path("logs/retrieval_shadow.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, sort_keys=True) + "\n")


def retrieve_for_analysis(
    mode: str,
    query: str,
    limit: int,
    *,
    legacy_loader: Callable,
) -> AnalysisReferences:
    backend = os.getenv("RETRIEVAL_BACKEND", "legacy")
    if backend not in {"legacy", "lexical"}:
        raise RetrievalError("Unsupported configured retrieval backend")
    if knowledge_enabled():
        from app.knowledge_workspace import (
            KNOWLEDGE_ERROR,
            MAX_CONTEXT_CHARACTERS,
            knowledge_for_analysis,
            protected_evidence_context,
        )

        local_hits, coverage, eligibility, gate = knowledge_for_analysis(
            mode, query, limit
        )
        # Curated cards remain guidance with their original categorical authority.
        # Neither set competes away the other; both are explicitly bounded.
        hits = local_hits + lexical_search(mode, query, limit)
        context = "\n".join(coverage.warnings) + "\n" + protected_evidence_context(hits)
        if len(context) > MAX_CONTEXT_CHARACTERS:
            raise RetrievalError(KNOWLEDGE_ERROR)
        return _observed(
            mode,
            query,
            AnalysisReferences(
                evidence_cards(hits),
                hits,
                context,
                coverage,
                eligibility,
                gate,
            ),
        )
    if backend == "lexical":
        hits = lexical_search(mode, query, limit)  # Errors propagate, no fallback.
        return _observed(
            mode,
            query,
            AnalysisReferences(evidence_cards(hits), hits, serialize_evidence(hits)),
        )
    started = time.perf_counter()
    cards = legacy_loader(mode=mode, query=query, limit=limit)
    legacy_ms = (time.perf_counter() - started) * 1000
    if os.getenv("RETRIEVAL_SHADOW_BACKEND"):
        # Every shadow operation, including logging/configuration, is isolated.
        started = time.perf_counter()
        record = {
            "workflow": LEGACY_WORKFLOWS[mode].value,
            "created_utc": datetime.now(UTC).isoformat(),
            "query_sha256": hashlib.sha256(query.encode()).hexdigest(),
            "legacy_ids": [c["source_id"] for c in cards],
            "legacy_ms": legacy_ms,
            "lexical_ids": [],
            "error": None,
        }
        try:
            if os.environ["RETRIEVAL_SHADOW_BACKEND"] != "lexical":
                raise RetrievalError("Unsupported shadow backend")
            hits = lexical_search(mode, query, limit)
            record["lexical_ids"] = [h.record.evidence_id for h in hits]
        except Exception:  # noqa: BLE001 -- shadow isolation includes unexpected backend faults.
            record["error"] = "shadow_retrieval_failed"
        record["lexical_ms"] = (time.perf_counter() - started) * 1000
        record["overlap"] = sorted(
            set(record["legacy_ids"]) & set(record["lexical_ids"])
        )
        try:
            write_shadow(record)
        except Exception:  # noqa: BLE001
            return _observed(
                mode, query, AnalysisReferences(cards)
            )  # Logging cannot influence generation.
    return _observed(mode, query, AnalysisReferences(cards))
