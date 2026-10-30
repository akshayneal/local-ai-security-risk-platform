import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from test_schemas import GOVERNANCE_RESPONSE, SOC_RESPONSE

from app import governance_analyzer, main, soc_analyzer
from app.evidence_inspector import (
    AnalystEvidenceReview,
    build_inspector,
    capture_selection,
    collect_evidence,
    inspector_export,
    validate_analyst_review,
)
from app.reference_loader import get_relevant_references
from app.retrieval.contracts import (
    Authority,
    EvidenceRecord,
    RetrievedEvidence,
    Workflow,
)
from app.retrieval.orchestration import AnalysisReferences, retrieve_for_analysis
from app.schemas import GovernanceRiskRequest, GovernanceRiskResponse, SocAlertResponse
from app.soc_inputs import MicrosoftSocAdapter
from app.soc_query import soc_retrieval_query
from dashboard.exports import export_document, json_export, markdown_export


def report_for(soc=True, case_id="INSPECTOR-SYNTHETIC"):
    if soc:
        request = (
            MicrosoftSocAdapter()
            .normalize(
                {
                    "case_id": case_id,
                    "tables": {
                        "DeviceProcessEvents": [
                            {
                                "ActionType": "ProcessCreated",
                                "FileName": "notepad.exe",
                                "ProcessCommandLine": "PRIVATE-INPUT-VALUE",
                                "DeviceId": "synthetic-device",
                            }
                        ]
                    },
                }
            )
            .request
        )
        result = SocAlertResponse(
            **{
                **SOC_RESPONSE,
                "alert_id": case_id,
                "summary": "Model-proposed process observation.",
                "observed_evidence": ["A process creation was supplied."],
            }
        )
        mode = "soc_alert"
        query = soc_retrieval_query(request)
    else:
        request = GovernanceRiskRequest(
            system_name=case_id,
            system_purpose="Synthetic public information. PRIVATE-INPUT-VALUE",
        )
        result = GovernanceRiskResponse(
            **{
                **GOVERNANCE_RESPONSE,
                "system_name": case_id,
                "required_controls": ["Model says daily audits are required."],
            }
        )
        mode = "governance"
        query = request.model_dump_json()
    with collect_evidence(mode) as capture:
        retrieve_for_analysis(mode, query, 5, legacy_loader=get_relevant_references)
    if capture.records:
        payload = result.model_dump(mode="json")
        payload["source_references"] = [
            {
                "source_id": capture.records[0].evidence_id,
                "title": "Model forged title",
                "framework": "Model forged law",
                "relevance": "Model says verified",
            }
        ]
        # Build receives a typed analyzer result; this fixture tests citation status,
        # while real analyzer tests below verify source sanitation before capture.
        result = type(result).model_validate(payload)
    return request, result, build_inspector(capture, request, result)


@pytest.mark.parametrize("soc", [True, False])
def test_actual_candidates_citations_and_model_claims_remain_separate(soc, monkeypatch):
    monkeypatch.delenv("RETRIEVAL_BACKEND", raising=False)
    monkeypatch.delenv("RETRIEVAL_SHADOW_BACKEND", raising=False)
    _, _, report = report_for(soc)
    assert report.retrieval_status == "captured" and report.sources
    assert sum(s.cited for s in report.sources) == 1
    assert any(not s.cited for s in report.sources)
    assert all(s.provenance.title != "Model forged title" for s in report.sources)
    assert report.claims and all(
        c.assessment.provenance == "model_proposed"
        and c.assessment.relationship == "unassessed"
        and c.assessment.verification_status == "not_verified"
        for c in report.claims
    )
    assert report.review_required
    assert "PRIVATE-INPUT-VALUE" not in report.model_dump_json()
    assert "raw_log" not in report.model_dump_json() or not soc
    assert report.input_inventory[0].field_names
    if not soc:
        assert (
            next(
                c for c in report.claims if c.response_field == "required_controls"
            ).kind
            == "recommendation"
        )


def test_forbidden_and_unknown_source_payloads_do_not_enter_inspector():
    private = EvidenceRecord(
        evidence_id="PRIVATE-ID",
        source_id="PRIVATE-ID",
        title="PRIVATE-TITLE",
        content="PRIVATE-CONTENT",
        source_type="policy",
        source_family="Synthetic",
        authority=Authority.POLICY,
        policy_scope="secret",
        required_scopes={"secret"},
        workflows={Workflow.SOC},
    )
    hit = RetrievedEvidence(record=private, rank=1, score=100, retriever="lexical")
    request, result, _ = report_for()
    with collect_evidence("soc_alert") as capture:
        capture_selection(
            "soc_alert",
            "SECRET-QUERY-RAW",
            AnalysisReferences([], [hit], "SECRET-CONTEXT"),
        )
    report = build_inspector(capture, request, result)
    body = report.model_dump_json()
    assert not report.sources and report.retrieval_status == "partial"
    assert all(
        secret not in body
        for secret in (
            "PRIVATE-ID",
            "PRIVATE-TITLE",
            "PRIVATE-CONTENT",
            "SECRET-QUERY-RAW",
            "SECRET-CONTEXT",
        )
    )
    assert report.query_sha256 == hashlib.sha256(b"SECRET-QUERY-RAW").hexdigest()
    with collect_evidence("soc_alert") as capture:
        capture_selection(
            "soc_alert",
            "query",
            AnalysisReferences(
                [
                    {
                        "source_id": "FAKE",
                        "title": "SECRET-UNREVIEWED",
                        "content": "PRIVATE-CONTENT",
                    }
                ]
            ),
        )
    assert (
        "SECRET-UNREVIEWED"
        not in build_inspector(capture, request, result).model_dump_json()
    )


