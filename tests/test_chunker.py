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
from app.document_loader import LoadedDocument


def make_loaded_document(text: str, document_id: str = "doc_test") -> LoadedDocument:
    return LoadedDocument(
        document_id=document_id,
        source_path="example.md",
        title="Example",
        file_type="md",
        text=text,
        metadata={"file_name": "example.md", "source_path": "example.md"},
    )


def test_split_text_by_paragraphs_removes_empty_paragraphs() -> None:
    text = "First paragraph.\n\n\nSecond paragraph.\n\n   \nThird paragraph."

    paragraphs = split_text_by_paragraphs(text)

    assert paragraphs == [
        "First paragraph.",
        "Second paragraph.",
        "Third paragraph.",
    ]


def test_split_large_text_window_uses_overlap() -> None:
    text = "abcdefghijklmnopqrstuvwxyz"

    chunks = split_large_text_window(text, chunk_size=10, chunk_overlap=3)

    assert chunks == [
        "abcdefghij",
        "hijklmnopq",
        "opqrstuvwx",
        "vwxyz",
    ]


def test_split_text_into_chunks_preserves_short_text() -> None:
    text = "Short paragraph.\n\nAnother short paragraph."

    chunks = split_text_into_chunks(text, chunk_size=100, chunk_overlap=20)

    assert chunks == ["Short paragraph.\n\nAnother short paragraph."]


def test_split_text_into_chunks_splits_on_paragraph_boundaries() -> None:
    text = "A" * 40 + "\n\n" + "B" * 40 + "\n\n" + "C" * 40

    chunks = split_text_into_chunks(text, chunk_size=85, chunk_overlap=10)

    assert len(chunks) == 2
    assert chunks[0] == "A" * 40 + "\n\n" + "B" * 40
    assert chunks[1].endswith("C" * 40)


def test_split_text_into_chunks_splits_large_paragraph_with_windowing() -> None:
    text = "a" * 25

    chunks = split_text_into_chunks(text, chunk_size=10, chunk_overlap=2)

    assert chunks == [
        "a" * 10,
        "a" * 10,
        "a" * 9,
    ]


def test_split_text_into_chunks_rejects_invalid_chunk_size() -> None:
    with pytest.raises(ValueError, match="chunk_size must be greater than 0"):
        split_text_into_chunks("text", chunk_size=0)


def test_split_text_into_chunks_rejects_negative_overlap() -> None:
    with pytest.raises(ValueError, match="chunk_overlap cannot be negative"):
        split_text_into_chunks("text", chunk_size=100, chunk_overlap=-1)


def test_split_text_into_chunks_rejects_overlap_larger_than_chunk_size() -> None:
    with pytest.raises(ValueError, match="chunk_overlap must be smaller than chunk_size"):
        split_text_into_chunks("text", chunk_size=100, chunk_overlap=100)


def test_build_chunk_id_is_stable_and_padded() -> None:
    chunk_id = build_chunk_id("doc_abc123", 7)

    assert chunk_id == "doc_abc123_chunk_0007"


def test_build_chunk_id_rejects_negative_index() -> None:
    with pytest.raises(ValueError, match="chunk_index cannot be negative"):
        build_chunk_id("doc_abc123", -1)


def test_chunk_document_creates_document_chunks() -> None:
    document = make_loaded_document("First paragraph.\n\nSecond paragraph.")

    chunks = chunk_document(document, chunk_size=100, chunk_overlap=20)

    assert len(chunks) == 1
    assert isinstance(chunks[0], DocumentChunk)
    assert chunks[0].chunk_id == "doc_test_chunk_0000"
    assert chunks[0].document_id == "doc_test"
    assert chunks[0].source_path == "example.md"
    assert chunks[0].title == "Example"
    assert chunks[0].chunk_index == 0
    assert chunks[0].text == "First paragraph.\n\nSecond paragraph."
    assert chunks[0].metadata["document_id"] == "doc_test"
    assert chunks[0].metadata["chunk_id"] == "doc_test_chunk_0000"
    assert chunks[0].metadata["chunk_index"] == "0"


def test_chunk_document_returns_empty_list_for_empty_document() -> None:
    document = make_loaded_document("   ")

    chunks = chunk_document(document)

    assert chunks == []


def test_chunk_documents_combines_chunks_from_multiple_documents() -> None:
    first_document = make_loaded_document("First document.", document_id="doc_first")
    second_document = make_loaded_document("Second document.", document_id="doc_second")

    chunks = chunk_documents([first_document, second_document])

    assert len(chunks) == 2
    assert {chunk.document_id for chunk in chunks} == {"doc_first", "doc_second"}