"""Immutable declarative AI threat models: claims and IDs, never live permissions."""

from typing import Annotated, Literal

from pydantic import AliasChoices, Field, StrictStr, TypeAdapter, model_validator

from app.retrieval.contracts import Contract
from app.support_contracts import SourceSupportProvenance

Identifier = Annotated[StrictStr, Field(pattern=r"^[A-Z][A-Z0-9_-]{0,31}$")]
Text = Annotated[StrictStr, Field(min_length=1, max_length=400)]
Ids = Annotated[tuple[Identifier, ...], Field(max_length=16)]
Notes = Annotated[tuple[Text, ...], Field(max_length=8)]
Category = Literal[
    "prompt_injection",
    "retrieval_poisoning",
    "sensitive_data_disclosure",
    "excessive_tool_agency",
    "broken_authorization",
    "unsafe_output_consumption",
]
MAX_INPUT_BYTES = 20_000
MAX_WIRE_BYTES = 24_000
MAX_OUTPUT_BYTES = 24_000


class Actor(Contract):
    id: Identifier
    role: Literal["internal_user", "external_user", "operator", "service", "unknown"]
    description: Text


class Component(Contract):
    id: Identifier
    kind: Literal[
        "model",
        "retrieval_store",
        "user_interface",
        "document_source",
        "external_service",
        "tool",
        "data_store",
        "filter",
        "human_gate",
        "unknown",
    ]
    description: Text


class DataFlow(Contract):
    id: Identifier
    source_id: Identifier
    target_id: Identifier
    classification: Literal["public", "internal", "sensitive", "unknown"]
    boundary_crossing: Literal["stated", "not_stated", "unknown"]
    description: Text


class IngestionSurface(Contract):
    id: Identifier
    component_id: Identifier
    origin: Text
    trust_level: Literal["untrusted", "claimed_trusted", "unknown"]
    review_status: Literal["claimed_reviewed", "unreviewed", "unknown"]


class DeclaredTool(Contract):
    id: Identifier
    component_id: Identifier
    capabilities: tuple[
        Literal["read", "write", "external_communication", "side_effect"], ...
    ] = Field(min_length=1, max_length=4)
    invoker_actor_ids: Ids = Field(min_length=1)
    human_gate: Literal["stated", "absent", "unknown"]


class ImplementationEvidence(Contract):
    id: Identifier
    kind: Literal["design_note", "test_report_claim", "approval_claim", "unknown"]
    description: Text
    provenance: Literal["caller_supplied_unverified"] = "caller_supplied_unverified"


class ClaimedControl(Contract):
    id: Identifier
    component_ids: Ids = Field(min_length=1)
    description: Text
    claimed_status: Literal["stated", "not_stated", "unknown"]
    implementation_evidence_ids: Ids = ()


