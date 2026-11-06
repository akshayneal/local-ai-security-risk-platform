"""Saved result/provenance checks; never rerun the diagnostic or model."""

import pytest

from evals.adaptive_security_reasoning_v1 import readout


def test_final_saved_artifact_and_source_inventory():
    result = readout.verify_inventory()
    assert result["saved_data_files_checked"] == len(readout.DATA_FILES)
    if not result["absent_local_roots_not_claimed_preserved"]:
        assert result["local_raw_files_checked"] == 79


def test_saved_diagnostic_matches_original_selection_and_score_without_replay():
    outputs = readout.read(readout.DOCS / "diagnostic_outputs.json")
    scores = readout.read(readout.DOCS / "diagnostic_scores.json")
    assert (
        readout.sha(readout.DOCS / "diagnostic_outputs.json")
        == scores["outcomes_sha256"]
    )
    assert outputs["selection"]["arm"] == "D"
    assert outputs["model_sends"] == scores["model_sends"] == 0
    assert len(outputs["outputs"]) == scores["denominator"] == 24
    assert scores["typed_matches"] == scores["integrity_matches"] == 24
    assert all(
        r["report"]["assessment"]["approval_granted"] is False
        for r in outputs["outputs"]
    )


def test_masked_packet_preserves_rejected_reply_and_has_no_answer_key_fields():
    packet = readout.read(readout.DOCS / "review_packet.json")
    key = readout.read(readout.DOCS / "reviewer_key.json")
    assert packet["output_count"] == len(packet["items"]) == len(key["items"]) == 60
    assert packet["independently_reviewed_count"] == 0
    assert {r["review_id"] for r in packet["items"]} == {
        r["review_id"] for r in key["items"]
    }
    rejected = [
        r
        for r in packet["items"]
        if r["unverified_interpretation"]
        .get("output_status", "")
        .startswith("structurally_withheld")
    ]
    assert len(rejected) == 1
    ids = rejected[0]["unverified_interpretation"]["support_premise_ids"]
    assert len(ids) > len(set(ids))  # The original failure was not repaired.
    for item in packet["items"]:
        assert {
            "arm",
            "phase",
            "generator",
            "authored_judgment",
            "expected",
        }.isdisjoint(item)
        assert all(value is None for value in item["adjudication"].values())


def test_same_size_saved_artifact_mutation_is_rejected(tmp_path):
    path = tmp_path / "result.json"
    path.write_text('{"state":"before"}', encoding="utf-8")
    expected = readout.sha(path)
    path.write_text('{"state":"after "}', encoding="utf-8")
    with pytest.raises(ValueError, match="artifact_hash_mismatch"):
        readout.verify_hashes(tmp_path, {"result.json": expected})


def test_readout_links_inventory_and_keeps_caps_without_reset():
    result = readout.read(readout.DOCS / "readout.json")
    assert result["artifact_manifest_sha256"] == readout.sha(
        readout.DOCS / "artifact_manifest.json"
    )
    assert result["raw_accounting"]["COMPLETED"] == 24
    assert (
        result["raw_accounting"]["PENDING"] == result["raw_accounting"]["UNKNOWN"] == 0
    )
    assert result["remaining_send_ceilings_unspent"] == {
        "development": 60,
        "diagnostic": 24,
        "global": 84,
    }
    assert result["model_generation_closed"] is True
    assert result["release"] == "NO-GO"
