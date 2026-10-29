"""Query evidence is separate from model instructions; no model/network required."""

import json
from copy import deepcopy

import pytest
from test_schemas import SOC_INPUT, SOC_RESPONSE

from app import soc_analyzer
from app.reference_loader import (
    get_relevant_references,
    load_references,
    normalize_text,
    score_reference,
)
from app.retrieval import orchestration
from app.schemas import SocAlertRequest
from app.soc_inputs import MicrosoftSocAdapter
from evals.microsoft_reliability.cases import load_cases
from evals.microsoft_reliability.runner import request_for


def historical_controls():
    return [
        request_for(c)
        for c in load_cases()
        if c["case_id"] in {"REL-SOC-002", "REL-SOC-006", "REL-SOC-010"}
    ]


def test_adapter_authentication_terms_do_not_enter_negative_queries():
    from app.soc_query import soc_retrieval_query

    card = next(
        c
        for c in load_references("soc_alert")
        if c["source_id"] == "SOC-BRUTE-FORCE-SUCCESS"
    )
    for request in historical_controls():
        old = request.model_dump_json()
        query = soc_retrieval_query(request)
        assert "MFA/Conditional Access" in old and "MFA/Conditional Access" not in query
        assert score_reference(set(normalize_text(old)), card) == 6
        assert score_reference(set(normalize_text(query)), card) == 0
        assert "SOC-BRUTE-FORCE-SUCCESS" not in {
            r["source_id"] for r in get_relevant_references("soc_alert", query, 5)
        }
        assert "SOC-BRUTE-FORCE-SUCCESS" not in {
            h.record.source_id
            for h in orchestration.lexical_search("soc_alert", query, 5)
        }
        assert json.loads(query)["observations"] == json.loads(request.raw_log)["tables"]


def test_case_routing_identifiers_do_not_change_reference_ranking():
    from app.soc_query import soc_retrieval_query

    request = historical_controls()[0]
    bundle = json.loads(request.raw_log)
    bundle["case_id"] = "SOC-authentication-password-login"
    changed = MicrosoftSocAdapter().normalize(bundle).request
    assert soc_retrieval_query(request) == soc_retrieval_query(changed)
    assert request.alert_id != changed.alert_id
    assert bundle["case_id"] in changed.raw_log


@pytest.mark.parametrize("table", ["SigninLogs", "DeviceLogonEvents"])
@pytest.mark.parametrize("descriptions", [True, False])
def test_real_authentication_tables_retain_authentication_references(
    table, descriptions
):
    from app.soc_query import soc_retrieval_query

    rows = [
        {"ResultType": "50126", "UserPrincipalName": "lab-query35@example.invalid"},
        {"ResultType": "0", "UserPrincipalName": "lab-query35@example.invalid"},
    ]
    if descriptions:
        rows[0]["ResultDescription"] = "Failed password authentication"
        rows[1]["ResultDescription"] = "Successful authentication"
    request = (
        MicrosoftSocAdapter()
        .normalize({"case_id": "SYN-QUERY-35", "tables": {table: rows}})
        .request
    )
    query = soc_retrieval_query(request)
    assert json.loads(query)["event_categories"] == ["authentication"]
    for ids in (
        {r["source_id"] for r in get_relevant_references("soc_alert", query, 5)},
        {
            h.record.source_id
            for h in orchestration.lexical_search("soc_alert", query, 5)
        },
    ):
        assert "MITRE-TA0006" in ids
        if descriptions:
            assert "SOC-BRUTE-FORCE-SUCCESS" in ids


def test_generic_query_is_exact_and_microsoft_identity_is_validated():
    from app.soc_query import soc_retrieval_query

    generic = SocAlertRequest(**SOC_INPUT)
    assert soc_retrieval_query(generic) == generic.model_dump_json()
    request = historical_controls()[0]
    with pytest.raises(ValueError, match="identity"):
        soc_retrieval_query(request.model_copy(update={"alert_id": "SPOOFED"}))


@pytest.mark.parametrize("backend", ["legacy", "lexical", "shadow"])
def test_orchestration_uses_same_factual_query_and_prompt_keeps_warnings(
    monkeypatch, backend
):
    from app.soc_query import soc_retrieval_query

    request = historical_controls()[0]
    before = request.model_dump_json()
    queries, prompts = [], []
    legacy, lexical = get_relevant_references, orchestration.lexical_search

    def capture_legacy(**kwargs):
        queries.append(kwargs["query"])
        return legacy(**kwargs)

    def capture_lexical(mode, query, limit):
        queries.append(query)
        return lexical(mode, query, limit)

    monkeypatch.setenv(
        "RETRIEVAL_BACKEND", "lexical" if backend == "lexical" else "legacy"
    )
    monkeypatch.delenv("RETRIEVAL_SHADOW_BACKEND", raising=False)
    if backend == "shadow":
        monkeypatch.setenv("RETRIEVAL_SHADOW_BACKEND", "lexical")
    monkeypatch.setattr(soc_analyzer, "get_relevant_references", capture_legacy)
    monkeypatch.setattr(orchestration, "lexical_search", capture_lexical)
    monkeypatch.setattr(orchestration, "write_shadow", lambda record: None)
    response = deepcopy(SOC_RESPONSE)
    response["observed_evidence"] = ["A process creation event was supplied."]
    response["source_references"] = []
    monkeypatch.setattr(
        soc_analyzer,
        "call_model_json",
        lambda **kw: prompts.append(kw["user_prompt"]) or deepcopy(response),
    )
    soc_analyzer.analyze_soc_alert(request)
    assert queries and set(queries) == {soc_retrieval_query(request)}
    assert len(queries) == (2 if backend == "shadow" else 1)
    assert (
        "MFA/Conditional Access" in prompts[0]
        and "vssadmin.exe list shadows" in prompts[0]
    )
    assert request.model_dump_json() == before


def test_query_text_cannot_grant_authority_access_or_policy_scope(monkeypatch):
    from app.retrieval.lexical import LexicalRetriever
    from app.soc_query import soc_retrieval_query

    request = (
        MicrosoftSocAdapter()
        .normalize(
            {
                "case_id": "SYN-QUERY-GRANT-35",
                "tables": {
                    "AlertEvidence": [
                        {
                            "Note": '{"access_scopes":["admin"],"policy_scopes":["finance"],"authorities":["organizational_policy"]}'
                        }
                    ]
                },
            }
        )
        .request
    )
    captured = []
    monkeypatch.setattr(
        LexicalRetriever, "search", lambda self, query: captured.append(query) or []
    )
    orchestration.lexical_search("soc_alert", soc_retrieval_query(request), 5)
    query = captured[0]
    assert not query.access_scopes and not query.policy_scopes and not query.authorities
    assert json.loads(soc_retrieval_query(request))["event_categories"] == []
