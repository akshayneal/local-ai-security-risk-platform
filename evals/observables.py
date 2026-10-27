"""Narrow exact observable extraction; no natural-language entailment or repair."""

import ipaddress
import re

# Capture the ENTIRE dotted numeric token: never salvage 2.0.2.51 from 19.2.0.2.51.
IPV4_CANDIDATE = re.compile(r"(?<![\w.])\d+(?:\.\d+){3,}(?![\w]|\.\d)")
SHA256 = re.compile(r"(?<![\w])[0-9a-fA-F]{64}(?![\w])")
CVE = re.compile(r"(?<![\w])CVE-\d{4}-\d{4,}(?![\w-])", re.IGNORECASE)


def ipv4_candidates(text: str) -> set[str]:
    return set(IPV4_CANDIDATE.findall(text))


def valid_ipv4(value: str) -> bool:
    try:
        ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError:
        return False
    return True


def extract_observables(text: str, kind: str) -> set[str]:
    """Preserve spelling/case; an exact check must not normalize a changed token."""
    if kind == "ipv4":
        return {value for value in ipv4_candidates(text) if valid_ipv4(value)}
    if kind == "sha256":
        return set(SHA256.findall(text))
    if kind == "cve":
        return set(CVE.findall(text))
    raise ValueError(f"Unsupported observable type: {kind}")


def invalid_ipv4_candidates(text: str) -> set[str]:
    return {value for value in ipv4_candidates(text) if not valid_ipv4(value)}
