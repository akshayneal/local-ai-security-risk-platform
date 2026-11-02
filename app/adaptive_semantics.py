"""Opt-in synthetic relationship checks, never policy parsing or authorization.

Only the separately reviewed context supplies source eligibility. The JSON body
supplies unverified assertions. Existing analyzers do not import this module.
"""

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, StrictBool, StrictInt, StrictStr, ValidationError

from app.ai_security_analyzer import reachable
from app.support_contracts import SupportModel

MAX_RAW_BYTES = 16_000
MAX_PREMISES = 256
Text = Annotated[StrictStr, Field(min_length=1, max_length=256)]
Identifier = Annotated[StrictStr, Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")]
Pillar = Literal["soc", "governance", "ai_security"]
Timing = Literal["before", "after", "unknown"]
Outcome = Literal[
    "declared_mismatch",
    "declared_alignment",
    "underdetermined",
    "conflicting_claims",
    "not_applicable",
    "projection_unavailable",
]
Scalar = StrictStr | StrictInt | StrictBool | None


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class SourceRef(SupportModel):
    id: Identifier
    revision: Text


class ReviewedSource(SourceRef):
    scope: Identifier
    classification: Text
    authority: Text
    current: StrictBool


class ReviewedContext(SupportModel):
    case_id: Identifier
    pillar: Pillar
    input_path: Literal["raw_log", "human_review_process", "human_oversight[0]"]
    raw_sha256: Annotated[StrictStr, Field(pattern=r"^[a-f0-9]{64}$")]
    sources: tuple[ReviewedSource, ...] = Field(min_length=1, max_length=4)
    requirement_reviewed: StrictBool


class Event(SupportModel):
    operation: Text | None
    result: Literal["completed", "failed", "attempted", "unknown"]
    principal: Text | None
    asset: Text | None
    source: Text | None
    destination: Text | None
    endpoint: Text | None
    time: Text | None
    amount: Annotated[StrictInt, Field(ge=0, le=10**12)] | None


class Authorization(SupportModel):
    status: Literal["reported_authorized", "reported_denied", "unknown"]
    operation: Text | None
    principal: Text | None
    asset: Text | None
    endpoint: Text | None
    window_start: Text | None
    window_end: Text | None


class SocData(SupportModel):
    event: Event
    authorization: Authorization


class Requirement(SupportModel):
    timing: Timing
    action: Text
    source: SourceRef


class Implementation(SupportModel):
    status: Literal["proposed", "reported_implemented", "explicitly_absent", "unknown"]
    actual_timing: Timing
    action: Text
    sample_size: Annotated[StrictInt, Field(ge=0, le=1_000_000)] | None
    sample_scope: Text | None


class GovernanceData(SupportModel):
    requirement: Requirement | None
    implementation: Implementation


class Node(SupportModel):
    id: Identifier
    kind: Literal["model", "tool", "other"]


class Edge(SupportModel):
    source: Identifier
    target: Identifier

    @property
    def source_id(self):
        return self.source

    @property
    def target_id(self):
        return self.target


class Tool(SupportModel):
    id: Identifier
    capabilities: tuple[Literal["read", "write", "external_communication"], ...] = (
        Field(max_length=3)
    )
    invoker: Literal["model", "human", "unknown"]
    gate_state: Literal["reported_present", "explicitly_absent", "unknown"]
    gate_timing: Timing


class AiData(SupportModel):
    nodes: tuple[Node, ...] = Field(min_length=1, max_length=12)
    edges: tuple[Edge, ...] = Field(max_length=20)
    tools: tuple[Tool, ...] = Field(min_length=1, max_length=6)
    selected_tool: Identifier
    requirement: Requirement | None


class Counterclaim(SupportModel):
    pointer: Annotated[StrictStr, Field(min_length=1, max_length=256)]
    value: Scalar
    source: SourceRef


class Envelope(SupportModel):
    schema_version: Literal["adaptive-security/1"]
    case_id: Identifier
    pillar: Pillar
    source: SourceRef
    data: dict
    counterclaims: tuple[Counterclaim, ...] = Field(max_length=8)
    annotations: tuple[Annotated[StrictStr, Field(max_length=500)], ...] = Field(
        max_length=8
    )


class Premise(SupportModel):
    id: Annotated[StrictStr, Field(pattern=r"^PREM-[a-f0-9]{20}$")]
    pointer: StrictStr
    input_path: StrictStr
    value: Scalar | tuple[()]
    source_id: StrictStr
    source_revision: StrictStr
    assertion_status: Literal["supplied_unverified"] = "supplied_unverified"


class Assessment(SupportModel):
    case_id: StrictStr
    pillar: Pillar
    input_path: StrictStr
    raw_sha256: StrictStr
    raw: StrictStr | None
    premises: tuple[Premise, ...]
    outcome: Outcome
    reason_codes: tuple[StrictStr, ...]
    decisive_premise_ids: tuple[StrictStr, ...]
    disconfirming_premise_ids: tuple[StrictStr, ...]
    unassessed_conditions: tuple[StrictStr, ...]
    report_sentence: StrictStr
    source_status: Literal["supplied assertions; not independently verified"] = (
        "supplied assertions; not independently verified"
    )
    capability_status: Literal["experimental_internal_off_by_default"] = (
        "experimental_internal_off_by_default"
    )
    action_status: Literal["no_actions_executed"] = "no_actions_executed"
    approval_granted: Literal[False] = False


class ProjectionError(ValueError):
    """A stable diagnostic reason; never includes rejected source content."""


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProjectionError("duplicate_json_key")
        result[key] = value
    return result


def _reject_number(_):
    raise ProjectionError("unsupported_json_number")


def _parse(raw):
    value = json.loads(
        raw,
        object_pairs_hook=_object,
        parse_constant=_reject_number,
        parse_float=_reject_number,
    )
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > 10:
            raise ProjectionError("unsupported_nested_layout")
        if isinstance(item, dict):
            pending.extend((v, depth + 1) for v in item.values())
        elif isinstance(item, list):
            pending.extend((v, depth + 1) for v in item)
    return value


def _leaves(value, pointer=""):
    if isinstance(value, dict):
        for key, item in value.items():
            token = key.replace("~", "~0").replace("/", "~1")
            yield from _leaves(item, pointer + "/" + token)
    elif isinstance(value, list) and value:
        for index, item in enumerate(value):
            yield from _leaves(item, f"{pointer}/{index}")
    else:
        yield pointer, () if value == [] else value


def _metadata(context):
    sources = {s.id: s for s in context.sources}
    if len(sources) != len(context.sources):
        raise ProjectionError("duplicate_source_metadata")
    for source in sources.values():
        if source.classification != "public_synthetic":
            raise ProjectionError("unsafe_classification")
        if source.authority != "synthetic_caller_assertion":
            raise ProjectionError("unsupported_source_authority")
        if source.scope != context.case_id or not source.current:
            raise ProjectionError("ineligible_source_metadata")
    expected_path = {
        "soc": "raw_log",
        "governance": "human_review_process",
        "ai_security": "human_oversight[0]",
    }[context.pillar]
    if context.input_path != expected_path:
        raise ProjectionError("input_path_scope")
    return sources


def _source(ref, sources):
    if ref.id not in sources or sources[ref.id].revision != ref.revision:
        raise ProjectionError("unknown_or_stale_source")


def _instant(text):
    if text is None:
        return None
    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})", text
    ):
        raise ProjectionError("invalid_or_naive_time")
    if not text.endswith("Z") and (int(text[-5:-3]) > 23 or int(text[-2:]) > 59):
        raise ProjectionError("invalid_or_naive_time")
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ProjectionError("invalid_or_naive_time") from exc


