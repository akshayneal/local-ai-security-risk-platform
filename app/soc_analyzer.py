import json
from typing import Any

from pydantic import ValidationError

from app.analysis_trace import AnalysisTrace
from app.observables import critical_observables
from app.ollama_client import call_model_json
from app.output_policy import (
    OutputPolicyError,
    replace_untrusted_source_ids,
    soc_contract_violations,
    text_values,
    untrusted_source_ids,
)
from app.prompts import build_soc_prompt
from app.reference_loader import (
    clean_inline_source_citations,
    format_references_for_prompt,
    get_reference_ids,
    get_relevant_references,
    sanitize_source_references,
)
from app.schemas import SocAlertRequest, SocAlertResponse


def analyze_soc_alert(
    request: SocAlertRequest,
    *,
    references: list[dict[str, Any]] | None = None,
    trace: AnalysisTrace | None = None,
) -> SocAlertResponse:
    query = request.model_dump_json()

    if references is None:
        references = get_relevant_references(mode="soc_alert", query=query, limit=5)

    reference_context = format_references_for_prompt(references)

    prompt = build_soc_prompt(
        request=request,
        reference_context=reference_context,
    )

    original_input = request.model_dump(mode="json")
    blocked = untrusted_source_ids(original_input, get_reference_ids(references))
    generation_prompt = prompt
    for generation in range(2):
        if trace is not None:
            trace.capture("generation_started", None, generation=generation)
            if generation == 1:
                trace.repair_failed = True  # Cleared only on a valid final response.
        try:
            raw_result = call_model_json(
                user_prompt=generation_prompt,
                response_schema=SocAlertResponse.model_json_schema(),
            )
        except Exception:
            if trace is not None and generation == 1:
                trace.repair_failed = True
            raise

        processed = _process_output(raw_result, references, blocked, trace, generation)
        violations = soc_contract_violations(processed, original_input)
        response = None
        if not violations:
            try:
                response = SocAlertResponse.model_validate(processed)
            except ValidationError as exc:
                if generation == 1:
                    if trace is not None:
                        trace.repair_failed = True
                    raise OutputPolicyError(
                        ["repaired response failed schema validation"]
                    ) from exc
                if any(
                    error["loc"][0] != "observed_evidence" for error in exc.errors()
                ):
                    raise
                violations = ["observed_evidence failed item/count bounds"]

        if trace is not None:
            trace.capture("policy_violations", violations, generation=generation)
        if response is not None:
            if trace is not None:
                trace.repair_failed = False
                trace.capture(
                    "final_response",
                    response.model_dump(mode="json"),
                    generation=generation,
                )
            return response
        if generation == 1:
            if trace is not None:
                trace.repair_failed = True
            raise OutputPolicyError(violations)
        if trace is not None:
            trace.repair_attempted = True
        authoritative = {
            kind: sorted(values)
            for kind, values in critical_observables(
                "\n".join(text_values(original_input))
            ).items()
        }
        # Use the already neutralized original prompt, never raw failed output.
        generation_prompt = (
            prompt
            + "\n"
            + (
                "APPLICATION OUTPUT REPAIR: Regenerate the entire SOC JSON response once.\n"
                "The previous generation failed these machine-checked contracts:\n"
                + json.dumps(violations)
                + "\n"
                "Supply at least one nonblank supported observed_evidence item. "
                "Only repeat critical observables exactly as supplied in the original request; "
                "do not correct, invent, or substitute values. Observables need not all be repeated.\n"
                "Authoritative input observables (not reputation or vulnerability verification):\n"
                + json.dumps(authoritative, sort_keys=True)
            )
        )
    raise AssertionError("Bounded generation loop exhausted unexpectedly")


def _process_output(
    raw_result: dict[str, Any],
    references: list[dict[str, Any]],
    blocked: set[str],
    trace: AnalysisTrace | None,
    generation: int,
) -> dict[str, Any]:
    if trace is not None:
        trace.capture("raw_model", raw_result, generation=generation)

    source_ids = get_reference_ids(references) | get_reference_ids(
        raw_result.get("source_references", [])
    )

    raw_result = clean_inline_source_citations(
        raw_result=raw_result,
        source_ids=source_ids,
        fields_to_clean=[
            "summary",
            "likely_incident_type",
            "mitre_mapping",
            "recommended_containment",
            "recommended_investigation_steps",
            "false_positive_considerations",
            "evidence_gaps",
            "analyst_note",
            "observed_evidence",
            "analyst_inferences",
        ],
    )

    if trace is not None:
        trace.capture("citation_cleaned", raw_result, generation=generation)

    raw_result["source_references"] = sanitize_source_references(
        returned_sources=raw_result.get("source_references", []),
        retrieved_references=references,
    )
    if trace is not None:
        trace.capture("source_sanitized", raw_result, generation=generation)

    raw_result = replace_untrusted_source_ids(raw_result, blocked)
    if trace is not None:
        trace.capture("output_policy", raw_result, generation=generation)
    return raw_result
