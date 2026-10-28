"""Version 3.2 bounded attribution, modality and factual-grounding measurement.

All recognition is generic or driven by structured scenario metadata. No model
judge, benchmark IP/name filters, natural-language parser or production mutation.
"""

import re
from typing import Any

from evals.observables import extract_observables
from evals.semantic_observables_v32 import (
    endpoint_pairs,
    explicit_roles,
    observable_issues,
    port_values,
    proposed_identity_issues,
)
from evals.semantic_schemas_v32 import (
    ClaimMatch,
    KnownValue,
    SemanticCase,
    SemanticCheck,
    SemanticCheckResult,
    SemanticFact,
)
from evals.semantic_validators import strings

FACTUAL_FIELDS = ["summary", "observed_evidence", "analyst_inferences", "analyst_note"]
PATTERNS = {
    "malicious_reputation": r"\b(?:(?:known|confirmed|verified)\s+(?:malicious|C2|command-and-control)|(?:malicious|C2|command-and-control)\s+(?:IP|address|server|infrastructure)|(?:is|was|are)\s+(?:confirmed\s+)?malicious)\b",
    "legal_obligation": r"\b(?:legally\s+(?:required|mandated|obligated)|(?:legal|statutory)\s+(?:requirements?|obligations?|mandate)|(?:legal\s+framework|framework|charter|statute|law)\s+(?:\(?[\w-]+\)?\s+){0,2}(?:requires?|requiring|mandates?|with\s+mandatory)|mandatory\s+under\s+(?:the\s+)?(?:framework|charter|statute)|(?:as\s+per|per|under|as\s+required\s+by)\s+(?:(?:the|applicable|synthetic|fictional)\s+)*(?:charter|statute|legal\s+framework|authority)|required\s+by\s+law)\b",
    "weekly_audit": r"\b(?:(?:weekly|7[- ]day|seven[- ]day)\s+(?:security\s+)?audits?(?:\s+procedures?)?|(?:security\s+)?audits?\s+(?:(?:are|is|required|mandatory|conducted|performed)\s+)*(?:every\s+(?:7|seven)\s+days|weekly))\b",
    "authentication_success": r"\b(?:successful\s+(?:(?:SSH|admin|root)\s+)?(?:login|logon|authentication)|(?:login|logon|authentication)\s+(?:was\s+)?(?:successful|succeeded)|accepted\s+password|authenticated\s+successfully)\b",
    "process_execution": r"\b(?:(?:confirmed|successful|completed)\s+(?:process\s+|PowerShell\s+)?execution|(?:process|PowerShell|payload|command|script)\s+(?:was\s+|has\s+been\s+)?(?:executed|ran|launched)|(?:executed|launched)\s+(?:PowerShell|payload|process|command|script)|(?:process|PowerShell|command|script)\s+execution)\b",
    "maintenance_authorized": r"\b(?:(?:approved|authorized|legitimate)\s+maintenance|maintenance(?:\s+activity)?\s+(?:was\s+|is\s+)?(?:approved|authorized)|(?:verify|confirm|validate)\s+(?:the\s+)?(?:maintenance\s+)?authorization|authorization\s+(?:is\s+|remains\s+)?(?:unknown|unverified|not\s+established))\b",
    "compromise": r"\b(?:(?:confirmed|successful)\s+(?:system\s+|account\s+)?compromise|(?:system|account|host)\s+(?:was\s+|is\s+)?compromised|compromise\s+(?:is\s+|was\s+)?(?:confirmed|not\s+confirmed))\b",
}
# Completion and attempt forms share a local event matcher. Attempt scope is
# attached to that match, never applied to an entire mixed-event sentence.
PATTERNS["process_execution"] += (
    r"|\b(?:execution\s+completed|process\s+started|process-start\s+telemetry|"
    r"(?:attempted\s+)?(?:process\s+creation|launch)|attempt\s+to\s+execute)\b"
)
SENTENCES = re.compile(r"(?<=[.!?])\s+(?=[A-Z])|\n")
BOUNDARY = re.compile(
    r";|\b(?:but|however|although|though|while|yet)\b|,\s*and\s+", re.IGNORECASE
)
ATTRIBUTION = re.compile(
    r"\b(?:(?:reference|report|note|user(?:\s+narrative)?|input|supplied\s+text|provided\s+text)\s+(?:reports?|claims?|states?|alleges?|says?|describes?|flags?|attributes?)|(?:flagged|described|reported|attributed)\s+(?:in|by)\s+(?:(?:a|the|synthetic|local|supplied)\s+)*(?:reference|report|user|input|note))\b",
    re.IGNORECASE,
)
POSSESSIVE_CLAIM = re.compile(
    r"\b(?:user|reference|source|report|supplied\s+narrative)['’]s\s+"
    r"(?:claim|allegation|assertion)\s+(?:that|about)\b",
    re.IGNORECASE,
)
CLAIM_QUALIFICATION = re.compile(
    r"^\s*(?:(?:is|remains|was)\s+)?(?:requires?\s+verification|"
    r"unverified|not\s+independently\s+established|lacks?\s+confirmation)\b",
    re.IGNORECASE,
)
ADOPTION = re.compile(
    r"\b(?:(?:we|I|telemetry|evidence|analysis)\s+(?:confirms?|establishes?|verifies?)|independently\s+confirmed|therefore|as\s+(?:a\s+)?fact|indeed)\b",
    re.IGNORECASE,
)
QUESTION = re.compile(
    r"\b(?:check|verify|determine|confirm|investigate|validate)\s+(?:if|whether)\b",
    re.IGNORECASE,
)
RECOMMEND = re.compile(
    r"\b(?:verify|validate|investigate|review|check|determine|confirm)\b", re.IGNORECASE
)
UNCERTAIN = re.compile(
    r"\b(?:unverified|unconfirmed|possible|possibly|potential|may|might|could|suspected|alleged|unknown|uncertain)\b",
    re.IGNORECASE,
)
DENIED = re.compile(
    r"\b(?:no|not|never|without|neither|absence\s+of|blocked|prevented)\b",
    re.IGNORECASE,
)
SUFFIX_STATE = re.compile(
    r"^\s*(?:(?:is|was|remains|has|been|not|independently)\s+)*(?:unverified|unconfirmed|unknown|verified|confirmed|observed|corroborated)\b",
    re.IGNORECASE,
)


