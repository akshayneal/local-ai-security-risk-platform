"""New synthetic v2 development fixtures; no diagnostic or historical imports."""

import hashlib
import json
from copy import deepcopy

from app.evidence_qualification import QualificationScope, SourceReview


def encode(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def make_scope(case_id="DEV2_JADE") -> QualificationScope:
    return QualificationScope(
        case_id=case_id,
        question_id="Q_" + case_id,
        question="Compare the declared catalog operation with separately reviewed synthetic scope",
        as_of="2026-11-06T16:00:00Z",
    )


def make_review(
    raw,
    scope=None,
    *,
    source_id="OBS_DEV2_JADE",
    source_format="synthetic_event",
    **changes,
):
    scope = scope or make_scope()
    value = {
        "source_id": source_id,
        "revision": "v2-dev-r1",
        "current_revision": "v2-dev-r1",
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "source_format": source_format,
        "role": "authorization_assertion"
        if source_format == "synthetic_authorization"
        else "event_observation",
        "case_id": scope.case_id,
        "workflows": ("soc_investigation",),
        "question_ids": (scope.question_id,),
        "source_path": "synthetic/v2/" + source_id,
        "synthetic": True,
        "authority": "synthetic_application_review",
        "approved": True,
        "requirement_reviewed": source_format == "synthetic_authorization",
        "reviewed_at": "2026-11-06T12:00:00Z",
        "effective_at": "2026-11-06T00:00:00Z",
        "expires_at": "2026-11-20T00:00:00Z",
    }
    value.update(changes)
    return SourceReview(**value)


def specimen(case_id="DEV2_JADE"):
    event = {
        "schema_version": "qualified-event/1",
        "event_id": "EVENT_" + case_id,
        "process_id": 4510,
        "process_created_at": "2026-11-06T13:40:00Z",
        "event": {
            "operation": "catalog_check",
            "result": "attempted",
            "principal": "svc-jade",
            "asset": "jade-node.example.invalid",
            "source": "192.0.2.143",
            "destination": "203.0.113.143",
            "endpoint": "catalog.example.invalid",
            "time": "2026-11-06T14:10:00Z",
            "amount": 0,
        },
        "annotations": [],
    }
    auth = {
        "schema_version": "qualified-authorization/1",
        "event_id": event["event_id"],
        "process_id": event["process_id"],
        "process_created_at": event["process_created_at"],
        "event_time": event["event"]["time"],
        "question_id": "Q_" + case_id,
        "authorization": {
            "status": "reported_authorized",
            "operation": "catalog_check",
            "principal": "svc-jade",
            "asset": "jade-node.example.invalid",
            "endpoint": "catalog.example.invalid",
            "window_start": "2026-11-06T14:00:00Z",
            "window_end": "2026-11-06T14:20:00Z",
        },
    }
    return event, auth


def prepare(event=None, authorizations=None, *, case_id="DEV2_JADE"):
    default_event, default_auth = specimen(case_id)
    event = default_event if event is None else event
    authorizations = [default_auth] if authorizations is None else authorizations
    scope = make_scope(case_id)
    raw = encode(event)
    sources = []
    for ordinal, auth in enumerate(authorizations, 1):
        auth_raw = encode(auth)
        sources.append(
            (
                auth_raw,
                make_review(
                    auth_raw,
                    scope,
                    source_id=f"AUTH_{case_id}_{ordinal}",
                    source_format="synthetic_authorization",
                ),
            )
        )
    return (
        raw,
        make_review(raw, scope, source_id="OBS_" + case_id),
        scope,
        {"authorization_sources": tuple(sources)},
    )


def native_inputs():
    scope = make_scope("DEV2_NATIVE")
    raw = encode(
        {
            "case_id": scope.case_id,
            "tables": {
                "DeviceNetworkEvents": [
                    {
                        "Timestamp": "2026-11-06T14:10:00Z",
                        "ActionType": "ConnectionSuccess",
                        "DeviceId": "synthetic-jade-native",
                        "RemoteIP": "203.0.113.143",
                        "RemotePort": 443,
                    }
                ]
            },
        }
    )
    return (
        raw,
        make_review(
            raw, scope, source_id="OBS_DEV2_NATIVE", source_format="microsoft_json"
        ),
        scope,
        {},
    )


def development_cases():
    """Small paired engineering matrix; expected labels are openly authored."""
    output = []
    for name in (
        "matching",
        "mismatching",
        "unknown_operation",
        "missing",
        "partial_only",
        "full_plus_partial",
        "duplicate",
        "complete_conflict",
        "unknown_denial",
        "different_operation",
        "reused_pid",
        "equivalent_timezone",
        "failed_attempt",
    ):
        case_id = "DEV2_" + name.upper()
        event, auth = specimen(case_id)
        auths = [auth]
        expected = {
            "execution_state": "completed",
            "relationship": "declared_alignment",
            "association_state": "unique",
        }
        if name == "mismatching":
            event["event"]["operation"] = "catalog_export"
            expected["relationship"] = "declared_mismatch"
        elif name == "unknown_operation":
            event["event"]["operation"] = None
            expected["relationship"] = "underdetermined"
        elif name == "missing":
            auths = []
            expected = {
                "execution_state": "not_executed",
                "relationship": "underdetermined",
                "association_state": "missing",
            }
        elif name == "partial_only":
            auth["authorization"]["principal"] = None
            expected = {
                "execution_state": "not_executed",
                "relationship": "underdetermined",
                "association_state": "incomplete",
            }
        elif name in {
            "full_plus_partial",
            "duplicate",
            "complete_conflict",
            "unknown_denial",
            "different_operation",
        }:
            other = deepcopy(auth)
            if name == "full_plus_partial":
                other["authorization"]["principal"] = None
            elif name == "complete_conflict":
                other["authorization"]["status"] = "reported_denied"
            elif name == "unknown_denial":
                other["authorization"].update(
                    status="reported_denied", operation=None, window_start=None
                )
            elif name == "different_operation":
                other["authorization"]["operation"] = "catalog_export"
            auths.append(other)
            expected = {
                "execution_state": "not_executed",
                "relationship": "conflicting_claims"
                if name == "complete_conflict"
                else "underdetermined",
                "association_state": "conflicting"
                if name == "complete_conflict"
                else "ambiguous",
            }
        elif name == "reused_pid":
            auth["process_created_at"] = "2026-11-06T13:41:00Z"
            expected = {
                "execution_state": "not_executed",
                "relationship": "underdetermined",
                "association_state": "no_match",
            }
        elif name == "equivalent_timezone":
            auth.update(
                process_created_at="2026-11-06T08:40:00-05:00",
                event_time="2026-11-06T09:10:00-05:00",
            )
        elif name == "failed_attempt":
            event["event"].update(operation="catalog_export", result="failed")
            expected["relationship"] = "declared_mismatch"
        output.append(
            {
                "id": case_id,
                "inputs": prepare(event, auths, case_id=case_id),
                "expected": expected,
            }
        )
    output.append(
        {
            "id": "DEV2_NATIVE",
            "inputs": native_inputs(),
            "expected": {
                "execution_state": "not_executed",
                "relationship": "unassessable",
                "association_state": "not_assessed",
            },
        }
    )
    return output
