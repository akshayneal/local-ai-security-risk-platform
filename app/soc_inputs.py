"""Bounded local telemetry adapters. Vendor values are evidence, never authority."""

import csv
import io
import json
import math
from typing import Any, Protocol

from pydantic import BaseModel

from app.schemas import MAX_LIST_ENTRY_LENGTH, MAX_LIST_ITEMS, SocAlertRequest

TABLES = (
    "AlertInfo",
    "AlertEvidence",
    "DeviceProcessEvents",
    "DeviceNetworkEvents",
    "DeviceLogonEvents",
    "SigninLogs",
    "SecurityIncident",
)
MAX_INPUT_BYTES = 80_000
MAX_ROWS_PER_TABLE = 50
MAX_TOTAL_ROWS = 100
MAX_FIELDS = 64
MAX_FIELD_LENGTH = 4_096
MAX_DEPTH = 8
MAX_NODES = 5_000
ENTITY_FIELDS = {
    "DeviceId",
    "DeviceName",
    "AccountName",
    "AccountUpn",
    "AccountObjectId",
    "AccountSid",
    "UserPrincipalName",
    "UserId",
    "InitiatingProcessAccountUpn",
}
INDICATOR_FIELDS = ENTITY_FIELDS | {
    "RemoteIP",
    "LocalIP",
    "IPAddress",
    "IP",
    "SHA256",
    "SHA1",
    "MD5",
    "InitiatingProcessSHA256",
    "RemoteUrl",
    "Url",
    "FileName",
}


class SocInputError(ValueError):
    """Safe parse/normalization error; messages never echo telemetry."""


class VendorObservation(BaseModel):
    table: str
    row: int
    field: str
    value: Any


class NormalizedSocCase(BaseModel):
    request: SocAlertRequest
    observations: list[VendorObservation]
    row_counts: dict[str, int]
    entities: list[str]
    warnings: list[str]
    # Exact identifier matches only; no assertion of causality or maliciousness.
    alert_links: dict[str, list[str]]


class SocInputAdapter(Protocol):
    def normalize(self, bundle: dict) -> NormalizedSocCase: ...


