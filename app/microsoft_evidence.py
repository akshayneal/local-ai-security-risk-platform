"""Row-bound Microsoft evidence views; original canonical telemetry stays intact."""

import json
import re
from dataclasses import dataclass
from typing import Any

from app.observables import IP, endpoint_violations, valid_ipv4
from app.soc_inputs import parse_json_bundle

MICROSOFT_SOURCE = "Microsoft Security local projected table bundle"
PROJECTED_FIELDS = (
    "Timestamp",
    "ActionType",
    "DeviceId",
    "DeviceName",
    "AccountName",
    "AccountUpn",
    "UserPrincipalName",
    "ProcessId",
    "InitiatingProcessId",
    "FileName",
    "ProcessCommandLine",
    "InitiatingProcessFileName",
    "InitiatingProcessCommandLine",
    "TargetProcess",
    "TargetProcessId",
    "LocalIP",
    "LocalPort",
    "RemoteIP",
    "RemotePort",
    "Protocol",
    "IPAddress",
    "ResultType",
    "AlertId",
    "Severity",
    "Status",
    "EvidenceRole",
    "SHA256",
    "InitiatingProcessSHA256",
    "LogonType",
    "ConditionalAccessStatus",
)
JSON_OBJECT = re.compile(r"\{[^{}]{0,8192}\}")
ROLE_IP = re.compile(
    r"\b(local|remote)(?:[_ ]?ip|\s+endpoint)?\s*[=:]?\s*[\"']?(" + IP + r")",
    re.IGNORECASE,
)
IP_ROLE = re.compile(r"(" + IP + r")\s*\((local|remote)\)", re.IGNORECASE)
ROLE_PAIR = re.compile(
    r"\b(?P<role>local|remote)[_ ]?ip\s*[=:]?\s*[\"']?(" + IP + r")[\"']?"
    r"\s*[,;]?\s*(?:on\s+)?(?:(?P=role)[_ ]?port|port)\s*[=:]?\s*[\"']?(\d{1,5})(?!\d)",
    re.IGNORECASE,
)


def port_number(value: Any) -> int | None:
    if type(value) is int and 0 <= value <= 65535:
        return value
    if isinstance(value, str) and re.fullmatch(r"[0-9]{1,5}", value):
        number = int(value)
        return number if number <= 65535 else None
    return None


def ipv4_value(value: Any) -> str | None:
    return value if isinstance(value, str) and valid_ipv4(value) else None


@dataclass(frozen=True)
class MicrosoftEvidence:
    bundle: dict

    @property
    def network_rows(self) -> list[dict]:
        return self.bundle["tables"].get("DeviceNetworkEvents", [])

    def pairs(self, role: str | None = None) -> set[tuple[str, int]]:
        result = set()
        for row in self.network_rows:
            for name in ("Local", "Remote"):
                if role is not None and name.lower() != role:
                    continue
                ip, port = (
                    ipv4_value(row.get(name + "IP")),
                    port_number(row.get(name + "Port")),
                )
                if ip is not None and port is not None:
                    result.add((ip, port))
        return result

    def role_ips(self, role: str) -> set[str]:
        return {
            ip
            for row in self.network_rows
            if (ip := ipv4_value(row.get(role.title() + "IP"))) is not None
        }

    def inventory(self) -> dict:
        """A named-field projection, not maliciousness or completeness inference."""
        return {
            "original_rows": sum(len(rows) for rows in self.bundle["tables"].values()),
            "selection": "none; all rows remain in canonical raw_log",
            "projection_fields": list(PROJECTED_FIELDS),
            "records": [
                {
                    "table": table,
                    "row": index,
                    "observed_fields": {
                        key: row[key] for key in PROJECTED_FIELDS if key in row
                    },
                }
                for table, rows in sorted(self.bundle["tables"].items())
                for index, row in enumerate(rows)
            ],
        }


def microsoft_evidence(original: dict) -> MicrosoftEvidence | None:
    if original.get("source_system") != MICROSOFT_SOURCE:
        return None
    bundle = parse_json_bundle(original.get("raw_log", ""))
    if bundle["case_id"] != original.get("alert_id"):
        raise ValueError("Microsoft case identity does not match its canonical bundle")
    return MicrosoftEvidence(bundle)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Ambiguous endpoint object")
        result[key] = value
    return result


def structured_endpoint_violations(
    text: str, original_text: str, evidence: MicrosoftEvidence, *, field: str
) -> list[str]:
    """Add validated row pairs to the legacy contract, without broadening its grammar.

    New JSON/local-remote forms are checked separately and stay row/role bound.
    Local/remote is not silently equated to source/destination direction.
    """
    pairs = evidence.pairs()
    anchors = (
        original_text + "\n" + "\n".join(f"{ip}:{port}" for ip, port in sorted(pairs))
    )
    violations = endpoint_violations(text, anchors, field=field)
    roles = {name: evidence.role_ips(name) for name in ("local", "remote")}
    for role, ip in ROLE_IP.findall(text):
        if ip not in roles[role.lower()]:
            violations.append(f"{field} contradicts an explicit input endpoint role")
    for ip, role in IP_ROLE.findall(text):
        if ip not in roles[role.lower()]:
            violations.append(f"{field} contradicts an explicit input endpoint role")
    for role, ip, port in ROLE_PAIR.findall(text):
        if (ip, int(port)) not in evidence.pairs(role.lower()):
            violations.append(
                f"{field} contains an endpoint relationship absent from the original request"
            )
    for match in JSON_OBJECT.finditer(text):
        try:
            row = json.loads(match.group(), object_pairs_hook=_unique_object)
        except ValueError:
            if re.search(r'"(?:Local|Remote)(?:IP|Port)"\s*:', match.group()):
                violations.append(
                    f"{field} contains an endpoint relationship absent from the original request"
                )
            continue
        supplied = {
            key: row[key]
            for key in ("LocalIP", "LocalPort", "RemoteIP", "RemotePort")
            if key in row
        }
        if not supplied:
            continue
        # A projected object must match one original network event, never a join.
        if not any(
            _matches_network_row(supplied, original)
            for original in evidence.network_rows
        ):
            violations.append(
                f"{field} contains an endpoint relationship absent from the original request"
            )
    return list(dict.fromkeys(violations))


def _matches_network_row(supplied: dict, original: dict) -> bool:
    for key, value in supplied.items():
        if key not in original:
            return False
        if key.endswith("Port"):
            number = port_number(value)
            if number is None or number != port_number(original[key]):
                return False
        elif ipv4_value(value) is None or value != original[key]:
            return False
    return True
