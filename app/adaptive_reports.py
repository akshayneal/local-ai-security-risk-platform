"""Deterministic report binding; arbitrary model prose is withheld from exports."""

import json
import re
from html import escape
from typing import Literal

from pydantic import Field, StrictStr

from app.adaptive_semantics import Assessment, ReviewedContext, project, sha
from app.support_contracts import SupportModel


class Commentary(SupportModel):
    questions: tuple[StrictStr, ...] = Field(max_length=6)
    premise_ids: tuple[StrictStr, ...] = Field(max_length=48)


class AdaptiveReport(SupportModel):
    assessment: Assessment
    commentary_status: Literal["not_requested", "withheld_unverified_model_prose"]
    commentary_sha256: StrictStr | None
    commentary_note: Literal[
        "Schema and premise membership do not establish entailment; generated prose is withheld."
    ] = "Schema and premise membership do not establish entailment; generated prose is withheld."
    independent_review: Literal["PENDING"] = "PENDING"


def _commentary(raw, assessment):
    if raw is None:
        return "not_requested", None
    if not isinstance(raw, dict):
        raise TypeError("commentary_schema")
    encoded = json.dumps(raw, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode()) > 8000:
        raise ValueError("commentary_budget")
    commentary = Commentary.model_validate(raw)
    if any(not q.strip() or len(q) > 500 for q in commentary.questions):
        raise ValueError("commentary_question_bound")
    available = {p.id for p in assessment.premises}
    if (
        len(set(commentary.premise_ids)) != len(commentary.premise_ids)
        or not set(commentary.premise_ids) <= available
    ):
        raise ValueError("commentary_premise_membership")
    return "withheld_unverified_model_prose", sha(encoded)


def build_report(
    raw: str, context: ReviewedContext, commentary: dict | None = None
) -> AdaptiveReport:
    assessment = project(raw, context)
    status, digest = _commentary(commentary, assessment)
    return AdaptiveReport(
        assessment=assessment, commentary_status=status, commentary_sha256=digest
    )


def _validate(raw, context, report, commentary):
    report = AdaptiveReport.model_validate(report.model_dump(mode="json"))
    if report.assessment.model_dump_json() != project(raw, context).model_dump_json():
        raise ValueError("canonical_report_mutation")
    if (report.commentary_status == "not_requested") != (
        report.commentary_sha256 is None
    ):
        raise ValueError("commentary_status_mutation")
    if report.commentary_sha256 is not None and not re.fullmatch(
        r"[a-f0-9]{64}", report.commentary_sha256
    ):
        raise ValueError("commentary_digest_mutation")
    if report.model_dump_json() != build_report(raw, context, commentary).model_dump_json():
        raise ValueError("report_commentary_provenance_mutation")
    return report


def export_json(
    raw, context, report: AdaptiveReport, commentary: dict | None = None
) -> str:
    return json.dumps(
        _validate(raw, context, report, commentary).model_dump(mode="json"),
        ensure_ascii=True,
        indent=2,
    )


def export_markdown(
    raw, context, report: AdaptiveReport, commentary: dict | None = None
) -> str:
    report = _validate(raw, context, report, commentary)

    def safe(value):
        return re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", escape(str(value))).replace(
            "\n", " "
        )

    assessment = report.assessment
    lines = [
        "# Experimental declared relationship",
        safe(assessment.report_sentence),
        safe(assessment.source_status),
        "## Exact supplied source",
    ]
    if assessment.raw is None:
        lines.append("Source withheld: ineligible classification, scope, or size.")
    else:
        lines.append(safe(assessment.raw))
    lines += ["## Canonical premises"]
    lines += [
        f"- {safe(p.id)} {safe(p.input_path)}#{safe(p.pointer)}: {safe(json.dumps(p.value, ensure_ascii=True))}"
        for p in assessment.premises
    ]
    lines += ["## Unassessed conditions"]
    lines += [f"- {safe(condition)}" for condition in assessment.unassessed_conditions]
    lines += [
        safe(report.commentary_status),
        safe(report.commentary_note),
        "No actions executed. No approval granted. Independent review PENDING.",
    ]
    return "\n".join(lines) + "\n"
