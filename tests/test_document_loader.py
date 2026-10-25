from pathlib import Path
from typing import ClassVar

import pytest

from app.document_limits import DocumentLimits
from app.document_loader import (
    LoadedDocument,
    build_document_id,
    build_document_title,
    load_document,
    load_documents,
    load_pdf_document,
    load_text_document,
    normalize_document_text,
)


class FakePdfPage:
    def __init__(self, text: str) -> None:
        self.text = text

    def extract_text(self) -> str:
        return self.text


class FakePdfReader:
    pages_to_return: ClassVar[list[FakePdfPage]] = [
        FakePdfPage("First PDF page."),
        FakePdfPage("Second PDF page."),
    ]
    encrypted = False

    def __init__(self, _path: Path, strict: bool = False) -> None:
        self.pages = self.pages_to_return
        self.is_encrypted = self.encrypted
        self.strict = strict


def test_normalize_document_text_removes_extra_blank_lines() -> None:
    raw_text = "Line one\r\n\r\n\r\nLine two  \n\nLine three\n"
    normalized_text = normalize_document_text(raw_text)

    assert normalized_text == "Line one\n\nLine two\n\nLine three"


def test_build_document_id_is_stable() -> None:
    source_path = "policy/example.md"

    first_id = build_document_id(source_path)
    second_id = build_document_id(source_path)

    assert first_id == second_id
    assert first_id.startswith("doc_")


def test_build_document_title_from_file_name(tmp_path: Path) -> None:
    document_path = tmp_path / "nist-ai-rmf-notes.md"

    assert build_document_title(document_path) == "Nist Ai Rmf Notes"


def test_load_text_document_loads_markdown_file(tmp_path: Path) -> None:
    raw_docs_dir = tmp_path / "raw_docs"
    raw_docs_dir.mkdir()

    document_path = raw_docs_dir / "ai_governance_notes.md"
    document_path.write_text(
        "# AI Governance\n\nHuman review required.\n",
        encoding="utf-8",
    )

    document = load_text_document(
        document_path,
        root_dir=raw_docs_dir,
    )

    assert isinstance(document, LoadedDocument)
    assert document.source_path == "ai_governance_notes.md"
    assert document.title == "Ai Governance Notes"
    assert document.file_type == "md"
    assert document.text == "# AI Governance\n\nHuman review required."
    assert document.metadata["file_name"] == "ai_governance_notes.md"
    assert document.metadata["source_path"] == "ai_governance_notes.md"
    assert document.metadata["extraction_method"] == "utf-8"
    assert len(document.content_hash) == 64
    assert document.document_version_id.startswith(
        f"{document.document_id}_v_"
    )
    assert (
        document.metadata["content_hash"]
        == document.content_hash
    )
    assert (
        document.metadata["document_version_id"]
        == document.document_version_id
    )

def test_load_documents_loads_supported_files_only(tmp_path: Path) -> None:
    raw_docs_dir = tmp_path / "raw_docs"
    raw_docs_dir.mkdir()

    markdown_path = raw_docs_dir / "governance.md"
    text_path = raw_docs_dir / "soc_notes.txt"
    unsupported_path = raw_docs_dir / "spreadsheet.csv"

    markdown_path.write_text("Governance content", encoding="utf-8")
    text_path.write_text("SOC content", encoding="utf-8")
    unsupported_path.write_text("name,value", encoding="utf-8")

    documents = load_documents(raw_docs_dir)

    assert len(documents) == 2
    assert {document.file_type for document in documents} == {"md", "txt"}
    assert {document.source_path for document in documents} == {
        "governance.md",
        "soc_notes.txt",
    }


def test_load_documents_supports_nested_directories(tmp_path: Path) -> None:
    raw_docs_dir = tmp_path / "raw_docs"
    nested_dir = raw_docs_dir / "nist"
    nested_dir.mkdir(parents=True)

    document_path = nested_dir / "ai_rmf.txt"
    document_path.write_text(
        "Map, measure, manage, govern.",
        encoding="utf-8",
    )

    documents = load_documents(raw_docs_dir)

    assert len(documents) == 1
    assert documents[0].source_path == "nist/ai_rmf.txt"


def test_load_documents_loads_pdf_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_docs_dir = tmp_path / "raw_docs"
    raw_docs_dir.mkdir()

    pdf_path = raw_docs_dir / "incident_response.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\nfake test content")

    monkeypatch.setattr(
        "app.document_loader.PdfReader",
        FakePdfReader,
    )

    documents = load_documents(raw_docs_dir)

    assert len(documents) == 1
    assert documents[0].file_type == "pdf"
    assert documents[0].source_path == "incident_response.pdf"


def test_load_document_dispatches_text_file(tmp_path: Path) -> None:
    raw_docs_dir = tmp_path / "raw_docs"
    raw_docs_dir.mkdir()

    document_path = raw_docs_dir / "notes.txt"
    document_path.write_text("SOC notes.", encoding="utf-8")

    document = load_document(
        document_path,
        root_dir=raw_docs_dir,
    )

    assert document.file_type == "txt"
    assert document.text == "SOC notes."


