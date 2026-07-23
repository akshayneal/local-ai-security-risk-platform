from argparse import ArgumentParser, Namespace
from pathlib import Path

from app.chunker import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, chunk_documents
from app.document_loader import load_documents


DEFAULT_PREVIEW_CHARS = 180


def truncate_text(text: str, max_chars: int = DEFAULT_PREVIEW_CHARS) -> str:
    """Return a single-line preview of text capped at max_chars."""

    if max_chars <= 0:
        raise ValueError("max_chars must be greater than 0")

    cleaned_text = " ".join(text.split())

    if len(cleaned_text) <= max_chars:
        return cleaned_text

    if max_chars <= 3:
        return cleaned_text[:max_chars]

    return f"{cleaned_text[: max_chars - 3].rstrip()}..."


def build_chunk_preview_lines(
    raw_docs_dir: Path | str = "knowledge_base/raw_docs",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    preview_chars: int = DEFAULT_PREVIEW_CHARS,
) -> list[str]:
    """Build readable preview lines for loaded documents and chunks."""

    raw_docs_path = Path(raw_docs_dir)
    documents = load_documents(raw_docs_path)
    chunks = chunk_documents(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    lines = [
        f"Raw docs directory: {raw_docs_path}",
        f"Loaded documents: {len(documents)}",
        f"Created chunks: {len(chunks)}",
    ]

    if not documents:
        lines.append("No supported documents found. Add .txt or .md files to the raw docs directory.")
        return lines

    lines.append("")
    lines.append("Documents:")

    for document in documents:
        lines.append(f"- {document.document_id}")
        lines.append(f"  title: {document.title}")
        lines.append(f"  source: {document.source_path}")
        lines.append(f"  type: {document.file_type}")
        lines.append(f"  chars: {len(document.text)}")

    if chunks:
        lines.append("")
        lines.append("Chunks:")

    for chunk in chunks:
        lines.append(f"- {chunk.chunk_id}")
        lines.append(f"  source: {chunk.source_path}")
        lines.append(f"  title: {chunk.title}")
        lines.append(f"  index: {chunk.chunk_index}")
        lines.append(f"  chars: {len(chunk.text)}")
        lines.append(f"  preview: {truncate_text(chunk.text, preview_chars)}")

    return lines


def parse_args() -> Namespace:
    """Parse command-line arguments for the chunk preview script."""

    parser = ArgumentParser(
        description="Preview loaded documents and generated chunks from the local knowledge base."
    )

    parser.add_argument(
        "raw_docs_dir",
        nargs="?",
        default="knowledge_base/raw_docs",
        help="Directory containing raw .txt and .md documents.",
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Maximum target chunk size in characters. Default: {DEFAULT_CHUNK_SIZE}.",
    )

    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help=f"Chunk overlap in characters. Default: {DEFAULT_CHUNK_OVERLAP}.",
    )

    parser.add_argument(
        "--preview-chars",
        type=int,
        default=DEFAULT_PREVIEW_CHARS,
        help=f"Maximum preview length per chunk. Default: {DEFAULT_PREVIEW_CHARS}.",
    )

    return parser.parse_args()


def main() -> None:
    """Run the chunk preview script."""

    args = parse_args()
    lines = build_chunk_preview_lines(
        raw_docs_dir=args.raw_docs_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        preview_chars=args.preview_chars,
    )

    for line in lines:
        print(line)


if __name__ == "__main__":
    main()