def _soc(data):
    event, auth = data.event, data.authorization
    observed = "/data/event/"
    allowed = "/data/authorization/"
    decisive = [allowed + "status", observed + "operation", observed + "result"]
    disconfirming = []
    if event.result != "completed":
        disconfirming.append(observed + "result")
    if event.amount == 0:
        disconfirming.append(observed + "amount")
    times = [_instant(v) for v in (event.time, auth.window_start, auth.window_end)]
    if times[1] is not None and times[2] is not None and times[1] > times[2]:
        raise ProjectionError("inverted_authorization_window")
    if auth.status == "unknown" or event.operation is None:
        return (
            "underdetermined",
            ["authorization_or_operation_unknown"],
            decisive,
            disconfirming,
        )
    if auth.status == "reported_denied":
        return (
            "declared_mismatch",
            ["reported_authorization_denied"],
            decisive,
            disconfirming,
        )
    unknown, mismatches = [], []
    for field in ("operation", "principal", "asset", "endpoint"):
        decisive += [observed + field, allowed + field]
        a, b = getattr(event, field), getattr(auth, field)
        if a is None or b is None:
            unknown.append(field + "_scope_unknown")
        elif a != b:
            mismatches.append(field + "_scope_mismatch")
        else:
            disconfirming += [observed + field, allowed + field]
    decisive += [observed + "time", allowed + "window_start", allowed + "window_end"]
    if any(t is None for t in times):
        unknown.append("time_scope_unknown")
    elif not times[1] <= times[0] <= times[2]:
        mismatches.append("outside_reported_time_window")
    if mismatches:
        return "declared_mismatch", mismatches + unknown, decisive, disconfirming
    return (
        "underdetermined" if unknown else "declared_alignment",
        unknown or ["reported_scope_matches"],
        decisive,
        disconfirming,
    )


