"""Export only typed analyst results and case identity, never diagnostic traces."""

import json
import re
from datetime import UTC, datetime

from app.evidence_inspector import EvidenceInspectorReport, inspector_export
from app.schemas import (
    GovernanceRiskRequest,
    GovernanceRiskResponse,
    SocAlertRequest,
    SocAlertResponse,
)

DISCLAIMER = "Analyst aid only. Human review is required before any operational or governance decision. No actions were executed."
SOC_SECTIONS = (
    ("summary", "Summary"),
    ("observed_evidence", "Observed Evidence"),
    ("analyst_inferences", "Analyst Inferences"),
    ("evidence_gaps", "Evidence Gaps"),
    ("recommended_investigation_steps", "Recommended Investigation Steps"),
    ("recommended_containment", "Recommended Containment"),
    ("false_positive_considerations", "False Positive Considerations"),
    ("mitre_mapping", "MITRE-Style Mapping"),
    ("analyst_note", "Analyst Note"),
)
GOVERNANCE_SECTIONS = (
    ("summary", "Summary"),
    ("key_risks", "Key Risks"),
    ("required_controls", "Required Controls"),
    ("evidence_gaps", "Evidence Gaps"),
    ("human_review_requirements", "Human Review Requirements"),
    ("logging_requirements", "Logging Requirements"),
    ("recommended_next_steps", "Recommended Next Steps"),
)


def export_document(
    request: SocAlertRequest | GovernanceRiskRequest,
    analysis: SocAlertResponse | GovernanceRiskResponse,
    *,
    generated_at: str | None = None,
    evidence_inspector: EvidenceInspectorReport | None = None,
) -> dict:
    if isinstance(request, SocAlertRequest) and isinstance(analysis, SocAlertResponse):
        identity = {
            "alert_id": request.alert_id,
            "alert_type": request.alert_type,
            "affected_asset": request.affected_asset,
        }
        workflow = "SOC Investigation"
    elif isinstance(request, GovernanceRiskRequest) and isinstance(
        analysis, GovernanceRiskResponse
    ):
        identity = {"system_name": request.system_name}
        workflow = "AI System Risk Review"
    else:
        raise TypeError("Request and analysis workflows must match.")
    document = {
        "workflow": workflow,
        "generated_at": generated_at or datetime.now(UTC).isoformat(),
        "case": identity,
        "analysis": analysis.model_dump(mode="json"),
        "human_review": DISCLAIMER,
    }
    if evidence_inspector is not None:
        document["evidence_inspector"] = inspector_export(evidence_inspector)
    return document


def json_export(document: dict) -> str:
    return json.dumps(document, ensure_ascii=False, indent=2)


def _text(value: str) -> str:
    # Keep model/input prose from becoming active Markdown links or HTML.
    return re.sub(r"([\\`*_{}\[\]()<>#!|])", r"\\\1", value).replace("\n", " ")


def markdown_export(document: dict) -> str:
    analysis = document["analysis"]
    soc = document["workflow"] == "SOC Investigation"
    lines = [
        f"# {document['workflow']} Brief",
        "",
        f"Generated: {_text(document['generated_at'])}",
        "",
    ]
    lines.extend(
        f"{key.replace('_', ' ').title()}: {_text(value)}"
        for key, value in document["case"].items()
    )
    lines.extend(
        [
            "",
            f"{'Severity' if soc else 'Risk level'}: {analysis['severity' if soc else 'risk_level']}",
        ]
    )
    lines.append(
        f"{'Likely incident type' if soc else 'Decision'}: {_text(analysis['likely_incident_type' if soc else 'decision'])}"
    )
    for field, title in SOC_SECTIONS if soc else GOVERNANCE_SECTIONS:
        value = analysis.get(field, [])
        lines.extend(["", f"## {title}", ""])
        lines.extend(
            [f"- {_text(item)}" for item in value] or ["None provided."]
            if isinstance(value, list)
            else [_text(value)]
        )
    lines.extend(["", "## Source References", ""])
    for source in analysis.get("source_references", []):
        lines.append(
            f"- {_text(source['title'])} | {_text(source['framework'])} | {_text(source['source_id'])}: {_text(source['relevance'])}"
        )
    if not analysis.get("source_references"):
        lines.append("No source references returned.")
    inspector = document.get("evidence_inspector")
    if inspector is not None:
        lines.extend(
            [
                "",
                "## Evidence Inspector",
                "",
                "Model assertions remain unassessed. Retrieved guidance is not binding policy; a requirement is not proof of implementation.",
            ]
        )
        for source in inspector.get("sources", []):
            p = source["provenance"]
            lines.append(
                f"- {_text(p['title'])} | {_text(p['authority'])} | {'cited' if source['cited'] else 'retrieved, uncited'} | scope: {_text(p['policy_scope'] or 'not established')}"
            )
        lines.append(
            f"Model assertions shown: {inspector['claims_shown']} / {inspector['total_claims']}; analyst verification required."
        )
        for review in inspector.get("analyst_reviews", []):
            lines.append(
                f"- Analyst-recorded judgment (not verified), claim {_text(review['claim_id'])}: {_text(review['relationship'])}. Evidence: {_text(', '.join(review['evidence_ids']))}. Note: {_text(review['note'])}"
            )
    lines.extend(
        [
            "",
            "Retrieved sources provide context and guidance; retrieval alone does not make every source claim authoritative.",
            "",
            DISCLAIMER,
            "",
        ]
    )
    return "\n".join(lines)
