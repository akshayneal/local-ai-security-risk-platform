from hashlib import sha256

import pytest

from app.chunker import (
    DocumentChunk,
    build_chunk_id,
    chunk_document,
    chunk_documents,
    split_large_text_window,
    split_text_by_paragraphs,
    split_text_into_chunks,
)
from app.document_identity import build_document_version_id
from app.document_limits import DocumentLimits
from app.document_loader import LoadedDocument


def make_loaded_document(
    text: str,
    source_path: str = "governance_notes.md",
    document_id: str = "doc_test123456",
) -> LoadedDocument:
    content_hash = sha256(text.encode("utf-8")).hexdigest()
    document_version_id = build_document_version_id(
        document_id,
        content_hash,
    )

    return LoadedDocument(
        document_id=document_id,
        document_version_id=document_version_id,
        content_hash=content_hash,
        source_path=source_path,
        title="Governance Notes",
        file_type="md",
        text=text,
        metadata={
            "source_path": source_path,
            "content_hash": content_hash,
            "document_version_id": document_version_id,
        },
    )


def make_limits(max_chunks: int) -> DocumentLimits:
    return DocumentLimits(
        max_file_size_bytes=10_000,
        max_pdf_pages=100,
        max_extracted_characters=10_000,
        max_chunks_per_document=max_chunks,
    )


def test_split_text_by_paragraphs() -> None:
    text = "First paragraph.\n\nSecond paragraph.\n\n\nThird paragraph."

    paragraphs = split_text_by_paragraphs(text)

    assert paragraphs == [
        "First paragraph.",
        "Second paragraph.",
        "Third paragraph.",
    ]


def test_split_text_into_chunks_keeps_small_paragraphs_together() -> None:
    text = "First paragraph.\n\nSecond paragraph."

    chunks = split_text_into_chunks(
        text,
        chunk_size=100,
        chunk_overlap=10,
    )

    assert chunks == [
        "First paragraph.\n\nSecond paragraph."
    ]


def test_split_text_into_chunks_separates_paragraphs_at_limit() -> None:
    text = "First paragraph.\n\nSecond paragraph."

    chunks = split_text_into_chunks(
        text,
        chunk_size=20,
        chunk_overlap=5,
    )

    assert chunks == [
        "First paragraph.",
        "Second paragraph.",
    ]


def test_split_large_text_window_creates_bounded_chunks() -> None:
    text = " ".join(f"word{index}" for index in range(100))

    chunks = split_large_text_window(
        text,
        chunk_size=100,
        chunk_overlap=20,
    )

    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_split_large_text_window_avoids_partial_word_starts() -> None:
    words = [f"word{index}" for index in range(100)]
    text = " ".join(words)

    chunks = split_large_text_window(
        text,
        chunk_size=80,
        chunk_overlap=20,
    )

    valid_words = set(words)

    for chunk in chunks:
        first_word = chunk.split()[0]
        assert first_word in valid_words


def test_split_large_text_window_uses_earlier_word_boundary() -> None:
    first_word = "a" * 50
    second_word = "b" * 60
    text = f"{first_word} {second_word} tail"

    chunks = split_large_text_window(
        text,
        chunk_size=100,
        chunk_overlap=20,
    )

    assert chunks == [
        first_word,
        f"{second_word} tail",
    ]


def test_split_large_text_window_preserves_some_overlap() -> None:
    text = " ".join(f"word{index}" for index in range(100))

    chunks = split_large_text_window(
        text,
        chunk_size=100,
        chunk_overlap=25,
    )

    first_chunk_words = set(chunks[0].split())
    second_chunk_words = set(chunks[1].split())

    assert first_chunk_words.intersection(second_chunk_words)


def test_build_chunk_id_uses_document_version() -> None:
    chunk_id = build_chunk_id(
        "doc_example_v_123456789abc",
        7,
    )

    assert chunk_id == (
        "doc_example_v_123456789abc_chunk_0007"
    )


def test_build_chunk_id_rejects_negative_index() -> None:
    with pytest.raises(
        ValueError,
        match="chunk_index must not be negative",
    ):
        build_chunk_id(
            "doc_example_v_123456789abc",
            -1,
        )


