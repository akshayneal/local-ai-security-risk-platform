"""Read-only development accounting and explicitly authored review-packet support.

No provider calls, automatic semantic scorer, or diagnostic-input loader exists
here. Packet callers supply their already-authorized records and canonical inputs.
"""

import json
import os
import random
import statistics
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path

from app.adaptive_reports import build_report, export_json, export_markdown
from app.adaptive_semantics import ReviewedContext, project
from evals.adaptive_security_reasoning_v1.runner import (
    dispatch_spec,
    parse_proposal,
    validate_proposal,
)
from evals.adaptive_security_reasoning_v1.transport import (
    MAX_RETAINED_BYTES,
    MODEL,
    OPTIONS,
    PHASE_CAPS,
    DiagnosticBudget,
    artifact_bytes,
    encoded,
    named_root,
    plain_path,
    sha,
)

HERE = Path(__file__).resolve().parent
DEFAULT_SEED = 13013
MAX_PACKET_BYTES = 32_000_000
MAX_VISIBLE_PROPOSAL_BYTES = 24_000
REVIEW_STATUS = "implementation_authored; independent_human_review_PENDING"


def _bytes(path, limit=MAX_RETAINED_BYTES):
    plain_path(path)
    if path.stat().st_size > limit:
        raise ValueError("review_input_budget")
    with path.open("rb") as source:
        value = source.read(limit + 1)
    if len(value) > limit:
        raise ValueError("review_input_budget")
    return value


def _json(path, limit=MAX_RETAINED_BYTES):
    return json.loads(_bytes(path, limit))


def _development_inputs(suite):
    """Read exactly the two frozen development files, never holdout identities/content."""
    freeze = _json(suite / "freeze.json")
    result = []
    for leaf in ("dev_cases.json", "dev_key.json"):
        name = "evals/adaptive_security_reasoning_v1/" + leaf
        raw = _bytes(suite / leaf)
        if sha(raw) != freeze["sha256"][name]:
            raise ValueError("frozen_development_input_changed")
        result.append(json.loads(raw))
    cases, key = result
    case_map, key_map = {c["id"]: c for c in cases}, {k["id"]: k for k in key}
    if (
        len(case_map) != len(cases)
        or len(key_map) != len(key)
        or set(case_map) != set(key_map)
    ):
        raise ValueError("development_identity")
    return case_map, key_map


def _journal(root):
    rows = [json.loads(line) for line in _bytes(root / "journal.jsonl").splitlines()]
    if (
        not rows
        or rows[0].get("event") != "campaign_started"
        or rows[0].get("track") != "lab"
    ):
        raise ValueError("development_journal_identity")
    stored, attempts, pending, blocked = {}, [], None, False
    phase_counts = Counter()
    seen = set()
    for row in rows[1:]:
        if row["event"] == "artifact_stored":
            artifact_bytes(root, row, seen)
            path = root.joinpath(*row["path"].split("/"))
            raw = _bytes(path)
            if sha(raw) != row["sha256"]:
                raise ValueError("artifact_changed_during_read")
            stored[row["path"]] = json.loads(raw)
        elif row["event"] == "provider_reserved":
            phase = row.get("contrast")
            if (
                pending
                or blocked
                or len(attempts) >= 84
                or phase not in {"D0", "D1", "D3"}
                or phase_counts[phase] >= PHASE_CAPS[phase]
                or row["attempt"] != f"s13-d-{len(attempts) + 1:04d}"
            ):
                raise ValueError("development_attempt_sequence")
            phase_counts[phase] += 1
            pending = {"reservation": row, "finish": None}
            attempts.append(pending)
        elif row["event"] == "provider_finished":
            if pending is None or row["attempt"] != pending["reservation"]["attempt"]:
                raise ValueError("development_completion_sequence")
            if row["outcome"] not in {"COMPLETED", "KNOWN_WITHHELD", "UNKNOWN"}:
                raise ValueError("development_completion_outcome")
            pending["finish"] = row
            blocked = row["outcome"] == "UNKNOWN"
            pending = None
        else:
            raise ValueError("development_journal_event")
    return stored, attempts