def _governance(data, reviewed):
    r, implementation = data.requirement, data.implementation
    decisive = (
        ["/data/requirement", "/data/implementation/status"]
        if r is None
        else [
            "/data/requirement/timing",
            "/data/requirement/action",
            "/data/implementation/status",
            "/data/implementation/actual_timing",
            "/data/implementation/action",
            "/data/implementation/sample_size",
            "/data/implementation/sample_scope",
        ]
    )
    disconfirming = []
    if implementation.status in {"proposed", "unknown"}:
        disconfirming.append("/data/implementation/status")
    if (
        implementation.actual_timing == "unknown"
        or r is not None
        and implementation.actual_timing == r.timing
    ):
        disconfirming.append("/data/implementation/actual_timing")
    if implementation.sample_size is not None:
        disconfirming += [
            "/data/implementation/sample_size",
            "/data/implementation/sample_scope",
        ]
    if r is None or not reviewed or r.timing == "unknown":
        return (
            "underdetermined",
            ["reviewed_typed_requirement_unavailable"],
            decisive,
            disconfirming,
        )
    if r.action != implementation.action:
        return (
            "underdetermined",
            ["behavior_action_scope_differs"],
            decisive,
            disconfirming,
        )
    if implementation.status == "explicitly_absent":
        if implementation.actual_timing != "unknown":
            return (
                "conflicting_claims",
                ["absent_review_has_reported_timing"],
                decisive,
                disconfirming,
            )
        return (
            "declared_mismatch",
            ["required_control_reported_absent"],
            decisive,
            disconfirming,
        )
    if implementation.status != "reported_implemented":
        return (
            "underdetermined",
            ["implementation_not_reported_as_implemented"],
            decisive,
            disconfirming,
        )
    if implementation.actual_timing == "unknown":
        return "underdetermined", ["actual_timing_unknown"], decisive, disconfirming
    if implementation.actual_timing != r.timing:
        return (
            "declared_mismatch",
            ["reported_review_timing_mismatch"],
            decisive,
            disconfirming,
        )
    if not implementation.sample_size or implementation.sample_scope is None:
        return (
            "underdetermined",
            ["bounded_implementation_sample_missing"],
            decisive,
            disconfirming,
        )
    return (
        "declared_alignment",
        ["reported_sample_timing_matches"],
        decisive,
        disconfirming,
    )


