import json
import re
from pathlib import Path
from typing import Any


REFERENCE_DIR = Path("reference_material")

REFERENCE_FILES = {
    "soc_alert": [
        REFERENCE_DIR / "soc_references.json",
        REFERENCE_DIR / "local_checklists.json",
    ],
    "governance": [
        REFERENCE_DIR / "governance_references.json",
        REFERENCE_DIR / "local_checklists.json",
    ],
}


def normalize_text(text: str) -> list[str]:
    """
    Converts text into lowercase keyword tokens.

    Example:
    "SSH brute force login!" becomes:
    ["ssh", "brute", "force", "login"]
    """
    return re.findall(r"[a-zA-Z0-9_:-]+", text.lower())


def load_reference_file(path: Path) -> list[dict[str, Any]]:
    """
    Loads one JSON reference file.

    If the file does not exist, return an empty list instead of crashing.
    """
    if not path.exists():
        return []

    return json.loads(path.read_text(encoding="utf-8"))


def load_references(mode: str) -> list[dict[str, Any]]:
    """
    Loads all reference cards for a workflow mode.

    Supported modes:
    - soc_alert
    - governance
    """
    paths = REFERENCE_FILES.get(mode, [])

    references: list[dict[str, Any]] = []

    for path in paths:
        references.extend(load_reference_file(path))

    return references


def score_reference(query_tokens: set[str], reference: dict[str, Any]) -> int:
    """
    Scores a reference card based on overlap with the user request.

    Higher score means the card is more likely to be relevant.
    """
    title = reference.get("title", "")
    framework = reference.get("framework", "")
    reference_type = reference.get("reference_type", "")
    tags = " ".join(reference.get("tags", []))
    content = reference.get("content", "")

    searchable_text = f"{title} {framework} {reference_type} {tags} {content}"
    reference_tokens = set(normalize_text(searchable_text))

    overlap_score = len(query_tokens.intersection(reference_tokens))

    tag_bonus = 0
    for tag in reference.get("tags", []):
        tag_tokens = set(normalize_text(tag))

        if tag_tokens and tag_tokens.issubset(query_tokens):
            tag_bonus += 3

    return overlap_score + tag_bonus


def get_relevant_references(
    mode: str,
    query: str,
    limit: int = 4,
) -> list[dict[str, Any]]:
    """
    Returns the most relevant local references for a given workflow.

    This is simple keyword/tag retrieval, not vector RAG.
    """
    references = load_references(mode)
    query_tokens = set(normalize_text(query))

    scored_references = []

    for reference in references:
        score = score_reference(query_tokens, reference)

        if score > 0:
            scored_references.append((score, reference))

    scored_references.sort(key=lambda item: item[0], reverse=True)

    return [reference for score, reference in scored_references[:limit]]


def format_references_for_prompt(references: list[dict[str, Any]]) -> str:
    """
    Converts retrieved reference cards into prompt-friendly text.
    """
    if not references:
        return "No local references were retrieved for this request."

    formatted_blocks = []

    for reference in references:
        block = (
            f"Source ID: {reference.get('source_id')}\n"
            f"Title: {reference.get('title')}\n"
            f"Framework: {reference.get('framework')}\n"
            f"Type: {reference.get('reference_type')}\n"
            f"Content: {reference.get('content')}"
        )

        formatted_blocks.append(block)

    return "\n\n---\n\n".join(formatted_blocks)