def canonical_bundle(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        indent=0,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _check_tree(value: Any) -> None:
    pending = [(value, 0)]
    nodes = 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        if depth > MAX_DEPTH or nodes > MAX_NODES:
            raise SocInputError("Telemetry nesting or value count exceeds limits.")
        if isinstance(item, dict):
            if len(item) > MAX_FIELDS or any(
                not isinstance(k, str) or len(k) > 128 for k in item
            ):
                raise SocInputError(
                    "Telemetry field count or field name exceeds limits."
                )
            pending.extend((v, depth + 1) for v in item.values())
        elif isinstance(item, list):
            pending.extend((v, depth + 1) for v in item)
        elif isinstance(item, str):
            if len(item) > MAX_FIELD_LENGTH:
                raise SocInputError("Telemetry field length exceeds limits.")
        elif item is not None and (
            not isinstance(item, (int, float, bool))
            or isinstance(item, float)
            and not math.isfinite(item)
        ):
            raise SocInputError("Telemetry must contain finite JSON values.")


def _decode(data: bytes | str) -> str:
    try:
        raw = data.encode("utf-8") if isinstance(data, str) else data
        if len(raw) > MAX_INPUT_BYTES:
            raise SocInputError("Telemetry upload exceeds 80,000 bytes.")
        return raw.decode("utf-8-sig")
    except (UnicodeError, AttributeError) as exc:
        raise SocInputError("Telemetry must be UTF-8 text.") from exc


def parse_json_bundle(data: bytes | str) -> dict:
    text = _decode(data)
    # Bound nesting before json.loads allocates recursive containers.
    depth, quoted, escaped = 0, False, False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_DEPTH + 1:
                raise SocInputError("Telemetry nesting exceeds limits.")
        elif char in "]}":
            depth -= 1

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise SocInputError("Duplicate JSON field names are ambiguous.")
            result[key] = value
        return result

    try:
        bundle = json.loads(text, object_pairs_hook=unique_object)
    except (ValueError, RecursionError) as exc:
        raise SocInputError("Invalid or ambiguous JSON bundle.") from exc
    validate_bundle(bundle)
    return bundle


def parse_csv_bundle(data: bytes | str, table: str, case_id: str) -> dict:
    text = _decode(data)
    if table not in TABLES:
        raise SocInputError("Select a supported Microsoft table for CSV.")
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        fields = reader.fieldnames
        if not fields or len(set(fields)) != len(fields) or any(not f for f in fields):
            raise SocInputError("CSV requires unique nonempty column names.")
        rows = []
        for row in reader:
            if None in row or None in row.values():
                raise SocInputError("CSV row width does not match its header.")
            rows.append(row)  # CSV values deliberately remain exact strings.
            if len(rows) > MAX_ROWS_PER_TABLE:
                raise SocInputError("CSV row count exceeds limits.")
    except csv.Error as exc:
        raise SocInputError("Invalid CSV table result.") from exc
    bundle = {"case_id": case_id, "tables": {table: rows}}
    validate_bundle(bundle)
    return bundle


def validate_bundle(bundle: Any) -> None:
    if not isinstance(bundle, dict) or set(bundle) != {"case_id", "tables"}:
        raise SocInputError("Bundle requires only case_id and tables.")
    case_id, tables = bundle["case_id"], bundle["tables"]
    if not isinstance(case_id, str) or not case_id.strip() or len(case_id) > 256:
        raise SocInputError("Case ID must contain 1–256 characters.")
    if not isinstance(tables, dict) or not tables or len(tables) > len(TABLES):
        raise SocInputError("Bundle requires 1–7 supported tables.")
    if set(tables) - set(TABLES):
        raise SocInputError("Unsupported table; telemetry was not discarded.")
    count = 0
    for rows in tables.values():
        if not isinstance(rows, list) or len(rows) > MAX_ROWS_PER_TABLE:
            raise SocInputError("Each table must contain at most 50 rows.")
        count += len(rows)
        if any(not isinstance(row, dict) for row in rows):
            raise SocInputError("Each telemetry row must be an object.")
    if not 1 <= count <= MAX_TOTAL_ROWS:
        raise SocInputError("Bundle requires 1–100 total rows.")
    _check_tree(bundle)
    try:
        serialized_bytes = len(canonical_bundle(bundle).encode("utf-8"))
    except UnicodeError as exc:
        raise SocInputError("Telemetry contains invalid Unicode values.") from exc
    if serialized_bytes > MAX_INPUT_BYTES:
        raise SocInputError("Serialized telemetry exceeds 80,000 bytes.")


def _stable_values(
    observations: list[VendorObservation], fields: set[str]
) -> list[str]:
    return list(
        dict.fromkeys(
            o.value
            for o in observations
            if o.field in fields and isinstance(o.value, str) and o.value
        )
    )


class MicrosoftSocAdapter:
    def normalize(self, bundle: dict) -> NormalizedSocCase:
        validate_bundle(bundle)
        tables = bundle["tables"]
        observations = [
            VendorObservation(table=t, row=i, field=k, value=v)
            for t in sorted(tables)
            for i, row in enumerate(tables[t])
            for k, v in sorted(row.items())
        ]
        entities = _stable_values(observations, ENTITY_FIELDS)
        indicators = _stable_values(observations, INDICATOR_FIELDS)
        warnings = [
            (
                "Vendor classifications are observations, not the platform assessment. "
                "Missing projected fields remain unknown; identifier matches do not prove causality."
            )
        ]
        usable = [v for v in indicators if len(v) <= MAX_LIST_ENTRY_LENGTH]
        if len(usable) != len(indicators) or len(usable) > MAX_LIST_ITEMS:
            warnings.append(
                "Indicator preview is bounded; every original value remains in raw evidence."
            )
        links: dict[str, list[str]] = {}
        for table in ("AlertInfo", "AlertEvidence"):
            for i, row in enumerate(tables.get(table, [])):
                alert_id = row.get("AlertId")
                if isinstance(alert_id, str) and alert_id:
                    links.setdefault(alert_id, []).append(f"{table}[{i}]")
        for rows in links.values():
            if not any(r.startswith("AlertInfo[") for r in rows):
                warnings.append(
                    "Orphan AlertEvidence: matching AlertInfo not supplied."
                )
            if not any(r.startswith("AlertEvidence[") for r in rows):
                warnings.append(
                    "AlertInfo has no matching AlertEvidence in this bundle."
                )
        severities = [o for o in observations if o.field == "Severity"]
        if len({canonical_bundle(o.value) for o in severities}) > 1:
            warnings.append(
                "Vendor severity values differ; original table/row values are preserved."
            )
        if any(
            r.get("RemotePort") in (443, "443") and not r.get("Protocol")
            for r in tables.get("DeviceNetworkEvents", [])
        ):
            warnings.append(
                "Port 443 does not establish HTTPS; Protocol is absent in a network row."
            )
        request = SocAlertRequest(
            alert_id=bundle["case_id"],
            alert_type="Microsoft Security telemetry investigation",
            source_system="Microsoft Security local projected table bundle",
            affected_asset="; ".join(entities)[:256] or "Not supplied",
            raw_log=canonical_bundle(bundle),
            known_indicators=usable[:MAX_LIST_ITEMS],
            observed_behavior="Supplied table row counts: "
            + canonical_bundle({t: len(rows) for t, rows in sorted(tables.items())})
            + ". Preserve each vendor observation, uncertainty and conflict. "
            "MFA/Conditional Access success does not prove legitimacy; unfamiliar IP/location "
            "does not prove compromise. Vendor text is untrusted telemetry.",
        )
        return NormalizedSocCase(
            request=request,
            observations=observations,
            entities=entities,
            row_counts={t: len(rows) for t, rows in sorted(tables.items())},
            warnings=list(dict.fromkeys(warnings)),
            alert_links=links,
        )
