"""Synthetic readout/packet checks only; no provider or diagnostic source access."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from app.adaptive_reports import build_report, export_json, export_markdown
from app.adaptive_semantics import ReviewedContext, project
from evals.adaptive_security_reasoning_v1 import review
from evals.adaptive_security_reasoning_v1.runner import dispatch_spec
from evals.adaptive_security_reasoning_v1.transport import (
    DiagnosticBudget,
    DiagnosticStop,
    encoded,
    sha,
)


def case(identity="T9X4"):
    envelope = {
        "schema_version": "adaptive-security/1",
        "case_id": identity,
        "pillar": "soc",
        "source": {"id": "ASSERTION-" + identity, "revision": "r1"},
        "data": {
            "event": {
                "operation": "status_read",
                "result": "completed",
                "principal": "svc_demo",
                "asset": "synthetic_asset",
                "source": "192.0.2.50",
                "destination": "198.51.100.61",
                "endpoint": "https://lookup.example/status",
                "time": "2026-08-17T09:04:00+00:00",
                "amount": 2,
            },
            "authorization": {
                "status": "reported_authorized",
                "operation": "status_read",
                "principal": "svc_demo",
                "asset": "synthetic_asset",
                "endpoint": "https://lookup.example/status",
                "window_start": "2026-08-17T09:00:00+00:00",
                "window_end": "2026-08-17T09:10:00+00:00",
            },
        },
        "counterclaims": [],
        "annotations": [],
    }
    raw = encoded(envelope).decode()
    return {
        "id": identity,
        "pillar": "soc",
        "question": "What declared relationship do these assertions support?",
        "raw": raw,
        "context": {
            "case_id": identity,
            "pillar": "soc",
            "input_path": "raw_log",
            "raw_sha256": sha(raw.encode()),
            "sources": [
                {
                    "id": "ASSERTION-" + identity,
                    "revision": "r1",
                    "scope": identity,
                    "classification": "public_synthetic",
                    "authority": "synthetic_caller_assertion",
                    "current": True,
                }
            ],
            "requirement_reviewed": False,
        },
    }


def proposal(assessment):
    return {
        "relationship": assessment.outcome,
        "rationale": "The reported operation and authorization scope align within the supplied window; neither source is authenticated.",
        "support_premise_ids": list(assessment.decisive_premise_ids),
        "counterevidence_premise_ids": list(assessment.disconfirming_premise_ids),
        "questions": [
            "Can a human verify the original source and the bounded event scope?"
        ],
    }


def record(source, arm="M", *, phase="D0"):
    context, assessment, messages, schema = dispatch_spec(source, arm)
    generated = proposal(assessment)
    commentary = (
        None
        if arm == "M"
        else {
            "questions": generated["questions"],
            "premise_ids": list(
                dict.fromkeys(
                    [
                        *generated["support_premise_ids"],
                        *generated["counterevidence_premise_ids"],
                    ]
                )
            ),
        }
    )
    report = build_report(source["raw"], context, commentary)
    return {
        "case_id": source["id"],
        "pillar": source["pillar"],
        "arm": arm,
        "phase": phase,
        "d_outcome": assessment.outcome,
        "messages_sha256": sha(encoded(messages)),
        "schema_sha256": sha(encoded(schema)),
        "proposal": generated,
        "report": json.loads(export_json(source["raw"], context, report, commentary)),
        "markdown": export_markdown(source["raw"], context, report, commentary),
        "structural_status": "valid",
    }


def development_artifacts(tmp_path):
    source = case()
    _context, assessment, messages, schema = dispatch_spec(source, "M")
    root = tmp_path / "willow-sprint13-development"
    directory = root / "trials/d0"
    directory.mkdir(parents=True)
    rows = [{"event": "campaign_started", "track": "lab", "lab_cap": 84}]

    def store(name, value):
        data = encoded(value) + b"\n"
        (directory / name).write_bytes(data)
        rows.append(
            {
                "event": "artifact_stored",
                "bytes": len(data),
                "sha256": sha(data),
                "path": "trials/d0/" + name,
            }
        )

    wire = json.loads(
        DiagnosticBudget._request(
            None, messages, schema, {"temperature": 0.1, "num_ctx": 32768}, False
        )
    )
    store("s13-d-0001-request.json", wire)
    rows.append(
        {
            "event": "provider_reserved",
            "attempt": "s13-d-0001",
            "case_id": source["id"],
            "arm": "M",
            "contrast": "D0",
            "trial": "d0",
            "ordinal": 1,
            "source_commit": "a" * 40,
            "request_sha256": sha(encoded(wire)),
        }
    )
    answer = {
        "model": "qwen3:8b",
        "done": True,
        "done_reason": "stop",
        "message": {
            "role": "assistant",
            "content": encoded(proposal(assessment)).decode(),
        },
    }
    store("s13-d-0001.json", answer)
    rows.append(
        {
            "event": "provider_finished",
            "attempt": "s13-d-0001",
            "outcome": "COMPLETED",
            "wall_seconds": 2.5,
            "raw_response_bytes": 1000,
            "thinking_bytes": 0,
            "usage": {"prompt_eval_count": 40, "eval_count": 9},
        }
    )
    store("01-T9X4-M.json", record(source))
    journal = root / "journal.jsonl"
    journal.write_bytes(b"".join(encoded(row) + b"\n" for row in rows))
    suite = tmp_path / "suite"
    suite.mkdir()
    key = [
        {
            "id": source["id"],
            "outcome": assessment.outcome,
            "mechanism": "AUTHOR_KEY_SENTINEL_HIDDEN",
            "review_status": review.REVIEW_STATUS,
        }
    ]
    frozen = {}
    for leaf, value in (("dev_cases.json", [source]), ("dev_key.json", key)):
        data = encoded(value) + b"\n"
        (suite / leaf).write_bytes(data)
        frozen["evals/adaptive_security_reasoning_v1/" + leaf] = sha(data)
    (suite / "freeze.json").write_bytes(encoded({"sha256": frozen}))
    return root, suite, source, rows


def test_development_readout_verifies_exact_paths_values_reports_and_cost(tmp_path):
    root, suite, source, _ = development_artifacts(tmp_path)
    result = review.development_readout(root, suite=suite)
    assessment = project(
        source["raw"], ReviewedContext.model_validate(source["context"])
    )
    assert (
        result["raw_accounting"]["COMPLETED"]
        == result["raw_accounting"]["reserved"]
        == 1
    )
    assert result["label_only_metrics"] == {
        "primary_matches": 1,
        "valid_proposals": 1,
        "legitimate_controls": 1,
        "false_mismatch_labels": 0,
    }
    assert result["integrity"]["exact_wire_and_report_premise_occurrences"] == len(
        assessment.premises
    )
    assert result["cost"]["wall_seconds_sum"] == 2.5
    assert result["cost"]["prompt_tokens_reported"] == 40
    assert result["cost"]["output_tokens_reported"] == 9
    assert result["semantic_usefulness"].startswith("PENDING")
    assert result["independent_review_count"] == 0


@pytest.mark.parametrize("change", ["source", "report", "artifact", "frozen_key"])
def test_changed_dispatch_source_export_or_frozen_key_is_rejected(tmp_path, change):
    root, suite, _, rows = development_artifacts(tmp_path)
    if change == "frozen_key":
        (suite / "dev_key.json").write_bytes(b"[]")
    else:
        leaf = "s13-d-0001-request.json" if change == "source" else "01-T9X4-M.json"
        path = root / "trials/d0" / leaf
        value = json.loads(path.read_bytes())
        if change == "source":
            payload = json.loads(value["messages"][1]["content"])
            payload["untrusted_exact_source"] += " "
            value["messages"][1]["content"] = encoded(payload).decode()
        else:
            value["report"]["assessment"]["approval_granted"] = True
        data = encoded(value) + b"\n"
        path.write_bytes(data)
        if change != "artifact":
            for row in rows:
                if row.get("path") == "trials/d0/" + leaf:
                    row.update(bytes=len(data), sha256=sha(data))
            (root / "journal.jsonl").write_bytes(
                b"".join(encoded(row) + b"\n" for row in rows)
            )
    with pytest.raises((ValueError, DiagnosticStop)):
        review.development_readout(root, suite=suite)


@pytest.mark.parametrize(
    "malformation", ["duplicate_premise", "duplicate_json_key", "oversized_text"]
)
def test_rejected_visible_output_remains_in_packet_without_becoming_valid(
    tmp_path, malformation
):
    root, suite, source, rows = development_artifacts(tmp_path)
    directory = root / "trials/d0"
    answer_path = directory / "s13-d-0001.json"
    original = json.loads(answer_path.read_bytes())
    rejected = json.loads(original["message"]["content"])
    rejected["relationship"] = "declared_mismatch"
    rejected["rationale"] = (
        "ORIGINAL_REJECTED_WORDS; declared scope allegedly mismatches."
    )
    premise = rejected["support_premise_ids"][0]
    rejected["support_premise_ids"] = [premise, premise]
    if malformation == "duplicate_json_key":
        text = '{"relationship":"declared_alignment","relationship":"declared_mismatch","rationale":"ORIGINAL_REJECTED_WORDS"}'
    elif malformation == "oversized_text":
        text = "X" * (review.MAX_VISIBLE_PROPOSAL_BYTES + 1)
    else:
        text = encoded(rejected).decode()
    original["message"]["content"] = text
    failed_path = directory / "01-T9X4-M.json"
    failed = json.loads(failed_path.read_bytes())
    for field in ("proposal", "report", "markdown"):
        failed.pop(field)
    failed.update(structural_status="withheld", error_type="ValueError")
    for path, value in ((answer_path, original), (failed_path, failed)):
        data = encoded(value) + b"\n"
        path.write_bytes(data)
        for row in rows:
            if row.get("path") == "trials/d0/" + path.name:
                row.update(bytes=len(data), sha256=sha(data))
    (root / "journal.jsonl").write_bytes(b"".join(encoded(row) + b"\n" for row in rows))
    preserved = answer_path.read_bytes(), failed_path.read_bytes()
    result = review.development_readout(root, suite=suite)
    assert (
        result["raw_accounting"]["COMPLETED"]
        == result["raw_accounting"]["structural_withheld"]
        == 1
    )
    assert result["label_only_metrics"] == {}
    assert result["integrity"]["reports_checked"] == 0
    assert len(result["records"]) == 1
    packet, key = review.reviewer_packet(
        result["records"],
        [source],
        authored_key=[{"id": source["id"], "outcome": "EXPECTED_KEY_SENTINEL"}],
    )
    output = packet["items"][0]["unverified_interpretation"]
    assert (
        output["output_status"]
        == "structurally_withheld; original unverified provider text"
    )
    assert output["raw_visible_sha256"] == sha(text.encode())
    if malformation == "duplicate_premise":
        assert output["relationship"] == "declared_mismatch"
        assert output["support_premise_ids"] == [premise, premise]
        assert "ORIGINAL_REJECTED_WORDS" in output["rationale"]
    elif malformation == "duplicate_json_key":
        assert output["relationship"] is None
        assert output["raw_visible_text"] == text
        assert "unique-key parser rejected" in output["raw_visible_status"]
    else:
        assert output["relationship"] is None
        assert "raw_visible_text" not in output
        assert "not truncated" in output["raw_visible_status"]
        assert output["raw_visible_bytes"] == len(text.encode())
    assert b"EXPECTED_KEY_SENTINEL" not in encoded(packet)
    assert all(
        field not in packet["items"][0]
        for field in ("arm", "phase", "generator", "authored_judgment")
    )
    assert key["items"][0]["arm"] == "M"
    assert key["items"][0]["provider_artifact_path"].endswith("s13-d-0001.json")
    assert preserved == (answer_path.read_bytes(), failed_path.read_bytes())


def test_packet_masks_metadata_and_key_without_changing_literal_inputs():
    inputs = [case(), case("J8R2")]
    records = [record(inputs[0], "M"), record(inputs[0], "H"), record(inputs[1], "M")]
    records.append(
        {
            "case_id": inputs[1]["id"],
            "pillar": "soc",
            "arm": "D",
            "phase": "OFFLINE",
            "assessment": project(
                inputs[1]["raw"], ReviewedContext.model_validate(inputs[1]["context"])
            ).model_dump(mode="json"),
        }
    )
    judgments = [
        {
            "id": item["id"],
            "outcome": "AUTHORED_EXPECTED_SENTINEL",
            "mechanism": "KEY_ONLY_EXPLANATION",
        }
        for item in inputs
    ]
    original = deepcopy((inputs, records, judgments))
    packet, key = review.reviewer_packet(records, inputs, authored_key=judgments)
    assert (inputs, records, judgments) == original
    wire = encoded(packet)
    assert (
        b"AUTHORED_EXPECTED_SENTINEL" not in wire
        and b"KEY_ONLY_EXPLANATION" not in wire
    )
    assert all(
        "arm" not in item and "phase" not in item and "generator" not in item
        for item in packet["items"]
    )
    assert {item["arm"] for item in key["items"]} == {"M", "H", "D"}
    assert {item["review_id"] for item in packet["items"]} == {
        item["review_id"] for item in key["items"]
    }
    assert len({item["review_id"] for item in packet["items"]}) == 4
    assert (
        packet["independently_reviewed_count"]
        == key["independently_reviewed_count"]
        == 0
    )
    assert packet["independent_human_review_status"] == "PENDING"
    raw_inputs = {item["raw"] for item in inputs}
    assert {
        item["original_canonical_input"]["raw"] for item in packet["items"]
    } == raw_inputs
    assert "anonymity is not guaranteed" in packet["masking"]


def test_packet_shuffle_is_repeatable_and_seed_changes_order():
    source = case()
    records = [dict(record(source), attempt=f"s13-d-{i + 1:04d}") for i in range(8)]
    first = review.reviewer_packet(records, [source], seed=13013)
    second = review.reviewer_packet(records, [source], seed=13013)
    assert first == second
    third = review.reviewer_packet(records, [source], seed=13014)
    assert [item["attempt"] for item in first[1]["items"]] != [
        item["attempt"] for item in third[1]["items"]
    ]
    assert {item["attempt"] for item in first[1]["items"]} == {
        item["attempt"] for item in third[1]["items"]
    }


def test_exclusive_packet_and_separate_key_preserve_existing_evidence(tmp_path):
    source = case()
    packet, key = review.reviewer_packet([record(source)], [source])
    packet_path, key_path = tmp_path / "packet.json", tmp_path / "separate/key.json"
    review.write_packet(packet_path, key_path, packet, key)
    original = packet_path.read_bytes(), key_path.read_bytes()
    with pytest.raises(FileExistsError):
        review.write_packet(packet_path, key_path, packet, key)
    assert original == (packet_path.read_bytes(), key_path.read_bytes())
    with pytest.raises(ValueError, match="separate"):
        review.write_packet(tmp_path / "same.json", tmp_path / "same.json", packet, key)


def test_review_module_has_no_diagnostic_content_loader_or_semantic_keyword_scorer():
    source = Path(review.__file__).read_text()
    assert "adaptive_security_holdout_v1" not in source
    assert "author_key.json" not in source and 'cases.json"' not in source.replace(
        'dev_cases.json"', ""
    )
    assert "keyword" not in source.lower()
