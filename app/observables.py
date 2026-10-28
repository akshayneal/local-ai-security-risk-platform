"""Exact critical SOC tokens; no correction, reputation lookup, or entailment."""

import ipaddress
import re
from difflib import SequenceMatcher

# Match the whole dotted token, including excess octets, before validating.
IPV4_CANDIDATE = re.compile(r"(?<![\w.,])\d+(?:\.\d+){3,}(?![\w]|[.,]\d)")
SHA256 = re.compile(r"(?<![\w])[0-9a-fA-F]{64}(?![\w])")
CVE = re.compile(r"(?<![\w])CVE-\d{4}-\d{4,}(?![\w-])", re.IGNORECASE)
IPV4_SHAPE = re.compile(r"(?<![\w.,])\d{1,6}(?:\s*[.,]\s*\d{1,6}){2,}(?!\w|[.,]\d)")
IP = r"(?<![\w.,])\d{1,3}(?:\.\d{1,3}){3}(?!\w|[.,]\d)"
IP_PORT = re.compile(r"(" + IP + r")\s*:\s*(\d{1,6})(?!\d)")
LABELED_ENDPOINT = re.compile(
    r"\b(?:destination[_ ]ip|dst_ip)\s*[=:]?\s*(?:is\s+)?(" + IP + r")"
    r"\s*[,;]?\s*(?:(?:with|and|on)\s+)?(?:destination[_ ]port|dst_port|port)\s*[=:]?\s*(?:is\s+)?(\d{1,6})(?!\w)",
    re.IGNORECASE,
)
TO_ENDPOINT = re.compile(
    r"\b(?:to\s+)?("
    + IP
    + r")\s+(?:on|at|using)\s+(?:destination\s+)?port\s+(\d{1,6})(?!\w)",
    re.IGNORECASE,
)


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


def observable_violations(
    observations: list[str], original_text: str, *, field: str = "observed_evidence"
) -> list[str]:
    """Membership only, not completeness or semantic factual support."""
    text = "\n".join(observations)
    authorized = critical_observables(original_text)
    generated = critical_observables(text)
    violations = []
    for token in IPV4_SHAPE.findall(text):
        normalized = re.sub(r"\s", "", token).replace(",", ".")
        near_input = any(
            SequenceMatcher(None, normalized, source, autojunk=False).ratio() >= 0.85
            for source in authorized["ipv4"]
        )
        if (len(normalized.split(".")) >= 4 or near_input) and not valid_ipv4(token):
            violations.append(f"{field} contains malformed IPv4-like tokens")
            break
    for kind in authorized:
        if generated[kind] - authorized[kind]:
            violations.append(
                f"{field} contains {kind} values absent from the original request"
            )
    for token in re.findall(r"(?<!\w)[0-9a-fA-F]{56,}(?!\w)", text):
        if len(token) == 64:
            continue  # Exact membership checked above, including spelling/case.
        if any(
            source.casefold() in token.casefold()
            or (
                len(token) <= 72
                and SequenceMatcher(
                    None, token.casefold(), source.casefold(), autojunk=False
                ).ratio()
                >= 0.90
            )
            for source in authorized["sha256"]
        ):
            violations.append(f"{field} contains a malformed near-input SHA-256 token")
            break
    return violations


def network_endpoints(text: str) -> set[tuple[str, int]]:
    """Only explicit IP:port, destination labels, or 'to IP on port N' forms."""
    return {
        (ip, int(port))
        for pattern in (IP_PORT, LABELED_ENDPOINT, TO_ENDPOINT)
        for ip, port in pattern.findall(text)
        if valid_ipv4(ip)
    }


def endpoint_violations(text: str, original_text: str, *, field: str) -> list[str]:
    supplied = network_endpoints(original_text)
    repeated = network_endpoints(text)
    violations = []
    if repeated - supplied:
        violations.append(
            f"{field} contains an endpoint relationship absent from the original request"
        )
    original_roles = labeled_ip_roles(original_text)
    for role, ips in labeled_ip_roles(text).items():
        if original_roles[role] and ips - original_roles[role]:
            violations.append(f"{field} contradicts an explicit input endpoint role")
    # Unbound prose ports remain advice. Machine-style assignments or explicit
    # observed/case labels alone bind a scalar to the supplied destination.
    if supplied:
        ports = {port for _, port in supplied}
        for match in re.finditer(
            r"\b(?:(?:destination_port|dst_port)\s*[=:]\s*|(?:observed|recorded|case)\s+destination\s+port\s+)(\d{1,6})(?!\w)",
            text,
            re.IGNORECASE,
        ):
            if int(match.group(1)) not in ports:
                violations.append(f"{field} changes a supplied destination port")
                break
    return violations


def labeled_ip_roles(text: str) -> dict[str, set[str]]:
    roles: dict[str, set[str]] = {"source": set(), "destination": set()}
    for label, ip in re.findall(
        r"\b(source[_ ]ip|src_ip|destination[_ ]ip|dst_ip)\s*[=:]?\s*(?:is\s+)?("
        + IP
        + r")",
        text,
        re.IGNORECASE,
    ):
        role = (
            "source" if label.lower().startswith(("source", "src")) else "destination"
        )
        roles[role].add(ip)
    for source, destination in re.findall(
        r"\bfrom\s+(" + IP + r")\s+to\s+(" + IP + r")", text, re.IGNORECASE
    ):
        roles["source"].add(source)
        roles["destination"].add(destination)
    return roles
