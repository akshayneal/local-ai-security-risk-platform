import sqlite3
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from app.chunker import DocumentChunk, chunk_document
from app.document_identity import (
    build_document_id,
    build_document_version_id,
)
from app.document_loader import LoadedDocument
from app.document_registry import (
    DocumentRegistry,
    RegistrationDecision,
)


def make_document(
    text: str,
    source_path: str = "policy.md",
    document_id: str | None = None,
) -> LoadedDocument:
    encoded_text = text.encode("utf-8")
    content_hash = sha256(encoded_text).hexdigest()

    resolved_document_id = (
        document_id
        if document_id is not None
        else build_document_id(source_path)
    )

    document_version_id = build_document_version_id(
        resolved_document_id,
        content_hash,
    )

    return LoadedDocument(
        document_id=resolved_document_id,
        document_version_id=document_version_id,
        content_hash=content_hash,
        source_path=source_path,
        title=Path(source_path).stem.replace("_", " ").title(),
        file_type=Path(source_path).suffix.lstrip("."),
        text=text,
        metadata={
            "file_name": Path(source_path).name,
            "source_path": source_path,
            "file_size_bytes": str(len(encoded_text)),
            "extraction_method": "utf-8",
            "content_hash": content_hash,
            "document_version_id": document_version_id,
        },
    )


def register_document(
    registry: DocumentRegistry,
    document: LoadedDocument,
):
    chunks = chunk_document(
        document,
        chunk_size=100,
        chunk_overlap=20,
    )

    return registry.register_chunked_document(
        document,
        chunks,
    )


def test_register_new_document(tmp_path: Path) -> None:
    database_path = tmp_path / "registry.db"
    document = make_document("Version one.")

    with DocumentRegistry(database_path) as registry:
        result = register_document(
            registry,
            document,
        )

        assert (
            result.decision
            == RegistrationDecision.NEW_DOCUMENT
        )
        assert registry.count_documents() == 1
        assert registry.count_versions() == 1
        assert result.version.version_number == 1
        assert result.version.chunk_count == 1
        assert (
            result.document.current_version_id
            == document.document_version_id
        )


