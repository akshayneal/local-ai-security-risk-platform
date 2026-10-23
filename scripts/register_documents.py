from argparse import ArgumentParser, Namespace
from collections import defaultdict
from pathlib import Path

from app.chunker import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DocumentChunk,
    chunk_documents,
)
from app.document_loader import load_documents
from app.document_registry import (
    DEFAULT_REGISTRY_PATH,
    DocumentRegistry,
    RegistrationResult,
)


def register_raw_documents(
    raw_docs_dir: Path | str = "knowledge_base/raw_docs",
    registry_path: Path | str = DEFAULT_REGISTRY_PATH,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[RegistrationResult]:
    """Load, chunk, and register all supported raw documents."""

    documents = load_documents(raw_docs_dir)

    if not documents:
        return []

    chunks = chunk_documents(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks_by_version: dict[str, list[DocumentChunk]] = (
        defaultdict(list)
    )

    for chunk in chunks:
        chunks_by_version[
            chunk.document_version_id
        ].append(chunk)

    results: list[RegistrationResult] = []

    with DocumentRegistry(registry_path) as registry:
        for document in documents:
            document_chunks = chunks_by_version.get(
                document.document_version_id,
                [],
            )

            results.append(
                registry.register_chunked_document(
                    document,
                    document_chunks,
                )
            )

    return results


def build_registration_lines(
    results: list[RegistrationResult],
    registry_path: Path | str,
) -> list[str]:
    """Create readable terminal output for registration results."""

    lines = [
        f"Registry: {Path(registry_path)}",
        f"Processed documents: {len(results)}",
    ]

    if not results:
        lines.append(
            "No supported documents were found."
        )
        return lines

    lines.append("")

    for result in results:
        lines.extend(
            [
                f"- {result.document.document_id}",
                f"  decision: {result.decision.value}",
                (
                    "  version: "
                    f"{result.version.document_version_id}"
                ),
                (
                    "  version number: "
                    f"{result.version.version_number}"
                ),
                f"  source: {result.document.source_path}",
                f"  status: {result.version.status.value}",
                f"  chunks: {result.version.chunk_count}",
            ]
        )

    return lines


def parse_args() -> Namespace:
    """Parse command-line arguments."""

    parser = ArgumentParser(
        description=(
            "Load, chunk, and register local knowledge-base "
            "documents without embedding or indexing them."
        )
    )

    parser.add_argument(
        "raw_docs_dir",
        nargs="?",
        default="knowledge_base/raw_docs",
        help=(
            "Directory containing raw .txt, .md, "
            "and .pdf documents."
        ),
    )

    parser.add_argument(
        "--registry-path",
        default=str(DEFAULT_REGISTRY_PATH),
        help="Path to the generated SQLite registry.",
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
    )

    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
    )

    return parser.parse_args()


def main() -> None:
    """Run document registration from the command line."""

    args = parse_args()

    results = register_raw_documents(
        raw_docs_dir=args.raw_docs_dir,
        registry_path=args.registry_path,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    lines = build_registration_lines(
        results,
        registry_path=args.registry_path,
    )

    print("\n".join(lines))


if __name__ == "__main__":
    main()