def _commentary(proposal, arm):
    if arm != "H":
        return None
    return {
        "questions": proposal.questions,
        "premise_ids": tuple(
            dict.fromkeys(
                (*proposal.support_premise_ids, *proposal.counterevidence_premise_ids)
            )
        ),
    }


def _cost(rows):
    finished = [row for row in rows if row["wall_seconds"] is not None]
    latency = [row["wall_seconds"] for row in finished]
    prompts = [
        row["usage"]["prompt_eval_count"]
        for row in finished
        if isinstance(row["usage"].get("prompt_eval_count"), int)
    ]
    outputs = [
        row["usage"]["eval_count"]
        for row in finished
        if isinstance(row["usage"].get("eval_count"), int)
    ]
    return {
        "raw_attempts": len(rows),
        "distinct_cases": len({row["case_id"] for row in rows}),
        "wall_seconds_sum": sum(latency),
        "wall_seconds_median": statistics.median(latency) if latency else None,
        "wall_seconds_range": [min(latency), max(latency)] if latency else None,
        "prompt_tokens_reported": sum(prompts),
        "prompt_usage_denominator": len(prompts),
        "output_tokens_reported": sum(outputs),
        "output_usage_denominator": len(outputs),
        "request_bytes": sum(row["request_bytes"] for row in rows),
        "raw_response_bytes": sum(row["raw_response_bytes"] or 0 for row in rows),
        "thinking_bytes_counted_not_retained": sum(
            row["thinking_bytes"] or 0 for row in rows
        ),
        "repeats_are_not_independent_cases": True,
    }


def _strata(attempts, labels, fields):
    groups, outcomes = defaultdict(list), defaultdict(list)
    for row in attempts:
        groups[tuple(row[field] for field in fields)].append(row)
    for row in labels:
        outcomes[tuple(row[field] for field in fields)].append(row)
    result = {}
    for identity, rows in groups.items():
        valid = outcomes[identity]
        distinct = len({row["case_id"] for row in rows})
        result["/".join(identity)] = {
            "label_only": {
                "raw_attempts": len(rows),
                "valid_proposals": len(valid),
                "primary_matches": sum(row["match"] for row in valid),
                "distinct_cases": distinct,
                "repeated_case_attempts": len(rows) - distinct,
                "raw_outcomes": dict(Counter(row["outcome"] for row in rows)),
                "repeats_are_not_independent_cases": True,
                "semantic_usefulness": "PENDING author review; label-only counts",
            },
            "cost": _cost(rows),
        }
    return result


def _rejected_visible(content):
    """Preserve rejected visible output without repairing its shape or duplicate IDs."""
    raw = content.encode("utf-8")
    value = {
        "raw_visible_proposal": None,
        "raw_visible_text": None,
        "raw_visible_bytes": len(raw),
        "raw_visible_sha256": sha(raw),
    }
    if len(raw) > MAX_VISIBLE_PROPOSAL_BYTES:
        value["raw_visible_status"] = (
            "budget_withheld; original provider artifact retained, not truncated"
        )
        return value
    try:
        parsed = parse_proposal(content)
    except (ValueError, TypeError):
        value.update(
            raw_visible_text=content,
            raw_visible_status="json_parse_failed; unique-key parser rejected original text",
        )
    else:
        if isinstance(parsed, dict):
            value.update(
                raw_visible_proposal=parsed,
                raw_visible_status="parsed_unvalidated; original schema or premise validation failed",
            )
        else:
            value.update(
                raw_visible_text=content,
                raw_visible_status="non_object_json; original visible text retained",
            )
    return value


