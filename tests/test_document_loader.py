import pytest

from app.document_loader import (
    LoadedDocument,
    build_document_id,
    build_document_title,
    load_documents,
    load_text_document,
    normalize_document_text,
)


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


def test_build_document_title_from_file_name(tmp_path) -> None:
    document_path = tmp_path / "nist-ai-rmf-notes.md"

    assert build_document_title(document_path) == "Nist Ai Rmf Notes"


def test_load_text_document_loads_markdown_file(tmp_path) -> None:
    raw_docs_dir = tmp_path / "raw_docs"
    raw_docs_dir.mkdir()

    document_path = raw_docs_dir / "ai_governance_notes.md"
    document_path.write_text("# AI Governance\n\nHuman review required.\n", encoding="utf-8")

    document = load_text_document(document_path, root_dir=raw_docs_dir)

    assert isinstance(document, LoadedDocument)
    assert document.source_path == "ai_governance_notes.md"
    assert document.title == "Ai Governance Notes"
    assert document.file_type == "md"
    assert document.text == "# AI Governance\n\nHuman review required."
    assert document.metadata["file_name"] == "ai_governance_notes.md"
    assert document.metadata["source_path"] == "ai_governance_notes.md"


def test_load_documents_loads_supported_files_only(tmp_path) -> None:
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


def test_load_documents_supports_nested_directories(tmp_path) -> None:
    raw_docs_dir = tmp_path / "raw_docs"
    nested_dir = raw_docs_dir / "nist"
    nested_dir.mkdir(parents=True)

    document_path = nested_dir / "ai_rmf.txt"
    document_path.write_text("Map, measure, manage, govern.", encoding="utf-8")

    documents = load_documents(raw_docs_dir)

    assert len(documents) == 1
    assert documents[0].source_path == "nist/ai_rmf.txt"


def test_load_text_document_rejects_unsupported_file_type(tmp_path) -> None:
    document_path = tmp_path / "data.csv"
    document_path.write_text("name,value", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported document type"):
        load_text_document(document_path)


def test_load_documents_rejects_missing_directory(tmp_path) -> None:
    missing_dir = tmp_path / "missing"

    with pytest.raises(FileNotFoundError, match="Raw documents directory does not exist"):
        load_documents(missing_dir)