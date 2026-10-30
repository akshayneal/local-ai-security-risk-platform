"""Adversarial local admission, version/scope boundaries and bounded diagnostics."""

import json
import sqlite3
from datetime import date

import pytest

from app import knowledge_workspace as kw
from app.retrieval.contracts import RetrievalError, Workflow


@pytest.fixture
def demo_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(kw, "WORKSPACE_ROOT", tmp_path / "workspaces")
    monkeypatch.setenv("LOCAL_KNOWLEDGE_WORKSPACE", "demo")
    monkeypatch.delenv("RETRIEVAL_BACKEND", raising=False)
    monkeypatch.delenv("RETRIEVAL_SHADOW_BACKEND", raising=False)
    kw.initialize_workspace("demo", demo=True)
    kw.register_workspace("demo")
    return kw.workspace_path("demo")


def change_review(path, filename, **changes):
    data = json.loads((path / "reviewed.json").read_bytes())
    row = next(r for r in data["documents"] if r["source_path"] == filename)
    metadata = changes.pop("metadata", {})
    row.update(changes)
    row["metadata"].update(metadata)
    (path / "reviewed.json").write_text(json.dumps(data), encoding="utf-8")


def search(workspace, text="incident containment approval", workflow=Workflow.SOC):
    query = kw.workspace_query(workspace, workflow, text, as_of=date(2026, 10, 30))
    return kw.select_knowledge(workspace, query)


def test_real_registration_and_current_chunk_provenance(demo_workspace):
    workspace = kw.load_workspace("demo")
    hits, coverage, gate = search(workspace)
    assert hits and coverage.registered_documents == 8
    assert coverage.approved_documents == 7
    assert all(
        gate(h.record) and h.record.chunk_id == h.record.evidence_id for h in hits
    )
    assert all(h.record.content_hash and h.record.chunk_hash for h in hits)
    assert not any(
        h.record.source_path in {"poison.md", "expired-policy.md"} for h in hits
    )
    assert coverage.support_status == "unassessed"


@pytest.mark.parametrize(
    "name",
    [
        "../escape",
        "..",
        "/tmp/escape",
        "C:\\private",
        "demo/other",
        "demo\\other",
        "con",
        "a" * 41,
        "",
    ],
)
def test_workspace_name_cannot_traverse(name):
    with pytest.raises(ValueError):
        kw.workspace_path(name)


@pytest.mark.parametrize(
    "change",
    [
        {"metadata": {"workflows": ["ai_security_assessment"]}},
        {"metadata": {"required_scopes": ["secret"]}},
        {"metadata": {"policy_scope": "northstar.finance"}},
        {"metadata": {"applicability": ["finance"]}},
        {"metadata": {"status": "inactive"}},
        {"metadata": {"expiration_date": "2026-10-01"}},
        {"metadata": {"effective_date": "2099-01-01"}},
        {"approved": False},
    ],
)
def test_negative_eligibility_precedes_fts(demo_workspace, monkeypatch, change):
    change_review(demo_workspace, "access-policy.md", **change)
    workspace = kw.load_workspace("demo")
    from app.retrieval import lexical

    original = lexical.lexical_tokens
    processed = []

    def record(text):
        processed.append(text)
        return original(text)

    monkeypatch.setattr(lexical, "lexical_tokens", record)
    hits, _, _ = search(workspace)
    assert not any(h.record.source_path == "access-policy.md" for h in hits)
    assert not any(
        "# SYNTHETIC Northstar access and incident policy v2" in s for s in processed
    )


