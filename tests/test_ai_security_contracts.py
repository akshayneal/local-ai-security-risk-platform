"""Declarative input graphs and immutable advisory result contracts."""

import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.ai_security_contracts import AiSecurityRequest, AiSecurityResponse

ROOT = Path(__file__).resolve().parents[1]


def frozen_cases():
    return json.loads((ROOT / "evals/ai_security_v1/cases.json").read_bytes())


def case(case_id="RISK-1"):
    return copy.deepcopy(next(c for c in frozen_cases() if c["id"] == case_id))


@pytest.mark.parametrize("row", frozen_cases(), ids=lambda c: c["id"])
def test_frozen_input_properties(row):
    if row["expected"] == "input_rejected":
        with pytest.raises(ValidationError):
            AiSecurityRequest.model_validate(row["input"])
    else:
        request = AiSecurityRequest.model_validate(row["input"])
        assert request.application_id == row["input"]["application_id"]
        with pytest.raises(ValidationError):
            request.purpose = "mutated"


@pytest.mark.parametrize(
    "change",
    [
        "actor",
        "tool-component",
        "control-component",
        "control-evidence",
        "duplicate-capability",
        "duplicate-invoker",
        "cross-kind-id",
        "bad-enum",
        "blank-name",
        "oversize-count",
        "oversize-total",
        "unknown-grants",
    ],
)
def test_invalid_graph_and_resource_controls(change):
    design = case()["input"]
    if change == "actor":
        design["tools"][0]["invoker_actor_ids"] = ["UNKNOWN"]
    elif change == "tool-component":
        design["tools"][0]["component_id"] = "C_MODEL"
    elif change == "control-component":
        design["controls"][0]["component_ids"] = ["UNKNOWN"]
    elif change == "control-evidence":
        design["controls"][0]["implementation_evidence_ids"] = ["UNKNOWN"]
    elif change == "duplicate-capability":
        design["tools"][0]["capabilities"] = ["read", "read"]
    elif change == "duplicate-invoker":
        design["tools"][0]["invoker_actor_ids"] = ["USER", "USER"]
    elif change == "cross-kind-id":
        design["actors"][0]["id"] = "C_UI"
    elif change == "bad-enum":
        design["flows"][0]["boundary_crossing"] = "verified"
    elif change == "blank-name":
        design["application_name"] = "   "
    elif change == "oversize-count":
        design["components"] *= 20
    elif change == "oversize-total":
        design["components"] = [
            {"id": "C" + str(i), "kind": "model", "description": "界" * 400}
            for i in range(16)
        ]
        design["flows"] = []
        design["controls"] = []
        design["tools"] = []
        design["ingestion_surfaces"] = []
    elif change == "unknown-grants":
        design["policy_scopes"] = ["all"]
    with pytest.raises(ValidationError):
        AiSecurityRequest.model_validate(design)


@pytest.mark.parametrize(
    "field,value",
    [
        ("verification_status", "verified"),
        ("action_status", "exploited"),
        ("approval_granted", True),
        ("confidence", 0.99),
    ],
)
def test_proof_and_approval_fields_cannot_be_promoted(field, value):
    output = case()["stub_output"]
    output[field] = value
    with pytest.raises(ValidationError):
        AiSecurityResponse.model_validate(output)
