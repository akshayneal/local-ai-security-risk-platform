"""Bounded local workspace bridge. No request-owned paths, grants or cached trust."""

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from app.chunker import chunk_documents
from app.document_identity import build_document_id
from app.document_limits import DocumentLimits
from app.document_loader import SUPPORTED_DOCUMENT_EXTENSIONS, load_document
from app.knowledge_contracts import (
    DocumentReview,
    KnowledgeCoverage,
    ReviewedMetadata,
    WorkspaceConfig,
    WorkspaceReviews,
)
from app.retrieval.contracts import (
    EvidenceRecord,
    RetrievalError,
    RetrievalQuery,
    Workflow,
)
from app.retrieval.filtering import filter_records, registry_version_gate
from app.retrieval.importers import LEGACY_WORKFLOWS, load_registered_records
from app.retrieval.lexical import LexicalRetriever
from app.retrieval.serialization import serialize_evidence

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT / "knowledge_base/workspaces"
DEMO_ROOT = ROOT / "sample_data/knowledge_demo_v1"
LIMITS = DocumentLimits(
    max_file_size_bytes=1_000_000,
    max_pdf_pages=16,
    max_extracted_characters=32_000,
    max_chunks_per_document=48,
)
MAX_CORPUS_BYTES = 4_000_000
MAX_CORPUS_CHARACTERS = 128_000
MAX_CONTEXT_CHARACTERS = 24_000
MAX_METADATA_BYTES = 200_000
MAX_QUERY_CHARACTERS = 20_000
KNOWLEDGE_ERROR = "Reviewed local knowledge unavailable or invalid; analysis withheld. Check the operator workspace with the local CLI."
CONTEXT_WARNING = (
    "Local retrieval is a bounded candidate selection, not complete evidence or verified support. "
    "Related hits cannot answer missing facts. State insufficient evidence when needed; "
    "a policy requirement does not prove implementation or granted approval. "
    "Preserve conflicts and require human review before action."
)


def _no_link(path: Path) -> None:
    if path.is_symlink() or path.is_junction():
        raise ValueError("Linked workspace paths are not supported")


def workspace_path(name: str) -> Path:
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", name) or name in {
        "con",
        "prn",
        "aux",
        "nul",
        *(f"com{i}" for i in range(1, 10)),
        *(f"lpt{i}" for i in range(1, 10)),
    }:
        raise ValueError("Use a bounded simple workspace name")
    path = WORKSPACE_ROOT / name
    for item in (WORKSPACE_ROOT.parent, WORKSPACE_ROOT, path):
        _no_link(item)
    if path.resolve().parent != WORKSPACE_ROOT.resolve():
        raise ValueError("Workspace must remain in the designated directory")
    return path


def workspace_file(workspace: Path, name: str) -> Path:
    path = workspace / name
    _no_link(path)
    if path.resolve().parent != workspace.resolve():
        raise ValueError("Workspace file escaped its root")
    return path


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate metadata key")
        result[key] = value
    return result


def read_json(path: Path):
    _no_link(path)
    if not path.is_file() or path.stat().st_size > MAX_METADATA_BYTES:
        raise ValueError("Workspace metadata missing or oversized")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs)


def raw_documents(workspace: Path):
    """Flat, explicit workspace only; cap enumeration before existing recursive loader."""
    raw = workspace_file(workspace, "documents")
    documents = []
    total_bytes = 0
    with os.scandir(raw) as entries:
        for entry in entries:
            if len(documents) >= 32:
                raise ValueError("Workspace document count exceeds 32")
            path = Path(entry.path)
            _no_link(path)
            if (
                not entry.is_file(follow_symlinks=False)
                or path.suffix.lower() not in SUPPORTED_DOCUMENT_EXTENSIONS
            ):
                raise ValueError("Only flat supported document files are admitted")
            if path.stat().st_nlink > 1:
                raise ValueError("Hard-linked documents are not supported")
            total_bytes += path.stat().st_size
            if total_bytes > MAX_CORPUS_BYTES:
                raise ValueError("Workspace byte budget exceeded")
            documents.append(path)
    loaded = [load_document(p, root_dir=raw, limits=LIMITS) for p in sorted(documents)]
    if sum(len(d.text) for d in loaded) > MAX_CORPUS_CHARACTERS:
        raise ValueError("Workspace extraction budget exceeded")
    if len(chunk_documents(loaded, limits=LIMITS)) > 256:
        raise ValueError("Workspace chunk budget exceeded")
    return loaded


