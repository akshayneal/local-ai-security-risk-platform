"""Development boundary tests; no diagnostic imports or generation."""

import ast
import json
from pathlib import Path

import pytest

from app.adaptive_reports import build_report, export_json
from app.adaptive_semantics import ReviewedContext
from evals.adaptive_security_reasoning_v1 import runner

DEV = Path("evals/adaptive_security_reasoning_v1/dev_cases.json")


def cases():
    return json.loads(DEV.read_bytes())


@pytest.mark.parametrize("case", cases(), ids=lambda c: c["id"])
def test_paired_arms_have_identical_original_premises_and_only_extra_comparison(case):
    context, assessment, baseline, schema = runner.dispatch_spec(case, "M")
    _, same_assessment, hybrid, hybrid_schema = runner.dispatch_spec(case, "H")
    assert assessment == same_assessment
    assert schema == hybrid_schema
    assert baseline[0] == hybrid[0]
    m, h = json.loads(baseline[1]["content"]), json.loads(hybrid[1]["content"])
    comparison = h.pop("application_comparison")
    assert m == h
    assert m["untrusted_exact_source"] == case["raw"]
    assert m["bound_premises"] == [
        p.model_dump(mode="json") for p in assessment.premises
    ]
    assert comparison["outcome"] == assessment.outcome
    assert comparison["approval_granted"] is False
    assert context == ReviewedContext.model_validate(case["context"])


def test_development_runner_has_no_diagnostic_input_or_key_dependency():
    source = Path(runner.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = [
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    ]
    assert not any("holdout" in (module or "") for module in imports)
    for literal in [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]:
        assert (
            not literal.endswith(("author_key.json", "cases.json"))
            or literal == "dev_cases.json"
        )
    assert "dev_key.json" not in source


def test_correct_pointer_does_not_certify_arbitrary_prose_and_it_never_enters_report():
    case = cases()[0]
    context, assessment, _, _ = runner.dispatch_spec(case, "M")
    invented = {
        "relationship": assessment.outcome,
        "rationale": "The source is authenticated and the operator has executed an isolation.",
        "support_premise_ids": [assessment.premises[0].id],
        "counterevidence_premise_ids": [],
        "questions": ["Was the fictional permission independently checked?"],
    }
    proposal = runner.validate_proposal(invented, assessment)
    assert (
        proposal.rationale == invented["rationale"]
    )  # Membership alone is insufficient.
    commentary = {
        "questions": proposal.questions,
        "premise_ids": proposal.support_premise_ids,
    }
    report = build_report(case["raw"], context, commentary)
    serialized = export_json(case["raw"], context, report, commentary)
    assert invented["rationale"] not in serialized
    assert report.commentary_status == "withheld_unverified_model_prose"
    assert report.assessment == assessment


def test_unavailable_pointer_and_duplicate_pointer_are_rejected_without_repair():
    case = cases()[0]
    _, assessment, _, _ = runner.dispatch_spec(case, "M")
    raw = {
        "relationship": "declared_mismatch",
        "rationale": "Unverified scope contrast.",
        "support_premise_ids": ["PREM-" + "0" * 20],
        "counterevidence_premise_ids": [],
        "questions": [],
    }
    with pytest.raises(ValueError, match="unavailable_or_duplicate_premise"):
        runner.validate_proposal(raw, assessment)
    raw["support_premise_ids"] = [assessment.premises[0].id] * 2
    with pytest.raises(ValueError, match="unavailable_or_duplicate_premise"):
        runner.validate_proposal(raw, assessment)


def test_changed_source_snapshot_is_withheld_before_dispatch():
    case = cases()[0]
    case["raw"] += " "
    with pytest.raises(ValueError, match="Ineligible development input"):
        runner.dispatch_spec(case, "M")


@pytest.mark.parametrize(
    "field,value", [("id", "OTHER_CASE"), ("pillar", "governance")]
)
def test_outer_identity_cannot_relabel_bound_source(field, value):
    case = cases()[0]
    case[field] = value
    with pytest.raises(ValueError, match="Outer case identity"):
        runner.dispatch_spec(case, "M")


def test_duplicate_model_keys_are_not_silently_resolved():
    with pytest.raises(ValueError, match="duplicate_proposal_key"):
        runner.parse_proposal(
            '{"relationship":"declared_alignment","relationship":"declared_mismatch"}'
        )


def test_all_model_pointers_survive_commentary_quarantine_without_truncation():
    case = cases()[0]
    context, assessment, _, _ = runner.dispatch_spec(case, "M")
    ids = tuple(p.id for p in assessment.premises)
    assert len(ids) > 16
    commentary = {
        "questions": ["Which evidence would independently verify this scope?"],
        "premise_ids": ids,
    }
    report = build_report(case["raw"], context, commentary)
    assert report.assessment == assessment
    assert (
        json.loads(export_json(case["raw"], context, report, commentary))[
            "commentary_status"
        ]
        == "withheld_unverified_model_prose"
    )
