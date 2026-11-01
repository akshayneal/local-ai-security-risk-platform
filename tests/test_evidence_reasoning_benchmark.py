"""Actual dispatch isolation and leakage checks, with no live generation."""

import json
from copy import deepcopy

import pytest

from app import evidence_reasoning as reasoning
from evals.deterministic_evidence_v1 import transport as original
from evals.evidence_reasoning_v1 import runner
from evals.evidence_reasoning_v1.transport import PHASES, track


def cases():
    return runner.read("dev_cases.json")


def test_new_identities_disjoint_and_neutral():
    dev, holdout = cases(), runner.read("diagnostic_cases.json")
    assert len(dev) == 6 and len(holdout) == 12
    assert not {c["id"] for c in dev} & {c["id"] for c in holdout}
    for group, count in ((dev, 2), (holdout, 4)):
        for pillar in runner.RESPONSES:
            assert sum(c["pillar"] == pillar for c in group) == count
        for case in group:
            assert all(
                word not in case["id"].upper()
                for word in ("POSITIVE", "NEGATIVE", "BENIGN", "BOUNDED", "GAP")
            )
            assert set(case) <= {
                "id",
                "pillar",
                "input",
                "required_paths",
                "optional_paths",
                "irrelevant_paths",
                "question",
                "classification",
            }


@pytest.mark.parametrize("case", range(6))
def test_gold_sentinels_never_reach_wire_and_schema_is_only_D1_difference(case):
    case = cases()[case]
    tampered = deepcopy(case)
    tampered.update(
        expected_verdict="SCORER_SENTINEL_X92",
        gold="GOLD_SENTINEL_J48",
        rubric="RUBRIC_SENTINEL_L61",
    )
    original_spec = runner.dispatch_spec(case, "linked")
    _, selected, messages, narrow = runner.dispatch_spec(tampered, "linked")
    assert messages == original_spec[2]
    _, _, baseline_messages, full = runner.dispatch_spec(case, "bundle")
    assert baseline_messages == messages
    assert narrow != full
    wire = original.DiagnosticBudget._request(
        None, messages, narrow, {"temperature": 0.1, "num_ctx": 32768}, False
    )
    assert all(
        s.encode() not in wire
        for s in ("SCORER_SENTINEL_X92", "GOLD_SENTINEL_J48", "RUBRIC_SENTINEL_L61")
    )
    decoded = json.loads(wire)
    assert decoded["think"] is False and decoded["stream"] is True
    assert decoded["shift"] is False and decoded["truncate"] is False
    assert decoded["options"]["num_predict"] == 4096
    # Actual transport preflight enforces conservative complete-context bounds.
    original.DiagnosticBudget._request(
        None, baseline_messages, full, {"temperature": 0.1, "num_ctx": 32768}, False
    )
    assert selected.facts


@pytest.mark.parametrize("case", range(6))
def test_compact_context_changes_only_optional_facts_with_complete_report(case):
    case = cases()[case]
    req, selected, full, _ = runner.dispatch_spec(case, "linked")
    _, _, compact, _ = runner.dispatch_spec(case, "compact")
    assert full[0] == compact[0]
    # Required facts cannot be removed by this predeclared arm.
    full_text, compact_text = json.dumps(full), json.dumps(compact)
    for fact in selected.facts:
        assert fact.fact_id in full_text
        assert (fact.fact_id in compact_text) == (
            fact.input_path in selected.required_paths
        )
    proposal = {
        "verdict": "insufficient_or_mixed_evidence",
        "support_fact_ids": [],
        "counterevidence_fact_ids": [],
        "rationale": "Human review is required to resolve the supplied evidence.",
        "uncertainties": ["Operational validation has not occurred."],
        "human_verification_actions": ["Review the original evidence with its owner."],
    }
    report = reasoning.project(req, selected, proposal)
    assert len(report.facts) == len(selected.facts)


def test_phase_identity_and_nontransferable_limits_reuse_audited_transport(tmp_path):
    assert PHASES == {"D1": "D0", "D2": "D1", "D3": "D3", "H1": "A"}
    assert [track(p) for p in PHASES] == ["lab", "lab", "lab", "acceptance"]
    with pytest.raises(ValueError):
        track("release")
    with original.CampaignLedger(
        tmp_path / "campaign",
        lab_journal=tmp_path / "lab/journal.jsonl",
        acceptance_journal=tmp_path / "diagnostic/journal.jsonl",
    ) as campaign:
        for i in range(24):
            campaign.reserve(track="lab", attempt=f"test-{i}")
            campaign.finish(track="lab", attempt=f"test-{i}", outcome="COMPLETED")
        with pytest.raises(original.CampaignStop):
            campaign.reserve(track="lab", attempt="test-25")
        campaign.reserve(track="acceptance", attempt="holdout-1")
        campaign.finish(track="acceptance", attempt="holdout-1", outcome="UNKNOWN")
        with pytest.raises(original.CampaignStop):
            campaign.reserve(track="acceptance", attempt="holdout-2")
    with pytest.raises(original.CampaignStop, match="Outstanding"):
        original.CampaignLedger(
            tmp_path / "campaign",
            lab_journal=tmp_path / "lab/journal.jsonl",
            acceptance_journal=tmp_path / "diagnostic/journal.jsonl",
        )
