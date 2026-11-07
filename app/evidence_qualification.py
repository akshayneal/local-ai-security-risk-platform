"""Internal synthetic source eligibility, separate from source content and truth.

Only application-side callers supply reviews/current snapshots. This module does
not authenticate their operator, read a registry, interpret policy prose, or grant
permission. Existing public analyzers do not import it.
"""

import hashlib
import json
import math
import re
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, StrictBool, StrictStr, ValidationError

from app.support_contracts import SupportModel

MAX_SOURCE_BYTES = 64_000
MAX_JSON_DEPTH = 10
MAX_JSON_NODES = 4096
MAX_TEXT_CHARACTERS = 16_000

Identifier = Annotated[StrictStr, Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")]


def _nonblank(value: str) -> str:
    if not value.strip() or any(ord(char) < 32 for char in value):
        raise ValueError("nonblank_metadata_required")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ValueError("malformed_metadata_encoding") from exc
    return value


Text = Annotated[
    StrictStr, Field(min_length=1, max_length=256), AfterValidator(_nonblank)
]
SourceRole = Literal[
    "event_observation",
    "authorization_assertion",
    "reviewed_requirement",
    "implementation_assertion",
    "counterclaim",
    "contextual_guidance",
]
SourceFormat = Literal[
    "microsoft_json",
    "microsoft_csv",
    "synthetic_event",
    "synthetic_authorization",
    "synthetic_context",
]
Workflow = Literal[
    "soc_investigation",
    "ai_system_risk",
    "ai_security_assessment",
    "soc_policy_governance",
]


class QualificationError(ValueError):
    """Stable refusal code; never includes rejected content or exception bodies."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def instant(value: str) -> datetime:
    """Accept only explicit timezone instants, without guessing a local timezone."""
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})",
        value,
    ):
        raise QualificationError("ambiguous_timestamp")
    if not value.endswith("Z") and (
        int(value[-5:-3]) > 23 or int(value[-2:]) > 59
    ):
        raise QualificationError("ambiguous_timestamp")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise QualificationError("malformed_timestamp") from exc


def _aware(value: str) -> str:
    instant(value)
    return value


Instant = Annotated[StrictStr, Field(max_length=40), AfterValidator(_aware)]


class QualificationScope(SupportModel):
    schema_version: Literal["qualification-scope/1"] = "qualification-scope/1"
    case_id: Identifier
    workflow: Workflow = "soc_investigation"
    question_id: Identifier
    question: Text = (
        "Compare declared event scope with separately reviewed synthetic authorization"
    )
    as_of: Instant


class SourceReview(SupportModel):
    """A fresh application-side review/current snapshot, never source-body data.

    The internal caller must supply current_revision/status again at use/export.
    These assertions establish demonstration eligibility, not source authenticity.
    """

    schema_version: Literal["source-review/1"] = "source-review/1"
    source_id: Identifier
    revision: Text
    current_revision: Text
    raw_sha256: Annotated[StrictStr, Field(pattern=r"^[a-f0-9]{64}$")]
    source_format: SourceFormat
    role: SourceRole
    case_id: Identifier
    workflows: tuple[Workflow, ...] = Field(min_length=1, max_length=4)
    question_ids: tuple[Identifier, ...] = Field(min_length=1, max_length=8)
    source_path: Text = "supplied"
    classification: Text = "public_synthetic"
    synthetic: StrictBool = False
    authority: Literal["synthetic_application_review", "unverified"] = "unverified"
    approved: StrictBool = False
    requirement_reviewed: StrictBool = False
    current: StrictBool = True
    status: Literal["current", "revoked", "inactive", "failed"] = "current"
    reviewed_at: Instant
    effective_at: Instant
    expires_at: Instant


class QualifiedSource(SupportModel):
    schema_version: Literal["qualified-source/1"] = "qualified-source/1"
    raw_text: StrictStr = Field(max_length=MAX_SOURCE_BYTES)
    raw_sha256: Annotated[StrictStr, Field(pattern=r"^[a-f0-9]{64}$")]
    review: SourceReview
    scope: QualificationScope
    eligibility: Literal["application_reviewed_synthetic_only"] = (
        "application_reviewed_synthetic_only"
    )
    authenticity: Literal["unverified"] = "unverified"
    approval_granted: Literal[False] = False
    actions_executed: Literal[False] = False


def source_text(raw: bytes) -> str:
    """Bound original upload bytes before decoding; preserve exact UTF-8 bytes."""
    if type(raw) is not bytes:
        raise QualificationError("malformed_input")
    if not raw or len(raw) > MAX_SOURCE_BYTES:
        raise QualificationError("source_byte_budget")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise QualificationError("malformed_encoding") from exc
    return text


def qualify_source(
    raw: bytes,
    review: SourceReview,
    scope: QualificationScope,
    *,
    expected_role: SourceRole,
    expected_format: SourceFormat,
) -> QualifiedSource:
    """Fail visibly before mapping. Neither raw content nor a hash grants a role."""
    try:
        review = SourceReview.model_validate(
            review.model_dump(mode="json", warnings=False)
        )
        scope = QualificationScope.model_validate(
            scope.model_dump(mode="json", warnings=False)
        )
    except (ValidationError, ValueError, TypeError, AttributeError) as exc:
        raise QualificationError("malformed_review_metadata") from exc
    text = source_text(raw)
    digest = hashlib.sha256(raw).hexdigest()
    if review.raw_sha256 != digest:
        raise QualificationError("source_snapshot_mismatch")
    if review.source_format != expected_format:
        raise QualificationError("source_format_mismatch")
    if review.role != expected_role:
        raise QualificationError("source_role_mismatch")
    if review.classification != "public_synthetic" or not review.synthetic:
        raise QualificationError("unsupported_classification")
    if review.authority != "synthetic_application_review" or not review.approved:
        raise QualificationError("unreviewed_source")
    if review.status == "revoked":
        raise QualificationError("source_revoked")
    if review.status != "current" or not review.current:
        raise QualificationError("source_not_current")
    if review.revision != review.current_revision:
        raise QualificationError("stale_source_revision")
    if review.case_id != scope.case_id:
        raise QualificationError("wrong_case_scope")
    if scope.workflow not in review.workflows:
        raise QualificationError("wrong_workflow_scope")
    if scope.question_id not in review.question_ids:
        raise QualificationError("wrong_question_scope")
    if len(set(review.workflows)) != len(review.workflows) or len(
        set(review.question_ids)
    ) != len(review.question_ids):
        raise QualificationError("duplicate_review_scope")
    as_of = instant(scope.as_of)
    reviewed, effective, expires = map(
        instant, (review.reviewed_at, review.effective_at, review.expires_at)
    )
    if effective >= expires or reviewed >= expires:
        raise QualificationError("malformed_review_window")
    if reviewed > as_of:
        raise QualificationError("review_not_yet_available")
    if as_of < effective:
        raise QualificationError("review_not_yet_effective")
    if as_of >= expires:
        raise QualificationError("stale_review")
    if expected_role in {"authorization_assertion", "reviewed_requirement"} and (
        not review.requirement_reviewed
    ):
        raise QualificationError("unreviewed_requirement")
    return QualifiedSource(
        raw_text=text, raw_sha256=digest, review=review, scope=scope
    )


# Exact structured keys are refused. Natural-language annotations remain inert
# data: this is not a semantic injection detector or a prose-to-policy parser.
AUTHORITY_KEYS = frozenset(
    {
        "source_id",
        "source_revision",
        "source_role",
        "role",
        "revision",
        "current_revision",
        "current",
        "approved",
        "authorized",
        "requirement_reviewed",
        "authority",
        "classification",
        "synthetic",
        "workflow",
        "workflows",
        "policy_scope",
        "policy_scopes",
        "access_scopes",
        "reviewed_at",
        "effective_at",
        "expires_at",
        "approval_granted",
        "actions_executed",
        "executed_action",
        "granted_access",
        "permission",
    }
)


def _unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise QualificationError("duplicate_json_key")
        value[key] = item
    return value


def _reject_number(_):
    raise QualificationError("unsupported_json_number")


def _integer(value):
    if len(value.lstrip("-")) > 16:
        raise QualificationError("integer_budget")
    return int(value)


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise QualificationError("unsupported_json_number")
    return number


def decode_json(
    raw: bytes,
    *,
    permitted_authority_keys: tuple[str, ...] = (),
    allow_finite_floats: bool = False,
) -> dict | list:
    """Decode bounded JSON losslessly; schema-specific types are checked later.

    A schema owner may explicitly allow a known key; this never turns its value
    into reviewed metadata. No inference, source lookup, or truncation occurs.
    """
    text = source_text(raw)
    # Existing Microsoft upload support accepts UTF-8 BOM. It remains in the
    # retained original bytes and is removed only from this parsing copy.
    text = text.removeprefix("\ufeff")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_pairs,
            parse_float=_finite_float if allow_finite_floats else _reject_number,
            parse_constant=_reject_number,
            parse_int=_integer,
        )
    except QualificationError:
        raise
    except (ValueError, RecursionError) as exc:
        raise QualificationError("malformed_json") from exc
    if not isinstance(value, (dict, list)):
        raise QualificationError("unsupported_json_layout")
    count = 0
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        count += 1
        if count > MAX_JSON_NODES:
            raise QualificationError("json_node_budget")
        if depth > MAX_JSON_DEPTH:
            raise QualificationError("json_depth_budget")
        if isinstance(item, dict):
            for key, child in item.items():
                if (
                    key in AUTHORITY_KEYS
                    and key not in permitted_authority_keys
                ):
                    raise QualificationError("source_content_authority_injection")
                if len(key) > 256 or any(ord(char) < 32 for char in key):
                    raise QualificationError("malformed_json_key")
                try:
                    key.encode("utf-8", errors="strict")
                except UnicodeError as exc:
                    raise QualificationError("malformed_encoding") from exc
                pending.append((child, depth + 1))
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)
        elif isinstance(item, str):
            if len(item) > MAX_TEXT_CHARACTERS:
                raise QualificationError("source_text_budget")
            try:
                item.encode("utf-8", errors="strict")
            except UnicodeError as exc:
                raise QualificationError("malformed_encoding") from exc
    return value
