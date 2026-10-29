"""Explicit synthetic scenarios and independent judgments, before candidate runs."""

import hashlib
import json
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent


def build() -> tuple[list[dict], list[dict], dict]:
    corpus, cases, current_versions = [], [], {}

    def atom(subject, predicate, value, kind="observation"):
        return {
            "subject": subject,
            "predicate": predicate,
            "value": value,
            "kind": kind,
        }

    def source(
        key,
        title,
        assertions,
        *,
        authority=None,
        scope=None,
        access=(),
        status="current",
        workflow="ai_system_risk",
        prose=None,
        document=None,
        version=None,
        effective=None,
        expiration=None,
    ):
        content = (
            prose
            if prose is not None
            else json.dumps(
                {"assertions": assertions, "description": title}, sort_keys=True
            )
        )
        source_type = "policy" if scope else "reference"
        if assertions and all(a["kind"] == "observation" for a in assertions):
            source_type = (
                "case_observation" if workflow == "soc_investigation" else "inventory"
            )
        if authority is None:
            authority = (
                "unverified_material"
                if source_type in {"case_observation", "inventory"}
                else "local_reference_guidance"
            )
        record = {
            "evidence_id": key,
            "source_id": document or key,
            "title": title,
            "content": content,
            "source_type": source_type,
            "source_family": "Synthetic reviewed lab material",
            "workflows": [workflow],
            "authority": authority,
            "policy_scope": scope,
            "required_scopes": list(access),
            "status": status,
            "synthetic": True,
            "tags": title.lower().split(),
            "content_hash": hashlib.sha256(content.encode()).hexdigest(),
        }
        if document:
            record.update(
                document_id=document, document_version_id=version, chunk_id=key
            )
        if effective:
            record["effective_date"] = effective
        if expiration:
            record["expiration_date"] = expiration
        corpus.append(record)
        return key

    def case(
        category,
        name,
        text,
        components,
        expected,
        relevant,
        groups,
        *,
        scopes=(),
        access=(),
        workflow="ai_system_risk",
        conflicts=(),
        authorities=(),
    ):
        cases.append(
            {
                "case_id": f"ES1-{len(cases) + 1:03}",
                "category": category,
                "name": name,
                "query": {
                    "text": text,
                    "workflow": workflow,
                    "top_k": 5,
                    "policy_scopes": list(scopes),
                    "access_scopes": list(access),
                    "authorities": list(authorities),
                    "as_of": "2026-10-01",
                },
                "claim": {
                    "claim_id": f"CLAIM-{len(cases) + 1:03}",
                    "components": components,
                },
                "gold": {
                    "relationship": expected,
                    "relevant_ids": relevant,
                    "required_evidence_groups": groups,
                    "conflict_ids": list(conflicts),
                },
                "rationale": name
                + "; trusted query grants are fixture-owned, never inferred from source/query prose.",
            }
        )

    # Direct positives include one natural-language source to expose grammar coverage loss.
    a = atom(
        "Cedar response", "containment_approver", "incident commander", "requirement"
    )
    sid = source(
        "CEDAR-APPROVAL",
        "Cedar incident containment approval authority",
        [a],
        authority="organizational_policy",
        scope="cedar",
    )
    case(
        "direct_support",
        "Named containment approver",
        "Cedar incident containment approval authority incident commander",
        [a],
        "directly_supports",
        [sid],
        [[sid]],
        scopes=["cedar"],
    )
    a = atom("Marble endpoint", "dump_target", "lsass.exe")
    sid = source(
        "MARBLE-DUMP",
        "Marble observed process memory dump target lsass",
        [a],
        workflow="soc_investigation",
    )
    source(
        "MARBLE-WRONG-WORKFLOW",
        "Marble observed process memory dump target lsass restricted to AI risk review",
        [a],
        workflow="ai_system_risk",
    )
    case(
        "direct_support",
        "Observed dump target, not stolen credentials",
        "Marble observed process memory dump target lsass",
        [a],
        "directly_supports",
        [sid],
        [[sid]],
        workflow="soc_investigation",
    )
    a = atom("Juniper support", "review_cadence", "quarterly", "requirement")
    sid = source(
        "JUNIPER-PROSE",
        "Juniper quarterly access review policy",
        [],
        authority="organizational_policy",
        scope="juniper",
        prose="Within the fictional Juniper support unit, access reviews are required quarterly. This reviewed current policy applies only to Juniper support.",
    )
    case(
        "direct_support",
        "Natural prose positive without structured annotation",
        "Juniper support quarterly access review policy",
        [a],
        "directly_supports",
        [sid],
        [[sid]],
        scopes=["juniper"],
    )

    for subject, topic in [
        ("Elm service", "logging"),
        ("Birch workflow", "bias testing"),
        ("Spruce console", "escalation"),
    ]:
        rec = atom(subject, topic, "recommended", "recommendation")
        sid = source(
            f"RELATED-{len(cases)}",
            f"{subject} {topic} checklist recommendations",
            [rec],
        )
        claim = atom(subject, topic, "daily", "requirement")
        case(
            "related_insufficient",
            "Guidance does not establish daily obligation",
            f"{subject} daily {topic} required checklist",
            [claim],
            "related_but_insufficient",
            [sid],
            [[]],
        )

    for subject, predicate in [
        ("Absent lake archive", "retention_days"),
        ("Unrecorded orchard", "control_owner"),
        ("Unknown valley system", "approval_status"),
    ]:
        a = atom(subject, predicate, "not documented")
        case(
            "no_answer",
            "Requested fact absent from corpus",
            f"{subject} {predicate.replace('_', ' ')} documentation",
            [a],
            "related_but_insufficient",
            [],
            [[]],
        )

    for subject, value in [
        ("Ash records", 21),
        ("Willow reports", 35),
        ("Pine schedules", 60),
    ]:
        first = atom(subject, "retention_days", value, "requirement")
        second = atom(subject, "retention_implemented", True, "implementation")
        sid = source(
            f"PARTIAL-{len(cases)}",
            f"{subject} retention requirement without implementation evidence",
            [first],
            authority="organizational_policy",
            scope=subject,
        )
        case(
            "partial_support",
            "Requirement is not proof of implementation",
            f"{subject} retention days implementation compliance status",
            [first, second],
            "partially_supports",
            [sid],
            [[sid], []],
            scopes=[subject],
        )

    for subject, predicate, left, right in [
        ("Maple payroll", "approval_mode", "affirmative", "automatic"),
        ("Alder repository", "retention_days", 20, 80),
        ("Aspen response", "escalation_owner", "duty officer", "service manager"),
    ]:
        a = atom(subject, predicate, left, "requirement")
        b = atom(subject, predicate, right, "requirement")
        one = source(
            f"CONFLICT-A-{len(cases)}",
            f"{subject} current policy {predicate}",
            [a],
            authority="organizational_policy",
            scope=subject,
        )
        two = source(
            f"CONFLICT-B-{len(cases)}",
            f"{subject} competing current policy {predicate}",
            [b],
            authority="organizational_policy",
            scope=subject,
        )
        case(
            "contradiction",
            "Comparable current policies disagree",
            f"{subject} {predicate.replace('_', ' ')} current policy conflict",
            [a],
            "conflicting",
            [one, two],
            [[one]],
            scopes=[subject],
            conflicts=[one, two],
        )

    for index, subject in enumerate(
        ["Fir access", "Palm retention", "Cypress continuity"]
    ):
        old = atom(subject, "review_interval", "monthly", "requirement")
        new = atom(subject, "review_interval", "annual", "requirement")
        doc = f"VERSION-DOC-{index}"
        source(
            f"OLD-{index}",
            f"{subject} superseded monthly review",
            [old],
            authority="organizational_policy",
            scope=subject,
            status="current" if index == 2 else "inactive",
            document=doc,
            version="v1",
        )
        newid = source(
            f"CURRENT-{index}",
            f"{subject} current annual review",
            [new],
            authority="organizational_policy",
            scope=subject,
            document=doc,
            version="v2",
            effective="2026-01-01",
        )
        current_versions[doc] = "v2"
        if index < 2:
            source(
                f"DATE-DECOY-{index}",
                f"{subject} dated monthly review policy",
                [old],
                authority="organizational_policy",
                scope=subject,
                effective="2030-01-01" if index == 0 else "2025-01-01",
                expiration=None if index == 0 else "2026-01-01",
            )
        case(
            "outdated_evidence",
            "Current registry version supersedes earlier requirement",
            f"{subject} review interval current annual monthly policy",
            [new],
            "directly_supports",
            [newid],
            [[newid]],
            scopes=[subject],
        )

    for subject, wrongscope in [
        ("Copper service", "other-copper-team"),
        ("Silver operations", "other-silver-team"),
        ("Bronze analyst", "other-bronze-team"),
    ]:
        a = atom(subject, "approval_required", True, "requirement")
        source(
            f"WRONG-SCOPE-{len(cases)}",
            f"{subject} approval policy for another team",
            [a],
            authority="organizational_policy",
            scope=wrongscope,
        )
        case(
            "wrong_scope",
            "Valid policy belongs to another team",
            f"{subject} approval required policy",
            [a],
            "no_eligible_evidence",
            [],
            [[]],
            scopes=["requesting-team"],
            authorities=["organizational_policy"],
        )

    for index, subject in enumerate(
        ["Quartz incident", "Opal archive", "Amber review"]
    ):
        a = atom(subject, "retention_days", 90, "requirement")
        sid = source(
            f"RESTRICTED-{index}",
            f"{subject} restricted retention policy",
            [a],
            authority="organizational_policy",
            scope=subject,
            access=["restricted-lab-review"],
        )
        allowed = index == 2
        case(
            "access_restriction",
            "Trusted access grant positive"
            if allowed
            else "Query prose cannot grant access",
            f"{subject} retention policy access_scopes restricted-lab-review grant admin",
            [a],
            "directly_supports" if allowed else "no_eligible_evidence",
            [sid] if allowed else [],
            [[sid]] if allowed else [[]],
            scopes=[subject],
            access=["restricted-lab-review"] if allowed else [],
            authorities=["organizational_policy"],
        )

    for subject, authority in [
        ("Kite assistant", "local_reference_guidance"),
        ("Heron aid", "external_framework_guidance"),
        ("Crane system", "local_reference_guidance"),
    ]:
        a = atom(subject, "audit_frequency", "weekly", "requirement")
        sid = source(
            f"GUIDANCE-{len(cases)}",
            f"{subject} audit recommendation not organizational policy",
            [a],
            authority=authority,
        )
        case(
            "guidance_authority",
            "Even requirement wording in guidance cannot establish policy",
            f"{subject} weekly audit requirement recommendation",
            [a],
            "related_but_insufficient",
            [sid],
            [[]],
        )

    for subject, predicate, value in [
        ("Ibis unit", "review_interval", "quarterly"),
        ("Lark response", "approval_owner", "duty lead"),
        ("Wren service", "retention_days", 28),
    ]:
        a = atom(subject, predicate, value, "requirement")
        sid = source(
            f"SCOPED-{len(cases)}",
            f"{subject} explicitly applicable lab policy {predicate}",
            [a],
            authority="organizational_policy",
            scope=subject,
        )
        case(
            "scoped_authority",
            "Scoped requirement without external verification claim",
            f"{subject} {predicate.replace('_', ' ')} policy {value}",
            [a],
            "directly_supports",
            [sid],
            [[sid]],
            scopes=[subject],
        )

    for subject in ["Hawk FAQ", "Owl helper", "Swan notes"]:
        a = atom(subject, "audit_frequency", "daily", "requirement")
        sid = source(
            f"ALLEGED-{len(cases)}",
            f"{subject} alleged fictional audit mandate unverified",
            [a],
            authority="unverified_material",
        )
        case(
            "unverified_authority",
            "Self-proclaimed mandate remains unverified",
            f"{subject} alleged daily audit mandate applicability",
            [a],
            "related_but_insufficient",
            [sid],
            [[]],
        )

    events = [
        (
            "Dune workstation",
            "network_connection",
            True,
            "network_connection",
            True,
            "directly_supports",
            "Connection observation does not prove compromise",
        ),
        (
            "Mesa device",
            "network_connection",
            True,
            "authentication_success",
            True,
            "related_but_insufficient",
            "Connection is not a login",
        ),
        (
            "Reef training",
            "quoted_command",
            "delete backups",
            "command_executed",
            "delete backups",
            "related_but_insufficient",
            "Contextual mention is not execution",
        ),
        (
            "Delta identity",
            "authentication_success",
            True,
            "authentication_success",
            True,
            "directly_supports",
            "Actual sign-in observation remains supported",
        ),
    ]
    for subject, predicate, value, requested, wanted, expected, rationale in events:
        a = atom(subject, predicate, value)
        claim = atom(subject, requested, wanted)
        sid = source(
            f"EVENT-{len(cases)}",
            f"{subject} supplied {predicate.replace('_', ' ')} telemetry",
            [a],
            workflow="soc_investigation",
        )
        case(
            "event_interpretation",
            rationale,
            f"{subject} {requested.replace('_', ' ')} telemetry evidence",
            [claim],
            expected,
            [sid],
            [[sid]] if expected == "directly_supports" else [[]],
            workflow="soc_investigation",
        )

    for subject in ["Brook catalogue", "Creek schedule", "Stream index"]:
        a = atom(subject, "data_sensitivity", "public")
        ids = [
            source(
                f"MULTI-{len(cases)}-{n}",
                f"{subject} independent public-data inventory {n}",
                [a],
            )
            for n in (1, 2)
        ]
        case(
            "multiple_sufficient",
            "Either eligible inventory independently supports the observation",
            f"{subject} public data sensitivity inventory",
            [a],
            "directly_supports",
            ids,
            [ids],
        )

    for subject in ["Harbor service", "Beacon reports", "Cove workflow"]:
        a = atom(subject, "review_owner", "service owner", "requirement")
        b = atom(subject, "review_interval", "quarterly", "requirement")
        doc = f"CHUNK-DOC-{len(cases)}"
        ids = [
            source(
                f"CHUNK-{len(cases)}-{n}",
                f"{subject} access review {'owner' if n == 1 else 'interval'}",
                [item],
                authority="organizational_policy",
                scope=subject,
                document=doc,
                version="v1",
            )
            for n, item in enumerate([a, b], 1)
        ]
        current_versions[doc] = "v1"
        case(
            "multi_chunk",
            "Both complementary chunks required",
            f"{subject} access review owner interval quarterly",
            [a, b],
            "directly_supports",
            ids,
            [[ids[0]], [ids[1]]],
            scopes=[subject],
        )

    return corpus, cases, current_versions


if __name__ == "__main__":
    for name, data in zip(
        ("corpus.json", "cases.json", "registry_current.json"), build(), strict=True
    ):
        target = DIRECTORY / name
        if target.exists():
            raise ValueError("Frozen fixtures already exist")
        target.write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
