from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path


SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md"}


@dataclass(frozen=True)
class LoadedDocument:
    """Represents one local source document loaded from the knowledge base."""

    document_id: str
    source_path: str
    title: str
    file_type: str
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


def is_supported_document(path: Path) -> bool:
    """Return True when the file extension is supported by the loader."""

    return path.is_file() and path.suffix.lower() in SUPPORTED_TEXT_EXTENSIONS


def normalize_document_text(text: str) -> str:
    """Normalize document text while preserving basic paragraph structure."""

    normalized_newlines = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized_newlines.split("\n")

    cleaned_lines: list[str] = []
    previous_line_blank = False

    for line in lines:
        cleaned_line = line.rstrip()
        current_line_blank = cleaned_line.strip() == ""

        if current_line_blank:
            if not previous_line_blank:
                cleaned_lines.append("")
            previous_line_blank = True
            continue

        cleaned_lines.append(cleaned_line)
        previous_line_blank = False

    return "\n".join(cleaned_lines).strip()


def get_relative_source_path(path: Path, root_dir: Path) -> str:
    """Return a stable relative source path when possible."""

    resolved_path = path.resolve()
    resolved_root = root_dir.resolve()

    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError:
        return resolved_path.as_posix()


def build_document_id(source_path: str) -> str:
    """Create a stable document ID from the document source path."""

    digest = sha256(source_path.encode("utf-8")).hexdigest()[:12]
    return f"doc_{digest}"


def build_document_title(path: Path) -> str:
    """Create a readable document title from the file name."""

    return path.stem.replace("_", " ").replace("-", " ").strip().title()


def load_text_document(path: Path | str, root_dir: Path | str | None = None) -> LoadedDocument:
    """Load a supported text-like document from disk."""

    document_path = Path(path)

    if not document_path.exists():
        raise FileNotFoundError(f"Document does not exist: {document_path}")

    if not document_path.is_file():
        raise ValueError(f"Document path is not a file: {document_path}")

    if document_path.suffix.lower() not in SUPPORTED_TEXT_EXTENSIONS:
        raise ValueError(f"Unsupported document type: {document_path.suffix}")

    root_path = Path(root_dir) if root_dir is not None else document_path.parent
    source_path = get_relative_source_path(document_path, root_path)

    raw_text = document_path.read_text(encoding="utf-8")
    normalized_text = normalize_document_text(raw_text)

    return LoadedDocument(
        document_id=build_document_id(source_path),
        source_path=source_path,
        title=build_document_title(document_path),
        file_type=document_path.suffix.lower().lstrip("."),
        text=normalized_text,
        metadata={
            "file_name": document_path.name,
            "source_path": source_path,
        },
    )


def load_documents(raw_docs_dir: Path | str = "knowledge_base/raw_docs") -> list[LoadedDocument]:
    """Load all supported documents from a raw document directory."""

    raw_docs_path = Path(raw_docs_dir)

    if not raw_docs_path.exists():
        raise FileNotFoundError(f"Raw documents directory does not exist: {raw_docs_path}")

    if not raw_docs_path.is_dir():
        raise ValueError(f"Raw documents path is not a directory: {raw_docs_path}")

    documents: list[LoadedDocument] = []

    for path in sorted(raw_docs_path.rglob("*")):
        if is_supported_document(path):
            documents.append(load_text_document(path, root_dir=raw_docs_path))

    return documents