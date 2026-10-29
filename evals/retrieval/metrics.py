"""Deterministic ranking metrics with explicit denominator and violation counts."""

import math
from collections import Counter

from app.retrieval.contracts import EvidenceRecord, RetrievalQuery


def ranking_metrics(
    returned: list[str], relevance: dict[str, int], required: list[str], k: int = 5
) -> dict:
    if k < 1 or len(returned) > k:
        raise ValueError("Returned results must fit positive K")
    if len(returned) != len(set(returned)):
        raise ValueError("Duplicate retrieval results cannot be scored")
    relevant = {key for key, grade in relevance.items() if grade > 0}
    found = set(returned)
    first = next(
        (rank for rank, key in enumerate(returned, 1) if key in relevant), None
    )
    dcg = sum(
        (2 ** relevance.get(key, 0) - 1) / math.log2(rank + 1)
        for rank, key in enumerate(returned, 1)
    )
    ideal = sorted(relevance.values(), reverse=True)[:k]
    ideal_dcg = sum(
        (2**grade - 1) / math.log2(rank + 1) for rank, grade in enumerate(ideal, 1)
    )
    return {
        "recall_at_k": len(found & relevant) / len(relevant) if relevant else None,
        "required_recall_at_k": len(found & set(required)) / len(required)
        if required
        else None,
        "mrr": 1 / first if first else 0.0,
        "ndcg_at_k": dcg / ideal_dcg if ideal_dcg else None,
    }


def policy_violations(
    records: list[EvidenceRecord], query: RetrievalQuery, forbidden: list[str]
) -> dict:
    counts = Counter(
        {
            key: 0
            for key in (
                "access",
                "stale_version",
                "workflow",
                "authority_scope",
                "applicability",
                "validity",
                "source_type",
                "forbidden_judgment",
            )
        }
    )
    for record in records:
        counts["access"] += not record.required_scopes <= query.access_scopes
        counts["stale_version"] += (
            record.status == "failed"
            or (not query.include_inactive and record.status != "current")
            or bool(
                query.version_ids
                and record.document_version_id not in query.version_ids
            )
        )
        counts["workflow"] += query.workflow not in record.workflows
        counts["authority_scope"] += bool(
            (query.authorities and record.authority not in query.authorities)
            or (record.policy_scope and record.policy_scope not in query.policy_scopes)
        )
        counts["applicability"] += not query.applicability <= record.applicability
        counts["validity"] += bool(
            (record.effective_date and query.as_of < record.effective_date)
            or (record.expiration_date and query.as_of >= record.expiration_date)
        )
        counts["source_type"] += bool(
            query.source_types and record.source_type not in query.source_types
        )
        counts["forbidden_judgment"] += record.evidence_id in forbidden
    return dict(counts)
