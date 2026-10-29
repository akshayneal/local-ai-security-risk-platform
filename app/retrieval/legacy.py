"""Control backend: exact existing token overlap/tag bonus and stable tie order."""

from collections.abc import Iterable

from app.reference_loader import normalize_text, score_reference
from app.retrieval.contracts import EvidenceRecord, RetrievalQuery, RetrievedEvidence
from app.retrieval.filtering import VersionGate, filter_records, unique_records


class LegacyRetriever:
    def __init__(
        self, records: Iterable[EvidenceRecord], version_gate: VersionGate | None = None
    ):
        self.records = unique_records(records)
        self.version_gate = version_gate

    def search(self, request: RetrievalQuery) -> list[RetrievedEvidence]:
        records = filter_records(self.records, request, self.version_gate)
        tokens = set(normalize_text(request.text))
        scored = [
            (score_reference(tokens, record.legacy_card()), record)
            for record in records
        ]
        scored = sorted(
            (item for item in scored if item[0] > 0), key=lambda item: -item[0]
        )
        return [
            RetrievedEvidence(record=record, score=score, retriever="legacy", rank=rank)
            for rank, (score, record) in enumerate(scored[: request.top_k], 1)
        ]