def actor_pattern(entity: str) -> str:
    name = re.escape(entity)
    return (
        r"\b(?:(?:operated|controlled|conducted)\s+by\s+(?:(?:the|synthetic|fictional|threat|actor)\s+)*"
        + name
        + r"|(?:attributed|linked|associated)\s+(?:to|with)\s+(?:(?:the|synthetic|fictional|threat|actor)\s+)*"
        + name
        + r"|"
        + name
        + r"\s+(?:operates|controls|conducted))\b"
    )


def speech_state(sentence: str, start: int, end: int, fact: str) -> str:
    left = list(BOUNDARY.finditer(sentence[:start]))
    right = BOUNDARY.search(sentence, end)
    before = sentence[left[-1].end() if left else 0 : start][-220:]
    after = sentence[end : right.start() if right else len(sentence)][:100]
    full_after = sentence[end:][:180]
    phrase = sentence[start:end]
    # An event coordinated after a distinct attempt is evaluated with its own
    # local context, including when the first event's implication is uncertain.
    if fact in {"process_execution", "authentication_success"}:
        event_clauses = re.split(r"\band\b", before, flags=re.IGNORECASE)
        if len(event_clauses) > 1 and re.search(
            r"\battempt(?:ed)?\b", " and ".join(event_clauses[:-1]), re.IGNORECASE
        ):
            before = event_clauses[-1]
    if re.match(
        r"\s*(?:(?:is|was|were|has|been)\s+)*(?:blocked|prevented|not\s+(?:completed|observed|occurred|started|executed|confirmed|available))\b",
        after,
        re.IGNORECASE,
    ):
        return "denied"
    if fact in {"process_execution", "authentication_success"} and (
        re.search(r"\battempted\s+(?:\w+\s+){0,1}$", before, re.IGNORECASE)
        or re.search(r"\battempt\s+to\s+$", before, re.IGNORECASE)
        or re.search(r"\battempt(?:ed)?\b", phrase, re.IGNORECASE)
        or re.match(r"\s+attempt(?:ed)?\b", after, re.IGNORECASE)
    ):
        return "qualified"
    if re.search(
        r"^\s*(?:(?:is|are|was|were)\s+)?not\s+(?:required|mandatory|authorized|supported)\b",
        after,
        re.IGNORECASE,
    ):
        return "denied"
    if QUESTION.search(before):
        return "question"
    if re.search(r"\b(?:if|unless|would)\b", before, re.IGNORECASE):
        return "conditional"
    if DENIED.search(before):
        return "denied"
    if ADOPTION.search(before):
        return "asserted"
    if POSSESSIVE_CLAIM.search(before):
        return "attributed"
    if RECOMMEND.search(before) or re.match(
        r"verify|confirm|validate", phrase, re.IGNORECASE
    ):
        return "recommendation"
    if ATTRIBUTION.search(before) or re.search(
        r"^.{0,35}\b(?:in\s+(?:the\s+)?user\s+narrative|according\s+to\s+(?:the\s+)?(?:reference|input|user))\b",
        after,
        re.IGNORECASE,
    ):
        return "attributed"
    # Same-sentence association only: later independent sentences never absolve
    # a preceding assertion. Cross-conjunction uncertainty needs a same-claim cue.
    subjects = {
        "malicious_reputation": r"this|that|it|the\s+claim|the\s+reputation|its\s+reputation",
        "actor_attribution": r"this|that|it|the\s+claim|this\s+attribution|the\s+attribution",
        "maintenance_authorized": r"this|that|it|authorization|the\s+authorization",
    }.get(fact, r"this|that|it|the\s+claim")
    conjunction_qualification = re.search(
        r"\b(?:but|however|although|though|while|yet)\b[,\s]+(?:"
        + subjects
        + r")\b.{0,60}\b(?:unverified|unconfirmed|not\s+(?:been\s+)?(?:independently\s+)?(?:verified|confirmed|corroborated))\b",
        full_after,
        re.IGNORECASE,
    )
    if (
        UNCERTAIN.search(before)
        or conjunction_qualification
        or CLAIM_QUALIFICATION.search(after)
    ):
        return "qualified"
    if SUFFIX_STATE.search(after) and (
        UNCERTAIN.search(after) or re.search(r"\bnot\b", after, re.IGNORECASE)
    ):
        return "qualified"
    if fact == "maintenance_authorized" and phrase.lower().startswith("authorization"):
        return "qualified"
    if fact == "compromise" and re.search(r"\bnot\b", phrase, re.IGNORECASE):
        return "denied"
    return "asserted"


