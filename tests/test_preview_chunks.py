import pytest

from scripts.preview_chunks import build_chunk_preview_lines, truncate_text


def test_truncate_text_returns_short_text_unchanged() -> None:
    text = "Short text."

    assert truncate_text(text, max_chars=50) == "Short text."


def test_truncate_text_collapses_whitespace() -> None:
    text = "First line.\n\nSecond    line."

    assert truncate_text(text, max_chars=100) == "First line. Second line."


def test_truncate_text_truncates_long_text() -> None:
    text = "abcdefghijklmnopqrstuvwxyz"

    assert truncate_text(text, max_chars=10) == "abcdefg..."


def test_truncate_text_rejects_invalid_max_chars() -> None:
    with pytest.raises(ValueError, match="max_chars must be greater than 0"):
        truncate_text("text", max_chars=0)


def test_build_chunk_preview_lines_reports_empty_directory(tmp_path) -> None:
    raw_docs_dir = tmp_path / "raw_docs"
    raw_docs_dir.mkdir()

    lines = build_chunk_preview_lines(raw_docs_dir)

    assert f"Raw docs directory: {raw_docs_dir}" in lines
    assert "Loaded documents: 0" in lines
    assert "Created chunks: 0" in lines
    assert "No supported documents found. Add .txt or .md files to the raw docs directory." in lines


def test_build_chunk_preview_lines_reports_loaded_documents_and_chunks(tmp_path) -> None:
    raw_docs_dir = tmp_path / "raw_docs"
    raw_docs_dir.mkdir()

    document_path = raw_docs_dir / "governance_notes.md"
    document_path.write_text(
        "# Governance Notes\n\nHuman review is required for high-impact decisions.",
        encoding="utf-8",
    )

    lines = build_chunk_preview_lines(
        raw_docs_dir,
        chunk_size=120,
        chunk_overlap=20,
        preview_chars=60,
    )

    joined_output = "\n".join(lines)

    assert "Loaded documents: 1" in lines
    assert "Created chunks: 1" in lines
    assert "Documents:" in lines
    assert "Chunks:" in lines
    assert "title: Governance Notes" in joined_output
    assert "source: governance_notes.md" in joined_output
    assert "preview: # Governance Notes Human review is required" in joined_output