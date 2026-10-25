from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.document_identity import (
    build_document_id,
    build_document_version_id,
    calculate_file_sha256,
)
from app.document_limits import DEFAULT_DOCUMENT_LIMITS, DocumentLimits

SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md"}
SUPPORTED_DOCUMENT_EXTENSIONS = SUPPORTED_TEXT_EXTENSIONS | {".pdf"}

PDF_SIGNATURE = b"%PDF-"
PDF_SIGNATURE_SCAN_BYTES = 1_024


@dataclass(frozen=True)
class LoadedDocument:
    """Represents one local source document loaded from the knowledge base."""

    document_id: str
    document_version_id: str
    content_hash: str
    source_path: str
    title: str
    file_type: str
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


def is_supported_document(path: Path) -> bool:
    """Return True when a regular file has a supported extension."""

    return (
        path.is_file()
        and not path.is_symlink()
        and path.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS
    )


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


def validate_document_path(
    path: Path,
    root_dir: Path,
    limits: DocumentLimits,
) -> tuple[Path, Path]:
    """Validate a document path before opening or parsing the file."""

    if not path.exists():
        raise FileNotFoundError(f"Document does not exist: {path}")

    if path.is_symlink():
        raise ValueError(f"Symbolic links are not supported: {path}")

    if not path.is_file():
        raise ValueError(f"Document path is not a file: {path}")

    if path.suffix.lower() not in SUPPORTED_DOCUMENT_EXTENSIONS:
        raise ValueError(f"Unsupported document type: {path.suffix}")

    file_size = path.stat().st_size

    if file_size == 0:
        raise ValueError(f"Document is empty: {path}")

    if file_size > limits.max_file_size_bytes:
        raise ValueError(
            "Document exceeds the maximum file size: "
            f"{file_size} bytes > {limits.max_file_size_bytes} bytes"
        )

    resolved_path = path.resolve()
    resolved_root = root_dir.resolve()

    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(
            f"Document must be inside the raw document directory: {resolved_root}"
        ) from exc

    return resolved_path, resolved_root


def get_relative_source_path(path: Path, root_dir: Path) -> str:
    """Return a stable path relative to the approved raw document directory."""

    try:
        return path.relative_to(root_dir).as_posix()
    except ValueError as exc:
        raise ValueError(
            f"Document path is outside the approved root directory: {path}"
        ) from exc


def build_document_title(path: Path) -> str:
    """Create a readable document title from the file name."""

    return path.stem.replace("_", " ").replace("-", " ").strip().title()


def validate_extracted_text(
    text: str,
    path: Path,
    limits: DocumentLimits,
) -> str:
    """Normalize extracted text and enforce content limits."""

    normalized_text = normalize_document_text(text)

    if not normalized_text:
        raise ValueError(
            "Document did not contain extractable text. "
            f"Scanned or image-only files are not currently supported: {path}"
        )

    if len(normalized_text) > limits.max_extracted_characters:
        raise ValueError(
            "Extracted document text exceeds the configured limit: "
            f"{len(normalized_text)} characters > "
            f"{limits.max_extracted_characters} characters"
        )

    return normalized_text


def has_pdf_signature(path: Path) -> bool:
    """Return True when the PDF signature appears near the start of the file."""

    with path.open("rb") as file:
        initial_bytes = file.read(PDF_SIGNATURE_SCAN_BYTES)

    return PDF_SIGNATURE in initial_bytes


def create_loaded_document(
    resolved_path: Path,
    resolved_root: Path,
    file_type: str,
    text: str,
    extraction_method: str,
    additional_metadata: dict[str, str] | None = None,
) -> LoadedDocument:
    """Create a loaded document with source and content identity."""

    source_path = get_relative_source_path(
        resolved_path,
        resolved_root,
    )
    document_id = build_document_id(source_path)
    content_hash = calculate_file_sha256(resolved_path)
    document_version_id = build_document_version_id(
        document_id,
        content_hash,
    )

    metadata = {
        "file_name": resolved_path.name,
        "source_path": source_path,
        "file_size_bytes": str(resolved_path.stat().st_size),
        "extraction_method": extraction_method,
        "content_hash": content_hash,
        "document_version_id": document_version_id,
    }

    if additional_metadata:
        metadata.update(additional_metadata)

    return LoadedDocument(
        document_id=document_id,
        document_version_id=document_version_id,
        content_hash=content_hash,
        source_path=source_path,
        title=build_document_title(resolved_path),
        file_type=file_type,
        text=text,
        metadata=metadata,
    )