def claim_matches(
    response: dict[str, Any], fields: list[str], fact: SemanticFact
) -> list[ClaimMatch]:
    pattern = (
        actor_pattern(fact.entity)
        if fact.name == "actor_attribution"
        else PATTERNS[fact.name]
    )
    matches = []
    for field in fields:
        for text in strings(response.get(field)):
            for sentence in SENTENCES.split(text):
                for match in re.finditer(pattern, sentence, re.IGNORECASE):
                    state = speech_state(
                        sentence, match.start(), match.end(), fact.name
                    )
                    matches.append(
                        ClaimMatch(field=field, text=sentence.strip(), state=state)
                    )
    return matches


def protocol_matches(response: dict[str, Any], fields: list[str]) -> list[ClaimMatch]:
    matches = []
    for field in fields:
        for text in strings(response.get(field)):
            for sentence in SENTENCES.split(text):
                for match in re.finditer(
                    r"\b(?:SSH|HTTPS?|RDP)\b", sentence, re.IGNORECASE
                ):
                    state = speech_state(
                        sentence, match.start(), match.end(), "protocol"
                    )
                    matches.append(
                        ClaimMatch(
                            field=field,
                            text=sentence.strip(),
                            state=state,
                            token=match.group().upper(),
                        )
                    )
    return matches