def initialize_workspace(name: str, *, demo: bool = False) -> dict:
    """Explicit CLI operation only; exclusive creation never overwrites a workspace."""
    path = workspace_path(name)
    path.mkdir(parents=True, exist_ok=False)
    (path / "documents").mkdir()
    config = WorkspaceConfig()
    if demo:
        config = WorkspaceConfig.model_validate(read_json(DEMO_ROOT / "workspace.json"))
        for source in sorted((DEMO_ROOT / "documents").iterdir()):
            with (path / "documents" / source.name).open("xb") as target:
                target.write(source.read_bytes())
        with (path / "reviewed.json").open("xb") as target:
            target.write((DEMO_ROOT / "reviewed.json").read_bytes())
    with (path / "workspace.json").open("x", encoding="utf-8") as target:
        target.write(config.model_dump_json(indent=2))
    return {"status": "initialized", "synthetic_demo": demo, "registered": False}


def register_workspace(name: str) -> dict:
    """Explicit CLI registration; never approves or overwrites existing reviews."""
    from scripts.register_documents import register_raw_documents

    path = workspace_path(name)
    documents = raw_documents(path)
    reviews_path = workspace_file(path, "reviewed.json")
    registry = workspace_file(path, "registry.db")
    if registry.exists() and registry.stat().st_size > 4_000_000:
        raise ValueError("Registry exceeds workspace budget")
    results = register_raw_documents(path / "documents", registry)
    if not reviews_path.exists():
        drafts = WorkspaceReviews(
            documents=tuple(
                DocumentReview(
                    source_path=d.source_path,
                    document_id=d.document_id,
                    document_version_id=d.document_version_id,
                    content_hash=d.content_hash,
                    metadata=ReviewedMetadata(
                        workflows=frozenset({Workflow.SOC, Workflow.AI_RISK}),
                        source_type="reference",
                        source_family="Local unverified material",
                        owner="unspecified",
                    ),
                )
                for d in documents
            )
        )
        with reviews_path.open("x", encoding="utf-8") as target:
            target.write(drafts.model_dump_json(indent=2))
    return {
        "status": "registered",
        "documents": len(results),
        "reviews_automatically_approved": False,
    }


@dataclass(frozen=True)
class KnowledgeWorkspace:
    path: Path
    config: WorkspaceConfig
    reviews: WorkspaceReviews
    records: tuple[EvidenceRecord, ...]


def load_workspace(name: str) -> KnowledgeWorkspace:
    """Read exact reviewed versions anew; no persisted evidence/trust cache."""
    try:
        path = workspace_path(name)
        config = WorkspaceConfig.model_validate(
            read_json(workspace_file(path, "workspace.json"))
        )
        reviews = WorkspaceReviews.model_validate(
            read_json(workspace_file(path, "reviewed.json"))
        )
        documents = raw_documents(path)
        by_path = {r.source_path: r for r in reviews.documents}
        if len(by_path) != len(reviews.documents) or len(
            {r.document_id for r in reviews.documents}
        ) != len(by_path):
            raise ValueError("Duplicate reviewed identity")
        if set(by_path) != {d.source_path for d in documents}:
            raise ValueError("Document review inventory mismatch")
        metadata = {}
        for document in documents:
            review = by_path[document.source_path]
            if (
                review.document_id != build_document_id(document.source_path)
                or review.document_version_id != document.document_version_id
                or review.content_hash != document.content_hash
            ):
                raise ValueError("Changed documents require a new exact-version review")
            metadata[review.document_id] = review.metadata.model_dump(mode="python")
        registry = workspace_file(path, "registry.db")
        if not registry.is_file() or registry.stat().st_size > 4_000_000:
            raise ValueError("Registry missing or oversized")
        imported = load_registered_records(path / "documents", registry, metadata)
        expected = chunk_documents(documents, limits=LIMITS)
        if {r.evidence_id for r in imported} != {c.chunk_id for c in expected}:
            raise ValueError("Unregistered or stale document versions")
        approved = {r.document_id for r in reviews.documents if r.approved}
        return KnowledgeWorkspace(
            path,
            config,
            reviews,
            tuple(r for r in imported if r.document_id in approved),
        )
    except (ValueError, OSError, RuntimeError, RecursionError) as exc:
        raise RetrievalError(KNOWLEDGE_ERROR) from exc


