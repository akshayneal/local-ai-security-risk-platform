"""Evaluation-only IPv4, SHA and endpoint fidelity; production stays frozen."""

import re
from difflib import SequenceMatcher

from evals.observables import extract_observables, valid_ipv4
from evals.semantic_validators import observable_issues as v3_hash_issues

IP = r"(?<![\w.,])\d{1,3}(?:\.\d{1,3}){3}(?!\w|[.,]\d)"
IP_SHAPE = re.compile(r"(?<![\w.,])\d{1,6}(?:\s*[.,]\s*\d{1,6}){2,4}(?!\w|[.,]\d)")
IP_PORT = re.compile(r"(" + IP + r")\s*:\s*(\d{1,6})(?!\d)")
PORT_LABEL = re.compile(
    r"\b(?:dst_port|destination_port|source_port|src_port|port)\s*[=:]?\s*(\d{1,6})(?!\w)",
    re.IGNORECASE,
)


def port_values(text: str) -> set[int]:
    """Port syntax only: integers in PID, date, count and CVE contexts are ignored."""
    return {int(port) for _, port in IP_PORT.findall(text)} | {
        int(port) for port in PORT_LABEL.findall(text)
    }


def ip_issues(text: str, original: str) -> list[str]:
    allowed = extract_observables(original, "ipv4")
    issues = []
    for match in IP_SHAPE.finditer(text):
        token = match.group()
        normalized = re.sub(r"\s", "", token).replace(",", ".")
        groups = normalized.split(".")
        if len(groups) >= 4:
            if token not in allowed or not valid_ipv4(token):
                issues.append(f"altered/invented IPv4 {token}")
        elif any(
            SequenceMatcher(None, normalized, ip, autojunk=False).ratio() >= 0.85
            for ip in allowed
        ):
            issues.append(f"near-input malformed IPv4 {token}")
    return issues


def observable_issues(text: str, original: str, kind: str) -> list[str]:
    if kind == "ipv4":
        return ip_issues(text, original)
    if kind == "sha256":
        # Explicit reuse of the immutable V3 hash-token algorithm, not its scorer.
        return v3_hash_issues(text, original, kind)
    if kind == "port":
        allowed = port_values(original)
        return [
            f"altered/invented port {p}"
            for p in sorted(port_values(text))
            if not 1 <= p <= 65535 or p not in allowed
        ]
    raise ValueError(f"Unknown observable kind: {kind}")


def endpoint_pairs(text: str) -> set[tuple[str, int]]:
    return {(ip, int(port)) for ip, port in IP_PORT.findall(text)}


def explicit_roles(text: str) -> list[tuple[str, str]]:
    """Only clear source/destination labels or 'from IP to IP' relations."""
    roles = []
    for role, value in re.findall(
        r"\b(source_ip|src_ip|destination_ip|dst_ip)\s*[=:]\s*(" + IP + r")",
        text,
        re.IGNORECASE,
    ):
        roles.append(
            (
                "source_ip"
                if role.lower() in {"source_ip", "src_ip"}
                else "destination_ip",
                value,
            )
        )
    for source, destination in re.findall(
        r"\bfrom\s+(" + IP + r")\s+to\s+(" + IP + r")", text, re.IGNORECASE
    ):
        roles.extend([("source_ip", source), ("destination_ip", destination)])
    return roles