def unique(values, message: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(message)


class AiSecurityRequest(Contract):
    application_id: Identifier
    application_name: Annotated[StrictStr, Field(min_length=1, max_length=128)]
    purpose: Text
    deployment_assumptions: Notes = ()
    actors: tuple[Actor, ...] = Field(default=(), max_length=8)
    components: tuple[Component, ...] = Field(default=(), max_length=16)
    flows: tuple[DataFlow, ...] = Field(default=(), max_length=24)
    ingestion_surfaces: tuple[IngestionSurface, ...] = Field(default=(), max_length=8)
    tools: tuple[DeclaredTool, ...] = Field(default=(), max_length=8)
    controls: tuple[ClaimedControl, ...] = Field(default=(), max_length=16)
    implementation_evidence: tuple[ImplementationEvidence, ...] = Field(
        default=(), max_length=16
    )
    human_oversight: Notes = ()
    known_limitations: Notes = ()

    @model_validator(mode="after")
    def graph_integrity(self):
        groups = (
            self.actors,
            self.components,
            self.flows,
            self.ingestion_surfaces,
            self.tools,
            self.controls,
            self.implementation_evidence,
        )
        unique(
            [v.id for group in groups for v in group],
            "Design IDs must be globally unique",
        )
        nodes = {v.id: v for v in self.components}
        actors = {a.id for a in self.actors}
        evidence = {e.id for e in self.implementation_evidence}
        for flow in self.flows:
            if flow.source_id not in nodes or flow.target_id not in nodes:
                raise ValueError("Flows must reference existing components")
        for surface in self.ingestion_surfaces:
            if surface.component_id not in nodes:
                raise ValueError("Ingestion surface references an unknown component")
        for tool in self.tools:
            if tool.component_id not in nodes or nodes[tool.component_id].kind not in {
                "tool",
                "external_service",
            }:
                raise ValueError(
                    "Declared tool must reference a tool or external service"
                )
            if not set(tool.invoker_actor_ids) <= actors:
                raise ValueError("Tool invokers must be declared actors")
            unique(tool.capabilities, "Duplicate tool capabilities")
            unique(tool.invoker_actor_ids, "Duplicate tool invokers")
        for control in self.controls:
            if (
                not set(control.component_ids) <= nodes.keys()
                or not set(control.implementation_evidence_ids) <= evidence
            ):
                raise ValueError("Control dependencies must exist")
            unique(control.component_ids, "Duplicate control components")
            unique(control.implementation_evidence_ids, "Duplicate control evidence")
        if not self.application_name.strip() or not self.purpose.strip():
            raise ValueError("Name and purpose must be nonblank")
        if len(self.model_dump_json().encode()) > MAX_INPUT_BYTES:
            raise ValueError("Threat model exceeds total UTF-8 budget")
        return self


class TechnicalFinding(Contract):
    finding_id: Identifier
    category: Category
    component_ids: Ids = Field(min_length=1)
    flow_ids: Ids = ()
    control_ids: Ids = ()
    evidence_ids: Ids = ()
    hypothesis: Text
    prerequisites: Notes = Field(min_length=1)
    possible_impact: Text
    proposed_mitigations: Notes = Field(min_length=1)
    validation_recommendations: Notes = Field(min_length=1)
    missing_evidence: Notes = Field(min_length=1)
    # The existing system prompt reserves source_references for citation values.
    # Accept the precommitted stub spelling as a validation alias, never both.
    source_references: tuple[
        Annotated[StrictStr, Field(min_length=1, max_length=80)], ...
    ] = Field(
        min_length=1,
        max_length=3,
        validation_alias=AliasChoices("source_references", "source_ids"),
    )
    review_status: Literal["candidate"] = "candidate"
    verification_status: Literal["not_verified"] = "not_verified"


class AiSecurityResponse(Contract):
    application_id: Identifier
    coverage_status: Literal["advisory_returned", "insufficient_information"]
    summary: Annotated[StrictStr, Field(min_length=1, max_length=1200)]
    findings: tuple[TechnicalFinding, ...] = Field(default=(), max_length=12)
    evidence_gaps: tuple[Text, ...] = Field(default=(), max_length=16)
    human_review_requirements: Notes = Field(min_length=1)
    action_status: Literal["no_actions_executed"] = "no_actions_executed"
    verification_status: Literal["not_verified"] = "not_verified"

    @model_validator(mode="after")
    def bounded_output(self):
        unique([f.finding_id for f in self.findings], "Duplicate finding IDs")
        unique(
            [
                (
                    f.category,
                    tuple(sorted(f.component_ids)),
                    tuple(sorted(f.flow_ids)),
                    f.hypothesis,
                )
                for f in self.findings
            ],
            "Duplicate findings",
        )
        if self.coverage_status == "insufficient_information" and (
            self.findings or not self.evidence_gaps
        ):
            raise ValueError("Insufficiency requires gaps and no candidate findings")
        if len(self.model_dump_json().encode()) > MAX_OUTPUT_BYTES:
            raise ValueError("Response exceeds total UTF-8 budget")
        return self


class CandidateGeneration(Contract):
    """Internal model proposals; identity and structural coverage belong to Python.

    A valid proposal remains unassessed. Its IDs and category can be checked
    against the declared graph/guidance, but that does not prove entailment.
    """

    findings: tuple[TechnicalFinding, ...] = Field(max_length=12)
    evidence_gaps: tuple[Text, ...] = Field(max_length=16)
    human_review_requirements: Notes = Field(min_length=1)

    @model_validator(mode="after")
    def bounded_proposals(self):
        unique([f.finding_id for f in self.findings], "Duplicate finding IDs")
        unique(
            [
                (
                    f.category,
                    tuple(sorted(f.component_ids)),
                    tuple(sorted(f.flow_ids)),
                    f.hypothesis,
                )
                for f in self.findings
            ],
            "Duplicate findings",
        )
        if len(self.model_dump_json().encode()) > MAX_OUTPUT_BYTES:
            raise ValueError("Candidate proposals exceed total UTF-8 budget")
        return self


class AdvisoryGeneration(AiSecurityResponse):
    """Provider-visible branch: a reviewable design may have zero findings."""

    coverage_status: Literal["advisory_returned"]


class InsufficientGeneration(AiSecurityResponse):
    """Encode the existing public cross-field rule in the decoder schema too."""

    coverage_status: Literal["insufficient_information"]
    findings: tuple[TechnicalFinding, ...] = Field(default=(), max_length=0)
    evidence_gaps: tuple[Text, ...] = Field(min_length=1, max_length=16)


_GENERATION = TypeAdapter(AdvisoryGeneration | InsufficientGeneration)


def generation_schema() -> dict:
    return _GENERATION.json_schema()


def validate_generation(raw: dict) -> AiSecurityResponse:
    # Neither convert status nor drop findings. Validate the raw provider payload
    # against both the model-visible variants and the unchanged public contract.
    _GENERATION.validate_python(raw)
    return AiSecurityResponse.model_validate(raw)


class AiSecuritySource(Contract):
    provenance: SourceSupportProvenance
    version: Literal["local-ai-security-guidance-v1"] = "local-ai-security-guidance-v1"
    category: Category
    cited_by_finding_ids: Ids = ()


class AiSecurityMetadata(Contract):
    status: Literal["experimental"] = "experimental"
    workflow: Literal["ai_security_assessment"] = "ai_security_assessment"
    request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    model_invoked: bool
    model: str = Field(max_length=128)
    human_review_required: Literal[True] = True
    claim_status: Literal["unassessed"] = "unassessed"
    design_provenance: Literal["caller_supplied_unverified"] = (
        "caller_supplied_unverified"
    )
    local_knowledge: Literal["unsupported; no workspace grants"] = (
        "unsupported; no workspace grants"
    )
    sources: tuple[AiSecuritySource, ...] = Field(default=(), max_length=6)
    control_status: Literal[
        "all claimed controls and supplied implementation evidence remain unverified"
    ] = "all claimed controls and supplied implementation evidence remain unverified"
    limitations: Notes


class AiSecurityEnvelope(Contract):
    analysis: AiSecurityResponse
    metadata: AiSecurityMetadata
