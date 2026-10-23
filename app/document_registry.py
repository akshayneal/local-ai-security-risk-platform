import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Iterable

from app.chunker import DocumentChunk, build_chunk_id
from app.document_identity import (
    build_document_version_id,
    is_valid_sha256_digest,
)
from app.document_loader import LoadedDocument


DEFAULT_REGISTRY_PATH = Path(
    "knowledge_base/registry/document_registry.db"
)


class RegistrationDecision(str, Enum):
    """Describes how a document registration affected the registry."""

    NEW_DOCUMENT = "new_document"
    NEW_VERSION = "new_version"
    UNCHANGED = "unchanged"
    REACTIVATED_VERSION = "reactivated_version"


class DocumentVersionStatus(str, Enum):
    """Current processing state recorded for a document version."""

    CHUNKED = "chunked"
    FAILED = "failed"
    INACTIVE = "inactive"


@dataclass(frozen=True)
class DocumentRecord:
    """Represents one logical document in the registry."""

    document_id: str
    source_path: str
    title: str
    file_type: str
    current_version_id: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class DocumentVersionRecord:
    """Represents one exact content version of a logical document."""

    document_version_id: str
    document_id: str
    version_number: int
    content_hash: str
    file_size_bytes: int
    extraction_method: str
    status: DocumentVersionStatus
    chunk_count: int
    error_message: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class RegistrationResult:
    """Returns the outcome and persisted records from registration."""

    decision: RegistrationDecision
    document: DocumentRecord
    version: DocumentVersionRecord


def utc_now_iso() -> str:
    """Return a timezone-aware UTC timestamp in ISO 8601 format."""

    return datetime.now(timezone.utc).isoformat()


def parse_nonnegative_metadata_integer(
    metadata: dict[str, str],
    key: str,
) -> int:
    """Read a required nonnegative integer from string metadata."""

    raw_value = metadata.get(key)

    if raw_value is None:
        raise ValueError(
            f"Document metadata must include {key}"
        )

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"Document metadata field {key} must be an integer"
        ) from exc

    if value < 0:
        raise ValueError(
            f"Document metadata field {key} must not be negative"
        )

    return value


