from pathlib import Path

from app.document_registry import (
    DocumentRegistry,
    RegistrationDecision,
)
from scripts.register_documents import (
    build_registration_lines,
    register_raw_documents,
)


def test_register_raw_documents_is_idempotent(
    tmp_path: Path,
) -> None:
    raw_docs_dir = tmp_path / "raw_docs"
    raw_docs_dir.mkdir()

    document_path = raw_docs_dir / "policy.md"
    document_path.write_text(
        "Human review is required.",
        encoding="utf-8",
    )

    registry_path = tmp_path / "registry.db"

    first_results = register_raw_documents(
        raw_docs_dir=raw_docs_dir,
        registry_path=registry_path,
        chunk_size=100,
        chunk_overlap=20,
    )

    second_results = register_raw_documents(
        raw_docs_dir=raw_docs_dir,
        registry_path=registry_path,
        chunk_size=100,
        chunk_overlap=20,
    )

    assert len(first_results) == 1
    assert len(second_results) == 1

    assert (
        first_results[0].decision
        == RegistrationDecision.NEW_DOCUMENT
    )
    assert (
        second_results[0].decision
        == RegistrationDecision.UNCHANGED
    )

    with DocumentRegistry(registry_path) as registry:
        assert registry.count_documents() == 1
        assert registry.count_versions() == 1


def test_register_raw_documents_detects_new_version(
    tmp_path: Path,
) -> None:
    raw_docs_dir = tmp_path / "raw_docs"
    raw_docs_dir.mkdir()

    document_path = raw_docs_dir / "policy.md"
    registry_path = tmp_path / "registry.db"

    document_path.write_text(
        "Version one.",
        encoding="utf-8",
    )

    first_results = register_raw_documents(
        raw_docs_dir=raw_docs_dir,
        registry_path=registry_path,
        chunk_size=100,
        chunk_overlap=20,
    )

    document_path.write_text(
        "Version two.",
        encoding="utf-8",
    )

    second_results = register_raw_documents(
        raw_docs_dir=raw_docs_dir,
        registry_path=registry_path,
        chunk_size=100,
        chunk_overlap=20,
    )

    assert (
        first_results[0].decision
        == RegistrationDecision.NEW_DOCUMENT
    )
    assert (
        second_results[0].decision
        == RegistrationDecision.NEW_VERSION
    )
    assert second_results[0].version.version_number == 2

    with DocumentRegistry(registry_path) as registry:
        assert registry.count_documents() == 1
        assert registry.count_versions() == 2


def test_build_registration_lines_handles_empty_results(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "registry.db"

    lines = build_registration_lines(
        [],
        registry_path=registry_path,
    )

    assert f"Registry: {registry_path}" in lines
    assert "Processed documents: 0" in lines
    assert "No supported documents were found." in lines