"""Reciprocal rank fusion of lexical/dense results over identical eligible records."""

from collections.abc import Iterable

from app.retrieval.contracts import EvidenceRecord, RetrievalQuery, RetrievedEvidence
from app.retrieval.dense import DenseRetriever
from app.retrieval.embeddings import EmbeddingProvider
from app.retrieval.filtering import VersionGate, unique_records
from app.retrieval.lexical import LexicalRetriever
from app.retrieval.storage import fingerprint


class HybridRetriever:
    def __init__(
        self,
        records: Iterable[EvidenceRecord],
        provider: EmbeddingProvider,
        version_gate: VersionGate | None = None,
        *,
        dense: DenseRetriever | None = None,
        rrf_constant: int = 60,
    ) -> None:
        if rrf_constant < 1:
            raise ValueError("RRF constant must be positive")
        self.records = unique_records(records)
        self.lexical = LexicalRetriever(self.records, version_gate)
        self.dense = dense or DenseRetriever(self.records, provider, version_gate)
        if (
            self.dense.corpus_sha256 != fingerprint(self.records)
            or self.dense.version_gate is not version_gate
        ):
            raise ValueError("Fusion components must share corpus and eligibility gate")
        self.rrf_constant = rrf_constant

    def search(self, request: RetrievalQuery) -> list[RetrievedEvidence]:
        candidates = request.model_copy(
            update={"top_k": min(100, max(20, request.top_k * 4))}
        )
        rankings = {
            "lexical": self.lexical.search(candidates),
            "dense": self.dense.search(candidates),
        }
        scores: dict[str, float] = {}
        records = {}
        ranks: dict[str, dict[str, int]] = {}
        for name, hits in rankings.items():
            for hit in hits:
                key = hit.record.evidence_id
                scores[key] = scores.get(key, 0.0) + 1 / (self.rrf_constant + hit.rank)
                records[key] = hit.record
                ranks.setdefault(key, {})[name] = hit.rank
        ordinal = {
            record.evidence_id: index for index, record in enumerate(self.records)
        }
        ordered = sorted(scores, key=lambda key: (-scores[key], ordinal[key]))
        return [
            RetrievedEvidence(
                record=records[key],
                score=scores[key],
                retriever="hybrid",
                rank=rank,
                component_ranks=ranks[key],
            )
            for rank, key in enumerate(ordered[: request.top_k], 1)
        ]