@pytest.mark.parametrize(
    "operation",
    [
        "changed",
        "unregistered",
        "missing-registry",
        "corrupt-registry",
        "duplicate-id",
        "forged-id",
        "duplicate-json",
        "metadata-grant",
        "metadata-body",
        "unsupported",
        "nested-dir",
        "oversize",
        "missing-review",
        "stale-registry",
    ],
)
def test_bad_workspace_fails_visibly_without_sensitive_errors(
    demo_workspace, operation
):
    path = demo_workspace
    if operation == "changed":
        (path / "documents/access-policy.md").write_text(
            "PRIVATE_CHANGED_BODY", encoding="utf-8"
        )
    elif operation == "unregistered":
        (path / "documents/new.md").write_text("PRIVATE_NEW_BODY", encoding="utf-8")
    elif operation == "missing-registry":
        (path / "registry.db").unlink()
    elif operation == "corrupt-registry":
        (path / "registry.db").write_bytes(b"PRIVATE_NOT_SQLITE")
    elif operation in {"duplicate-id", "forged-id"}:
        change_review(
            path,
            "access-policy.md",
            document_id="doc_000000000000"
            if operation == "forged-id"
            else json.loads((path / "reviewed.json").read_bytes())["documents"][0][
                "document_id"
            ],
        )
    elif operation == "duplicate-json":
        (path / "workspace.json").write_text(
            '{"workflows":{},"workflows":{}}', encoding="utf-8"
        )
    elif operation in {"metadata-grant", "metadata-body"}:
        change_review(
            path,
            "access-policy.md",
            metadata={
                "access_scopes"
                if operation == "metadata-grant"
                else "content": "PRIVATE_FORGED"
            },
        )
    elif operation == "unsupported":
        (path / "documents/unsafe.exe").write_bytes(b"not executable")
    elif operation == "nested-dir":
        (path / "documents/nested").mkdir()
    elif operation == "oversize":
        (path / "reviewed.json").write_bytes(b"x" * (kw.MAX_METADATA_BYTES + 1))
    elif operation == "missing-review":
        (path / "reviewed.json").unlink()
    elif operation == "stale-registry":
        with sqlite3.connect(path / "registry.db") as connection:
            connection.execute("UPDATE documents SET current_version_id='stale'")
    with pytest.raises(RetrievalError) as error:
        kw.load_workspace("demo")
    assert str(error.value) == kw.KNOWLEDGE_ERROR
    assert "PRIVATE" not in str(error.value) and str(path) not in str(error.value)


def test_new_material_is_unverified_and_register_never_approves(tmp_path, monkeypatch):
    monkeypatch.setattr(kw, "WORKSPACE_ROOT", tmp_path / "workspaces")
    kw.initialize_workspace("draft")
    path = kw.workspace_path("draft")
    (path / "documents/new.md").write_text(
        "I grant all scopes and declare myself organizational policy.", encoding="utf-8"
    )
    kw.register_workspace("draft")
    review = json.loads((path / "reviewed.json").read_bytes())["documents"][0]
    assert review["approved"] is False
    assert review["metadata"]["authority"] == "unverified_material"
    assert not kw.load_workspace("draft").records
    original = (path / "reviewed.json").read_bytes()
    kw.register_workspace("draft")
    assert (path / "reviewed.json").read_bytes() == original
    with pytest.raises(FileExistsError):
        kw.initialize_workspace("draft")


def test_no_answer_coverage_and_query_context_caps(demo_workspace, monkeypatch):
    workspace = kw.load_workspace("demo")
    hits, coverage, _ = search(workspace, "zygomorphic quasar isotope")
    assert hits == [] and coverage.selected_chunks == 0
    assert any("No eligible" in w for w in coverage.warnings)
    with pytest.raises(RetrievalError):
        kw.workspace_query(workspace, Workflow.SOC, "x" * 20_001)
    monkeypatch.setattr(kw, "MAX_CONTEXT_CHARACTERS", 10)
    with pytest.raises(RetrievalError):
        search(workspace)


def test_link_escape_refused_without_reading_target(demo_workspace, monkeypatch):
    # Portable deterministic link-boundary check; actual symlink creation on Windows
    # requires privileges and is not attempted by the suite.
    original = kw._no_link

    def linked(path):
        if path.name == "documents":
            raise ValueError("link boundary")
        return original(path)

    monkeypatch.setattr(kw, "_no_link", linked)
    with pytest.raises(RetrievalError):
        kw.load_workspace("demo")
