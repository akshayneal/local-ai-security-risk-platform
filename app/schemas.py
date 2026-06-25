from pydantic import BaseModel, Field


class GovernanceRiskRequest(BaseModel):
    system_name: str = Field(..., description="Name of the proposed AI system.")
    system_purpose: str = Field(..., description="What the AI system is supposed to do.")
    data_types: list[str] = Field(default_factory=list, description="Types of data used by the system.")
    users: list[str] = Field(default_factory=list, description="Who will use the system.")
    external_integrations: list[str] = Field(
        default_factory=list,
        description="External tools, APIs, vendors, or platforms connected to the system.",
    )
    human_review_process: str = Field(
        default="Not specified",
        description="How humans review, approve, or override AI outputs.",
    )
    business_impact: str = Field(
        default="Not specified",
        description="How important this system is to the organization.",
    )


class GovernanceRiskResponse(BaseModel):
    system_name: str
    risk_level: str = Field(..., description="Use one of: low, medium, high, critical.")
    decision: str = Field(..., description="Use one of: approved, needs_review, rejected.")
    summary: str
    key_risks: list[str]
    required_controls: list[str]
    human_review_requirements: list[str]
    logging_requirements: list[str]
    evidence_gaps: list[str]
    recommended_next_steps: list[str]


class SocAlertRequest(BaseModel):
    alert_id: str = Field(..., description="Unique identifier for the alert.")
    alert_type: str = Field(..., description="Type of alert, such as failed login or malware.")
    source_system: str = Field(..., description="System that generated the alert.")
    affected_asset: str = Field(..., description="Host, user, application, or system affected.")
    raw_log: str = Field(..., description="Original alert text or log content.")
    known_indicators: list[str] = Field(
        default_factory=list,
        description="Known IPs, domains, hashes, usernames, or other indicators.",
    )
    observed_behavior: str = Field(
        default="Not specified",
        description="Plain-English description of what was observed.",
    )


class SocAlertResponse(BaseModel):
    alert_id: str
    severity: str = Field(..., description="Use one of: low, medium, high, critical.")
    likely_incident_type: str
    summary: str
    mitre_mapping: list[str]
    recommended_containment: list[str]
    recommended_investigation_steps: list[str]
    false_positive_considerations: list[str]
    evidence_gaps: list[str]
    analyst_note: str


class AuditLogEntry(BaseModel):
    timestamp: str
    mode: str
    model: str
    input_summary: str
    result_summary: str
    success: bool
    error: str | None = None