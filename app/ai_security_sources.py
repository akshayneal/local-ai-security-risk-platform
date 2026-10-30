"""Reviewed, versioned local author guidance; no organizational-document grants."""

import hashlib
import json
from pathlib import Path

from pydantic import Field

from app.ai_security_contracts import Category, Text
from app.retrieval.contracts import (
    Authority,
    Contract,
    EvidenceRecord,
    RetrievalQuery,
    RetrievedEvidence,
    Workflow,
)
from app.retrieval.filtering import filter_records

SOURCE_PATH = (
    Path(__file__).resolve().parents[1] / "reference_material/ai_security_v1/cards.json"
)
SOURCE_SHA256 = "d3b4a40d66f6f868f64909e93b0c0ad0641f33e3834af22295feab0f48d25e7f"
VERSION = "local-ai-security-guidance-v1"


class AiSecurityBoundaryError(RuntimeError):
    """Fixed message only; never expose submitted designs or model output."""

    def __init__(self):
        super().__init__(
            "AI Security assessment withheld: input, source or output boundary unavailable."
        )


class GuidanceCard(Contract):
    source_id: str = Field(max_length=80)
    category: Category
    title: str = Field(min_length=1, max_length=128)
    content: Text


def load_guidance() -> tuple[tuple[RetrievedEvidence, ...], dict[str, Category]]:
    try:
        if (
            SOURCE_PATH.is_symlink()
            or not SOURCE_PATH.is_file()
            or SOURCE_PATH.stat().st_size > 12_000
        ):
            raise ValueError("Guidance unavailable")
        raw = SOURCE_PATH.read_bytes()
        if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
            raise ValueError("Guidance identity mismatch")
        data = json.loads(raw)
        if (
            set(data) != {"version", "authority", "workflow", "cards"}
            or data["version"] != VERSION
            or data["authority"] != Authority.LOCAL
            or data["workflow"] != Workflow.AI_SECURITY
        ):
            raise ValueError("Guidance metadata mismatch")
        cards = tuple(GuidanceCard.model_validate(c) for c in data["cards"])
        categories = {c.source_id: c.category for c in cards}
        if (
            len(cards) != 6
            or len(categories) != 6
            or len({c.category for c in cards}) != 6
        ):
            raise ValueError("Guidance inventory mismatch")
        records = []
        for card in cards:
            if card.source_id != "AISEC-V1-" + card.category.replace("_", "-").upper():
                raise ValueError("Guidance category identity mismatch")
            records.append(
                EvidenceRecord(
                    evidence_id=card.source_id,
                    source_id=card.source_id,
                    title=card.title,
                    content=card.content,
                    source_type="technical_guidance",
                    source_family=VERSION,
                    workflows=frozenset({Workflow.AI_SECURITY}),
                    authority=Authority.LOCAL,
                    content_hash=hashlib.sha256(card.content.encode()).hexdigest(),
                )
            )
        eligible = filter_records(
            records,
            RetrievalQuery(
                text="AI technical architecture", workflow=Workflow.AI_SECURITY, top_k=6
            ),
        )
        if len(eligible) != 6:
            raise ValueError("Guidance eligibility failed")
        return tuple(
            RetrievedEvidence(
                record=r, score=0, rank=i, retriever="reviewed-fixed-guidance"
            )
            for i, r in enumerate(eligible, 1)
        ), categories
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise AiSecurityBoundaryError() from exc
