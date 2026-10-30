import json
from copy import deepcopy

import pytest
from test_analyst_corrections import correction
from test_evidence_inspector import report_for
from test_field_anchors import field_report

from app.evidence_inspector import (
    EvidenceInspectorReport,
    build_inspector,
    collect_evidence,
    inspector_export,
)
from dashboard.exports import export_document, json_export, markdown_export


def document_for(request, analysis, report, history=()):
    document = export_document(
        request, analysis, generated_at="fixed", evidence_inspector=report
    )
    document["evidence_inspector"] = inspector_export(report, corrections=history)
    return document


def test_new_fields_without_corrections_preserve_previous_export_shape_and_bytes():
    request, analysis, report = field_report()
    legacy = EvidenceInspectorReport.model_validate(
        report.model_dump(exclude={"field_anchors"})
    )
    old = document_for(request, analysis, legacy)
    new = document_for(request, analysis, report)
    assert old == new
    assert json_export(old) == json_export(new) and markdown_export(
        old
    ) == markdown_export(new)
    assert "review_summary" not in new["evidence_inspector"]
    assert "field_anchors" not in new["evidence_inspector"]


def test_latest_per_claim_summary_all_history_and_original_analysis_are_preserved():
    request, analysis, report = field_report()
    original = deepcopy(analysis.model_dump(mode="json"))
    target = next(c for c in report.claims if c.response_field == "summary")
    anchor = next(
        a
        for a in report.field_anchors
        if a.row_index == 1 and a.field_name == "UserPrincipalName"
    )
    history = correction(
        report,
        claim_id=target.claim_id,
        proposed_text="First analyst wording.",
        evidence_ids=(anchor.evidence_id,),
    )
    history = correction(
        report,
        history,
        claim_id=target.claim_id,
        proposed_text="Success belongs to a different supplied account.",
    )
    history = correction(
        report,
        history,
        claim_id=report.claims[0].claim_id,
        proposed_text="Separate severity clarification.",
    )
    document = document_for(request, analysis, report, history)
    summary = document["evidence_inspector"]["review_summary"]
    assert (
        summary["format"] == "analyst-review-summary-v1" and len(summary["claims"]) == 2
    )
    first = summary["claims"][0]
    assert first["original_response_field"] == "summary"
    assert first["original_claim_excerpt"] == analysis.summary
    assert (
        first["latest_proposed_text"]
        == "Success belongs to a different supplied account."
    )
    assert first["revision_count"] == 2 and first["evidence_linked"] is False
    assert first["verification_status"] == "not_verified"
    assert first["history_section"] == "correction_history"
    assert len(document["evidence_inspector"]["correction_history"]["revisions"]) == 3
    # A previously linked field still explains an earlier revision after latest unlinking.
    assert document["evidence_inspector"]["field_anchors"] == [
        anchor.model_dump(mode="json")
    ]
    payload = json_export(document)
    assert next(iter(json.loads(payload))) == "evidence_inspector"
    assert payload.index('"review_summary"') < payload.index('"analysis"')
    assert json.loads(payload)["analysis"] == original == document["analysis"]
    md = markdown_export(document)
    assert (
        md.index("## Analyst Correction Summary")
        < md.index("Likely incident type:")
        < md.index("## Summary")
    )
    assert md.index("## Summary") < md.index("## Analyst-Proposed Corrections")
    assert "First analyst wording." not in md.split("## Summary")[0]
    assert "First analyst wording." in md and "Supersedes revision" in md
    assert "Linked supplied field: SigninLogs" in md
    # Existing case identity can contain account/asset names; this feature adds no
    # field values to the Inspector summary, history or linked-anchor metadata.
    assert "PRIVATE-SERVICE" not in json.dumps(document["evidence_inspector"])
    baseline_md = markdown_export(document_for(request, analysis, report))
    assert "PRIVATE-SERVICE" in baseline_md  # Existing affected_asset identity.
    summary_md = md.split("## Analyst Correction Summary")[1].split("Severity:")[0]
    history_md = md.split("## Analyst-Proposed Corrections")[1]
    assert "PRIVATE-SERVICE" not in summary_md and "PRIVATE-SERVICE" not in history_md


@pytest.mark.parametrize("soc", [True, False])
def test_summary_works_for_generic_and_governance_and_escapes_untrusted_text(soc):
    request, analysis, report = report_for(soc)
    text = "[verified](javascript:alert(1))\r\n## forged\n<script>bad</script> &lt;fake&gt;"
    history = correction(report, proposed_text=text)
    document = document_for(request, analysis, report, history)
    md = markdown_export(document)
    assert "[verified](" not in md and "<script>" not in md and "\n## forged" not in md
    assert "&amp;lt;fake&amp;gt;" in md
    summary = document["evidence_inspector"]["review_summary"]
    assert summary["claims"][0]["latest_proposed_text"] == text
    assert "not redacted" in summary["notice"]
    assert "PRIVATE-INPUT-VALUE" not in json_export(document)


def test_original_claim_excerpt_is_bounded_and_truncation_is_explicit():
    request, analysis, _ = field_report()
    analysis = type(analysis).model_validate(
        {**analysis.model_dump(), "summary": "x" * 450 + "PRIVATE-TAIL"}
    )
    with collect_evidence("soc_alert") as capture:
        pass
    report = build_inspector(capture, request, analysis)
    target = next(c for c in report.claims if c.response_field == "summary")
    document = document_for(
        request, analysis, report, correction(report, claim_id=target.claim_id)
    )
    summary = document["evidence_inspector"]["review_summary"]["claims"][0]
    assert len(summary["original_claim_excerpt"]) == 400
    assert summary["original_claim_excerpt_truncated"] is True
    assert "PRIVATE-TAIL" not in str(summary)
    assert "bounded excerpt; truncated" in markdown_export(document)
    assert "PRIVATE-TAIL" in document["analysis"]["summary"]


def test_legacy_serialized_corrections_still_parse_without_added_fields():
    from app.evidence_inspector import AnalystCorrection, validate_correction_history

    _, _, report = field_report()
    legacy = EvidenceInspectorReport.model_validate(
        report.model_dump(exclude={"field_anchors"})
    )
    history = correction(
        legacy, evidence_ids=(legacy.input_inventory[0].observation_id,)
    )
    serialized = [r.model_dump_json() for r in history]
    restored = tuple(AnalystCorrection.model_validate_json(r) for r in serialized)
    assert validate_correction_history(report, restored) == history
    assert [r.model_dump_json() for r in restored] == serialized
