from typing import Annotated, Literal

from pydantic import BaseModel, Field

MAX_LABEL_LENGTH = 256
MAX_DESCRIPTION_LENGTH = 10_000
MAX_RAW_LOG_LENGTH = 100_000
MAX_LIST_ITEMS = 100
MAX_LIST_ENTRY_LENGTH = 1_024

RequestLabel = Annotated[str, Field(max_length=MAX_LABEL_LENGTH)]
RequestDescription = Annotated[str, Field(max_length=MAX_DESCRIPTION_LENGTH)]
RequestListEntry = Annotated[str, Field(max_length=MAX_LIST_ENTRY_LENGTH)]
RequestList = Annotated[list[RequestListEntry], Field(max_length=MAX_LIST_ITEMS)]


class SourceReference(BaseModel):
    source_id: str = Field(..., description="Unique ID of the local reference card.")
    title: str = Field(..., description="Title of the local reference card.")
    framework: str = Field(..., description="Framework, checklist, or source family.")
    relevance: str = Field(
        ...,
        description="Brief explanation of why this source was relevant to the response.",
    )


class GovernanceRiskRequest(BaseModel):
    system_name: RequestLabel = Field(
        ..., description="Name of the proposed AI system."
    )
    system_purpose: RequestDescription = Field(
        ..., description="What the AI system is supposed to do."
    )
    data_types: RequestList = Field(
        default_factory=list,
        description="Types of data used by the system.",
    )
    users: RequestList = Field(
        default_factory=list, description="Who will use the system."
    )
    external_integrations: RequestList = Field(
        default_factory=list,
        description="External tools, APIs, vendors, or platforms connected to the system.",
    )
    human_review_process: RequestDescription = Field(
        default="Not specified",
        description="How humans review, approve, or override AI outputs.",
    )
    business_impact: RequestDescription = Field(
        default="Not specified",
        description="How important this system is to the organization.",
    )


class GovernanceRiskResponse(BaseModel):
    system_name: str
    risk_level: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Use one of: low, medium, high, critical."
    )
    decision: Literal["approved", "needs_review", "rejected"] = Field(
        ..., description="Use one of: approved, needs_review, rejected."
    )
    summary: str
    key_risks: list[str]
    required_controls: list[str]
    human_review_requirements: list[str]
    logging_requirements: list[str]
    evidence_gaps: list[str]
    recommended_next_steps: list[str]
    source_references: list[SourceReference] = Field(
        default_factory=list,
        description="Local reference cards that influenced the response.",
    )


class SocAlertRequest(BaseModel):
    alert_id: RequestLabel = Field(..., description="Unique identifier for the alert.")
    alert_type: RequestLabel = Field(
        ..., description="Type of alert, such as failed login or malware."
    )
    source_system: RequestLabel = Field(
        ..., description="System that generated the alert."
    )
    affected_asset: RequestLabel = Field(
        ..., description="Host, user, application, or system affected."
    )
    raw_log: str = Field(
        ...,
        max_length=MAX_RAW_LOG_LENGTH,
        description="Original alert text or log content.",
    )
    known_indicators: RequestList = Field(
        default_factory=list,
        description="Known IPs, domains, hashes, usernames, or other indicators.",
    )
    observed_behavior: RequestDescription = Field(
        default="Not specified",
        description="Plain-English description of what was observed.",
    )


class SocAlertResponse(BaseModel):
    alert_id: str
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Use one of: low, medium, high, critical."
    )
    likely_incident_type: str
    summary: str
    mitre_mapping: list[str]
    recommended_containment: list[str]
    recommended_investigation_steps: list[str]
    false_positive_considerations: list[str]
    evidence_gaps: list[str]
    analyst_note: str
    observed_evidence: list[str] = Field(
        default_factory=list,
        description="Concise observations supported by supplied evidence, not unsupported conclusions.",
    )
    analyst_inferences: list[str] = Field(
        default_factory=list,
        description="Concise analyst findings with appropriate uncertainty, not hidden reasoning.",
    )
    source_references: list[SourceReference] = Field(
        default_factory=list,
        description="Local reference cards that influenced the response.",
    )


class AuditLogEntry(BaseModel):
    timestamp: str
    mode: str
    model: str
    input_summary: str
    result_summary: str
    success: bool
    error: str | None = None
    source_ids: list[str] = Field(default_factory=list)