def validate_metadata(case: SemanticCase) -> None:
    original = "\n".join(strings(list(case.input.values())))
    checks = case.checks
    for value in case.known_values:
        if value.evidence not in original:
            raise ValueError("Known-value evidence missing from request")
        if (
            value.value is not None
            and value.value.lower() not in value.evidence.lower()
        ):
            raise ValueError("Known value absent from authoritative evidence")
        if value.value is None and not re.search(
            r"\b(?:unknown|unspecified|not\s+(?:provided|established|identified))\b",
            value.evidence,
            re.IGNORECASE,
        ):
            raise ValueError("Unknown value must be explicit in evidence")
        if not any(
            c.type == "known_value_consistency"
            and c.value_key == value.key
            and set(
                FACTUAL_FIELDS + ["evidence_gaps"]
                if case.mode == "soc_alert"
                else ["summary", "key_risks", "required_controls", "evidence_gaps"]
            )
            <= set(c.fields)
            for c in checks
        ):
            raise ValueError("Known-value metadata requires a consistency check")
    if case.mode == "soc_alert":
        for kind in ["ipv4", "sha256", "port"]:
            supplied = (
                port_values(original)
                if kind == "port"
                else extract_observables(original, kind)
            )
            if supplied and not any(
                c.type == "observable_integrity"
                and c.observable == kind
                and set(FACTUAL_FIELDS) <= set(c.fields)
                for c in checks
            ):
                raise ValueError(
                    f"SOC supplied {kind} requires whole-factual-response coverage"
                )
            if supplied and not any(
                c.type == "proposed_identity_integrity" and c.observable == kind
                for c in checks
            ):
                raise ValueError(
                    f"SOC supplied {kind} requires investigation identity coverage"
                )
        if any(not 1 <= p <= 65535 for p in port_values(original)):
            raise ValueError("Invalid input port")
    for check in checks:
        if (
            check.type in {"observable_integrity", "proposed_identity_integrity"}
            and check.observable == "port"
            and not port_values(original)
        ):
            raise ValueError("Port check has no supplied port")
    if case.protocol and case.protocol.evidence not in original:
        raise ValueError("Protocol evidence missing from request")
    if (
        case.protocol
        and case.protocol.value == "unknown"
        and not re.search(
            r"\b(?:unknown|unspecified|not\s+established|not\s+identified)\b",
            case.protocol.evidence,
            re.IGNORECASE,
        )
    ):
        raise ValueError("Unknown protocol must be explicit in scenario evidence")
    if case.protocol and not any(
        c.type == "protocol_grounding" and set(FACTUAL_FIELDS) <= set(c.fields)
        for c in checks
    ):
        raise ValueError("Protocol metadata requires factual-field grounding coverage")
    if case.endpoints and not any(
        c.type == "endpoint_integrity" and set(FACTUAL_FIELDS) <= set(c.fields)
        for c in checks
    ):
        raise ValueError("Endpoint metadata requires factual-field relation coverage")
    if (
        case.protocol
        and case.protocol.value != "unknown"
        and not re.search(
            r"\b" + case.protocol.value + r"\b", case.protocol.evidence, re.IGNORECASE
        )
    ):
        raise ValueError("Established protocol absent from evidence")
    for endpoint in case.endpoints:
        if endpoint.evidence not in original:
            raise ValueError("Endpoint evidence absent")
        for ip in [endpoint.source_ip, endpoint.destination_ip]:
            if ip is not None and ip not in extract_observables(
                endpoint.evidence, "ipv4"
            ):
                raise ValueError("Endpoint IP absent from evidence")
        for role, value in explicit_roles(endpoint.evidence):
            if getattr(endpoint, role) is not None and value != getattr(endpoint, role):
                raise ValueError("Endpoint role contradicts explicitly labeled input")
        if (
            endpoint.destination_port is not None
            and endpoint.destination_port not in port_values(endpoint.evidence)
        ):
            raise ValueError("Endpoint port absent from evidence")


def missing_value_matches(
    response: dict[str, Any], fields: list[str], value: KnownValue
) -> list[ClaimMatch]:
    """Only explicit missingness about literal subjects in structured keys.

    Unknown keys do not acquire a made-up value. External verification caution
    is exempt only in the same local clause, with an explicit scope modifier.
    Ambiguous 'unclear context' is deliberately left for manual review.
    """
    if value.value is None:
        return []
    missing = r"(?:missing|unspecified|unknown|unavailable|absent|not\s+(?:provided|specified|established|supplied|known))"
    found = []
    for field in fields:
        for text in strings(response.get(field)):
            for sentence in SENTENCES.split(text):
                for clause in BOUNDARY.split(sentence):
                    for subject in value.subjects:
                        for match in re.finditer(
                            r"\b" + re.escape(subject) + r"\b", clause, re.IGNORECASE
                        ):
                            before, after = (
                                clause[: match.start()],
                                clause[match.end() :],
                            )
                            if re.search(
                                r"\b(?:external|externally|real-world|independent|independently)\s+(?:\w+\s+){0,2}$",
                                before,
                                re.IGNORECASE,
                            ) or re.match(
                                r"\s+(?:(?:validity|verification|applicability|is|cannot|be|not|remains)\s+){0,4}(?:externally|independently)\b",
                                after,
                                re.IGNORECASE,
                            ):
                                continue
                            # Explicit value before a different coordinated
                            # missing attribute is not a missingness claim.
                            if re.match(
                                r"\s*(?:(?:is|remains)\s+)?"
                                + re.escape(value.value)
                                + r"\b",
                                after,
                                re.IGNORECASE,
                            ):
                                continue
                            suffix = re.match(
                                r"\s*(?:and\s+[\w -]{1,35}\s+)?(?:(?:is|are|was|were|remains|information|details)\s+)*"
                                + missing
                                + r"\b",
                                after,
                                re.IGNORECASE,
                            )
                            prefix = re.search(
                                r"\b(?:no|missing|absence\s+of|without)\s+(?:(?:any|supplied|provided|available)\s+){0,2}$",
                                before,
                                re.IGNORECASE,
                            )
                            # Questions, attribution and proposed collection do
                            # not independently assert that evidence is absent.
                            state = speech_state(
                                clause, match.start(), match.end(), value.key
                            )
                            if (suffix or prefix) and state not in {
                                "attributed",
                                "question",
                                "recommendation",
                                "conditional",
                            }:
                                found.append(
                                    ClaimMatch(
                                        field=field,
                                        text=sentence.strip(),
                                        token=value.key,
                                        state="denied",
                                    )
                                )
    return found


