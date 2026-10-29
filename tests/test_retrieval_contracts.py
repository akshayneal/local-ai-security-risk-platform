"""Deterministic contract, eligibility, provenance and legacy preservation checks."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.chunker import chunk_document
from app.document_loader import load_text_document
from app.document_registry import DocumentRegistry
from app.reference_loader import get_relevant_references
from app.retrieval.contracts import (
    Authority,
    EvidenceRecord,
    RetrievalError,
    RetrievalQuery,
    Workflow,
)
from app.retrieval.filtering import eligible, registry_version_gate, unique_records
from app.retrieval.importers import (
    chunk_record,
    load_curated_records,
    load_registered_records,
)
from app.retrieval.legacy import LegacyRetriever


def record(**updates):
    values = {
        "evidence_id": "one",
        "source_id": "source-one",
        "title": "Isolation approval",
        "content": "System owner approval is required before host isolation.",
        "source_type": "procedure",
        "source_family": "Synthetic",
        "synthetic": True,
        "workflows": [Workflow.SOC],
        "tags": ["isolation"],
    }
    return EvidenceRecord(**(values | updates))


def query(**updates):
    return RetrievalQuery(
        **(
            {
                "text": "host isolation approval",
                "workflow": Workflow.SOC,
                "as_of": date(2026, 10, 28),
            }
            | updates
        )
    )


@pytest.mark.parametrize("workflow", list(Workflow))
def test_all_four_workflows_have_common_contract(workflow):
    assert query(workflow=workflow).workflow == workflow


@pytest.mark.parametrize(
    "updates",
    [
        {"text": ""},
        {"text": "  "},
        {"top_k": 0},
        {"top_k": 101},
        {"workflow": "bad"},
        {"unused": True},
    ],
)
def test_query_rejects_invalid_or_unused_semantics(updates):
    with pytest.raises(ValidationError):
        query(**updates)


@pytest.mark.parametrize(
    "updates",
    [
        {"workflows": []},
        {"authority": Authority.POLICY},
        {"content_hash": "bad"},
        {"effective_date": "2026-02-01", "expiration_date": "2026-01-01"},
        {"document_id": "doc"},
        {"chunk_id": "chunk"},
        {"status": "unknown"},
        {"surprise": "no"},
    ],
)
def test_invalid_evidence_is_rejected(updates):
    with pytest.raises(ValidationError):
        record(**updates)


@pytest.mark.parametrize(
    ("metadata", "query_values", "expected"),
    [
        ({}, {}, True),
        ({"workflows": [Workflow.AI_RISK]}, {}, False),
        ({"workflows": list(Workflow)}, {}, True),
        ({"required_scopes": ["soc", "secret"]}, {"access_scopes": ["soc"]}, False),
        (
            {"required_scopes": ["soc", "secret"]},
            {"access_scopes": ["soc", "secret"]},
            True,
        ),
        ({"status": "inactive"}, {}, False),
        ({"status": "inactive"}, {"include_inactive": True}, True),
        ({"status": "failed"}, {"include_inactive": True}, False),
        ({"effective_date": "2027-01-01"}, {}, False),
        ({"effective_date": "2026-10-28"}, {}, True),
        ({"expiration_date": "2026-10-28"}, {}, False),
        ({"expiration_date": "2026-10-29"}, {}, True),
        ({"authority": Authority.EXTERNAL}, {"authorities": [Authority.POLICY]}, False),
        ({"authority": Authority.POLICY, "policy_scope": "example-org"}, {}, False),
        (
            {"authority": Authority.POLICY, "policy_scope": "example-org"},
            {"policy_scopes": ["example-org"], "authorities": [Authority.POLICY]},
            True,
        ),
        (
            {"applicability": ["production"]},
            {"applicability": ["production", "critical"]},
            False,
        ),
        (
            {"applicability": ["production", "critical"]},
            {"applicability": ["critical"]},
            True,
        ),
        ({}, {"source_types": ["policy"]}, False),
        ({}, {"source_types": ["procedure"]}, True),
        (
            {"document_id": "doc", "document_version_id": "v1"},
            {"version_ids": ["v2"]},
            False,
        ),
        (
            {"document_id": "doc", "document_version_id": "v1"},
            {"version_ids": ["v1"]},
            True,
        ),
    ],
)
def test_filter_semantics(metadata, query_values, expected):
    assert eligible(record(**metadata), query(**query_values)) is expected


@pytest.mark.parametrize("mode", ["soc_alert", "governance"])
@pytest.mark.parametrize(
    "text",
    [
        "SSH brute force followed by successful login",
        "Suspicious encoded PowerShell command",
        "AI resume screening assistant using candidate resumes for hiring decisions",
        "human review approval logging",
        "",
        "no_matching_qzx",
        "audit evidence gaps",
    ],
)
@pytest.mark.parametrize("k", [1, 4, 6])
def test_legacy_adapter_exact_order_and_cards(mode, text, k):
    workflow = Workflow.SOC if mode == "soc_alert" else Workflow.AI_RISK
    results = (
        LegacyRetriever(load_curated_records(mode)).search(
            query(text=text or " ", workflow=workflow, top_k=k)
        )
        if text
        else []
    )
    assert [hit.record.legacy_card() for hit in results] == get_relevant_references(
        mode, text, k
    )


def test_no_false_authority_and_no_duplicate_shared_cards():
    records = load_curated_records()
    assert len({r.evidence_id for r in records}) == len(records)
    assert not any(r.authority == Authority.POLICY for r in records)
    shared = next(r for r in records if r.source_id == "LOCAL-AUDITABILITY")
    assert shared.workflows == {Workflow.SOC, Workflow.AI_RISK}
    assert shared.content_hash and shared.authority == Authority.LOCAL


def test_duplicates_and_stable_ties():
    first = record()
    second = record(evidence_id="two", source_id="two")
    assert unique_records([first, first]) == (first,)
    with pytest.raises(ValueError, match="Conflicting"):
        unique_records([first, record(content="different")])
    assert [
        r.record.evidence_id for r in LegacyRetriever([second, first]).search(query())
    ] == ["two", "one"]


def test_filter_before_legacy_scoring(monkeypatch):
    def scoring(tokens, card):
        assert card["source_id"] != "forbidden"
        return 1

    monkeypatch.setattr("app.retrieval.legacy.score_reference", scoring)
    results = LegacyRetriever(
        [record(source_id="forbidden", required_scopes=["private"])]
    ).search(query())
    assert results == []


def test_registry_reuses_ingestion_and_rechecks_new_versions(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    path = raw / "procedure.md"
    path.write_text("System owner approval before isolation.", encoding="utf-8")
    database = tmp_path / "registry.db"
    document = load_text_document(path, raw)
    chunks = chunk_document(document)
    with DocumentRegistry(database) as registry:
        registry.register_chunked_document(document, chunks)
    metadata = {
        document.document_id: {
            "workflows": [Workflow.SOC],
            "source_type": "document",
            "source_family": "Local",
        }
    }
    records = load_registered_records(raw, database, metadata)
    assert len(records) == 1
    evidence = records[0]
    assert evidence.document_id == document.document_id
    assert evidence.document_version_id == document.document_version_id
    assert evidence.chunk_id == chunks[0].chunk_id
    assert evidence.content_hash == document.content_hash
    assert evidence.chunk_hash and evidence.authority == Authority.UNVERIFIED
    retriever = LegacyRetriever(records, registry_version_gate(database))
    assert retriever.search(query())
    path.write_text(
        "New active policy: investigate before isolation.", encoding="utf-8"
    )
    changed = load_text_document(path, raw)
    with DocumentRegistry(database) as registry:
        registry.register_chunked_document(changed, chunk_document(changed))
    assert retriever.search(query()) == []  # Old in-memory/index snapshot is excluded.
    assert (
        load_registered_records(raw, database, metadata)[0].document_version_id
        == changed.document_version_id
    )
    with pytest.raises(ValueError, match="override"):
        chunk_record(chunks[0], {"content": "forged"})
    with pytest.raises(ValueError, match="Missing trusted"):
        load_registered_records(raw, database, {})


@pytest.mark.parametrize("corrupt", [False, True])
def test_registry_failure_never_bypasses_version_filter(tmp_path, corrupt):
    path = tmp_path / "bad.db"
    if corrupt:
        path.write_text("corrupt")
    gate = registry_version_gate(path)
    with pytest.raises(RetrievalError):
        gate(record(document_id="doc", document_version_id="v1", content_hash="a" * 64))
    assert not path.exists() if not corrupt else True