def test_load_text_document_rejects_unsupported_file_type(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "data.csv"
    document_path.write_text("name,value", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported document type"):
        load_text_document(document_path)


def test_load_documents_rejects_missing_directory(tmp_path: Path) -> None:
    missing_dir = tmp_path / "missing"

    with pytest.raises(
        FileNotFoundError,
        match="Raw documents directory does not exist",
    ):
        load_documents(missing_dir)


def test_load_text_document_rejects_empty_file(tmp_path: Path) -> None:
    document_path = tmp_path / "empty.md"
    document_path.touch()

    with pytest.raises(ValueError, match="Document is empty"):
        load_text_document(document_path)


def test_load_text_document_rejects_oversized_file(tmp_path: Path) -> None:
    document_path = tmp_path / "large.txt"
    document_path.write_text("123456", encoding="utf-8")

    limits = DocumentLimits(
        max_file_size_bytes=5,
        max_pdf_pages=10,
        max_extracted_characters=100,
        max_chunks_per_document=10,
    )

    with pytest.raises(
        ValueError,
        match="Document exceeds the maximum file size",
    ):
        load_text_document(document_path, limits=limits)


def test_load_text_document_rejects_excessive_extracted_text(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "large_text.md"
    document_path.write_text("abcdef", encoding="utf-8")

    limits = DocumentLimits(
        max_file_size_bytes=100,
        max_pdf_pages=10,
        max_extracted_characters=5,
        max_chunks_per_document=10,
    )

    with pytest.raises(
        ValueError,
        match="Extracted document text exceeds the configured limit",
    ):
        load_text_document(document_path, limits=limits)


def test_load_text_document_rejects_path_outside_root(
    tmp_path: Path,
) -> None:
    raw_docs_dir = tmp_path / "raw_docs"
    raw_docs_dir.mkdir()

    outside_path = tmp_path / "outside.md"
    outside_path.write_text("Outside content.", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="inside the raw document directory",
    ):
        load_text_document(
            outside_path,
            root_dir=raw_docs_dir,
        )


def test_load_pdf_document_extracts_pages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_docs_dir = tmp_path / "raw_docs"
    raw_docs_dir.mkdir()

    pdf_path = raw_docs_dir / "incident_response.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\nfake test content")

    monkeypatch.setattr(
        "app.document_loader.PdfReader",
        FakePdfReader,
    )

    document = load_pdf_document(
        pdf_path,
        root_dir=raw_docs_dir,
    )

    assert document.file_type == "pdf"
    assert document.source_path == "incident_response.pdf"
    assert document.metadata["page_count"] == "2"
    assert document.metadata["extraction_method"] == "pypdf"
    assert document.text == (
        "[Page 1]\nFirst PDF page.\n\n"
        "[Page 2]\nSecond PDF page."
    )


def test_load_pdf_document_rejects_missing_signature(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "fake.pdf"
    pdf_path.write_bytes(b"This is not really a PDF.")

    with pytest.raises(ValueError, match="PDF signature is missing"):
        load_pdf_document(pdf_path)


def test_load_pdf_document_rejects_signature_after_scan_limit(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "late_signature.pdf"
    pdf_path.write_bytes(b"x" * 1_024 + b"%PDF-1.7")

    with pytest.raises(ValueError, match="PDF signature is missing"):
        load_pdf_document(pdf_path)


def test_load_pdf_document_rejects_encrypted_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_path = tmp_path / "encrypted.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\nfake encrypted content")

    class EncryptedFakePdfReader(FakePdfReader):
        encrypted = True

    monkeypatch.setattr(
        "app.document_loader.PdfReader",
        EncryptedFakePdfReader,
    )

    with pytest.raises(
        ValueError,
        match="Encrypted PDF documents are not supported",
    ):
        load_pdf_document(pdf_path)


def test_load_pdf_document_rejects_excessive_page_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_path = tmp_path / "large.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\nfake large content")

    class LargeFakePdfReader(FakePdfReader):
        pages_to_return: ClassVar[list[FakePdfPage]] = [
            FakePdfPage("Page one."),
            FakePdfPage("Page two."),
        ]

    monkeypatch.setattr(
        "app.document_loader.PdfReader",
        LargeFakePdfReader,
    )

    limits = DocumentLimits(
        max_file_size_bytes=1_000,
        max_pdf_pages=1,
        max_extracted_characters=1_000,
        max_chunks_per_document=10,
    )

    with pytest.raises(
        ValueError,
        match="PDF exceeds the maximum page count",
    ):
        load_pdf_document(pdf_path, limits=limits)


def test_document_limits_reject_nonpositive_values() -> None:
    with pytest.raises(
        ValueError,
        match="max_pdf_pages must be greater than 0",
    ):
        DocumentLimits(max_pdf_pages=0)

def test_same_content_at_different_paths_has_different_document_ids(
    tmp_path: Path,
) -> None:
    raw_docs_dir = tmp_path / "raw_docs"
    raw_docs_dir.mkdir()

    first_path = raw_docs_dir / "first.md"
    second_path = raw_docs_dir / "second.md"

    first_path.write_text("Identical content.", encoding="utf-8")
    second_path.write_text("Identical content.", encoding="utf-8")

    first_document = load_text_document(
        first_path,
        root_dir=raw_docs_dir,
    )
    second_document = load_text_document(
        second_path,
        root_dir=raw_docs_dir,
    )

    assert first_document.document_id != second_document.document_id
    assert first_document.content_hash == second_document.content_hash
    assert (
        first_document.document_version_id
        != second_document.document_version_id
    )


def test_changed_content_preserves_document_id_but_changes_version(
    tmp_path: Path,
) -> None:
    raw_docs_dir = tmp_path / "raw_docs"
    raw_docs_dir.mkdir()

    document_path = raw_docs_dir / "policy.md"
    document_path.write_text("Version one.", encoding="utf-8")

    first_document = load_text_document(
        document_path,
        root_dir=raw_docs_dir,
    )

    document_path.write_text("Version two.", encoding="utf-8")

    second_document = load_text_document(
        document_path,
        root_dir=raw_docs_dir,
    )

    assert first_document.document_id == second_document.document_id
    assert first_document.content_hash != second_document.content_hash
    assert (
        first_document.document_version_id
        != second_document.document_version_id
    )
