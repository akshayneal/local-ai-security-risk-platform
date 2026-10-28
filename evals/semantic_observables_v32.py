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


def proposed_identity_issues(text: str, original: str, kind: str) -> list[str]:
    """Copied case identities only, rather than all proposed numeric values.

    IP candidates must resemble a reference (>=70% sequence similarity) or be
    explicitly attached to a case/source/destination identity. SHA candidates
    must be near a reference (>=90%, 56..72 hex). Ports need an endpoint or a
    case/traffic label. Explicit hypothetical/example clauses are excluded.
    This is a bounded identity detector, not a general recommendation judge.
    """
    issues = []
    ips = extract_observables(original, "ipv4")
    hashes = extract_observables(original, "sha256")
    ports = port_values(original)
    supplied_pairs = endpoint_pairs(original)
    for clause in re.split(r"(?<=[.!?])\s+(?=[A-Z])|;\s*|\n", text):
        if re.search(
            r"\b(?:hypothetical|illustrative|for\s+example|example\s+(?:query|address|hash|endpoint)|e\.g\.)",
            clause,
            re.IGNORECASE,
        ):
            continue
        if kind == "ipv4":
            for match in IP_SHAPE.finditer(clause):
                token = match.group()
                if token in ips:
                    continue
                normalized = re.sub(r"\s", "", token).replace(",", ".")
                near = any(
                    SequenceMatcher(None, normalized, ip, autojunk=False).ratio()
                    >= 0.70
                    for ip in ips
                )
                bound = re.search(
                    r"\b(?:case|source|destination|observed|reported|alert)\b",
                    clause[max(0, match.start() - 50) : match.start()],
                    re.IGNORECASE,
                )
                if ips and (near or bound):
                    issues.append(f"altered reference IPv4 {token}")
        elif kind == "sha256":
            for token in re.findall(r"(?<!\w)[0-9a-fA-F]{56,72}(?!\w)", clause):
                if token.lower() not in hashes and any(
                    SequenceMatcher(None, token.lower(), h, autojunk=False).ratio()
                    >= 0.90
                    for h in hashes
                ):
                    issues.append(f"altered reference SHA-256 {token}")
        elif kind == "port":
            # The endpoint grammar establishes a copied endpoint rather than
            # treating hours, PIDs, counts or an arbitrary scalar as a port.
            for ip, port in endpoint_pairs(clause):
                if (
                    ips
                    and any(
                        SequenceMatcher(None, ip, source, autojunk=False).ratio()
                        >= 0.70
                        for source in ips
                    )
                    and (
                        port not in ports
                        or (
                            ip in ips
                            and supplied_pairs
                            and (ip, port) not in supplied_pairs
                        )
                    )
                ):
                    issues.append(f"altered reference endpoint port {ip}:{port}")
            for match in PORT_LABEL.finditer(clause):
                port = int(match.group(1))
                bound = re.search(
                    r"\b(?:case|alert|observed|reported|source|destination|traffic|connection)\b",
                    clause[max(0, match.start() - 65) : match.start()],
                    re.IGNORECASE,
                )
                labeled_role = (
                    match.group()
                    .lower()
                    .startswith(
                        ("destination_port", "source_port", "dst_port", "src_port")
                    )
                )
                if ports and (bound or labeled_role) and port not in ports:
                    issues.append(f"altered reference contextual port {port}")
        else:
            raise ValueError(f"Unknown proposed identity kind: {kind}")
    return issues
