"""Exact critical SOC tokens; no correction, reputation lookup, or entailment."""

import ipaddress
import re

# Match the whole dotted token, including excess octets, before validating.
IPV4_CANDIDATE = re.compile(r"(?<![\w.])\d+(?:\.\d+){3,}(?![\w]|\.\d)")
SHA256 = re.compile(r"(?<![\w])[0-9a-fA-F]{64}(?![\w])")
CVE = re.compile(r"(?<![\w])CVE-\d{4}-\d{4,}(?![\w-])", re.IGNORECASE)


def valid_ipv4(value: str) -> bool:
    try:
        ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError:
        return False
    return True


def critical_observables(text: str) -> dict[str, set[str]]:
    """Preserve spelling and case so changed tokens cannot silently normalize."""
    return {
        "ipv4": {v for v in IPV4_CANDIDATE.findall(text) if valid_ipv4(v)},
        "sha256": set(SHA256.findall(text)),
        "cve": set(CVE.findall(text)),
    }


def observable_violations(observations: list[str], original_text: str) -> list[str]:
    """Membership only, not completeness or semantic factual support."""
    text = "\n".join(observations)
    authorized = critical_observables(original_text)
    generated = critical_observables(text)
    violations = []
    if any(not valid_ipv4(v) for v in IPV4_CANDIDATE.findall(text)):
        violations.append("observed_evidence contains malformed IPv4-like tokens")
    for kind in authorized:
        if generated[kind] - authorized[kind]:
            violations.append(
                f"observed_evidence contains {kind} values absent from the original request"
            )
    return violations
