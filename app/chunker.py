from dataclasses import dataclass, field

from app.document_loader import LoadedDocument


DEFAULT_CHUNK_SIZE = 1_000
DEFAULT_CHUNK_OVERLAP = 200


@dataclass(frozen=True)
class DocumentChunk:
    """Represents one retrievable chunk from a loaded source document."""

    chunk_id: str
    document_id: str
    source_path: str
    title: str
    chunk_index: int
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


def normalize_chunk_text(text: str) -> str:
    """Normalize chunk text without destroying paragraph structure."""

    return text.strip()


def split_text_by_paragraphs(text: str) -> list[str]:
    """Split text into non-empty paragraph blocks."""

    paragraphs = []

    for paragraph in text.split("\n\n"):
        cleaned_paragraph = paragraph.strip()
        if cleaned_paragraph:
            paragraphs.append(cleaned_paragraph)

    return paragraphs


def split_large_text_window(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping character windows."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    cleaned_text = normalize_chunk_text(text)

    if not cleaned_text:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(cleaned_text):
        end = start + chunk_size
        chunk = normalize_chunk_text(cleaned_text[start:end])

        if chunk:
            chunks.append(chunk)

        if end >= len(cleaned_text):
            break

        start = end - chunk_overlap

    return chunks


def split_text_into_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into chunks while trying to preserve paragraph boundaries."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    cleaned_text = normalize_chunk_text(text)

    if not cleaned_text:
        return []

    paragraphs = split_text_by_paragraphs(cleaned_text)

    if not paragraphs:
        return []

    chunks: list[str] = []
    current_chunk_parts: list[str] = []
    current_length = 0

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if current_chunk_parts:
                chunks.append("\n\n".join(current_chunk_parts))
                current_chunk_parts = []
                current_length = 0

            chunks.extend(split_large_text_window(paragraph, chunk_size, chunk_overlap))
            continue

        paragraph_length = len(paragraph)

        if current_chunk_parts and current_length + paragraph_length + 2 > chunk_size:
            chunks.append("\n\n".join(current_chunk_parts))

            overlap_text = chunks[-1][-chunk_overlap:] if chunk_overlap > 0 else ""
            current_chunk_parts = [overlap_text, paragraph] if overlap_text else [paragraph]
            current_length = sum(len(part) for part in current_chunk_parts) + 2 * (
                len(current_chunk_parts) - 1
            )
            continue

        current_chunk_parts.append(paragraph)
        current_length += paragraph_length + (2 if len(current_chunk_parts) > 1 else 0)

    if current_chunk_parts:
        chunks.append("\n\n".join(current_chunk_parts))

    return [normalize_chunk_text(chunk) for chunk in chunks if normalize_chunk_text(chunk)]


def build_chunk_id(document_id: str, chunk_index: int) -> str:
    """Create a stable chunk ID from a document ID and chunk index."""

    if chunk_index < 0:
        raise ValueError("chunk_index cannot be negative")

    return f"{document_id}_chunk_{chunk_index:04d}"


def chunk_document(
    document: LoadedDocument,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    """Create retrievable chunks from one loaded document."""

    chunk_texts = split_text_into_chunks(
        document.text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks: list[DocumentChunk] = []

    for chunk_index, chunk_text in enumerate(chunk_texts):
        chunk_id = build_chunk_id(document.document_id, chunk_index)

        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                document_id=document.document_id,
                source_path=document.source_path,
                title=document.title,
                chunk_index=chunk_index,
                text=chunk_text,
                metadata={
                    **document.metadata,
                    "document_id": document.document_id,
                    "chunk_id": chunk_id,
                    "chunk_index": str(chunk_index),
                    "source_path": document.source_path,
                    "title": document.title,
                    "file_type": document.file_type,
                },
            )
        )

    return chunks


def chunk_documents(
    documents: list[LoadedDocument],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    """Create retrievable chunks from multiple loaded documents."""

    chunks: list[DocumentChunk] = []

    for document in documents:
        chunks.extend(
            chunk_document(
                document,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        )

    return chunks