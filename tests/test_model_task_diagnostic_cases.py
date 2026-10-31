"""Prospective Elm controls are valid, bounded and distinct from prior dev data."""

import json
from pathlib import Path

from app.ai_security_analyzer import category_flow_scope, reviewability_gaps
from app.ai_security_contracts import AiSecurityRequest
from app.evidence_ledger import build_evidence_ledger
from app.schemas import GovernanceRiskRequest, SocAlertRequest
from evals.model_task_diagnostic_v1 import runner

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "evals/model_task_diagnostic_v1/cases.json").read_bytes())


def test_prospective_literal_development_bytes_match_current_commit():
    freeze = runner.verify_plan()
    assert set(freeze["sha256"]) == {
        "evals/model_task_diagnostic_v1/cases.json",
        "evals/model_task_diagnostic_v1/rubric.md",
        "evals/model_task_diagnostic_v1/plan.json",
    }


def test_four_prospective_cases_have_full_fact_and_forbidden_gold():
    assert len(CASES) == 4
    assert len({case["id"] for case in CASES}) == 4
    for case in CASES:
        assert case["version"] == 1
        assert len(case["expected_facts"]) == 6
        assert len({f["id"] for f in case["expected_facts"]}) == 6
        assert len(case["forbidden_inferences"]) >= 5
        assert case["source_scope"]["authority"] == "caller_supplied_unverified"
        assert "not independent review" in case["source_scope"]["status"]


def test_same_incoming_category_exists_for_positive_and_negative_graph():
    for case in CASES[:2]:
        request = AiSecurityRequest.model_validate(case["input"])
        assert reviewability_gaps(request) == ()
        assert "prompt_injection" in category_flow_scope(request)[1]
        assert all(f.classification == "public" for f in request.flows)
        assert not request.tools
        assert not any(c.kind == "retrieval_store" for c in request.components)
        assert sum(f["scope"] == "selected_input_path" for f in case["expected_facts"]) == 4


def test_new_technical_graph_topologies_differ_from_older_development_graphs():
    # Deliberately no Aster input access, even in this deterministic comparison.
    old_paths = (
        "evals/inference_lab_v1/cases.json",
        "evals/cross_pillar_v1/cases.json",
        "evals/reliability_v1/cases.json",
    )

    def topology(case):
        request = case["input"]
        kinds = {c["id"]: c["kind"] for c in request["components"]}
        return sorted((kinds[f["source_id"]], kinds[f["target_id"]]) for f in request["flows"])

    old = [
        case
        for path in old_paths
        for case in json.loads((ROOT / path).read_bytes())
        if case["pillar"] == "ai_security"
    ]
    for case in CASES[:2]:
        assert all(case["input"] != other["input"] for other in old)
        assert all(topology(case) != topology(other) for other in old)


def test_ledger_soc_case_has_exact_typed_roles_and_no_projection_omission():
    request = SocAlertRequest.model_validate(CASES[2]["input"])
    ledger = build_evidence_ledger(request)
    facts = {fact.input_path: fact for fact in ledger.facts}
    prefix = "raw_log.tables.DeviceNetworkEvents[0]."
    assert ledger.complete
    assert facts[prefix + "LocalIP"].value == "192.0.2.170"
    assert facts[prefix + "LocalPort"].value == 51234
    assert facts[prefix + "RemoteIP"].value == "203.0.113.170"
    assert facts[prefix + "RemotePort"].value == 9445
    assert facts[prefix + "ActionType"].value == "ConnectionFailed"
    assert facts[prefix + "InitiatingProcessId"].role == "initiating_process"
    assert facts[prefix + "Protocol"].value == "TCP"
    assert "four TCP reachability attempts" in facts["observed_behavior"].value


def test_governance_polarities_are_supplied_prose_not_machine_resolved_states():
    request = GovernanceRiskRequest.model_validate(CASES[3]["input"])
    ledger = build_evidence_ledger(request)
    assert ledger.complete
    fact = next(f for f in ledger.facts if f.input_path == "human_review_process")
    assert fact.value == request.human_review_process
    assert fact.state == "supplied"
    for text in ("7 of 7", "explicitly absent", "proposed, not implemented", "are unknown"):
        assert text in fact.value
    assert "one offline P2 rehearsal" in request.business_impact