def development_readout(development_root: Path, *, suite: Path = HERE) -> dict:
    """Verify finished development artifacts and count labels separately from usefulness.

    This function is read-only and must be called after the foreground batch has
    stopped. Pending/UNKNOWN remain visible accounting states, never replacements.
    It does not open any diagnostic path or infer semantic usefulness from labels.
    """
    root = named_root(development_root, "lab")
    cases, key = _development_inputs(Path(suite))
    stored, attempts = _journal(root)
    counts, labels, canonical, by_pillar, by_arm = (
        Counter(),
        Counter(),
        {},
        defaultdict(Counter),
        defaultdict(Counter),
    )
    latency, prompt_tokens, output_tokens, records, ledger_rows = [], [], [], [], []
    label_rows = []
    premise_occurrences = request_bytes = response_bytes = thinking_bytes = 0
    for attempt in attempts:
        row, finish = attempt["reservation"], attempt["finish"]
        case, arm = cases[row["case_id"]], row["arm"]
        scope_mode = row.get("scope_mode", "legacy")
        context, assessment, messages, schema = dispatch_spec(
            case, arm, scope_mode=scope_mode
        )
        prefix = "trials/" + row["trial"] + "/"
        wire = stored.get(prefix + row["attempt"] + "-request.json")
        expected = json.loads(
            DiagnosticBudget._request(
                None, messages, schema, {"temperature": 0.1, "num_ctx": 32768}, False
            )
        )
        if wire != expected or row["request_sha256"] != sha(encoded(expected)):
            raise ValueError("actual_dispatch_source_or_schema_changed")
        if (
            wire["model"] != MODEL
            or wire["options"] != OPTIONS
            or wire["truncate"]
            or wire["shift"]
        ):
            raise ValueError("dispatch_runtime_changed")
        canonical[case["id"]] = assessment.outcome
        counts["reserved"] += 1
        outcome = finish["outcome"] if finish else "PENDING"
        counts[outcome] += 1
        request_bytes += len(encoded(wire))
        if finish:
            latency.append(finish["wall_seconds"])
            response_bytes += finish.get("raw_response_bytes", 0)
            thinking_bytes += finish.get("thinking_bytes", 0)
            usage = finish.get("usage", {})
            if isinstance(usage.get("prompt_eval_count"), int):
                prompt_tokens.append(usage["prompt_eval_count"])
            if isinstance(usage.get("eval_count"), int):
                output_tokens.append(usage["eval_count"])
        ledger_rows.append(
            {
                "attempt": row["attempt"],
                "case_id": case["id"],
                "arm": arm,
                "phase": row["contrast"],
                "scope_mode": scope_mode,
                "source_commit": row.get("source_commit"),
                "outcome": outcome,
                "request_sha256": row["request_sha256"],
                "raw_input_sha256": sha(case["raw"].encode()),
                "request_bytes": len(encoded(wire)),
                "wall_seconds": finish.get("wall_seconds") if finish else None,
                "usage": deepcopy(finish.get("usage", {})) if finish else {},
                "raw_response_bytes": finish.get("raw_response_bytes")
                if finish
                else None,
                "thinking_bytes": finish.get("thinking_bytes") if finish else None,
            }
        )
        name = prefix + f"{row['ordinal']:02d}-{case['id']}-{arm}.json"
        record = stored.get(name)
        if outcome != "COMPLETED":
            continue
        answer = stored.get(prefix + row["attempt"] + ".json")
        if (
            not isinstance(answer, dict)
            or answer.get("done") is not True
            or answer.get("done_reason") != "stop"
        ):
            raise ValueError("completed_answer_missing_or_changed")
        if record is None:
            counts["result_record_missing_after_completed_send"] += 1
            continue
        if (
            record["case_id"] != case["id"]
            or record["pillar"] != case["pillar"]
            or record["arm"] != arm
            or record.get("scope_mode", "legacy") != scope_mode
            or record["d_outcome"] != assessment.outcome
        ):
            raise ValueError("result_identity_or_core_changed")
        if record["messages_sha256"] != sha(encoded(messages)) or record[
            "schema_sha256"
        ] != sha(encoded(schema)):
            raise ValueError("result_dispatch_identity_changed")
        item = deepcopy(record)
        item.update(
            phase=row["contrast"],
            scope_mode=scope_mode,
            attempt=row["attempt"],
            source_commit=row.get("source_commit"),
            artifact_path=name,
        )
        if record["structural_status"] != "valid":
            counts["structural_withheld"] += 1
            item.update(_rejected_visible(answer["message"]["content"]))
            item["provider_artifact_path"] = prefix + row["attempt"] + ".json"
            records.append(item)
            continue
        proposal = validate_proposal(
            parse_proposal(answer["message"]["content"]), assessment
        )
        if record["proposal"] != proposal.model_dump(mode="json"):
            raise ValueError("proposal_changed_from_provider_answer")
        commentary = _commentary(proposal, arm)
        report = build_report(case["raw"], context, commentary)
        if record["report"] != json.loads(
            export_json(case["raw"], context, report, commentary)
        ) or record["markdown"] != export_markdown(
            case["raw"], context, report, commentary
        ):
            raise ValueError("canonical_report_or_export_changed")
        if (
            report.assessment.approval_granted is not False
            or report.assessment.action_status != "no_actions_executed"
        ):
            raise ValueError("approval_or_action_changed")
        delivered = json.loads(wire["messages"][1]["content"])
        if delivered["untrusted_exact_source"] != case["raw"] or delivered[
            "bound_premises"
        ] != [p.model_dump(mode="json") for p in assessment.premises]:
            raise ValueError("premise_path_value_or_source_changed")
        premise_occurrences += len(assessment.premises)
        counts["reports_integrity_checked"] += 1
        expected_label = key[case["id"]]["outcome"]
        match = proposal.relationship == expected_label
        label_rows.append(
            {
                "case_id": case["id"],
                "arm": arm,
                "phase": row["contrast"],
                "scope_mode": scope_mode,
                "match": match,
            }
        )
        labels["primary_matches"] += match
        labels["valid_proposals"] += 1
        if expected_label == "declared_mismatch":
            labels["expected_mismatch"] += 1
            labels["missed_mismatch_labels"] += (
                proposal.relationship != "declared_mismatch"
            )
        if expected_label in {"declared_alignment", "not_applicable"}:
            labels["legitimate_controls"] += 1
            labels["false_mismatch_labels"] += (
                proposal.relationship == "declared_mismatch"
            )
        if expected_label in {"underdetermined", "conflicting_claims"}:
            labels["unknown_or_conflict_controls"] += 1
            labels["unknown_or_conflict_label_matches"] += match
        for group in (by_pillar[case["pillar"]], by_arm[arm]):
            group["valid_proposals"] += 1
            group["primary_matches"] += match
        records.append(item)
    return {
        "status": "development_only; no diagnostic inputs loaded",
        "review_status": REVIEW_STATUS,
        "semantic_usefulness": "PENDING implementation-author review; no automatic semantic scorer",
        "independent_review_count": 0,
        "raw_accounting": {
            name: counts[name]
            for name in (
                "reserved",
                "COMPLETED",
                "KNOWN_WITHHELD",
                "UNKNOWN",
                "PENDING",
                "structural_withheld",
                "result_record_missing_after_completed_send",
            )
        },
        "label_only_metrics": dict(labels),
        "label_only_by_pillar": {
            name: dict(value) for name, value in by_pillar.items()
        },
        "label_only_by_arm": {name: dict(value) for name, value in by_arm.items()},
        "stratification_by_phase": _strata(ledger_rows, label_rows, ("phase",)),
        "stratification_by_scope_mode": _strata(
            ledger_rows, label_rows, ("scope_mode",)
        ),
        "stratification_by_phase_scope_arm": _strata(
            ledger_rows, label_rows, ("phase", "scope_mode", "arm")
        ),
        "deterministic_typed_case_labels": {
            "distinct_cases": len(canonical),
            "matches": sum(
                value == key[name]["outcome"] for name, value in canonical.items()
            ),
        },
        "integrity": {
            "reports_checked": counts["reports_integrity_checked"],
            "exact_wire_and_report_premise_occurrences": premise_occurrences,
            "approval_false_and_no_actions_executed": counts[
                "reports_integrity_checked"
            ],
            "all_stored_artifact_hashes_verified": len(stored),
        },
        "cost": {
            "wall_seconds_sum": sum(latency),
            "wall_seconds_median": statistics.median(latency) if latency else None,
            "wall_seconds_range": [min(latency), max(latency)] if latency else None,
            "prompt_tokens_reported": sum(prompt_tokens),
            "prompt_usage_denominator": len(prompt_tokens),
            "output_tokens_reported": sum(output_tokens),
            "output_usage_denominator": len(output_tokens),
            "request_bytes": request_bytes,
            "raw_response_bytes": response_bytes,
            "thinking_bytes_counted_not_retained": thinking_bytes,
            "seed": "not fixed; no repeatability guarantee",
        },
        "attempts": ledger_rows,
        "records": records,
    }