def configured_workspace() -> KnowledgeWorkspace:
    name = os.getenv("LOCAL_KNOWLEDGE_WORKSPACE", "")
    if not name:
        raise RetrievalError(KNOWLEDGE_ERROR)
    return load_workspace(name)


def workspace_query(
    workspace: KnowledgeWorkspace,
    workflow: Workflow,
    text: str,
    *,
    top_k: int = 8,
    as_of=None,
) -> RetrievalQuery:
    grants = workspace.config.workflows.get(workflow)
    if grants is None or len(text) > MAX_QUERY_CHARACTERS:
        raise RetrievalError(KNOWLEDGE_ERROR)
    return RetrievalQuery(
        text=text,
        workflow=workflow,
        top_k=top_k,
        **grants.model_dump(mode="python"),
        **({"as_of": as_of} if as_of else {}),
    )


def select_knowledge(workspace: KnowledgeWorkspace, query: RetrievalQuery):
    gate = registry_version_gate(workspace_file(workspace.path, "registry.db"))
    eligible = filter_records(workspace.records, query, gate)
    hits = LexicalRetriever(workspace.records, gate).search(query)
    if len(serialize_evidence(hits)) > MAX_CONTEXT_CHARACTERS:
        raise RetrievalError(KNOWLEDGE_ERROR)
    warnings = [CONTEXT_WARNING]
    if not hits:
        warnings.append(
            "No eligible local document matched this query; local knowledge cannot answer it."
        )
    if len(eligible) > len(hits):
        warnings.append(
            "Some eligible chunks were not selected. Required material or conflicting evidence may be omitted."
        )
    coverage = KnowledgeCoverage(
        registered_documents=len(workspace.reviews.documents),
        approved_documents=sum(r.approved for r in workspace.reviews.documents),
        eligible_chunks=len(eligible),
        selected_chunks=len(hits),
        eligible_evidence_ids=tuple(r.evidence_id for r in eligible),
        selected_evidence_ids=tuple(h.record.evidence_id for h in hits),
        omitted_eligible_chunks=len(eligible) - len(hits),
        warnings=tuple(warnings),
    )
    return hits, coverage, gate


def knowledge_for_analysis(mode: str, text: str, limit: int):
    workspace = configured_workspace()
    query = workspace_query(workspace, LEGACY_WORKFLOWS[mode], text, top_k=limit)
    hits, coverage, gate = select_knowledge(workspace, query)
    return hits, coverage, query, gate


def workspace_status() -> dict:
    if not os.getenv("LOCAL_KNOWLEDGE_WORKSPACE"):
        return {
            "status": "disabled",
            "message": "No operator workspace configured. Local knowledge is off.",
        }
    try:
        workspace = configured_workspace()
        return {
            "status": "experimental",
            "registered_documents": len(workspace.reviews.documents),
            "approved_documents": sum(r.approved for r in workspace.reviews.documents),
            "approved_chunks": len(workspace.records),
            "message": "Read-only workspace validated. Each request rechecks workflow, scope, dates and current versions. Claims remain unassessed.",
        }
    except RetrievalError:
        return {"status": "unavailable", "message": KNOWLEDGE_ERROR}