def load_text_document(
    path: Path | str,
    root_dir: Path | str | None = None,
    limits: DocumentLimits = DEFAULT_DOCUMENT_LIMITS,
) -> LoadedDocument:
    """Load a supported UTF-8 text or Markdown document."""

    document_path = Path(path)
    root_path = Path(root_dir) if root_dir is not None else document_path.parent

    resolved_path, resolved_root = validate_document_path(
        document_path,
        root_path,
        limits,
    )

    if resolved_path.suffix.lower() not in SUPPORTED_TEXT_EXTENSIONS:
        raise ValueError(f"Unsupported text document type: {resolved_path.suffix}")

    try:
        raw_text = resolved_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"Text document must use UTF-8 encoding: {resolved_path}"
        ) from exc

    normalized_text = validate_extracted_text(
        raw_text,
        resolved_path,
        limits,
    )

    return create_loaded_document(
        resolved_path=resolved_path,
        resolved_root=resolved_root,
        file_type=resolved_path.suffix.lower().lstrip("."),
        text=normalized_text,
        extraction_method="utf-8",
    )


def load_pdf_document(
    path: Path | str,
    root_dir: Path | str | None = None,
    limits: DocumentLimits = DEFAULT_DOCUMENT_LIMITS,
) -> LoadedDocument:
    """Load text from a supported, non-encrypted PDF document."""

    document_path = Path(path)
    root_path = Path(root_dir) if root_dir is not None else document_path.parent

    resolved_path, resolved_root = validate_document_path(
        document_path,
        root_path,
        limits,
    )

    if resolved_path.suffix.lower() != ".pdf":
        raise ValueError(f"Unsupported PDF document type: {resolved_path.suffix}")

    if not has_pdf_signature(resolved_path):
        raise ValueError(
            f"File extension is .pdf but the PDF signature is missing: {resolved_path}"
        )

    try:
        reader = PdfReader(resolved_path, strict=False)
    except (OSError, PdfReadError, ValueError) as exc:
        raise ValueError(f"Unable to read PDF document: {resolved_path}") from exc

    if reader.is_encrypted:
        raise ValueError(f"Encrypted PDF documents are not supported: {resolved_path}")

    page_count = len(reader.pages)

    if page_count == 0:
        raise ValueError(f"PDF document does not contain any pages: {resolved_path}")

    if page_count > limits.max_pdf_pages:
        raise ValueError(
            "PDF exceeds the maximum page count: "
            f"{page_count} pages > {limits.max_pdf_pages} pages"
        )

    page_sections: list[str] = []

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except (KeyError, PdfReadError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Unable to extract text from PDF page {page_number}: {resolved_path}"
            ) from exc

        cleaned_page_text = normalize_document_text(page_text)

        if cleaned_page_text:
            page_sections.append(
                f"[Page {page_number}]\n{cleaned_page_text}"
            )

    combined_text = "\n\n".join(page_sections)
    normalized_text = validate_extracted_text(
        combined_text,
        resolved_path,
        limits,
    )

    return create_loaded_document(
        resolved_path=resolved_path,
        resolved_root=resolved_root,
        file_type="pdf",
        text=normalized_text,
        extraction_method="pypdf",
        additional_metadata={
            "page_count": str(page_count),
        },
    )


def load_document(
    path: Path | str,
    root_dir: Path | str | None = None,
    limits: DocumentLimits = DEFAULT_DOCUMENT_LIMITS,
) -> LoadedDocument:
    """Load one supported document using the appropriate file-type loader."""

    document_path = Path(path)
    extension = document_path.suffix.lower()

    if extension in SUPPORTED_TEXT_EXTENSIONS:
        return load_text_document(
            document_path,
            root_dir=root_dir,
            limits=limits,
        )

    if extension == ".pdf":
        return load_pdf_document(
            document_path,
            root_dir=root_dir,
            limits=limits,
        )

    raise ValueError(f"Unsupported document type: {extension}")


def load_documents(
    raw_docs_dir: Path | str = "knowledge_base/raw_docs",
    limits: DocumentLimits = DEFAULT_DOCUMENT_LIMITS,
) -> list[LoadedDocument]:
    """Load all supported documents from the raw document directory."""

    raw_docs_path = Path(raw_docs_dir)

    if not raw_docs_path.exists():
        raise FileNotFoundError(
            f"Raw documents directory does not exist: {raw_docs_path}"
        )

    if not raw_docs_path.is_dir():
        raise ValueError(
            f"Raw documents path is not a directory: {raw_docs_path}"
        )

    documents: list[LoadedDocument] = []

    for path in sorted(raw_docs_path.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Symbolic links are not supported: {path}")

        if is_supported_document(path):
            documents.append(
                load_document(
                    path,
                    root_dir=raw_docs_path,
                    limits=limits,
                )
            )

    return documents