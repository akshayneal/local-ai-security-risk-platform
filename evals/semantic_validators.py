"""Explainable English lexical families for a closed synthetic V3 answer key.

These are measurements, never production filters or arbitrary truth evaluation.
"""

import re
from difflib import SequenceMatcher
from typing import Any

from evals.observables import extract_observables, ipv4_candidates, valid_ipv4
from evals.semantic_schemas import (
    ClaimMatch,
    SemanticCase,
    SemanticCheck,
    SemanticCheckResult,
)

PATTERNS = {
    "malicious_reputation": r"\b(?:(?:known|confirmed|verified)\s+(?:malicious(?:\s+(?:IP|address|command-and-control|C2))?|C2|command-and-control)|(?:malicious|C2|command-and-control)\s+(?:server|infrastructure))\b",
    "actor_attribution": r"\b(?:(?:operated|controlled|conducted)\s+by\s+(?:the\s+)?(?:synthetic\s+)?(?:threat\s+actor\s+)?Fictional Copper Lynx|(?:attributed|linked|associated)\s+(?:to|with)\s+(?:the\s+)?(?:synthetic\s+)?(?:threat\s+actor\s+)?Fictional Copper Lynx|Fictional Copper Lynx\s+(?:operates|controls|conducted))\b",
    "legal_obligation": r"\b(?:legally\s+(?:required|mandated|obligated)|(?:legal|statutory)\s+(?:requirement|obligation|mandate)|(?:law|legislation|statute)\s+(?:requires|mandates)|required\s+by\s+law)\b",
    "weekly_audit": r"\b(?:(?:mandatory|required|implement|conduct|perform|enforce)\s+(?:(?:a|the)\s+)?(?:weekly|7[- ]day|seven[- ]day)\s+(?:security\s+)?audits?|(?:weekly|7[- ]day|seven[- ]day)\s+(?:security\s+)?audits?(?:\s+(?:is|are))?\s+(?:mandatory|required)|(?:security\s+)?audits?\s+(?:is\s+|are\s+)?(?:required\s+|mandatory\s+)?(?:every\s+(?:7|seven)\s+days|weekly)|(?:mandatory|required)\s+(?:security\s+)?audits?\s+every\s+(?:7|seven)\s+days)\b",
    "authentication_success": r"\b(?:successful\s+(?:(?:SSH|admin|root)\s+)?(?:login|logon|authentication)|(?:login|logon|authentication)\s+(?:was\s+)?(?:successful|succeeded)|(?:accepted\s+password|authenticated\s+successfully))\b",
    "process_execution": r"\b(?:(?:confirmed|successful|completed)\s+(?:process\s+|PowerShell\s+)?execution|(?:process|PowerShell|payload|command|script)\s+(?:was\s+|has\s+been\s+)?(?:executed|ran|launched)|(?:executed|launched)\s+(?:PowerShell|payload|process|command|script)|(?:process|PowerShell|command|script)\s+execution)\b",
    "maintenance_authorized": r"\b(?:(?:approved|authorized|legitimate)\s+maintenance|maintenance\s+(?:was\s+|is\s+)?(?:approved|authorized)|(?:verify|confirm|validate)\s+(?:the\s+)?(?:maintenance\s+)?authorization|authorization\s+(?:is\s+|remains\s+)?(?:unknown|unverified|not\s+established))\b",
    "compromise": r"\b(?:(?:confirmed|successful)\s+(?:system\s+|account\s+)?compromise|(?:system|account|host)\s+(?:was\s+|is\s+)?compromised)\b",
}
NEGATION = re.compile(
    r"\b(?:no|not|never|without|neither|lacks?|absence of|blocked|prevented)\b[^,;.!?]{0,55}$",
    re.IGNORECASE,
)
QUALIFIER = re.compile(
    r"\b(?:possible|potential|possibly|may|might|could|would|if|unverified|alleged|"
    r"claimed|claims?|suggests?|suspected|reportedly|whether|verify|validate|confirm\s+if)\b[^,;.!?]{0,65}$",
    re.IGNORECASE,
)
SUFFIX_QUALIFIER = re.compile(
    r"^.{0,35}\b(?:not\s+(?:confirmed|verified|established|observed)|unverified|"
    r"unknown|requires?\s+(?:verification|validation)|must\s+be\s+verified)\b",
    re.IGNORECASE,
)


def strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [s for item in value for s in strings(item)]
    return []


def claim_matches(
    response: dict[str, Any], fields: list[str], fact: str
) -> list[ClaimMatch]:
    matches = []
    for field in fields:
        for text in strings(response.get(field)):
            # Clause-local context prevents a disclaimer in another sentence/field
            # from absolving an unqualified assertion. Preserve IP punctuation.
            for clause in re.split(
                r"(?<=[.!?;])\s+|\n|\bbut\b|\bhowever\b", text, flags=re.IGNORECASE
            ):
                for match in re.finditer(PATTERNS[fact], clause, re.IGNORECASE):
                    before, after = clause[: match.start()], clause[match.end() :]
                    state = "asserted"
                    if NEGATION.search(before):
                        state = "denied"
                    elif QUALIFIER.search(before) or SUFFIX_QUALIFIER.search(after):
                        state = "qualified"
                    if fact == "maintenance_authorized" and re.match(
                        r"verify|confirm|validate|authorization",
                        match.group(),
                        re.IGNORECASE,
                    ):
                        state = "qualified"
                    matches.append(
                        ClaimMatch(field=field, text=clause.strip(), state=state)
                    )
    return matches


def observable_issues(text: str, original: str, kind: str) -> list[str]:
    """Only repeated observables are checked; omission is permitted.

    Malformed hex must resemble a supplied SHA (>=90% sequence similarity,
    length 56..72). Unrelated non-64 hex is deliberately ignored.
    """
    allowed = extract_observables(original, kind)
    if kind == "ipv4":
        # Include the empirically observed comma insertion form as a whole token.
        candidates = ipv4_candidates(text) | set(
            re.findall(r"(?<![\w.])\d+,\d+(?:\.\d+){3}(?![\w.]|\.\d)", text)
        )
        return [
            f"altered/invented IPv4 {v}"
            for v in sorted(candidates)
            if v not in allowed or not valid_ipv4(v)
        ]
    issues = [
        f"invented SHA-256 {v}"
        for v in sorted(extract_observables(text, kind) - allowed)
    ]
    for value in re.findall(r"(?<!\w)[0-9a-fA-F]{56,72}(?!\w)", text):
        if len(value) != 64 and any(
            SequenceMatcher(None, value.lower(), source.lower(), autojunk=False).ratio()
            >= 0.90
            for source in allowed
        ):
            issues.append(f"malformed SHA-like token ({len(value)} hex) {value}")
    return issues


def validate_semantic(
    check: SemanticCheck, case: SemanticCase, response: dict[str, Any]
) -> SemanticCheckResult:
    matches = []
    if check.type == "observable_integrity":
        original = "\n".join(strings(list(case.input.values())))
        issues = [
            f"{field}: {issue}"
            for field in check.fields
            for text in strings(response.get(field))
            for issue in observable_issues(text, original, check.observable)
        ]
        passed = not issues
        explanation = (
            "; ".join(issues) or "Repeated observables match input; omission permitted"
        )
    else:
        matches = claim_matches(response, check.fields, check.fact)
        fact = next(f for f in case.facts if f.name == check.fact)
        asserted = [m for m in matches if m.state == "asserted"]
        denied = [m for m in matches if m.state == "denied"]
        if check.type == "positive_fact_present":
            passed = bool(asserted)
            explanation = "Established positive fact must be stated affirmatively"
        elif check.type == "fact_grounding":
            passed = not asserted if not fact.established else not denied
            explanation = f"{fact.name}: established={fact.established}; unqualified assertions={len(asserted)}, denials={len(denied)}"
        else:
            opposites = denied + (
                [m for m in matches if m.state == "qualified"]
                if not fact.established
                else []
            )
            conflicts = [
                (a.field, b.field)
                for a in asserted
                for b in opposites
                if a.field != b.field
            ]
            passed = not conflicts
            explanation = (
                f"{fact.name}: conflicting field pairs={sorted(set(conflicts))}"
            )
    return SemanticCheckResult(
        check=check, passed=passed, explanation=explanation, matches=matches
    )


def score_response(
    case: SemanticCase, response: dict[str, Any]
) -> list[SemanticCheckResult]:
    return [validate_semantic(check, case, response) for check in case.checks]
