from copy import deepcopy

import pytest
from pydantic import ValidationError
from test_evidence_inspector import report_for

from app.evidence_inspector import (
    AnalystCorrection,
    CorrectionCategory,
    append_analyst_correction,
    fingerprint,
    validate_correction_history,
)


def correction(report, history=(), **changes):
    return append_analyst_correction(
        report,
        history,
        **{
            "claim_id": report.claims[0].claim_id,
            "category": CorrectionCategory.INCIDENT,
            "proposed_text": "A lone connection does not establish Command and Control.",
            "rationale": "The supplied observation is insufficient for that incident inference.",
            **changes,
        },
    )


def modified(item, **changes):
    payload = {**item.model_dump(mode="json", exclude={"revision_id"}), **changes}
    return AnalystCorrection(**payload, revision_id=fingerprint(payload))


@pytest.mark.parametrize("soc", [True, False])
def test_correction_and_second_revision_preserve_original_and_first(soc):
    _, analysis, report = report_for(soc)
    original = deepcopy((analysis.model_dump(), report.model_dump()))
    first = correction(report)
    second = correction(
        report,
        first,
        category=CorrectionCategory.IMPLEMENTATION,
        proposed_text="The requirement is stated; implementation is not established.",
        rationale="A binding requirement is not evidence of completed implementation.",
        evidence_ids=(report.input_inventory[0].observation_id,),
    )
    assert second[0] == first[0] and len(first) == 1 and len(second) == 2
    assert second[1].revision == 2
    assert second[1].correction_id == first[0].correction_id
    assert second[1].supersedes_revision_id == first[0].revision_id
    assert second[1].revision_id != first[0].revision_id
    assert second[1].verification_status == "not_verified"
    assert second[1].provenance == "analyst_recorded"
    assert (analysis.model_dump(), report.model_dump()) == original


@pytest.mark.parametrize(
    "changes",
    [
        {"inspector_id": "OTHER-RESULT"},
        {"claim_id": "OTHER-CLAIM"},
        {"original_response_field": "another_field"},
        {"original_claim_fingerprint": "forged"},
        {"correction_id": "other-chain"},
        {"evidence_ids": ["FORBIDDEN-SOURCE"]},
        {"revision": 2},
        {"supersedes_revision_id": "missing-predecessor"},
    ],
)
def test_invalid_binding_and_first_revision_lineage_rejected(changes):
    _, _, report = report_for()
    item = correction(report)[0]
    with pytest.raises(ValueError):
        validate_correction_history(report, (modified(item, **changes),))


def test_cross_case_evidence_and_cross_claim_predecessors_rejected():
    _, _, report = report_for()
    _, _, other = report_for(case_id="OTHER-CASE")
    with pytest.raises(ValueError):
        correction(report, evidence_ids=(other.input_inventory[0].observation_id,))
    with pytest.raises(ValueError):
        correction(report, claim_id=other.claims[0].claim_id)
    first = correction(report)
    other_claim = correction(report, first, claim_id=report.claims[1].claim_id)
    forged = modified(
        other_claim[-1], revision=2, supersedes_revision_id=first[0].revision_id
    )
    with pytest.raises(ValueError):
        validate_correction_history(report, (*first, forged))
    with pytest.raises(ValueError):
        validate_correction_history(report, (*first, first[0]))


@pytest.mark.parametrize(
    "changes",
    [
        {"proposed_text": ""},
        {"proposed_text": " \n\t"},
        {"rationale": ""},
        {"rationale": " \n"},
        {"proposed_text": "x" * 4097},
        {"rationale": "x" * 2001},
    ],
)
def test_empty_and_oversized_content_rejected(changes):
    _, _, report = report_for()
    with pytest.raises(ValidationError):
        correction(report, **changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"verification_status": "verified"},
        {"provenance": "deterministic_record_match"},
        {"policy_scope": "grant"},
        {"revision": True},
    ],
)
def test_editable_fields_cannot_grant_verification_or_authority(changes):
    _, _, report = report_for()
    with pytest.raises(ValidationError):
        modified(correction(report)[0], **changes)


def test_content_tampering_and_model_copy_bypass_rejected():
    _, _, report = report_for()
    item = correction(report)[0]
    with pytest.raises(ValidationError):
        AnalystCorrection(**{**item.model_dump(), "proposed_text": "Altered wording"})
    with pytest.raises(ValidationError):
        validate_correction_history(
            report, (item.model_copy(update={"verification_status": "verified"}),)
        )