def test_repeated_registration_is_unchanged(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "registry.db"
    document = make_document("Unchanged content.")

    with DocumentRegistry(database_path) as registry:
        first_result = register_document(
            registry,
            document,
        )
        second_result = register_document(
            registry,
            document,
        )

        assert (
            first_result.decision
            == RegistrationDecision.NEW_DOCUMENT
        )
        assert (
            second_result.decision
            == RegistrationDecision.UNCHANGED
        )
        assert registry.count_documents() == 1
        assert registry.count_versions() == 1


def test_changed_content_creates_new_version(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "registry.db"

    first_document = make_document(
        "Version one.",
        source_path="policy.md",
    )
    second_document = make_document(
        "Version two.",
        source_path="policy.md",
    )

    with DocumentRegistry(database_path) as registry:
        first_result = register_document(
            registry,
            first_document,
        )
        second_result = register_document(
            registry,
            second_document,
        )

        assert (
            first_result.decision
            == RegistrationDecision.NEW_DOCUMENT
        )
        assert (
            second_result.decision
            == RegistrationDecision.NEW_VERSION
        )
        assert second_result.version.version_number == 2
        assert registry.count_documents() == 1
        assert registry.count_versions() == 2

        current_version = registry.get_current_version(
            first_document.document_id
        )

        assert current_version is not None
        assert (
            current_version.document_version_id
            == second_document.document_version_id
        )


def test_previous_version_can_be_reactivated(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "registry.db"

    first_document = make_document(
        "Version one.",
        source_path="policy.md",
    )
    second_document = make_document(
        "Version two.",
        source_path="policy.md",
    )

    with DocumentRegistry(database_path) as registry:
        register_document(registry, first_document)
        register_document(registry, second_document)

        result = register_document(
            registry,
            first_document,
        )

        assert (
            result.decision
            == RegistrationDecision.REACTIVATED_VERSION
        )
        assert registry.count_versions() == 2

        current_version = registry.get_current_version(
            first_document.document_id
        )

        assert current_version is not None
        assert (
            current_version.document_version_id
            == first_document.document_version_id
        )
        assert current_version.version_number == 1


def test_same_content_at_different_paths_creates_two_documents(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "registry.db"

    first_document = make_document(
        "Identical content.",
        source_path="first.md",
    )
    second_document = make_document(
        "Identical content.",
        source_path="second.md",
    )

    with DocumentRegistry(database_path) as registry:
        first_result = register_document(
            registry,
            first_document,
        )
        second_result = register_document(
            registry,
            second_document,
        )

        assert (
            first_result.decision
            == RegistrationDecision.NEW_DOCUMENT
        )
        assert (
            second_result.decision
            == RegistrationDecision.NEW_DOCUMENT
        )
        assert registry.count_documents() == 2
        assert registry.count_versions() == 2

        assert (
            first_document.content_hash
            == second_document.content_hash
        )
        assert (
            first_document.document_id
            != second_document.document_id
        )


def test_registry_persists_across_reopen(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "registry.db"
    document = make_document("Persistent content.")

    with DocumentRegistry(database_path) as registry:
        register_document(registry, document)

    with DocumentRegistry(database_path) as registry:
        stored_document = registry.get_document(
            document.document_id
        )
        stored_version = registry.get_version(
            document.document_version_id
        )

        assert stored_document is not None
        assert stored_version is not None
        assert stored_document.source_path == "policy.md"
        assert stored_version.version_number == 1


def test_document_id_collision_is_rejected(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "registry.db"

    first_document = make_document(
        "First document.",
        source_path="first.md",
        document_id="doc_forced_collision",
    )
    second_document = make_document(
        "Second document.",
        source_path="second.md",
        document_id="doc_forced_collision",
    )

    with DocumentRegistry(database_path) as registry:
        register_document(registry, first_document)

        with pytest.raises(
            ValueError,
            match="Document ID collision",
        ):
            register_document(
                registry,
                second_document,
            )

        assert registry.count_documents() == 1
        assert registry.count_versions() == 1


def test_mismatched_chunk_provenance_is_rejected(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "registry.db"
    document = make_document("Policy content.")

    valid_chunk = chunk_document(
        document,
        chunk_size=100,
        chunk_overlap=20,
    )[0]

    invalid_chunk = DocumentChunk(
        chunk_id=valid_chunk.chunk_id,
        document_id="doc_wrong",
        document_version_id=(
            valid_chunk.document_version_id
        ),
        content_hash=valid_chunk.content_hash,
        source_path=valid_chunk.source_path,
        title=valid_chunk.title,
        chunk_index=valid_chunk.chunk_index,
        text=valid_chunk.text,
        metadata=valid_chunk.metadata,
    )

    with DocumentRegistry(database_path) as registry:
        with pytest.raises(
            ValueError,
            match="Chunk document_id does not match document",
        ):
            registry.register_chunked_document(
                document,
                [invalid_chunk],
            )

        assert registry.count_documents() == 0
        assert registry.count_versions() == 0


def test_mismatched_chunk_metadata_is_rejected(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "registry.db"
    document = make_document("Policy content.")
    valid_chunk = chunk_document(
        document,
        chunk_size=100,
        chunk_overlap=20,
    )[0]
    invalid_metadata = dict(valid_chunk.metadata)
    invalid_metadata["content_hash"] = "0" * 64
    invalid_chunk = replace(
        valid_chunk,
        metadata=invalid_metadata,
    )

    with DocumentRegistry(database_path) as registry:
        with pytest.raises(
            ValueError,
            match="Chunk metadata content_hash",
        ):
            registry.register_chunked_document(
                document,
                [invalid_chunk],
            )

        assert registry.count_documents() == 0
        assert registry.count_versions() == 0


def test_shortened_version_id_collision_is_rejected(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "registry.db"
    first_document = make_document("First version.")
    second_document = make_document("Second version.")
    colliding_hash = (
        first_document.content_hash[:12]
        + second_document.content_hash[12:]
    )
    colliding_document = replace(
        second_document,
        document_id=first_document.document_id,
        document_version_id=first_document.document_version_id,
        content_hash=colliding_hash,
        metadata={
            **second_document.metadata,
            "content_hash": colliding_hash,
            "document_version_id": first_document.document_version_id,
        },
    )

    with DocumentRegistry(database_path) as registry:
        register_document(registry, first_document)

        with pytest.raises(
            ValueError,
            match="Document version ID collision",
        ):
            register_document(registry, colliding_document)

        assert registry.count_documents() == 1
        assert registry.count_versions() == 1


def test_registration_rolls_back_partial_insert(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "registry.db"
    document = make_document("Policy content.")

    with DocumentRegistry(database_path) as registry:
        registry.connection.execute(
            """
            CREATE TRIGGER reject_version_insert
            BEFORE INSERT ON document_versions
            BEGIN
                SELECT RAISE(ABORT, 'forced version failure');
            END
            """
        )
        registry.connection.commit()

        with pytest.raises(
            sqlite3.IntegrityError,
            match="forced version failure",
        ):
            register_document(registry, document)

        assert registry.count_documents() == 0
        assert registry.count_versions() == 0


def test_current_version_foreign_key_rejects_dangling_id(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "registry.db"

    with DocumentRegistry(database_path) as registry:
        foreign_keys_enabled = registry.connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

        assert foreign_keys_enabled == 1

        registry.connection.execute("BEGIN")
        registry.connection.execute(
            """
            INSERT INTO documents (
                document_id,
                source_path,
                title,
                file_type,
                current_version_id,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "doc_orphan",
                "orphan.md",
                "Orphan",
                "md",
                "missing_version",
                "now",
                "now",
            ),
        )

        with pytest.raises(sqlite3.IntegrityError):
            registry.connection.commit()

        registry.connection.rollback()
        assert registry.count_documents() == 0


def test_list_versions_returns_version_order(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "registry.db"

    documents = [
        make_document(
            f"Version {number}.",
            source_path="policy.md",
        )
        for number in range(1, 4)
    ]

    with DocumentRegistry(database_path) as registry:
        for document in documents:
            register_document(
                registry,
                document,
            )

        versions = registry.list_versions(
            documents[0].document_id
        )

        assert [
            version.version_number
            for version in versions
        ] == [1, 2, 3]
