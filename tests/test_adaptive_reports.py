"""Source-to-report preservation and real negative mutation checks."""

import json

import pytest
from test_adaptive_semantics import prepare, specimen

from app import adaptive_reports as reports
from app import adaptive_semantics as semantic


def test_report_and_escaped_export_keep_source_and_typed_result():
    case = specimen()
    case["annotations"] = ["<script>alert('synthetic')</script> [fake](https://example.invalid)\n# heading"]
    raw, context = prepare(case)
    report = reports.build_report(raw, context)
    data = json.loads(reports.export_json(raw, context, report))
    assert data["assessment"]["raw"] == raw
    assert data["assessment"]["outcome"] == "declared_alignment"
    text = reports.export_markdown(raw, context, report)
    assert "<script>" not in text and "&lt;script&gt;" in text
    assert "\\[fake\\]\\(https://example.invalid\\)" in text
    assert "No actions executed. No approval granted." in text


def test_arbitrary_false_model_questions_are_withheld_even_with_valid_ids():
    raw, context = prepare(specimen())
    assessment = semantic.project(raw, context)
    commentary = {"questions": ["Why was the approved destructive action executed?"],
                  "premise_ids": [assessment.premises[0].id]}
    report = reports.build_report(raw, context, commentary)
    assert report.commentary_status == "withheld_unverified_model_prose"
    assert report.assessment == assessment
    assert report.commentary_sha256
    exported = reports.export_json(raw, context, report, commentary) + reports.export_markdown(raw, context, report, commentary)
    assert commentary["questions"][0] not in exported
    assert report.assessment.approval_granted is False


@pytest.mark.parametrize("commentary", [
    {"questions": ["Question"], "premise_ids": ["PREM-forged"]},
    {"questions": ["Question"], "premise_ids": [], "approval_granted": True},
    {"questions": [" "], "premise_ids": []},
    {"questions": ["x" * 501], "premise_ids": []},
    {"questions": ["x"] * 7, "premise_ids": []},
])
def test_commentary_contract_bounds_and_membership_fail_visibly(commentary):
    raw, context = prepare(specimen())
    with pytest.raises(ValueError):
        reports.build_report(raw, context, commentary)


@pytest.mark.parametrize("field,forged", [
    ("outcome", "declared_mismatch"), ("raw", "forged source"),
    ("approval_granted", True), ("report_sentence", "Approved for production"),
    ("decisive_premise_ids", ("PREM-forged",)),
])
def test_actual_canonical_mutations_are_rejected_at_export(field, forged):
    raw, context = prepare(specimen())
    report = reports.build_report(raw, context)
    modified = report.model_copy(update={"assessment": report.assessment.model_copy(update={field: forged})})
    with pytest.raises(ValueError):
        reports.export_json(raw, context, modified)
    with pytest.raises(ValueError):
        reports.export_markdown(raw, context, modified)


def test_actual_premise_value_identity_version_or_scope_mutations_are_rejected():
    raw, context = prepare(specimen())
    report = reports.build_report(raw, context)
    premise = report.assessment.premises[0]
    for field, value in [("value", "changed"), ("id", "PREM-" + "f" * 20),
                         ("source_revision", "r999"), ("input_path", "another_path")]:
        mutated = premise.model_copy(update={field: value})
        assessment = report.assessment.model_copy(update={"premises": (mutated, *report.assessment.premises[1:])})
        with pytest.raises(ValueError):
            reports.export_json(raw, context, report.model_copy(update={"assessment": assessment}))


def test_rejected_private_source_is_not_in_json_or_markdown_exports():
    raw, context = prepare(specimen())
    context_data = context.model_dump(mode="json")
    context_data["sources"][0]["classification"] = "private"
    context = semantic.ReviewedContext.model_validate(context_data)
    report = reports.build_report(raw, context)
    assert report.assessment.outcome == "projection_unavailable"
    exported = reports.export_json(raw, context, report) + reports.export_markdown(raw, context, report)
    assert "inventory_query" not in exported
    assert "svc-lime" not in exported


def test_off_by_default_new_modules_have_no_public_import_or_route():
    from pathlib import Path

    for name in ["app/main.py", "app/soc_analyzer.py", "app/governance_analyzer.py", "app/ai_security_analyzer.py"]:
        assert "adaptive_semantics" not in Path(name).read_text(encoding="utf-8")
        assert "adaptive_reports" not in Path(name).read_text(encoding="utf-8")


def test_commentary_original_digest_and_status_are_bound_at_export():
    raw, context = prepare(specimen())
    commentary = {"questions": ["What evidence would resolve timing?"], "premise_ids": []}
    report = reports.build_report(raw, context, commentary)
    for modified in [report.model_copy(update={"commentary_sha256": "0" * 64}),
                     report.model_copy(update={"commentary_status": "not_requested", "commentary_sha256": None})]:
        with pytest.raises(ValueError):
            reports.export_json(raw, context, modified, commentary)
    with pytest.raises(ValueError):
        reports.export_json(raw, context, report)
    with pytest.raises(ValueError):
        reports.export_json(raw, context, report, {"questions": ["changed"], "premise_ids": []})


def test_unreviewed_snapshot_source_bytes_are_withheld_from_exports():
    case = specimen()
    raw, context = prepare(case)
    changed = raw.replace("inventory_query", "UNREVIEWED_SYNTHETIC", 1)
    report = reports.build_report(changed, context)
    assert report.assessment.reason_codes == ("source_snapshot_mismatch",)
    assert report.assessment.raw is None
    assert report.assessment.raw_sha256 == semantic.sha(changed)
    assert "UNREVIEWED_SYNTHETIC" not in reports.export_json(changed, context, report)
    assert "UNREVIEWED_SYNTHETIC" not in reports.export_markdown(changed, context, report)


@pytest.mark.parametrize("amount,altered", [(1, True), (0, False)])
def test_integer_to_boolean_literal_type_mutation_fails_export(amount, altered):
    case = specimen()
    case["data"]["event"]["amount"] = amount
    raw, context = prepare(case)
    report = reports.build_report(raw, context)
    premises = tuple(p.model_copy(update={"value": altered}) if p.pointer == "/data/event/amount" else p
                     for p in report.assessment.premises)
    modified = report.model_copy(update={"assessment": report.assessment.model_copy(update={"premises": premises})})
    with pytest.raises(ValueError):
        reports.export_json(raw, context, modified)
    with pytest.raises(ValueError):
        reports.export_markdown(raw, context, modified)