def _ai(data, reviewed):
    nodes = {n.id: n for n in data.nodes}
    tools = {t.id: t for t in data.tools}
    if len(nodes) != len(data.nodes) or len(tools) != len(data.tools):
        raise ProjectionError("duplicate_graph_identity")
    if len({(e.source, e.target) for e in data.edges}) != len(data.edges):
        raise ProjectionError("duplicate_graph_edge")
    if any(e.source not in nodes or e.target not in nodes for e in data.edges):
        raise ProjectionError("unknown_graph_endpoint")
    if any(t.id not in nodes or nodes[t.id].kind != "tool" for t in data.tools):
        raise ProjectionError("tool_node_mismatch")
    if data.selected_tool not in tools:
        raise ProjectionError("unknown_selected_tool")
    for tool in data.tools:
        if len(set(tool.capabilities)) != len(tool.capabilities):
            raise ProjectionError("duplicate_capability")
    tool = tools[data.selected_tool]
    index = next(i for i, t in enumerate(data.tools) if t.id == tool.id)
    prefix = f"/data/tools/{index}/"
    downstream = set().union(
        *(reachable(n.id, data.edges) for n in data.nodes if n.kind == "model")
    )
    upstream = reachable(tool.id, data.edges, reverse=True)
    path = tool.id in downstream
    relevant_nodes = downstream & upstream if path else set(nodes)
    graph_pointers = []
    for node_index, node in enumerate(data.nodes):
        if node.id in relevant_nodes:
            graph_pointers += [
                f"/data/nodes/{node_index}/id", f"/data/nodes/{node_index}/kind"
            ]
    for edge_index, edge in enumerate(data.edges):
        if not path or edge.source in downstream and edge.target in upstream:
            graph_pointers += [
                f"/data/edges/{edge_index}/source", f"/data/edges/{edge_index}/target"
            ]
    decisive = graph_pointers + [
        p for p, _ in _leaves(data.model_dump(mode="json"), "/data")
        if p.startswith("/data/requirement")
    ]
    decisive += [
        "/data/selected_tool",
        prefix + "id",
        prefix + "invoker",
        prefix + "gate_state",
        prefix + "gate_timing",
    ]
    decisive += [prefix + f"capabilities/{i}" for i in range(len(tool.capabilities))]
    if not tool.capabilities:
        decisive.append(prefix + "capabilities")
    disconfirming = []
    if tool.gate_state in {"reported_present", "unknown"}:
        disconfirming.append(prefix + "gate_state")
    if (
        tool.gate_timing == "unknown"
        or data.requirement is not None
        and tool.gate_timing == data.requirement.timing
    ):
        disconfirming.append(prefix + "gate_timing")
    if tool.invoker != "model":
        disconfirming.append(prefix + "invoker")
    if not set(tool.capabilities) & {"write", "external_communication"}:
        disconfirming += [
            prefix + f"capabilities/{i}" for i in range(len(tool.capabilities))
        ]
    if not path:
        return (
            "not_applicable",
            ["no_declared_model_to_selected_tool_path"],
            decisive,
            disconfirming,
        )
    if tool.invoker == "human":
        return (
            "not_applicable",
            ["selected_tool_declared_human_invoked"],
            decisive,
            disconfirming,
        )
    if tool.invoker == "unknown" or not tool.capabilities:
        return (
            "underdetermined",
            ["invoker_or_capability_unknown"],
            decisive,
            disconfirming,
        )
    if not set(tool.capabilities) & {"write", "external_communication"}:
        return (
            "not_applicable",
            ["selected_tool_declared_read_only"],
            decisive,
            disconfirming,
        )
    r = data.requirement
    if r is None or not reviewed or r.timing == "unknown" or r.action != "tool_action":
        return (
            "underdetermined",
            ["reviewed_typed_requirement_unavailable"],
            decisive,
            disconfirming,
        )
    if tool.gate_state == "explicitly_absent":
        if tool.gate_timing != "unknown":
            return (
                "conflicting_claims",
                ["absent_gate_has_reported_timing"],
                decisive,
                disconfirming,
            )
        return (
            "declared_mismatch",
            ["required_gate_reported_absent"],
            decisive,
            disconfirming,
        )
    if tool.gate_state == "unknown" or tool.gate_timing == "unknown":
        return (
            "underdetermined",
            ["gate_state_or_timing_unknown"],
            decisive,
            disconfirming,
        )
    if tool.gate_timing != r.timing:
        return (
            "declared_mismatch",
            ["reported_gate_timing_mismatch"],
            decisive,
            disconfirming,
        )
    return (
        "declared_alignment",
        ["reported_gate_timing_matches"],
        decisive,
        disconfirming,
    )


