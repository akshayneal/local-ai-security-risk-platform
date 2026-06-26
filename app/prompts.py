from app.schemas import GovernanceRiskRequest, SocAlertRequest


SYSTEM_PROMPT = """
You are a local AI security assistant.

You support two workflows:
1. AI governance risk intake.
2. SOC alert triage.

Rules:
- Return only valid JSON.
- Do not include markdown.
- Do not include code fences.
- Do not invent facts that are not supported by the input or local reference context.
- Use the local reference context when it is relevant.
- If the local reference context is insufficient, clearly identify that as an evidence gap.
- Do not claim that an IP, domain, hash, CVE, malware family, threat actor, control, or policy is confirmed unless that fact appears in the input or local reference context.
- Distinguish between observed evidence, reasonable inference, and missing information.
- Prefer practical security controls and analyst actions.
- Recommendations should support human review, not replace accountable human judgment.
- Do not provide hidden chain-of-thought. Provide concise explanations only.
"""


def build_governance_prompt(
    request: GovernanceRiskRequest,
    reference_context: str,
) -> str:
    return f"""
Analyze the following proposed AI system for governance, security, privacy, and operational risk.

Use the local reference context when relevant.
Do not claim that a framework, policy, control, or checklist supports a recommendation unless that support appears in the local reference context.
If the reference context does not provide enough information, say so under evidence_gaps.
Keep the response practical and suitable for an AI governance or GRC review workflow.

Return JSON with these fields:
- system_name
- risk_level
- decision
- summary
- key_risks
- required_controls
- human_review_requirements
- logging_requirements
- evidence_gaps
- recommended_next_steps

Risk level must be one of:
low, medium, high, critical

Decision must be one of:
approved, needs_review, rejected

Local reference context:
{reference_context}

Input:
{request.model_dump_json(indent=2)}
"""


def build_soc_prompt(
    request: SocAlertRequest,
    reference_context: str,
) -> str:
    return f"""
Analyze the following SOC alert.

Use the local reference context when relevant.
Do not claim that an IP, domain, hash, CVE, malware family, or threat actor is confirmed malicious unless that fact appears in the input or local reference context.
If the reference context does not provide enough information, say so under evidence_gaps.
Keep containment recommendations proportional to the evidence and frame them for analyst review.
Do not recommend destructive, irreversible, or business-disruptive actions as automatic steps.

Return JSON with these fields:
- alert_id
- severity
- likely_incident_type
- summary
- mitre_mapping
- recommended_containment
- recommended_investigation_steps
- false_positive_considerations
- evidence_gaps
- analyst_note

Severity must be one of:
low, medium, high, critical

For mitre_mapping, use practical MITRE-style labels if possible, such as:
Credential Access, Initial Access, Persistence, Execution, Defense Evasion, Discovery, Lateral Movement, Exfiltration, Command and Control

Use careful language when the input suggests but does not prove compromise.
Prefer terms like "suspected," "possible," or "potential" unless the input or local reference context confirms malicious activity.
Do not describe access as unauthorized unless the input states that it was unauthorized or provides enough evidence to support that conclusion.

Containment recommendations should be conditional when legitimacy is not yet confirmed.
For example, say "consider disabling the account pending verification" rather than "disable the account" when the evidence is incomplete.

Local reference context:
{reference_context}

Input:
{request.model_dump_json(indent=2)}
"""