def validate_semantic(
    check: SemanticCheck, case: SemanticCase, response: dict[str, Any]
) -> SemanticCheckResult:
    matches = []
    issues = []
    original = "\n".join(strings(list(case.input.values())))
    if check.type == "known_value_consistency":
        value = next(v for v in case.known_values if v.key == check.value_key)
        matches = missing_value_matches(response, check.fields, value)
        passed = not matches
        explanation = f"{value.key}: supplied value={value.value!r}; absolute missingness claims={len(matches)}; scope={value.support_scope}; external caution permitted"
    elif check.type == "proposed_identity_integrity":
        issues = [
            f"{field}: {issue}"
            for field in check.fields
            for text in strings(response.get(field))
            for issue in proposed_identity_issues(text, original, check.observable)
        ]
        passed = not issues
        explanation = (
            "; ".join(issues)
            or "Reference-bound proposed identities preserve supplied values; unrelated numbers and explicit hypothetical examples excluded"
        )
    elif check.type == "observable_integrity":
        issues = [
            f"{field}: {issue}"
            for field in check.fields
            for text in strings(response.get(field))
            for issue in observable_issues(text, original, check.observable)
        ]
        passed = not issues
        explanation = (
            "; ".join(issues)
            or "Repeated observable values preserve input; omission permitted"
        )
    elif check.type == "endpoint_integrity":
        pairs = {
            (e.destination_ip, e.destination_port)
            for e in case.endpoints
            if e.destination_port is not None
        }
        for field in check.fields:
            for text in strings(response.get(field)):
                for ip, port in endpoint_pairs(text):
                    if pairs and (ip, port) not in pairs:
                        issues.append(
                            f"{field}: unsupported destination pair {ip}:{port}"
                        )
                for role, value in explicit_roles(text):
                    allowed = {
                        getattr(e, role)
                        for e in case.endpoints
                        if getattr(e, role) is not None
                    }
                    if allowed and value not in allowed:
                        issues.append(f"{field}: unsupported {role}={value}")
        passed = not issues
        explanation = (
            "; ".join(issues)
            or "Explicit endpoint relations agree with established tuple members"
        )
    elif check.type in {"protocol_grounding", "positive_protocol_present"}:
        matches = protocol_matches(response, check.fields)
        established = case.protocol.value
        asserted = [m for m in matches if m.state == "asserted"]

        def protocols(match: ClaimMatch) -> set[str]:
            return {match.token}

        bad = [m for m in asserted if protocols(m) - {established}]
        passed = (
            bool([m for m in asserted if established in protocols(m)])
            if check.type == "positive_protocol_present"
            else not bad
        )
        explanation = f"Protocol key={established}; unsupported assertions={len(bad)}; positive required={check.type == 'positive_protocol_present'}"
    else:
        fact = next(f for f in case.facts if f.name == check.fact)
        matches = claim_matches(response, check.fields, fact)
        asserted = [m for m in matches if m.state == "asserted"]
        denied = [m for m in matches if m.state == "denied"]
        if check.type == "positive_fact_present":
            passed = bool(asserted)
            explanation = (
                f"Established {fact.name} requires an affirmative supported statement"
            )
        elif check.type == "fact_grounding":
            passed = not asserted if not fact.established else not denied
            explanation = f"{fact.name}: established={fact.established}, assertions={len(asserted)}, denials={len(denied)}"
        else:
            opposite = denied + (
                [m for m in matches if m.state == "qualified"]
                if not fact.established
                else []
            )
            pairs = sorted(
                {
                    (a.field, b.field)
                    for a in asserted
                    for b in opposite
                    if a.field != b.field
                }
            )
            passed = not pairs
            explanation = f"{fact.name}: contradictory field pairs={pairs}"
    return SemanticCheckResult(
        check=check, passed=passed, explanation=explanation, matches=matches
    )


def score_response(
    case: SemanticCase, response: dict[str, Any]
) -> list[SemanticCheckResult]:
    return [validate_semantic(c, case, response) for c in case.checks]
