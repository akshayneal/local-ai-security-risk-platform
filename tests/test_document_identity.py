from pathlib import Path

import pytest

from app.document_identity import (
    build_document_id,
    build_document_version_id,
    calculate_file_sha256,
    is_valid_sha256_digest,
    normalize_source_path,
)


def test_normalize_source_path_uses_forward_slashes() -> None:
    normalized_path = normalize_source_path(
        r"policies\access_control.md"
    )

    assert normalized_path == "policies/access_control.md"


def test_normalize_source_path_rejects_empty_value() -> None:
    with pytest.raises(ValueError, match="source_path must not be empty"):
        normalize_source_path("   ")


def test_build_document_id_is_stable() -> None:
    first_id = build_document_id("policies/access_control.md")
    second_id = build_document_id("policies/access_control.md")

    assert first_id == second_id
    assert first_id.startswith("doc_")


def test_build_document_id_normalizes_path_separators() -> None:
    windows_style_id = build_document_id(
        r"policies\access_control.md"
    )
    posix_style_id = build_document_id(
        "policies/access_control.md"
    )

    assert windows_style_id == posix_style_id


def test_calculate_file_sha256_is_stable(tmp_path: Path) -> None:
    document_path = tmp_path / "policy.md"
    document_path.write_text(
        "Human review is required.",
        encoding="utf-8",
    )

    first_hash = calculate_file_sha256(document_path)
    second_hash = calculate_file_sha256(document_path)

    assert first_hash == second_hash
    assert len(first_hash) == 64
    assert is_valid_sha256_digest(first_hash)


def test_calculate_file_sha256_changes_with_content(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "policy.md"
    document_path.write_text("Version one.", encoding="utf-8")

    first_hash = calculate_file_sha256(document_path)

    document_path.write_text("Version two.", encoding="utf-8")

    second_hash = calculate_file_sha256(document_path)

    assert first_hash != second_hash


def test_same_content_at_different_paths_has_same_hash(
    tmp_path: Path,
) -> None:
    first_path = tmp_path / "first.md"
    second_path = tmp_path / "second.md"

    first_path.write_text("Identical content.", encoding="utf-8")
    second_path.write_text("Identical content.", encoding="utf-8")

    assert calculate_file_sha256(first_path) == calculate_file_sha256(
        second_path
    )


def test_build_document_version_id_is_stable(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "policy.md"
    document_path.write_text("Policy content.", encoding="utf-8")

    document_id = build_document_id("policy.md")
    content_hash = calculate_file_sha256(document_path)

    first_version_id = build_document_version_id(
        document_id,
        content_hash,
    )
    second_version_id = build_document_version_id(
        document_id,
        content_hash,
    )

    assert first_version_id == second_version_id
    assert first_version_id.startswith(f"{document_id}_v_")


def test_build_document_version_id_changes_with_content(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "policy.md"
    document_id = build_document_id("policy.md")

    document_path.write_text("Version one.", encoding="utf-8")
    first_hash = calculate_file_sha256(document_path)
    first_version_id = build_document_version_id(
        document_id,
        first_hash,
    )

    document_path.write_text("Version two.", encoding="utf-8")
    second_hash = calculate_file_sha256(document_path)
    second_version_id = build_document_version_id(
        document_id,
        second_hash,
    )

    assert first_version_id != second_version_id


def test_build_document_version_id_rejects_invalid_hash() -> None:
    with pytest.raises(
        ValueError,
        match="complete hexadecimal SHA-256 digest",
    ):
        build_document_version_id(
            "doc_example",
            "not-a-valid-hash",
        )


def test_calculate_file_sha256_rejects_nonpositive_block_size(
    tmp_path: Path,
) -> None:
    document_path = tmp_path / "policy.md"
    document_path.write_text("Policy content.", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="block_size must be greater than 0",
    ):
        calculate_file_sha256(
            document_path,
            block_size=0,
        )