def test_capture_context_is_request_local_and_resets_after_errors():
    def worker(mode):
        with collect_evidence(mode) as capture:
            capture_selection(mode, mode, AnalysisReferences([]))
            return capture.query_sha256, capture.status

    with ThreadPoolExecutor(max_workers=2) as executor:
        values = list(executor.map(worker, ["soc_alert", "governance"]))
    assert values[0][0] != values[1][0] and all(v[1] == "captured" for v in values)
    with pytest.raises(RuntimeError), collect_evidence("soc_alert") as old:
        raise RuntimeError("fixture only")
    capture_selection("soc_alert", "later", AnalysisReferences([]))
    assert old.status == "not_observed"


@pytest.mark.parametrize("soc", [True, False])
def test_ui_api_adds_provenance_without_extra_generation_audit_or_public_shape_change(
    monkeypatch, soc
):
    request, fixture, _ = report_for(soc)
    module = soc_analyzer if soc else governance_analyzer
    calls = []
    output = fixture.model_dump(mode="json")
    output["source_references"] = []
    monkeypatch.setattr(
        module, "call_model_json", lambda **kw: calls.append(kw) or deepcopy(output)
    )
    audits = []
    monkeypatch.setattr(main, "write_audit_log", lambda **kw: audits.append(kw))
    client = TestClient(main.app)
    endpoint = "/analyze/soc-alert" if soc else "/analyze/governance"
    public = client.post(endpoint, json=request.model_dump(mode="json"))
    ui = client.post("/ui" + endpoint, json=request.model_dump(mode="json"))
    assert public.status_code == ui.status_code == 200
    assert public.json() == ui.json()["analysis"]
    assert "metadata" not in public.json()
    inspector = ui.json()["metadata"]["evidence_inspector"]
    assert inspector["retrieval_status"] == "captured"
    assert len(calls) == len(audits) == 2
    assert "evidence_inspector" not in json.dumps(audits)
    assert "user_prompt" not in json.dumps(
        inspector
    ) and "PRIVATE-INPUT-VALUE" not in json.dumps(inspector)


def test_analyst_review_is_bound_to_case_claim_and_eligible_evidence():
    _, _, report = report_for()
    proof = report.sources[0].provenance.evidence_id
    review = AnalystEvidenceReview(
        inspector_id=report.inspector_id,
        claim_id=report.claims[0].claim_id,
        relationship="directly_supports",
        evidence_ids=(proof,),
        note="Synthetic reviewer judgment",
    )
    assert validate_analyst_review(report, review).verification_status == "not_verified"
    for updates in (
        {"inspector_id": "another-case"},
        {"claim_id": "another-claim"},
        {"evidence_ids": ("FORBIDDEN",)},
        {"evidence_ids": ()},
    ):
        with pytest.raises(ValueError):
            validate_analyst_review(report, review.model_copy(update=updates))
    with pytest.raises(ValidationError):
        AnalystEvidenceReview(
            **{**review.model_dump(), "verification_status": "record_match_only"}
        )


def test_exports_add_safe_provenance_and_manual_judgments_without_raw_values():
    request, result, report = report_for()
    original = export_document(request, result, generated_at="fixed")
    assert "evidence_inspector" not in original
    document = export_document(
        request, result, generated_at="fixed", evidence_inspector=report
    )
    review = AnalystEvidenceReview(
        inspector_id=report.inspector_id,
        claim_id=report.claims[0].claim_id,
        relationship="related_but_insufficient",
        note="<script>[link](https://example.invalid)</script>",
    )
    document["evidence_inspector"] = inspector_export(report, [review])
    body = json_export(document)
    assert "PRIVATE-INPUT-VALUE" not in body
    assert document["analysis"] == original["analysis"]
    md = markdown_export(document)
    assert "Evidence Inspector" in md and "not verified" in md
    assert "<script>" not in md and "[link](https://example.invalid)" not in md


def test_claim_inventory_is_explicitly_bounded_without_marking_omitted_claims_verified():
    request, result, _ = report_for()
    payload = result.model_dump(mode="json")
    payload["recommended_investigation_steps"] = [f"Step {i}" for i in range(50)]
    payload["recommended_containment"] = [f"Proposal {i}" for i in range(50)]
    # Pydantic bounds individual arrays; use the actual schema maximum.
    result = SocAlertResponse.model_validate(payload)
    with collect_evidence("soc_alert") as capture:
        pass
    report = build_inspector(capture, request, result)
    assert len(report.claims) == 60 and report.total_claims > 60
    assert all(c.assessment.review_required for c in report.claims)