def _normalized(record):
    if record.get("structural_status") == "withheld":
        rejected = record.get("raw_visible_proposal")
        fields = (
            "relationship",
            "rationale",
            "support_premise_ids",
            "counterevidence_premise_ids",
            "questions",
        )
        value = {
            name: deepcopy(rejected.get(name)) if isinstance(rejected, dict) else None
            for name in fields
        }
        value.update(
            output_status="structurally_withheld; original unverified provider text",
            raw_visible_status=record.get(
                "raw_visible_status", "original visible output unavailable"
            ),
            raw_visible_bytes=record.get("raw_visible_bytes"),
            raw_visible_sha256=record.get("raw_visible_sha256"),
        )
        if record.get("raw_visible_text") is not None:
            value["raw_visible_text"] = record["raw_visible_text"]
        return value
    proposal = record.get("proposal")
    if proposal is not None:
        return {
            name: deepcopy(proposal[name])
            for name in (
                "relationship",
                "rationale",
                "support_premise_ids",
                "counterevidence_premise_ids",
                "questions",
            )
        }
    assessment = record.get("assessment", record.get("report", {}).get("assessment"))
    if assessment is None:
        return {
            "relationship": None,
            "rationale": None,
            "support_premise_ids": [],
            "counterevidence_premise_ids": [],
            "questions": [],
            "output_status": "withheld_or_unavailable",
        }
    return {
        "relationship": assessment["outcome"],
        "rationale": assessment["report_sentence"],
        "support_premise_ids": deepcopy(assessment["decisive_premise_ids"]),
        "counterevidence_premise_ids": deepcopy(
            assessment["disconfirming_premise_ids"]
        ),
        "questions": [],
    }