def _sentence(pillar, outcome, reasons, details=""):
    relation = {
        "declared_mismatch": "The supplied typed assertions declare a mismatch",
        "declared_alignment": "The supplied typed assertions declare alignment",
        "underdetermined": "The declared relationship is underdetermined",
        "conflicting_claims": "The supplied typed assertions conflict",
        "not_applicable": "The narrow relationship check is not applicable to the declared scope",
        "projection_unavailable": "The typed projection is unavailable",
    }[outcome]
    return (
        f"{relation} for {pillar}: {', '.join(reasons)}. {details}"
        "This checks supplied assertions only; it verifies no deployed behavior, "
        "source authenticity, permission, violation, compromise, or safety outcome."
    )


def _details(pillar, data):
    def quoted(value):
        return json.dumps(value, ensure_ascii=True)

    if pillar == "soc":
        return (
            f"Reported operation {quoted(data.event.operation)} has result "
            f"{quoted(data.event.result)} and amount {quoted(data.event.amount)}; "
            f"reported authorization operation is {quoted(data.authorization.operation)}. "
        )
    if pillar == "governance":
        required = data.requirement.timing if data.requirement else "unknown"
        return (
            f"Reported requirement timing is {quoted(required)}; implementation status "
            f"is {quoted(data.implementation.status)}, actual review timing is "
            f"{quoted(data.implementation.actual_timing)}, sample size is "
            f"{quoted(data.implementation.sample_size)}. "
        )
    tool = next(t for t in data.tools if t.id == data.selected_tool)
    required = data.requirement.timing if data.requirement else "unknown"
    return (
        f"Selected tool {quoted(tool.id)} declares capabilities "
        f"{quoted(tool.capabilities)}, invoker {quoted(tool.invoker)}, gate state "
        f"{quoted(tool.gate_state)} and timing {quoted(tool.gate_timing)}; "
        f"reported required timing is {quoted(required)}. "
    )


def _counterclaim_data(data, pointer, value, pillar, reviewed):
    """Validate an alternative in isolation; never change canonical source data."""
    if pointer.startswith("/data/requirement/source/"):
        raise ProjectionError("counterclaim_cannot_change_source_reference")
    candidate = deepcopy(data.model_dump(mode="json"))
    tokens = [
        part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[2:]
    ]
    current = candidate
    for token in tokens[:-1]:
        current = current[int(token)] if isinstance(current, list) else current[token]
    key = int(tokens[-1]) if isinstance(current, list) else tokens[-1]
    current[key] = value
    try:
        candidate = type(data).model_validate(candidate)
        if pillar == "soc":
            _soc(candidate)
        elif pillar == "ai_security":
            _ai(candidate, reviewed)
    except (ValidationError, ProjectionError) as exc:
        raise ProjectionError("invalid_typed_counterclaim") from exc


def _unknown(pointer, value):
    if value is None:
        return True
    enum_leaf = pointer.rsplit("/", 1)[-1] in {
        "result",
        "status",
        "actual_timing",
        "timing",
        "invoker",
        "gate_state",
        "gate_timing",
    }
    return enum_leaf and value == "unknown"


