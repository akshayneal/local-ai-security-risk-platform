from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentLimits:
    """Security and resource limits for local document processing."""

    max_file_size_bytes: int = 10 * 1024 * 1024
    max_pdf_pages: int = 100
    max_extracted_characters: int = 500_000
    max_chunks_per_document: int = 750

    def __post_init__(self) -> None:
        """Validate that every configured limit is positive."""

        values = {
            "max_file_size_bytes": self.max_file_size_bytes,
            "max_pdf_pages": self.max_pdf_pages,
            "max_extracted_characters": self.max_extracted_characters,
            "max_chunks_per_document": self.max_chunks_per_document,
        }

        for name, value in values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than 0")


DEFAULT_DOCUMENT_LIMITS = DocumentLimits()