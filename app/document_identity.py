from hashlib import sha256
from pathlib import Path


FILE_HASH_BLOCK_SIZE = 64 * 1024
SHA256_HEX_LENGTH = 64
VERSION_HASH_PREFIX_LENGTH = 12


def normalize_source_path(source_path: str) -> str:
    """Normalize a relative source path before using it as identity input."""

    normalized_path = source_path.strip().replace("\\", "/")

    if not normalized_path:
        raise ValueError("source_path must not be empty")

    return normalized_path


def build_document_id(source_path: str) -> str:
    """Create a stable logical document ID from its relative source path."""

    normalized_path = normalize_source_path(source_path)
    digest = sha256(normalized_path.encode("utf-8")).hexdigest()[:12]

    return f"doc_{digest}"


def calculate_file_sha256(
    path: Path | str,
    block_size: int = FILE_HASH_BLOCK_SIZE,
) -> str:
    """Calculate a SHA-256 digest without loading the entire file into memory."""

    file_path = Path(path)

    if block_size <= 0:
        raise ValueError("block_size must be greater than 0")

    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a regular file: {file_path}")

    digest = sha256()

    with file_path.open("rb") as file:
        while block := file.read(block_size):
            digest.update(block)

    return digest.hexdigest()


def is_valid_sha256_digest(content_hash: str) -> bool:
    """Return True when a value is a complete hexadecimal SHA-256 digest."""

    if len(content_hash) != SHA256_HEX_LENGTH:
        return False

    return all(character in "0123456789abcdefABCDEF" for character in content_hash)


def build_document_version_id(
    document_id: str,
    content_hash: str,
) -> str:
    """Combine logical document identity with a specific content version."""

    normalized_document_id = document_id.strip()

    if not normalized_document_id:
        raise ValueError("document_id must not be empty")

    if not is_valid_sha256_digest(content_hash):
        raise ValueError(
            "content_hash must be a complete hexadecimal SHA-256 digest"
        )

    hash_prefix = content_hash.lower()[:VERSION_HASH_PREFIX_LENGTH]

    return f"{normalized_document_id}_v_{hash_prefix}"