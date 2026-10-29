"""Backend-independent contracts; metadata is supplied by a trusted importer."""

from datetime import date
from enum import StrEnum
from typing import Protocol, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Workflow(StrEnum):
    SOC = "soc_investigation"
    SOC_POLICY = "soc_policy_governance"
    AI_SECURITY = "ai_security_assessment"
    AI_RISK = "ai_system_risk"


class Authority(StrEnum):
    EXTERNAL = "external_framework_guidance"
    LOCAL = "local_reference_guidance"
    POLICY = "organizational_policy"
    UNVERIFIED = "unverified_material"


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RetrievalQuery(Contract):
    text: str = Field(min_length=1, max_length=20000)
    workflow: Workflow
    top_k: int = Field(default=5, ge=1, le=100)
    source_types: frozenset[str] = frozenset()
    authorities: frozenset[Authority] = frozenset()
    applicability: frozenset[str] = frozenset()
    access_scopes: frozenset[str] = frozenset()
    policy_scopes: frozenset[str] = frozenset()
    as_of: date = Field(default_factory=date.today)
    include_inactive: bool = False
    version_ids: frozenset[str] = frozenset()

    @model_validator(mode="after")
    def nonblank_query(self) -> Self:
        if not self.text.strip():
            raise ValueError("query must contain nonblank text")
        return self


class EvidenceRecord(Contract):
    evidence_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    source_family: str = Field(min_length=1)
    workflows: frozenset[Workflow] = Field(min_length=1)
    tags: tuple[str, ...] = ()
    document_id: str | None = None
    document_version_id: str | None = None
    chunk_id: str | None = None
    content_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    chunk_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    source_path: str | None = None
    authority: Authority = Authority.UNVERIFIED
    policy_scope: str | None = None
    owner: str | None = None
    required_scopes: frozenset[str] = frozenset()
    sensitivity: str = "unspecified"
    applicability: frozenset[str] = frozenset()
    effective_date: date | None = None
    expiration_date: date | None = None
    status: str = Field(default="current", pattern=r"^(current|inactive|failed)$")
    synthetic: bool = False

    @model_validator(mode="after")
    def consistent_metadata(self) -> Self:
        if self.authority == Authority.POLICY and not self.policy_scope:
            raise ValueError("organizational policies require an explicit policy_scope")
        if (
            self.effective_date
            and self.expiration_date
            and self.expiration_date <= self.effective_date
        ):
            raise ValueError("expiration must follow effective date")
        if bool(self.document_id) != bool(self.document_version_id):
            raise ValueError(
                "document and version identities must be supplied together"
            )
        if self.chunk_id and not self.document_version_id:
            raise ValueError("chunks require document-version provenance")
        return self

    def legacy_card(self) -> dict:
        """Lossless ranking fields for the existing keyword/tag algorithm."""
        return {
            "source_id": self.source_id,
            "title": self.title,
            "framework": self.source_family,
            "reference_type": self.source_type,
            "tags": list(self.tags),
            "content": self.content,
        }


class RetrievedEvidence(Contract):
    record: EvidenceRecord
    score: float = Field(allow_inf_nan=False)
    retriever: str
    rank: int = Field(ge=1)
    component_ranks: dict[str, int] = Field(default_factory=dict)


class Retriever(Protocol):
    def search(self, request: RetrievalQuery) -> list[RetrievedEvidence]: ...


class RetrievalError(RuntimeError):
    """Predictable index/provider failure; never relax filters on failure."""
