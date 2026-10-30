from copy import deepcopy

import pytest
from pydantic import ValidationError
from test_analyst_corrections import correction
from test_evidence_inspector import report_for
from test_schemas import SOC_RESPONSE

from app.evidence_inspector import (
    EvidenceInspectorReport,
    SuppliedFieldAnchor,
    build_inspector,
    collect_evidence,
    fingerprint,
    validate_correction_history,
)
from app.schemas import SocAlertResponse
from app.soc_inputs import MicrosoftSocAdapter


def field_report(case="FIELD-CASE", rows=None):
    bundle = {
        "case_id": case,
        "tables": {
            "SigninLogs": rows
            if rows is not None
            else [
                {
                    "UserPrincipalName": "PRIVATE-OPERATOR",
                    "IPAddress": "203.0.113.76",
                    "ResultType": "50126",
                    "Empty": "",
                    "Null": None,
                    "Zero": 0,
                    "Flag": False,
                },
                {"UserPrincipalName": "PRIVATE-SERVICE", "ResultType": "0"},
            ]
        },
    }
    request = MicrosoftSocAdapter().normalize(bundle).request
    result = SocAlertResponse(
        **{
            **SOC_RESPONSE,
            "alert_id": case,
            "summary": "The operator successfully authenticated.",
        }
    )
    with collect_evidence("soc_alert") as capture:
        pass
    return request, result, build_inspector(capture, request, result)


def test_stable_field_paths_presence_privacy_and_original_evidence_preserved():
    request, result, report = field_report()
    original = deepcopy(request.model_dump())
    assert report == field_report()[2]
    anchors = {(a.row_index, a.field_name): a for a in report.field_anchors}
    assert len(anchors) == 9 and len({a.evidence_id for a in anchors.values()}) == 9
    assert (
        anchors[0, "Empty"].value_presence
        == anchors[0, "Null"].value_presence
        == "empty"
    )
    assert (
        anchors[0, "Zero"].value_presence
        == anchors[0, "Flag"].value_presence
        == "nonempty"
    )
    assert (1, "Empty") not in anchors
    assert (
        anchors[0, "UserPrincipalName"].evidence_id
        != anchors[1, "UserPrincipalName"].evidence_id
    )
    assert {a.evidence_id for a in anchors.values()}.isdisjoint(
        a.evidence_id for a in field_report("OTHER-CASE")[2].field_anchors
    )
    assert "PRIVATE-" not in str([a.model_dump() for a in report.field_anchors])
    assert "203.0.113.76" not in str(report.field_anchors)
    assert all(
        a.parent_observation_id in {r.observation_id for r in report.input_inventory}
        for a in report.field_anchors
    )
    assert (
        request.model_dump() == original
        and result.summary == "The operator successfully authenticated."
    )


@pytest.mark.parametrize("path", [(0, "Missing"), (99, "UserPrincipalName")])
def test_missing_fields_or_rows_cannot_be_linked(path):
    _, _, report = field_report()
    fake = fingerprint(
        [report.request_sha256, "SigninLogs", *path, "supplied-field-v1"]
    )
    with pytest.raises(ValueError):
        correction(report, evidence_ids=(fake,))


def test_field_links_row_links_and_legacy_correction_identity_are_compatible():
    _, _, report = field_report()
    legacy = EvidenceInspectorReport.model_validate(
        report.model_dump(exclude={"field_anchors"})
    )
    assert legacy.field_anchors == ()
    row = correction(legacy, evidence_ids=(legacy.input_inventory[0].observation_id,))
    assert validate_correction_history(report, row) == row
    revised = correction(
        report, row, evidence_ids=(report.field_anchors[0].evidence_id,)
    )
    assert revised[0] == row[0] and revised[1].correction_id == row[0].correction_id
    assert revised[1].supersedes_revision_id == row[0].revision_id
    assert revised[1].verification_status == "not_verified"
    with pytest.raises(ValueError):
        correction(
            field_report("OTHER-CASE")[2],
            evidence_ids=(report.field_anchors[0].evidence_id,),
        )
    with pytest.raises(ValueError):
        correction(
            report_for(False)[2], evidence_ids=(report.field_anchors[0].evidence_id,)
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"request_sha256": "forged"},
        {"table": "OtherTable"},
        {"row_index": 99},
        {"field_name": "Missing"},
        {"parent_observation_id": "other-row"},
        {"evidence_id": "forged"},
        {"authority": "organizational_policy"},
    ],
)
def test_forged_anchor_metadata_rejected(changes):
    _, _, report = field_report()
    payload = report.model_dump(mode="json")
    payload["field_anchors"][0].update(changes)
    with pytest.raises(ValidationError):
        EvidenceInspectorReport.model_validate(payload)


def test_tampered_request_and_model_copy_cannot_bypass_validation():
    _, _, report = field_report()
    payload = report.model_dump(mode="json")
    payload["request_sha256"] = "altered"
    with pytest.raises(ValidationError):
        EvidenceInspectorReport.model_validate(payload)
    forged = report.field_anchors[0].model_copy(update={"field_name": "Missing"})
    with pytest.raises(ValidationError):
        correction(report.model_copy(update={"field_anchors": (forged,)}))
    with pytest.raises(ValidationError):
        SuppliedFieldAnchor(
            **{**report.field_anchors[0].model_dump(), "raw_value": "PRIVATE"}
        )
