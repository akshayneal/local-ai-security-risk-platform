"""Small English instruction heuristic for model-facing copies, not a detector.

Original requests/reference cards remain authoritative for provenance and checks.
Only high-confidence instruction-like sentences/lines are quarantined. Technical
syntax by itself is never a reason to remove data.
"""

import re
from typing import Any

QUARANTINE_MARKER = "[potential instruction-like content removed from untrusted data]"
INSTRUCTION_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(?:ignore|disregard|forget)\s+[^\n.!?]{0,100}\b(?:previous|prior|earlier|system|developer)\b[^\n.!?]{0,60}\binstructions?\b",
        r"\b(?:system\s+override|(?:system|developer|AI)\s+instruction\s*:)",
        r"\bfollow\s+(?:these|my|the following)\s+instructions\b",
        r"\b(?:write|include|place|return|output|insert|print)\b[^\n.!?]{0,60}\b(?:exact|literal|verbatim)\s+(?:phrase|text|string|words?|value)\b",
        r"\b(?:write|include|place|output|insert|put)\s+[^\n.!?]{0,160}\b(?:in|into|as)\s+(?:the\s+)?(?:analyst[_ ]note|risk_level|source_references|response[_ ]field|summary)\b",
        r"\b(?:return|set|output)\s+[^\n.!?]{0,60}\b(?:decision|risk_level|analyst_note|summary)\s*[:=]",
        r"\b(?:state|claim|say|report)\s+that\s+(?:you|the (?:assistant|application|system))\s+(?:have|has|already)\b[^\n.!?]{0,100}\b(?:isolated|blocked|disabled|contained|completed|executed)\b",
        r"\b(?:you are now|your new role is|instructions? (?:have|has) (?:the )?highest priority)\b",
        r"(?:\[/?(?:system|developer)\]|<\|(?:im_start|system|developer)\|>|BEGIN (?:SYSTEM|DEVELOPER) INSTRUCTIONS)",
    )
)


def neutralize_text(text: str) -> str:
    """Replace a matching sentence/line; retain surrounding benign sentences."""
    # Split at whitespace after sentence punctuation, never at URL/IP dots.
    spans = re.split(r"(\r?\n|(?<=[.!?])[ \t]+(?=[A-Z]))", text)
    return "".join(
        QUARANTINE_MARKER if any(p.search(span) for p in INSTRUCTION_PATTERNS) else span
        for span in spans
    )


def neutralize_content(value: Any) -> Any:
    """Return a fresh prompt-only copy, preserving shape and non-string values."""
    if isinstance(value, str):
        return neutralize_text(value)
    if isinstance(value, list):
        return [neutralize_content(item) for item in value]
    if isinstance(value, dict):
        return {key: neutralize_content(item) for key, item in value.items()}
    return value
