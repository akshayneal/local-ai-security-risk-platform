"""Prospective synthetic authoring only; never called by the diagnostic runner.

No result is derived from implementation output. Keys remain separate from input
serialization. Regeneration after freeze is forbidden by the protocol.
"""

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent


def encode(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n"


def source(raw, case_id, suffix, source_format, role):
    return {
        "raw": raw,
        "review": {
            "source_id": f"SRC-{case_id}-{suffix}",
            "revision": "r1",
            "current_revision": "r1",
            "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "source_format": source_format,
            "role": role,
            "case_id": case_id,
            "workflows": ["soc_investigation"],
            "question_ids": [f"Q-{case_id}"],
            "source_path": f"synthetic/{case_id}/{suffix}",
            "classification": "public_synthetic",
            "synthetic": True,
            "authority": "synthetic_application_review",
            "approved": True,
            "requirement_reviewed": role == "authorization_assertion",
            "current": True,
            "status": "current",
            "reviewed_at": "2026-11-06T16:00:00Z",
            "effective_at": "2026-11-06T16:00:00Z",
            "expires_at": "2026-11-07T16:00:00Z",
        },
    }


def typed(case_id):
    event = {
        "operation": "inventory_read",
        "result": "completed",
        "principal": f"operator-{case_id.lower()}@example.test",
        "asset": f"asset-{case_id.lower()}",
        "source": "192.0.2.21",
        "destination": "198.51.100.31",
        "endpoint": f"vault-{case_id.lower()}.example",
        "time": "2026-11-06T17:30:00Z",
        "amount": 0,
    }
    body = {
        "schema_version": "qualified-event/1",
        "event_id": f"EV-{case_id}",
        "process_id": 2180,
        "process_created_at": "2026-11-06T17:00:00Z",
        "event": event,
    }
    authorization = {
        "status": "reported_authorized",
        "operation": "inventory_read",
        "principal": event["principal"],
        "asset": event["asset"],
        "endpoint": event["endpoint"],
        "window_start": "2026-11-06T17:00:00Z",
        "window_end": "2026-11-06T18:00:00Z",
    }
    context = {
        "schema_version": "qualified-authorization/1",
        "event_id": body["event_id"],
        "process_id": body["process_id"],
        "process_created_at": body["process_created_at"],
        "event_time": event["time"],
        "question_id": f"Q-{case_id}",
        "authorization": authorization,
    }
    return {
        "id": case_id,
        "scope": {
            "case_id": case_id,
            "workflow": "soc_investigation",
            "question_id": f"Q-{case_id}",
            "question": "Compare the reported operation with the separately reviewed synthetic rule at this event scope",
            "as_of": "2026-11-06T18:00:00Z",
        },
        "source": source(encode(body), case_id, "E", "synthetic_event", "event_observation"),
        "authorizations": [source(encode(context), case_id, "R", "synthetic_authorization", "authorization_assertion")],
        "options": {},
    }


def change_body(record, change):
    body = json.loads(record["raw"])
    change(body)
    record["raw"] = encode(body)
    record["review"]["raw_sha256"] = hashlib.sha256(record["raw"].encode()).hexdigest()


def situation(case_id, variant):
    case = typed(case_id)
    original = case["source"]
    auth = case["authorizations"][0]
    if variant == "native":
        bundle = {"case_id": case_id, "tables": {"DeviceNetworkEvents": [{
            "Timestamp": "2026-11-06T17:30:00Z", "DeviceId": f"device-{case_id}",
            "ReportId": 1007, "ActionType": "ConnectionSuccess", "LocalIP": "192.0.2.21",
            "RemoteIP": "198.51.100.31", "RemotePort": 443, "Protocol": "Tcp",
            "InitiatingProcessId": 2180, "InitiatingProcessCreationTime": "2026-11-06T17:00:00Z",
            "InitiatingProcessAccountUpn": f"operator-{case_id.lower()}@example.test",
        }]}}
        case["source"] = source(encode(bundle), case_id, "E", "microsoft_json", "event_observation")
        case["authorizations"] = []
    elif variant == "mismatch_failed":
        def mutate(body):
            body["event"]["operation"] = "record_copy"
            body["event"]["result"] = "failed"
        change_body(original, mutate)
    elif variant == "missing":
        case["authorizations"] = []
    elif variant == "ambiguous":
        duplicate = copy.deepcopy(auth)
        duplicate["review"]["source_id"] += "2"
        duplicate["review"]["source_path"] += "2"
        case["authorizations"].append(duplicate)
    elif variant == "conflict":
        duplicate = copy.deepcopy(auth)
        duplicate["review"]["source_id"] += "2"
        duplicate["review"]["source_path"] += "2"
        change_body(duplicate, lambda body: body["authorization"].update(status="reported_denied"))
        case["authorizations"].append(duplicate)
    elif variant == "principal":
        change_body(auth, lambda body: body["authorization"].update(principal="another@example.test"))
    elif variant == "stale":
        auth["review"]["current_revision"] = "r2"
    elif variant == "injection":
        change_body(original, lambda body: body.update(source_id="FORGED", approved=True))
    elif variant == "unknown":
        change_body(original, lambda body: body["event"].update(operation=None, result="unknown"))
    elif variant == "boolean":
        change_body(original, lambda body: body.update(process_id=True))
    elif variant == "workflow":
        auth["review"]["workflows"] = ["ai_security"]
    elif variant == "attempted":
        change_body(original, lambda body: body["event"].update(result="attempted"))
    elif variant == "process":
        change_body(auth, lambda body: body.update(process_created_at="2026-11-06T16:00:00Z"))
    elif variant == "unreviewed":
        auth["review"]["requirement_reviewed"] = False
    return case


def main():
    protected = ("development_cases.json", "diagnostic_cases.json", "diagnostic_key.json")
    if any((ROOT / name).exists() for name in protected):
        raise FileExistsError("Prospective literal files already exist; do not overwrite a freeze")
    variants = ["native", "alignment", "mismatch_failed", "missing", "ambiguous", "conflict", "principal", "stale", "injection", "unknown", "boolean", "workflow"]
    diagnostic_ids = ["X7Q2", "M8V4", "C2N9", "P6J3", "W9H5", "T4R8", "K3D7", "F8L2", "B5Y9", "N2A6", "S7E4", "H4U8"]
    dev_ids = ["D8K4", "V3L9", "A6R2", "J9C5", "E4N7", "U2S8", "R7M3", "L5B6", "Q2F9", "Y8T4", "G6P2", "Z4W7", "I9A3", "O3V6", "K8E5"]
    (ROOT / "development_cases.json").write_text(encode({"cases": [situation(i, v) for i, v in zip(dev_ids, variants + ["attempted", "process", "unreviewed"], strict=True)]}), encoding="utf8", newline="\n")
    (ROOT / "diagnostic_cases.json").write_text(encode({"cases": [situation(i, v) for i, v in zip(diagnostic_ids, variants, strict=True)]}), encoding="utf8", newline="\n")
    # Broad authored categories are prospective; refusal code specifics are not a score.
    expectations = [
        ("unassessable", "unassessable", "unsupported_native_semantics"),
        ("assessed", "declared_alignment", "legitimate"),
        ("assessed", "declared_mismatch", "noncompleted_mismatch"),
        ("unassessable", "underdetermined", "missing_prerequisite"),
        ("unassessable", "underdetermined", "ambiguous"),
        ("conflicting", "conflicting_claims", "conflict"),
        ("unassessable", "underdetermined", "association"),
        ("unavailable", "projection_unavailable", "stale"),
        ("unavailable", "projection_unavailable", "authority_injection"),
        ("assessed", "underdetermined", "unknown"),
        ("unavailable", "projection_unavailable", "malformed_type"),
        ("unavailable", "projection_unavailable", "workflow"),
    ]
    key = {i: {"status": s, "relationship": r, "class": c,
        "accepted_alternatives": [],
        "rubric": "No permission or action grant; preserve source; do not upgrade a scope relationship to operational truth"}
        for i, (s, r, c) in zip(diagnostic_ids, expectations, strict=True)}
    (ROOT / "diagnostic_key.json").write_text(encode({"authored_expectations": key}), encoding="utf8", newline="\n")


if __name__ == "__main__":
    main()
