import json

import pytest
from pydantic import ValidationError

from app.retrieval.contracts import EvidenceRecord, RetrievalQuery
from app.retrieval.legacy import LegacyRetriever
from app.support_assessor import assess_support
from app.support_contracts import EvidenceClaim
from evals.provenance import ROOT
from evals.soc_policy_design.contracts import (
    DraftPolicyReviewProposal,
    DraftPolicyReviewRequest,
)


@pytest.mark.parametrize("unit", ["synthetic-unit-a", "synthetic-unit-b"])
def test_design_fixture_unit_scope_isolation_and_requirement_not_approval(unit):
    fixture = json.loads(
        (ROOT / "Documentation/policy_review_design/scenarios.json").read_bytes()
    )
    records = [EvidenceRecord.model_validate(r) for r in fixture["records"]]
    query = RetrievalQuery(
        text="containment approval role evidence retention",
        **fixture["trusted_scenario_context"][unit],
    )
    hits = LegacyRetriever(records).search(query)
    assert len(hits) == 1 and hits[0].record.policy_scope == unit
    assertion = json.loads(hits[0].record.content)["assertions"][0]
    claim = EvidenceClaim(claim_id="REQUIREMENT", components=[assertion])
    assert assess_support(claim, query, hits).relationship == "directly_supports"
    granted = EvidenceClaim(
        claim_id="GRANTED",
        components=[
            dict(
                assertion,
                predicate="approval_granted",
                value=True,
                kind="implementation",
            )
        ],
    )
    assert (
        assess_support(granted, query, hits).relationship == "related_but_insufficient"
    )
    denied = RetrievalQuery(
        text="containment approval", workflow=query.workflow, policy_scopes={unit}
    )
    assert not LegacyRetriever(records).search(denied)


def test_draft_contract_cannot_accept_grants_or_claim_application_approval():
    request = {
        "scenario": "synthetic-unit-a",
        "incident_context": "Synthetic incident",
        "proposed_action": "Consider isolation",
    }
    assert DraftPolicyReviewRequest(**request).scenario == "synthetic-unit-a"
    with pytest.raises(ValidationError):
        DraftPolicyReviewRequest(**request, access_scopes=["admin"])
    with pytest.raises(ValidationError):
        DraftPolicyReviewProposal(
            verification_needs=("Review actual approval",),
            application_approval_status="granted",
        )
    assert DraftPolicyReviewProposal(
        verification_needs=("Review policy applicability",)
    ).human_review_required
