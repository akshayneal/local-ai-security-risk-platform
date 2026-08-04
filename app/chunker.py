import re
from dataclasses import dataclass, field

from app.document_limits import DEFAULT_DOCUMENT_LIMITS, DocumentLimits
from app.document_loader import LoadedDocument


DEFAULT_CHUNK_SIZE = 1_000
DEFAULT_CHUNK_OVERLAP = 200
MINIMUM_BREAK_FRACTION = 0.60


@dataclass(frozen=True)
class DocumentChunk:
    """Represents one bounded, version-specific document chunk."""

    chunk_id: str
    document_id: str
    document_version_id: str
    content_hash: str
    source_path: str
    title: str
    chunk_index: int
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


def normalize_chunk_text(text: str) -> str:
    """Normalize line endings and remove surrounding whitespace."""

    normalized_newlines = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized_newlines.strip()


def split_text_by_paragraphs(text: str) -> list[str]:
    """Split normalized text at one or more blank lines."""

    normalized_text = normalize_chunk_text(text)

    if not normalized_text:
        return []

    paragraphs = re.split(r"\n\s*\n", normalized_text)

    return [
        paragraph.strip()
        for paragraph in paragraphs
        if paragraph.strip()
    ]


def validate_chunk_configuration(
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    """Validate chunk-size and overlap settings."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must not be negative")

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size"
        )


def find_preferred_window_end(
    text: str,
    start: int,
    hard_end: int,
    chunk_size: int,
) -> int:
    """Prefer a natural boundary near the end of a character window."""

    if hard_end >= len(text):
        return len(text)

    minimum_end = start + max(
        1,
        int(chunk_size * MINIMUM_BREAK_FRACTION),
    )

    preferred_markers = (
        "\n\n",
        "\n",
        ". ",
        "? ",
        "! ",
        "; ",
        ", ",
        " ",
    )

    for marker in preferred_markers:
        marker_index = text.rfind(
            marker,
            minimum_end,
            hard_end,
        )

        if marker_index != -1:
            return marker_index + len(marker)

    for boundary_index in range(minimum_end - 1, start, -1):
        if text[boundary_index].isspace():
            return boundary_index + 1

    return hard_end


def move_start_to_word_boundary(
    text: str,
    proposed_start: int,
    previous_end: int,
) -> int:
    """Move a proposed overlapping start forward out of a partial word."""

    next_start = proposed_start

    if next_start <= 0 or next_start >= len(text):
        return next_start

    while (
        next_start < previous_end
        and next_start > 0
        and not text[next_start - 1].isspace()
        and not text[next_start].isspace()
    ):
        next_start += 1

    while next_start < len(text) and text[next_start].isspace():
        next_start += 1

    return next_start


def split_large_text_window(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    """Split oversized text using bounded, overlapping natural windows."""

    validate_chunk_configuration(
        chunk_size,
        chunk_overlap,
    )

    normalized_text = normalize_chunk_text(text)

    if not normalized_text:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(normalized_text):
        hard_end = min(
            start + chunk_size,
            len(normalized_text),
        )

        end = find_preferred_window_end(
            normalized_text,
            start,
            hard_end,
            chunk_size,
        )

        if end <= start:
            end = hard_end

        chunk_text = normalized_text[start:end].strip()

        if chunk_text:
            chunks.append(chunk_text)

        if end >= len(normalized_text):
            break

        proposed_start = max(
            end - chunk_overlap,
            start + 1,
        )

        next_start = move_start_to_word_boundary(
            normalized_text,
            proposed_start,
            end,
        )

        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


def split_text_into_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into paragraph-aligned chunks.

Overlap is applied only when an individual paragraph exceeds the
configured chunk size and must be divided using windowed splitting.
"""

    validate_chunk_configuration(
        chunk_size,
        chunk_overlap,
    )

    paragraphs = split_text_by_paragraphs(text)

    if not paragraphs:
        return []

    chunks: list[str] = []
    current_chunk = ""

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            chunks.extend(
                split_large_text_window(
                    paragraph,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
            )
            continue

        candidate = (
            paragraph
            if not current_chunk
            else f"{current_chunk}\n\n{paragraph}"
        )

        if len(candidate) <= chunk_size:
            current_chunk = candidate
            continue

        if current_chunk:
            chunks.append(current_chunk)

        current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def build_chunk_id(
    document_version_id: str,
    chunk_index: int,
) -> str:
    """Create a stable chunk ID tied to one document version."""

    if not document_version_id.strip():
        raise ValueError("document_version_id must not be empty")

    if chunk_index < 0:
        raise ValueError("chunk_index must not be negative")

    return f"{document_version_id}_chunk_{chunk_index:04d}"


def chunk_document(
    document: LoadedDocument,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    limits: DocumentLimits = DEFAULT_DOCUMENT_LIMITS,
) -> list[DocumentChunk]:
    """Create bounded, traceable chunks for one loaded document."""

    if not document.content_hash:
        raise ValueError(
            "Loaded document must include a content hash"
        )

    if not document.document_version_id:
        raise ValueError(
            "Loaded document must include a document version ID"
        )

    chunk_texts = split_text_into_chunks(
        document.text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    if len(chunk_texts) > limits.max_chunks_per_document:
        raise ValueError(
            "Document exceeds the maximum chunk count: "
            f"{len(chunk_texts)} chunks > "
            f"{limits.max_chunks_per_document} chunks"
        )

    chunks: list[DocumentChunk] = []

    for chunk_index, chunk_text in enumerate(chunk_texts):
        chunk_id = build_chunk_id(
            document.document_version_id,
            chunk_index,
        )
        chunk_metadata = dict(document.metadata)
        chunk_metadata.update(
            {
                "document_id": document.document_id,
                "document_version_id": document.document_version_id,
                "content_hash": document.content_hash,
                "chunk_id": chunk_id,
                "chunk_index": str(chunk_index),
                "source_path": document.source_path,
                "title": document.title,
                "file_type": document.file_type,
            }
        )

        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                document_id=document.document_id,
                document_version_id=document.document_version_id,
                content_hash=document.content_hash,
                source_path=document.source_path,
                title=document.title,
                chunk_index=chunk_index,
                text=chunk_text,
                metadata=chunk_metadata,
            )
        )

    return chunks


def chunk_documents(
    documents: list[LoadedDocument],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    limits: DocumentLimits = DEFAULT_DOCUMENT_LIMITS,
) -> list[DocumentChunk]:
    """Create chunks for multiple loaded documents."""

    chunks: list[DocumentChunk] = []

    for document in documents:
        chunks.extend(
            chunk_document(
                document,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                limits=limits,
            )
        )

    return chunks
