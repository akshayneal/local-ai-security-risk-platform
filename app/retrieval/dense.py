"""Exact local cosine search, with no vector database dependency."""

from collections.abc import Iterable

from app.retrieval.contracts import (
    EvidenceRecord,
    RetrievalError,
    RetrievalQuery,
    RetrievedEvidence,
)
from app.retrieval.embeddings import EmbeddingProvider, normalized
from app.retrieval.filtering import VersionGate, filter_records, unique_records
from app.retrieval.storage import fingerprint


def document_text(record: EvidenceRecord) -> str:
    return (
        f"{record.source_id}\n{record.title}\n{' '.join(record.tags)}\n{record.content}"
    )


class DenseRetriever:
    def __init__(
        self,
        records: Iterable[EvidenceRecord],
        provider: EmbeddingProvider,
        version_gate: VersionGate | None = None,
    ) -> None:
        self.records = unique_records(records)
        self.corpus_sha256 = fingerprint(self.records)
        self.provider = provider
        self.version_gate = version_gate
        self.vectors: dict[str, list[float]] = {}
        self.dimensions: int | None = None

    def search(self, request: RetrievalQuery) -> list[RetrievedEvidence]:
        records = filter_records(self.records, request, self.version_gate)
        if not records:
            return []
        # Only authorized evidence reaches even the embedding provider. Cache is
        # internal; a future hosted index must preserve this prefilter property.
        missing = [
            record for record in records if record.evidence_id not in self.vectors
        ]
        if missing:
            vectors = self.provider.embed_documents(
                [document_text(record) for record in missing]
            )
            if len(vectors) != len(missing):
                raise RetrievalError("Embedding provider returned wrong document count")
            staged = {}
            dimensions = self.dimensions
            for record, vector in zip(missing, vectors, strict=True):
                staged[record.evidence_id] = normalized(vector, dimensions)
                dimensions = len(vector)
            self.vectors.update(staged)
            self.dimensions = dimensions
        query_vector = normalized(
            self.provider.embed_query(request.text), self.dimensions
        )
        scored = [
            (
                sum(
                    a * b
                    for a, b in zip(
                        self.vectors[record.evidence_id], query_vector, strict=True
                    )
                ),
                ordinal,
                record,
            )
            for ordinal, record in enumerate(records)
        ]
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [
            RetrievedEvidence(record=record, score=score, retriever="dense", rank=rank)
            for rank, (score, _, record) in enumerate(scored[: request.top_k], 1)
        ]
