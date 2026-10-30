"""Operator-owned knowledge metadata; requests can only opt in, never grant scope."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date
from typing import Annotated, Literal

from pydantic import Field, StrictBool, model_validator

from app.retrieval.contracts import Authority, Contract, Workflow

Label = Annotated[str, Field(min_length=1, max_length=128)]
Labels = Annotated[frozenset[Label], Field(max_length=16)]


class KnowledgeGrants(Contract):
    access_scopes: Labels = frozenset()
    policy_scopes: Labels = frozenset()
    applicability: Labels = frozenset()


class WorkspaceConfig(Contract):
    format: Literal["local-knowledge-workspace-v1"] = "local-knowledge-workspace-v1"
    workflows: dict[Workflow, KnowledgeGrants] = Field(
        default_factory=dict, max_length=2
    )

    @model_validator(mode="after")
    def active_workflows_only(self):
        if not set(self.workflows) <= {Workflow.SOC, Workflow.AI_RISK}:
            raise ValueError("Only existing active workflows can use the bridge")
        return self


class ReviewedMetadata(Contract):
    workflows: frozenset[Workflow] = Field(min_length=1, max_length=4)
    source_type: Label
    source_family: Label
    owner: Label
    sensitivity: Label = "unspecified"
    authority: Authority = Authority.UNVERIFIED
    policy_scope: Label | None = None
    required_scopes: Labels = frozenset()
    applicability: Labels = frozenset()
    tags: tuple[Label, ...] = Field(default=(), max_length=16)
    effective_date: date | None = None
    expiration_date: date | None = None
    status: Literal["current", "inactive", "failed"] = "current"
    synthetic: StrictBool = False


class DocumentReview(Contract):
    source_path: str = Field(min_length=1, max_length=128)
    document_id: str = Field(pattern=r"^doc_[a-f0-9]{12}$")
    document_version_id: str = Field(pattern=r"^doc_[a-f0-9]{12}_v_[a-f0-9]{12}$")
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    approved: StrictBool = False
    metadata: ReviewedMetadata


class WorkspaceReviews(Contract):
    format: Literal["local-knowledge-reviews-v1"] = "local-knowledge-reviews-v1"
    documents: tuple[DocumentReview, ...] = Field(default=(), max_length=32)


class KnowledgeCoverage(Contract):
    status: Literal["experimental"] = "experimental"
    registered_documents: int = Field(ge=0, le=32)
    approved_documents: int = Field(ge=0, le=32)
    eligible_chunks: int = Field(ge=0, le=256)
    selected_chunks: int = Field(ge=0, le=100)
    eligible_evidence_ids: tuple[str, ...] = Field(max_length=256)
    selected_evidence_ids: tuple[str, ...] = Field(max_length=100)
    omitted_eligible_chunks: int = Field(ge=0, le=256)
    support_status: Literal["unassessed"] = "unassessed"
    warnings: tuple[str, ...]


_ENABLED: ContextVar[bool] = ContextVar("local_knowledge_opt_in", default=False)


def knowledge_enabled() -> bool:
    return _ENABLED.get()


@contextmanager
def local_knowledge_request(enabled: bool) -> Iterator[None]:
    token = _ENABLED.set(enabled)
    try:
        yield
    finally:
        _ENABLED.reset(token)