def test_chunk_document_preserves_identity_and_metadata() -> None:
    document = make_loaded_document(
        "Human review is required."
    )

    chunks = chunk_document(
        document,
        chunk_size=100,
        chunk_overlap=10,
    )

    assert len(chunks) == 1

    chunk = chunks[0]

    assert isinstance(chunk, DocumentChunk)
    assert chunk.document_id == document.document_id
    assert chunk.document_version_id == document.document_version_id
    assert chunk.content_hash == document.content_hash
    assert chunk.source_path == document.source_path
    assert chunk.title == document.title
    assert chunk.metadata["content_hash"] == document.content_hash
    assert (
        chunk.metadata["document_version_id"]
        == document.document_version_id
    )
    assert chunk.metadata["chunk_id"] == chunk.chunk_id
    assert chunk.metadata["source_path"] == document.source_path
    assert chunk.metadata["title"] == document.title
    assert chunk.metadata["file_type"] == document.file_type


def test_chunk_ids_change_when_document_content_changes() -> None:
    first_document = make_loaded_document(
        "Version one.",
    )
    second_document = make_loaded_document(
        "Version two.",
    )

    first_chunks = chunk_document(
        first_document,
        chunk_size=100,
        chunk_overlap=10,
    )
    second_chunks = chunk_document(
        second_document,
        chunk_size=100,
        chunk_overlap=10,
    )

    assert first_chunks[0].chunk_id != second_chunks[0].chunk_id


def test_chunk_document_accepts_exact_chunk_limit() -> None:
    document = make_loaded_document(
        "A" * 60,
    )

    chunks = chunk_document(
        document,
        chunk_size=20,
        chunk_overlap=0,
        limits=make_limits(max_chunks=3),
    )

    assert len(chunks) == 3


def test_chunk_document_rejects_excessive_chunk_count() -> None:
    document = make_loaded_document(
        "A" * 60,
    )

    with pytest.raises(
        ValueError,
        match="Document exceeds the maximum chunk count",
    ):
        chunk_document(
            document,
            chunk_size=20,
            chunk_overlap=0,
            limits=make_limits(max_chunks=2),
        )


def test_chunk_document_rejects_missing_content_hash() -> None:
    document = LoadedDocument(
        document_id="doc_example",
        document_version_id="doc_example_v_123456789abc",
        content_hash="",
        source_path="example.md",
        title="Example",
        file_type="md",
        text="Example content.",
    )

    with pytest.raises(
        ValueError,
        match="must include a content hash",
    ):
        chunk_document(document)


def test_chunk_documents_combines_multiple_documents() -> None:
    first_document = make_loaded_document(
        "First document.",
        source_path="first.md",
        document_id="doc_first",
    )
    second_document = make_loaded_document(
        "Second document.",
        source_path="second.md",
        document_id="doc_second",
    )

    chunks = chunk_documents(
        [first_document, second_document],
        chunk_size=100,
        chunk_overlap=10,
    )

    assert len(chunks) == 2
    assert {
        chunk.document_id
        for chunk in chunks
    } == {
        "doc_first",
        "doc_second",
    }


def test_split_text_rejects_overlap_equal_to_chunk_size() -> None:
    with pytest.raises(
        ValueError,
        match="chunk_overlap must be smaller than chunk_size",
    ):
        split_text_into_chunks(
            "Example text.",
            chunk_size=10,
            chunk_overlap=10,
        )
def test_split_text_rejects_nonpositive_chunk_size() -> None:
    with pytest.raises(
        ValueError,
        match="chunk_size must be greater than 0",
    ):
        split_text_into_chunks(
            "Example text.",
            chunk_size=0,
            chunk_overlap=0,
        )


def test_split_text_rejects_negative_overlap() -> None:
    with pytest.raises(
        ValueError,
        match="chunk_overlap must not be negative",
    ):
        split_text_into_chunks(
            "Example text.",
            chunk_size=100,
            chunk_overlap=-1,
        )