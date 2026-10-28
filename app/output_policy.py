"""Deterministic response policies, separate from prompt guidance and citations."""

import re
from typing import Any

from app.observables import observable_violations

# Context is required. Generic punctuation is not evidence of a reference ID.
SOURCE_CONTEXT = re.compile(
    r"\b(?P<label>source[_ ]id|reference[_ ]id|feed[_ ]id|"
    r"(?:source|reference|feed)\s+(?:named|called|identifier)|"
    r"cite|citing|cites|references|source|reference|feed|per)\b"
    r"\s*[:=]?\s*[`\"']?(?P<identifier>[A-Za-z][A-Za-z0-9_.:@/\\-]*)",
    re.IGNORECASE,
)


class OutputPolicyError(RuntimeError):
    """SOC contract still invalid after the single authorized repair attempt."""

    def __init__(self, violations: list[str]) -> None:
        # Machine descriptions only: no raw output, hostile spans, or indicators.
        super().__init__("OutputPolicyError: " + "; ".join(violations))


def text_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in text_values(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in text_values(item)]
    return []


def untrusted_source_ids(
    original_input: dict[str, Any], approved: set[str]
) -> set[str]:
    """Extract narrowly contextual IDs, never infer sources from observables/hosts.

    Unlabelled citations need uppercase multi-part source syntax. Explicit source-ID
    labels also support lowercase IDs. Domains, hashes, CVEs, IPs, user paths, and
    ordinary lowercase hosts are excluded. Ambiguous/unrecognized names may escape.
    """
    candidates = set()
    for text in text_values(original_input):
        for match in SOURCE_CONTEXT.finditer(text):
            identifier = match["identifier"].rstrip(".")
            if re.fullmatch(r"CVE-\d{4}-\d{4,}", identifier, re.IGNORECASE):
                continue
            if any(char in identifier for char in ".:@/\\"):
                continue
            explicit = bool(
                re.search(r"id|identifier|named|called", match["label"], re.IGNORECASE)
            )
            shape = (
                r"(?:[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+|[A-Z][A-Z0-9]*(?:-[A-Z0-9]+){2,})"
                if explicit
                else r"[A-Z][A-Z0-9]*(?:[-_][A-Z0-9]+){2,}"
            )
            if re.fullmatch(shape, identifier):
                candidates.add(identifier)
    approved_folded = {item.casefold() for item in approved}
    return {item for item in candidates if item.casefold() not in approved_folded}


def replace_untrusted_source_ids(
    result: dict[str, Any], blocked: set[str]
) -> dict[str, Any]:
    """Replace recognized unapproved IDs in every ordinary field, including echoes.

    Structured source membership/metadata is handled only by the existing allowlist.
    """

    def replace(value: Any) -> Any:
        if isinstance(value, str):
            for identifier in sorted(blocked, key=lambda item: (-len(item), item)):
                value = re.sub(
                    re.escape(identifier),
                    "unverified reference",
                    value,
                    flags=re.IGNORECASE,
                )
            return value
        if isinstance(value, list):
            return [replace(item) for item in value]
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        return value

    return {
        key: value if key == "source_references" else replace(value)
        for key, value in result.items()
    }


def soc_contract_violations(
    result: dict[str, Any], original_input: dict[str, Any]
) -> list[str]:
    observations = result.get("observed_evidence")
    if not isinstance(observations, list) or not observations:
        return ["observed_evidence must be a nonempty list of supported observations"]
    if not all(isinstance(item, str) and item.strip() for item in observations):
        return ["observed_evidence items must be nonblank strings"]
    return observable_violations(observations, "\n".join(text_values(original_input)))