class DocumentRegistry:
    """SQLite-backed authoritative document-version registry."""

    def __init__(
        self,
        database_path: Path | str = DEFAULT_REGISTRY_PATH,
    ) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.connection = sqlite3.connect(
            self.database_path,
            timeout=5.0,
        )
        self.connection.row_factory = sqlite3.Row

        self.connection.execute(
            "PRAGMA foreign_keys = ON"
        )
        self.connection.execute(
            "PRAGMA journal_mode = WAL"
        )
        self.connection.execute(
            "PRAGMA synchronous = NORMAL"
        )
        self.connection.execute(
            "PRAGMA busy_timeout = 5000"
        )

        self.initialize_schema()

    def initialize_schema(self) -> None:
        """Create the document-registry tables and indexes."""

        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                source_path TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                file_type TEXT NOT NULL,
                current_version_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (current_version_id)
                    REFERENCES document_versions(document_version_id)
                    ON DELETE RESTRICT
                    DEFERRABLE INITIALLY DEFERRED
            );

            CREATE TABLE IF NOT EXISTS document_versions (
                document_version_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                version_number INTEGER NOT NULL
                    CHECK (version_number > 0),
                content_hash TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL
                    CHECK (file_size_bytes >= 0),
                extraction_method TEXT NOT NULL,
                status TEXT NOT NULL,
                chunk_count INTEGER NOT NULL
                    CHECK (chunk_count >= 0),
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (document_id)
                    REFERENCES documents(document_id)
                    ON DELETE RESTRICT,
                UNIQUE (document_id, version_number),
                UNIQUE (document_id, content_hash)
            );

            CREATE INDEX IF NOT EXISTS
                idx_document_versions_document_id
            ON document_versions(document_id);

            CREATE INDEX IF NOT EXISTS
                idx_document_versions_content_hash
            ON document_versions(content_hash);

            CREATE INDEX IF NOT EXISTS
                idx_document_versions_status
            ON document_versions(status);
            """
        )
        self.connection.commit()

    def close(self) -> None:
        """Close the SQLite connection."""

        self.connection.close()

    def __enter__(self) -> "DocumentRegistry":
        return self

    def __exit__(
        self,
        _exception_type: object,
        _exception_value: object,
        _traceback: object,
    ) -> None:
        self.close()

    def get_document(
        self,
        document_id: str,
    ) -> DocumentRecord | None:
        """Return one logical document, if present."""

        row = self.connection.execute(
            """
            SELECT
                document_id,
                source_path,
                title,
                file_type,
                current_version_id,
                created_at,
                updated_at
            FROM documents
            WHERE document_id = ?
            """,
            (document_id,),
        ).fetchone()

        if row is None:
            return None

        return self._document_from_row(row)

    def get_version(
        self,
        document_version_id: str,
    ) -> DocumentVersionRecord | None:
        """Return one exact document version, if present."""

        row = self.connection.execute(
            """
            SELECT
                document_version_id,
                document_id,
                version_number,
                content_hash,
                file_size_bytes,
                extraction_method,
                status,
                chunk_count,
                error_message,
                created_at,
                updated_at
            FROM document_versions
            WHERE document_version_id = ?
            """,
            (document_version_id,),
        ).fetchone()

        if row is None:
            return None

        return self._version_from_row(row)

    def get_current_version(
        self,
        document_id: str,
    ) -> DocumentVersionRecord | None:
        """Return the currently active version for one document."""

        row = self.connection.execute(
            """
            SELECT
                versions.document_version_id,
                versions.document_id,
                versions.version_number,
                versions.content_hash,
                versions.file_size_bytes,
                versions.extraction_method,
                versions.status,
                versions.chunk_count,
                versions.error_message,
                versions.created_at,
                versions.updated_at
            FROM document_versions AS versions
            INNER JOIN documents
                ON documents.current_version_id
                = versions.document_version_id
            WHERE documents.document_id = ?
            """,
            (document_id,),
        ).fetchone()

        if row is None:
            return None

        return self._version_from_row(row)

    def list_versions(
        self,
        document_id: str,
    ) -> list[DocumentVersionRecord]:
        """Return all versions of a document in version order."""

        rows = self.connection.execute(
            """
            SELECT
                document_version_id,
                document_id,
                version_number,
                content_hash,
                file_size_bytes,
                extraction_method,
                status,
                chunk_count,
                error_message,
                created_at,
                updated_at
            FROM document_versions
            WHERE document_id = ?
            ORDER BY version_number
            """,
            (document_id,),
        ).fetchall()

        return [
            self._version_from_row(row)
            for row in rows
        ]

    def count_documents(self) -> int:
        """Return the number of logical documents."""

        row = self.connection.execute(
            "SELECT COUNT(*) AS count FROM documents"
        ).fetchone()

        return int(row["count"])

    def count_versions(self) -> int:
        """Return the number of persisted document versions."""

        row = self.connection.execute(
            "SELECT COUNT(*) AS count FROM document_versions"
        ).fetchone()

        return int(row["count"])

    def register_chunked_document(
        self,
        document: LoadedDocument,
        chunks: Iterable[DocumentChunk],
    ) -> RegistrationResult:
        """Register one successfully loaded and chunked document."""

        chunk_list = list(chunks)

        self._validate_registration(
            document,
            chunk_list,
        )

        file_size_bytes = parse_nonnegative_metadata_integer(
            document.metadata,
            "file_size_bytes",
        )

        extraction_method = document.metadata.get(
            "extraction_method",
            "",
        ).strip()

        if not extraction_method:
            raise ValueError(
                "Document metadata must include extraction_method"
            )

        timestamp = utc_now_iso()

        try:
            self.connection.execute("BEGIN IMMEDIATE")

            existing_document_row = self.connection.execute(
                """
                SELECT
                    document_id,
                    source_path,
                    title,
                    file_type,
                    current_version_id,
                    created_at,
                    updated_at
                FROM documents
                WHERE document_id = ?
                """,
                (document.document_id,),
            ).fetchone()

            existing_version_row = self.connection.execute(
                """
                SELECT
                    document_version_id,
                    document_id,
                    version_number,
                    content_hash,
                    file_size_bytes,
                    extraction_method,
                    status,
                    chunk_count,
                    error_message,
                    created_at,
                    updated_at
                FROM document_versions
                WHERE document_version_id = ?
                """,
                (document.document_version_id,),
            ).fetchone()

            if existing_document_row is None:
                self._insert_new_document(
                    document=document,
                    file_size_bytes=file_size_bytes,
                    extraction_method=extraction_method,
                    chunk_count=len(chunk_list),
                    timestamp=timestamp,
                )
                decision = RegistrationDecision.NEW_DOCUMENT

            else:
                self._validate_existing_document_identity(
                    document,
                    existing_document_row,
                )

                if existing_version_row is not None:
                    self._validate_existing_version_identity(
                        document,
                        existing_version_row,
                    )

                    self.connection.execute(
                        """
                        UPDATE document_versions
                        SET
                            status = ?,
                            chunk_count = ?,
                            error_message = NULL,
                            updated_at = ?
                        WHERE document_version_id = ?
                        """,
                        (
                            DocumentVersionStatus.CHUNKED.value,
                            len(chunk_list),
                            timestamp,
                            document.document_version_id,
                        ),
                    )

                    self.connection.execute(
                        """
                        UPDATE documents
                        SET
                            title = ?,
                            file_type = ?,
                            current_version_id = ?,
                            updated_at = ?
                        WHERE document_id = ?
                        """,
                        (
                            document.title,
                            document.file_type,
                            document.document_version_id,
                            timestamp,
                            document.document_id,
                        ),
                    )

                    if (
                        existing_document_row["current_version_id"]
                        == document.document_version_id
                    ):
                        decision = RegistrationDecision.UNCHANGED
                    else:
                        decision = (
                            RegistrationDecision.REACTIVATED_VERSION
                        )

                else:
                    self._validate_no_version_id_collision(
                        document,
                    )

                    next_version_number = (
                        self._get_next_version_number(
                            document.document_id
                        )
                    )

                    self._insert_version(
                        document=document,
                        version_number=next_version_number,
                        file_size_bytes=file_size_bytes,
                        extraction_method=extraction_method,
                        chunk_count=len(chunk_list),
                        timestamp=timestamp,
                    )

                    self.connection.execute(
                        """
                        UPDATE documents
                        SET
                            title = ?,
                            file_type = ?,
                            current_version_id = ?,
                            updated_at = ?
                        WHERE document_id = ?
                        """,
                        (
                            document.title,
                            document.file_type,
                            document.document_version_id,
                            timestamp,
                            document.document_id,
                        ),
                    )

                    decision = RegistrationDecision.NEW_VERSION

            self.connection.commit()

        except Exception:
            self.connection.rollback()
            raise

        stored_document = self.get_document(
            document.document_id
        )
        stored_version = self.get_version(
            document.document_version_id
        )

        if stored_document is None or stored_version is None:
            raise RuntimeError(
                "Registry transaction completed without readable records"
            )

        return RegistrationResult(
            decision=decision,
            document=stored_document,
            version=stored_version,
        )

    def _insert_new_document(
        self,
        document: LoadedDocument,
        file_size_bytes: int,
        extraction_method: str,
        chunk_count: int,
        timestamp: str,
    ) -> None:
        """Insert a logical document and its first version."""

        self.connection.execute(
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
                document.document_id,
                document.source_path,
                document.title,
                document.file_type,
                document.document_version_id,
                timestamp,
                timestamp,
            ),
        )

        self._insert_version(
            document=document,
            version_number=1,
            file_size_bytes=file_size_bytes,
            extraction_method=extraction_method,
            chunk_count=chunk_count,
            timestamp=timestamp,
        )

    def _insert_version(
        self,
        document: LoadedDocument,
        version_number: int,
        file_size_bytes: int,
        extraction_method: str,
        chunk_count: int,
        timestamp: str,
    ) -> None:
        """Insert one exact document version."""

        self.connection.execute(
            """
            INSERT INTO document_versions (
                document_version_id,
                document_id,
                version_number,
                content_hash,
                file_size_bytes,
                extraction_method,
                status,
                chunk_count,
                error_message,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
            """,
            (
                document.document_version_id,
                document.document_id,
                version_number,
                document.content_hash,
                file_size_bytes,
                extraction_method,
                DocumentVersionStatus.CHUNKED.value,
                chunk_count,
                timestamp,
                timestamp,
            ),
        )

    def _get_next_version_number(
        self,
        document_id: str,
    ) -> int:
        """Return the next sequential version number."""

        row = self.connection.execute(
            """
            SELECT COALESCE(MAX(version_number), 0) AS maximum
            FROM document_versions
            WHERE document_id = ?
            """,
            (document_id,),
        ).fetchone()

        return int(row["maximum"]) + 1

    def _validate_registration(
        self,
        document: LoadedDocument,
        chunks: list[DocumentChunk],
    ) -> None:
        """Validate document and chunk identity before persistence."""

        if not is_valid_sha256_digest(
            document.content_hash
        ):
            raise ValueError(
                "Document content_hash must be a complete "
                "hexadecimal SHA-256 digest"
            )

        expected_version_id = build_document_version_id(
            document.document_id,
            document.content_hash,
        )

        if document.document_version_id != expected_version_id:
            raise ValueError(
                "Document version ID does not match its "
                "document ID and content hash"
            )

        if not chunks:
            raise ValueError(
                "A chunked document must include at least one chunk"
            )

        expected_indices = list(range(len(chunks)))
        actual_indices = sorted(
            chunk.chunk_index
            for chunk in chunks
        )

        if actual_indices != expected_indices:
            raise ValueError(
                "Chunk indexes must be unique and sequential "
                "starting at zero"
            )

        seen_chunk_ids: set[str] = set()

        for chunk in chunks:
            if chunk.chunk_id in seen_chunk_ids:
                raise ValueError(
                    f"Duplicate chunk ID: {chunk.chunk_id}"
                )

            seen_chunk_ids.add(chunk.chunk_id)

            if chunk.document_id != document.document_id:
                raise ValueError(
                    "Chunk document_id does not match document"
                )

            if (
                chunk.document_version_id
                != document.document_version_id
            ):
                raise ValueError(
                    "Chunk document_version_id does not "
                    "match document"
                )

            if chunk.content_hash != document.content_hash:
                raise ValueError(
                    "Chunk content_hash does not match document"
                )

            if chunk.source_path != document.source_path:
                raise ValueError(
                    "Chunk source_path does not match document"
                )

            if chunk.title != document.title:
                raise ValueError(
                    "Chunk title does not match document"
                )

            expected_chunk_id = build_chunk_id(
                document.document_version_id,
                chunk.chunk_index,
            )

            if chunk.chunk_id != expected_chunk_id:
                raise ValueError(
                    "Chunk ID does not match document version "
                    "and chunk index"
                )

            expected_metadata = {
                "document_id": document.document_id,
                "document_version_id": document.document_version_id,
                "content_hash": document.content_hash,
                "chunk_id": chunk.chunk_id,
                "chunk_index": str(chunk.chunk_index),
                "source_path": document.source_path,
                "title": document.title,
                "file_type": document.file_type,
            }

            for key, expected_value in expected_metadata.items():
                if chunk.metadata.get(key) != expected_value:
                    raise ValueError(
                        f"Chunk metadata {key} does not match document"
                    )

    def _validate_existing_document_identity(
        self,
        document: LoadedDocument,
        row: sqlite3.Row,
    ) -> None:
        """Reject a document-ID collision across source paths."""

        if row["source_path"] != document.source_path:
            raise ValueError(
                "Document ID collision: the stored source path "
                "does not match the incoming source path"
            )

    def _validate_existing_version_identity(
        self,
        document: LoadedDocument,
        row: sqlite3.Row,
    ) -> None:
        """Reject mismatched content behind an existing version ID."""

        if row["document_id"] != document.document_id:
            raise ValueError(
                "Document version belongs to a different document"
            )

        if row["content_hash"] != document.content_hash:
            raise ValueError(
                "Document version ID collision: stored content "
                "hash does not match incoming content hash"
            )

    def _validate_no_version_id_collision(
        self,
        document: LoadedDocument,
    ) -> None:
        """Detect a shortened-hash version-ID collision."""

        row = self.connection.execute(
            """
            SELECT
                document_id,
                content_hash
            FROM document_versions
            WHERE document_version_id = ?
            """,
            (document.document_version_id,),
        ).fetchone()

        if row is None:
            return

        if (
            row["document_id"] != document.document_id
            or row["content_hash"] != document.content_hash
        ):
            raise ValueError(
                "Document version ID collision detected"
            )

    @staticmethod
    def _document_from_row(
        row: sqlite3.Row,
    ) -> DocumentRecord:
        return DocumentRecord(
            document_id=row["document_id"],
            source_path=row["source_path"],
            title=row["title"],
            file_type=row["file_type"],
            current_version_id=row["current_version_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _version_from_row(
        row: sqlite3.Row,
    ) -> DocumentVersionRecord:
        return DocumentVersionRecord(
            document_version_id=row["document_version_id"],
            document_id=row["document_id"],
            version_number=int(row["version_number"]),
            content_hash=row["content_hash"],
            file_size_bytes=int(row["file_size_bytes"]),
            extraction_method=row["extraction_method"],
            status=DocumentVersionStatus(row["status"]),
            chunk_count=int(row["chunk_count"]),
            error_message=row["error_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
