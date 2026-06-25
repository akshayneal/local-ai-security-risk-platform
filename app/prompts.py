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
- Do not invent facts that are not supported by the input.
- Clearly identify uncertainty and evidence gaps.
- Prefer practical security controls and analyst actions.
- Do not provide hidden chain-of-thought. Provide concise explanations only.
"""


def build_governance_prompt(request: GovernanceRiskRequest) -> str:
    return f"""
Analyze the following proposed AI system for governance, security, privacy, and operational risk.

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

Input:
{request.model_dump_json(indent=2)}
"""


def build_soc_prompt(request: SocAlertRequest) -> str:
    return f"""
Analyze the following SOC alert.

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

Input:
{request.model_dump_json(indent=2)}
"""