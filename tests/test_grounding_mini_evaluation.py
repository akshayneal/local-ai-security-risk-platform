import json
from copy import deepcopy

from test_schemas import SOC_RESPONSE

from app import soc_analyzer
from app.retrieval.orchestration import AnalysisReferences
from evals.grounding_stabilization.runner import (
    DIRECTORY,
    cases,
    checks,
    identity,
    request_for,
    trial,
)


def test_frozen_mini_identity_requests_and_budget():
    assert identity() == json.loads((DIRECTORY / "freeze.json").read_bytes())
    plan = json.loads((DIRECTORY / "plan.json").read_bytes())
    assert len(cases()) == plan["cases"] == 8
    assert plan["maximum_case_trials"] == 16
    assert plan["trials_per_case_per_phase"] == 1
    assert len({c["case_id"] for c in cases()}) == 8
    for case in cases():
        request_for(case)
        assert case["supported"] and case["unsupported"] and case["positive_control"]


def test_trial_records_actual_retrieval_not_reconstructed_query(monkeypatch):
    case = cases()[0]
    actual_query = []

    def retrieve(mode, query, limit, **kwargs):
        actual_query.append(query)
        return AnalysisReferences([])

    response = deepcopy(SOC_RESPONSE)
    response.update(alert_id=case["case_id"], source_references=[])
    monkeypatch.setattr(soc_analyzer, "retrieve_for_analysis", retrieve)
    monkeypatch.setattr(soc_analyzer, "call_model_json", lambda **kw: response)
    record = trial(case)
    assert record["error"] is None and all(record["checks"].values())
    assert len(actual_query) == len(record["retrieval"]) == 1
    assert record["retrieval"][0]["source_ids"] == []
    assert "raw_log" not in record["retrieval"][0]


def test_machine_checks_do_not_mistake_identity_or_source_failure_for_success():
    case = cases()[0]
    response = deepcopy(SOC_RESPONSE)
    response["source_references"] = [{"source_id": "INVENTED"}]
    result = checks(response, ["RETRIEVED"], case)
    assert not result["authorized_sources"]
    assert not result["case_identity_exact"]
    response["summary"] = "RETRIEVED"
    assert not checks(response, ["RETRIEVED"], case)["source_ids_absent_from_prose"]