def reviewer_packet(
    records: list[dict],
    inputs: list[dict],
    *,
    authored_key: list[dict] | None = None,
    seed: int = DEFAULT_SEED,
) -> tuple[dict, dict]:
    """Normalize caller-supplied records without loading a suite or exposing its key."""
    if type(seed) is not int or not 0 <= seed <= 2**32 or not 0 < len(records) <= 200:
        raise ValueError("review_packet_bound")
    cases = {case["id"]: deepcopy(case) for case in inputs}
    judgments = {item["id"]: deepcopy(item) for item in authored_key or []}
    if len(cases) != len(inputs) or len(judgments) != len(authored_key or []):
        raise ValueError("review_packet_duplicate_identity")
    order = list(range(len(records)))
    random.Random(seed).shuffle(order)
    items, links = [], []
    for index in order:
        record = records[index]
        case = cases[record["case_id"]]
        context = ReviewedContext.model_validate(case["context"])
        if case["id"] != context.case_id or case["pillar"] != context.pillar:
            raise ValueError("review_packet_case_identity")
        assessment = project(case["raw"], context)
        review_id = (
            "R13-"
            + sha(
                encoded(
                    {
                        "index": index,
                        "seed": seed,
                        "case_id": case["id"],
                        "output": _normalized(record),
                    }
                )
            )[:20]
        )
        items.append(
            {
                "review_id": review_id,
                "question": case["question"],
                "original_canonical_input": {
                    "raw": case["raw"],
                    "reviewed_context": deepcopy(case["context"]),
                },
                "canonical_premises": [
                    p.model_dump(mode="json") for p in assessment.premises
                ],
                "unverified_interpretation": _normalized(record),
                "adjudication": {
                    "reviewer_identifier": None,
                    "relationship": None,
                    "correct_mechanism": None,
                    "premise_relevance_and_entailment": None,
                    "counterevidence": None,
                    "source_scope_and_unknowns": None,
                    "useful_questions": None,
                    "unsupported_high_impact_claims": None,
                    "disagreement_with_authored_rubric": None,
                },
            }
        )
        links.append(
            {
                "review_id": review_id,
                "case_id": case["id"],
                "arm": record.get("arm"),
                "phase": record.get("phase"),
                "scope_mode": record.get("scope_mode", "legacy"),
                "generator": record.get(
                    "generator", "deterministic" if record.get("arm") == "D" else MODEL
                ),
                "attempt": record.get("attempt"),
                "artifact_path": record.get("artifact_path"),
                "provider_artifact_path": record.get("provider_artifact_path"),
                "source_commit": record.get("source_commit"),
                "record_sha256": sha(encoded(record)),
                "raw_input_sha256": sha(case["raw"].encode()),
                "authored_judgment": judgments.get(case["id"]),
                "review_status": REVIEW_STATUS,
            }
        )
    packet = {
        "format": "sprint13-common-review-packet-v1",
        "independent_human_review_status": "PENDING",
        "independently_reviewed_count": 0,
        "output_count": len(items),
        "masking": "Run/arm/generator/expected/linkage metadata concealed in a separate key. Literal opaque source case IDs and premise IDs remain unchanged; style may reveal templates. Generator anonymity is not guaranteed. This packet is not a completed independent blinded human study.",
        "source_boundary": "All source inputs are supplied unverified synthetic assertions; no actions executed or approval granted. A matching label or premise ID is not entailment, safety or usefulness.",
        "review_instructions": [
            "Review the original exact source and premise paths before judging each material claim.",
            "Score mechanism, relevant support, decisive counterevidence, timing/polarity, unknowns and bounded questions separately from relationship label.",
            "Record disagreement or ambiguous gold without modifying the frozen authored key.",
            "Complete adjudication before opening the separately held linkage/key; independent review remains PENDING until another human actually completes it.",
        ],
        "items": items,
    }
    key = {
        "format": "sprint13-common-review-key-v1",
        "handling": "Keep separate and concealed until adjudication; this is authored material, not independent agreement.",
        "shuffle_seed": seed,
        "review_status": REVIEW_STATUS,
        "independently_reviewed_count": 0,
        "items": links,
    }
    if len(encoded(packet)) > MAX_PACKET_BYTES or len(encoded(key)) > MAX_PACKET_BYTES:
        raise ValueError("review_packet_budget")
    return packet, key


def write_packet(packet_path: Path, key_path: Path, packet: dict, key: dict) -> None:
    """Exclusive fsynced creation; existing or partial review evidence is preserved."""
    paths = [Path(packet_path).absolute(), Path(key_path).absolute()]
    if paths[0] == paths[1]:
        raise ValueError("separate_review_key_required")
    for path in paths:
        plain_path(path)
        if path.exists():
            raise FileExistsError(path.name)
    for path, value in ((paths[1], key), (paths[0], packet)):
        data = encoded(value) + b"\n"
        if len(data) > MAX_PACKET_BYTES:
            raise ValueError("review_packet_budget")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