def project(raw: str, context: ReviewedContext) -> Assessment:
    """Compare one explicitly supported synthetic record without model judgment."""
    digest = ""
    premises, retained = (), None
    outcome, reasons, decisive_ids, disconfirming_ids = (
        "projection_unavailable",
        [],
        (),
        (),
    )
    details = ""
    unassessed = [
        "source authenticity",
        "real deployment",
        "security severity",
        "all other relationships",
    ]
    try:
        context = ReviewedContext.model_validate(context.model_dump(mode="json"))
        if isinstance(raw, str) and len(raw) <= MAX_RAW_BYTES:
            digest = sha(raw)
        sources = _metadata(context)
        if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_RAW_BYTES:
            raise ProjectionError("raw_byte_budget")
        digest = sha(raw)
        if digest != context.raw_sha256:
            raise ProjectionError("source_snapshot_mismatch")
        retained = raw
        original = _parse(raw)
        envelope = Envelope.model_validate(original)
        if envelope.case_id != context.case_id or envelope.pillar != context.pillar:
            raise ProjectionError("case_or_pillar_mismatch")
        _source(envelope.source, sources)
        models = {"soc": SocData, "governance": GovernanceData, "ai_security": AiData}
        data = models[context.pillar].model_validate(envelope.data)
        if context.pillar != "soc" and data.requirement is not None:
            _source(data.requirement.source, sources)
        leaves = dict(_leaves(original))
        for claim in envelope.counterclaims:
            _source(claim.source, sources)
            if not claim.pointer.startswith("/data/") or claim.pointer not in leaves:
                raise ProjectionError("counterclaim_pointer_unavailable")
            _counterclaim_data(
                data,
                claim.pointer,
                claim.value,
                context.pillar,
                context.requirement_reviewed,
            )
        refs = []
        for pointer, value in leaves.items():
            ref = envelope.source
            if (
                pointer.startswith("/data/requirement/")
                and data.requirement is not None
            ):
                ref = data.requirement.source
            if pointer.startswith("/counterclaims/"):
                ref = envelope.counterclaims[int(pointer.split("/")[2])].source
            refs.append(
                Premise(
                    id="PREM-" + sha(digest + "\n" + pointer)[:20],
                    pointer=pointer,
                    input_path=context.input_path,
                    value=value,
                    source_id=ref.id,
                    source_revision=ref.revision,
                )
            )
        if len(refs) > MAX_PREMISES:
            raise ProjectionError("premise_budget")
        premises = tuple(refs)
        if context.pillar == "soc":
            result = _soc(data)
        elif context.pillar == "governance":
            result = _governance(data, context.requirement_reviewed)
        else:
            result = _ai(data, context.requirement_reviewed)
        outcome, reasons, decisive, disconfirming = result
        details = _details(context.pillar, data)
        decisive = list(dict.fromkeys(decisive))
        for index, claim in enumerate(envelope.counterclaims):
            if _unknown(claim.pointer, leaves[claim.pointer]) or _unknown(
                claim.pointer, claim.value
            ):
                unassessed.append(
                    f"unknown counterclaim values not resolved at {claim.pointer}"
                )
                continue
            if claim.pointer in decisive and claim.value != leaves[claim.pointer]:
                outcome, reasons = "conflicting_claims", ["decisive_typed_counterclaim"]
                decisive.append(f"/counterclaims/{index}/value")
                disconfirming.append(f"/counterclaims/{index}/value")
        lookup = {p.pointer: p.id for p in premises}
        decisive_ids = tuple(lookup[p] for p in decisive if p in lookup)
        disconfirming_ids = tuple(
            dict.fromkeys(lookup[p] for p in disconfirming if p in lookup)
        )
        if context.pillar == "soc":
            unassessed += [
                f"reported_event_result={data.event.result}",
                "event result is not inferred from scope alignment or mismatch",
                "amount is preserved; no transfer-content or maliciousness inference",
            ]
        if context.pillar == "governance":
            unassessed += [
                "implementation evidence is a bounded caller report, not independent verification"
            ]
        if context.pillar == "ai_security":
            unassessed += [
                "declared path and capability are not proof of exploitability or execution"
            ]
            if "no_declared_model_to_selected_tool_path" in reasons:
                unassessed += [
                    "no-path graph conflicts use the whole declared graph conservatively; actual absence is unverified"
                ]
    except ProjectionError as exc:
        outcome, reasons, decisive_ids, disconfirming_ids = (
            "projection_unavailable",
            [str(exc)],
            (),
            (),
        )
    except (
        ValidationError,
        ValueError,
        TypeError,
        RecursionError,
        AttributeError,
        UnicodeError,
    ):
        outcome, reasons, decisive_ids, disconfirming_ids = (
            "projection_unavailable",
            ["invalid_typed_schema"],
            (),
            (),
        )
    return Assessment(
        case_id=context.case_id,
        pillar=context.pillar,
        input_path=context.input_path,
        raw_sha256=digest,
        raw=retained,
        premises=premises,
        outcome=outcome,
        reason_codes=tuple(reasons),
        decisive_premise_ids=decisive_ids,
        disconfirming_premise_ids=disconfirming_ids,
        unassessed_conditions=tuple(unassessed),
        report_sentence=_sentence(context.pillar, outcome, reasons, details),
    )
