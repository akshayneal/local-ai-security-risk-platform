"""Prospective authored mini-diagnostic literals; never run after files exist."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).parent


def encode(value):
    return json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def source(body, case_id, suffix, source_format, role):
    raw = encode(body)
    return {"raw": raw, "review": {
        "source_id": f"V2-{case_id}-{suffix}", "revision": "v1", "current_revision": "v1",
        "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(), "source_format": source_format,
        "role": role, "case_id": case_id, "workflows": ["soc_investigation"],
        "question_ids": [f"Q-{case_id}"], "source_path": f"fiction/{case_id}/{suffix}",
        "classification": "public_synthetic", "synthetic": True,
        "authority": "synthetic_application_review", "approved": True,
        "requirement_reviewed": role == "authorization_assertion", "current": True,
        "status": "current", "reviewed_at": "2026-10-12T00:00:00Z",
        "effective_at": "2026-10-12T00:00:00Z", "expires_at": "2026-10-13T00:00:00Z",
    }}


def case(case_id, variant):
    event = {"schema_version": "qualified-event/1", "event_id": f"ENTRY-{case_id}",
        "process_id": 3912, "process_created_at": "2026-10-12T17:50:00Z",
        "event": {"operation": "state_query", "result": "completed",
            "principal": f"synthetic-{case_id.lower()}@example.test", "asset": f"station-{case_id}",
            "source": "203.0.113.42", "destination": "192.0.2.83",
            "endpoint": f"records-{case_id.lower()}.example", "time": "2026-10-12T18:20:00Z", "amount": 0}}
    auth = {"schema_version": "qualified-authorization/1", "event_id": event["event_id"],
        "process_id": event["process_id"], "process_created_at": event["process_created_at"],
        "event_time": event["event"]["time"], "question_id": f"Q-{case_id}",
        "authorization": {"status": "reported_authorized", "operation": "state_query",
            "principal": event["event"]["principal"], "asset": event["event"]["asset"],
            "endpoint": event["event"]["endpoint"], "window_start": "2026-10-12T18:00:00Z",
            "window_end": "2026-10-12T19:00:00Z"}}
    auths = [auth]
    if variant == "unknown":
        event["event"]["operation"] = None
        event["event"]["result"] = "unknown"
    elif variant == "partial_actor":
        other = deepcopy(auth)
        other["authorization"]["principal"] = None
        auths.append(other)
    elif variant == "partial_denial":
        other = deepcopy(auth)
        other["authorization"].update(status="reported_denied", operation=None, window_start=None, window_end=None)
        auths.append(other)
    elif variant == "opposed":
        other = deepcopy(auth)
        other["authorization"]["status"] = "reported_denied"
        auths.append(other)
    elif variant == "equivalent":
        auths.append(deepcopy(auth))
    elif variant == "creation":
        auth["process_created_at"] = "2026-10-12T16:50:00Z"
    elif variant == "failed_mismatch":
        event["event"].update(operation="archive_copy", result="failed")
    source_format = "synthetic_event"
    if variant == "native":
        event = {"case_id": case_id, "tables": {"DeviceNetworkEvents": [{
            "Timestamp": "2026-10-12T18:20:00Z", "DeviceId": f"station-{case_id}",
            "ReportId": 241, "ActionType": "ConnectionSuccess", "LocalIP": "203.0.113.42",
            "RemoteIP": "192.0.2.83", "RemotePort": 8443, "Protocol": "Tcp",
            "InitiatingProcessId": 3912, "InitiatingProcessCreationTime": "2026-10-12T17:50:00Z"}]}}
        source_format, auths = "microsoft_json", []
    result = {"id": case_id, "scope": {"case_id": case_id, "workflow": "soc_investigation",
        "question_id": f"Q-{case_id}", "question": "Compare the declared action at this exact synthetic event scope",
        "as_of": "2026-10-12T20:00:00Z"},
        "source": source(event, case_id, "E", source_format, "event_observation"),
        "authorizations": [source(a, case_id, f"R{i}", "synthetic_authorization", "authorization_assertion") for i, a in enumerate(auths)],
        "options": {}}
    if variant == "revoked":
        result["authorizations"][0]["review"]["status"] = "revoked"
    return result


def main():
    names = ("cases.json", "key.json", "input_freeze.json")
    if any((ROOT / name).exists() for name in names):
        raise FileExistsError("Prospective files exist; preserve original literals")
    authored = [
        ("V6J4", "unknown", "comparison_returned", "completed", 1, "underdetermined", "unique"),
        ("C8P2", "native", "observations_projected", "not_executed", 0, "unassessable", "not_assessed"),
        ("Q4H7", "partial_actor", "association_resolved", "not_executed", 0, "underdetermined", "ambiguous"),
        ("L7S3", "partial_denial", "association_resolved", "not_executed", 0, "underdetermined", "ambiguous"),
        ("A3M9", "opposed", "association_resolved", "not_executed", 0, "conflicting_claims", "conflicting"),
        ("R9F2", "equivalent", "association_resolved", "not_executed", 0, "underdetermined", "ambiguous"),
        ("G2W8", "creation", "association_resolved", "not_executed", 0, "underdetermined", "no_match"),
        ("N8D5", "revoked", "source_refused", "not_executed", 0, "projection_unavailable", "not_assessed"),
        ("T5K3", "failed_mismatch", "comparison_returned", "completed", 1, "declared_mismatch", "unique"),
        ("B7Y6", "alignment", "comparison_returned", "completed", 1, "declared_alignment", "unique"),
    ]
    key = {identity: {"class": variant, "processing_state": processing, "execution_state": execution,
        "comparator_invocations": count, "relationship": relationship, "association_state": association,
        "accepted_alternatives": [], "rubric": "Supplied synthetic assertions only; no source-body authority, grant or action"}
        for identity, variant, processing, execution, count, relationship, association in authored}
    (ROOT / "cases.json").write_text(encode({"cases": [case(row[0], row[1]) for row in authored]}), encoding="utf8", newline="\n")
    (ROOT / "key.json").write_text(encode({"authored_expectations": key}), encoding="utf8", newline="\n")
    frozen = [ROOT / name for name in ["cases.json", "key.json", "rubric.md", "author_cases.py"]]
    value = {"format": "qualified-soc-v2-input-freeze/1", "date": "2026-11-06", "cases": 10,
        "model_sends": 0, "independent_review": "PENDING (0 completed)",
        "sha256": {p.as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in frozen}}
    (ROOT / "input_freeze.json").write_text(encode(value), encoding="utf8", newline="\n")


if __name__ == "__main__":
    main()
