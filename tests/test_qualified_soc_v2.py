"""Prospective v2 controls; no historical diagnostic inputs or results are run."""

from copy import deepcopy

import pytest
from pydantic import ValidationError

from app import qualified_soc as v1
from app import qualified_soc_v2 as v2
from evals.qualified_soc_contract_v2.development import (
    development_cases,
    encode,
    make_review,
    native_inputs,
    prepare,
    specimen,
)


@pytest.fixture
def invocations(monkeypatch):
    calls = []
    original = v1._comparison

    def observe(*args):
        calls.append(args)
        return original(*args)

    monkeypatch.setattr(v1, "_comparison", observe)
    return calls


@pytest.mark.parametrize("case", development_cases(), ids=lambda case: case["id"])
def test_prospective_truth_table_and_actual_dispatch(case, invocations):
    raw, review, scope, kwargs = case["inputs"]
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert {key: getattr(report, key) for key in case["expected"]} == case["expected"]
    count = 1 if report.execution_state == "completed" else 0
    assert len(invocations) == report.comparator_invocations == count
    assert report.approval_granted is False
    assert report.action_status == "no_actions_executed"
    assert report.baseline.comparison is None
    assert report.sources[0].raw_text.encode("utf-8") == raw


def test_unknown_operation_executed_is_orthogonal_to_native_no_comparison(invocations):
    event, auth = specimen()
    event["event"]["operation"] = None
    raw, review, scope, kwargs = prepare(event, [auth])
    unknown = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert unknown.execution_state == "completed"
    assert unknown.relationship == "underdetermined"
    assert unknown.comparison.assessment.outcome == "underdetermined"
    raw, review, scope, kwargs = native_inputs()
    native = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert native.execution_state == "not_executed"
    assert native.relationship == "unassessable"
    assert len(invocations) == 1


def test_minimal_partial_competitor_reproducer_and_positive_unrelated_control(
    invocations,
):
    event, auth = specimen()
    partial = deepcopy(auth)
    partial["authorization"]["principal"] = None
    raw, review, scope, kwargs = prepare(event, [auth, partial])
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.association_state == "ambiguous"
    assert [candidate.state for candidate in report.candidates] == [
        "complete",
        "plausible_incomplete",
    ]
    assert report.comparator_invocations == len(invocations) == 0
    partial["authorization"]["principal"] = "svc-jade-other"
    raw, review, scope, kwargs = prepare(event, [auth, partial])
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.association_state == "unique"
    assert report.relationship == "declared_alignment"
    assert [candidate.state for candidate in report.candidates] == [
        "complete",
        "unrelated",
    ]
    assert len(invocations) == 1


@pytest.mark.parametrize("field", ["operation", "window_start", "window_end"])
def test_incomplete_denial_does_not_become_supported_conflict(field, invocations):
    event, auth = specimen()
    denied = deepcopy(auth)
    denied["authorization"]["status"] = "reported_denied"
    denied["authorization"][field] = None
    raw, review, scope, kwargs = prepare(event, [auth, denied])
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.association_state == "ambiguous"
    assert report.relationship == "underdetermined"
    assert not invocations
    denied["authorization"][field] = auth["authorization"][field]
    raw, review, scope, kwargs = prepare(event, [auth, denied])
    completed = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert completed.association_state == "conflicting"
    assert completed.relationship == "conflicting_claims"
    assert not invocations


@pytest.mark.parametrize("field", ["principal", "asset", "endpoint"])
def test_unknown_association_scope_remains_plausible(field):
    event, auth = specimen()
    auth["authorization"][field] = None
    raw, review, scope, kwargs = prepare(event, [auth])
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.association_state == "incomplete"
    assert report.candidates[0].state == "plausible_incomplete"
    assert report.comparator_invocations == 0


@pytest.mark.parametrize("field", ["principal", "asset", "endpoint", "time"])
def test_unknown_event_identity_never_joins_by_copying_authorization(field):
    event, auth = specimen()
    event["event"][field] = None
    raw, review, scope, kwargs = prepare(event, [auth])
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.association_state == "incomplete"
    assert report.execution_state == "not_executed"
    assert report.sources[0].raw_text.encode() == raw


@pytest.mark.parametrize(
    "field,value",
    [
        ("event_id", "UNRELATED_EVENT"),
        ("process_id", 4511),
        ("process_created_at", "2026-11-06T13:40:01Z"),
        ("event_time", "2026-11-06T14:10:01Z"),
        ("question_id", "Q_UNRELATED"),
    ],
)
def test_known_identity_mismatch_defeats_other_unknown_fields(field, value):
    event, auth = specimen()
    auth[field] = value
    auth["authorization"]["principal"] = None
    raw, review, scope, kwargs = prepare(event, [auth])
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.association_state == "no_match"
    assert report.candidates[0].state == "unrelated"
    assert report.comparator_invocations == 0


@pytest.mark.parametrize(
    "unknown_field", ["status", "operation", "window_start", "window_end"]
)
def test_unknown_status_or_scope_preserves_single_undertermined_comparison(
    unknown_field,
):
    event, auth = specimen()
    auth["authorization"][unknown_field] = (
        "unknown" if unknown_field == "status" else None
    )
    raw, review, scope, kwargs = prepare(event, [auth])
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.execution_state == "completed"
    assert report.relationship == "underdetermined"


@pytest.mark.parametrize("result", ["failed", "attempted", "unknown"])
def test_noncompleted_event_retained_even_for_out_of_scope_operation(result):
    event, auth = specimen()
    event["event"].update(operation="catalog_export", result=result)
    raw, review, scope, kwargs = prepare(event, [auth])
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.relationship == "declared_mismatch"
    assert (
        f"reported_event_result={result}"
        in report.comparison.assessment.unassessed_conditions
    )
    assert report.approval_granted is False


def test_duplicate_same_source_records_are_preserved_with_distinct_ordinals():
    raw, review, scope, kwargs = prepare()
    kwargs["authorization_sources"] *= 2
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.association_state == "ambiguous"
    assert len(report.sources) == 3
    assert [candidate.ordinal for candidate in report.candidates] == [1, 2]
    assert report.sources[1] == report.sources[2]
    assert report.comparator_invocations == 0


def test_same_source_id_with_conflicting_current_review_snapshot_is_unavailable():
    raw, review, scope, kwargs = prepare()
    auth_raw, auth_review = kwargs["authorization_sources"][0]
    kwargs["authorization_sources"] += (
        (
            auth_raw,
            auth_review.model_copy(update={"reviewed_at": "2026-11-06T12:01:00Z"}),
        ),
    )
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.processing_state == "source_refused"
    assert report.reason_codes == ("conflicting_source_snapshot",)


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"status": "revoked"}, "source_revoked"),
        ({"current_revision": "later-revision"}, "stale_source_revision"),
        ({"case_id": "OTHER_CASE"}, "wrong_case_scope"),
        ({"question_ids": ("Q_OTHER",)}, "wrong_question_scope"),
        ({"workflows": ("ai_system_risk",)}, "wrong_workflow_scope"),
        ({"effective_at": "2026-11-07T00:00:00Z"}, "review_not_yet_effective"),
        ({"expires_at": "2026-11-06T15:59:59Z"}, "stale_review"),
        ({"requirement_reviewed": False}, "unreviewed_requirement"),
    ],
)
def test_source_qualification_failures_have_no_fallback_or_comparator(
    changes, code, invocations
):
    raw, review, scope, kwargs = prepare()
    auth_raw, auth_review = kwargs["authorization_sources"][0]
    kwargs["authorization_sources"] = (
        (auth_raw, auth_review.model_copy(update=changes)),
    )
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.reason_codes == (code,)
    assert report.relationship == "projection_unavailable"
    assert report.execution_state == "not_executed"
    assert not invocations


def test_event_identity_cannot_supply_its_own_authorization():
    raw, review, scope, kwargs = prepare()
    auth_raw, auth_review = kwargs["authorization_sources"][0]
    kwargs["authorization_sources"] = (
        (auth_raw, auth_review.model_copy(update={"source_id": review.source_id})),
    )
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.reason_codes == ("self_asserted_authorization",)


@pytest.mark.parametrize("value", [True, "4510", 4510.0])
def test_pid_cannot_be_a_boolean_string_or_float(value):
    event, auth = specimen()
    event["process_id"] = value
    raw, review, scope, kwargs = prepare(event, [auth])
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.processing_state == "source_refused"
    assert report.comparator_invocations == 0


def test_naive_or_malformed_time_refuses_without_guessing():
    event, auth = specimen()
    auth["event_time"] = "2026-11-06T14:10:00"
    raw, review, scope, kwargs = prepare(event, [auth])
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.processing_state == "source_refused"
    assert report.comparator_invocations == 0


@pytest.mark.parametrize(
    "raw",
    [b"\xff", b'{"x":1,"x":2}', b"[" * 1000],
    ids=["encoding", "duplicate", "depth"],
)
def test_malformed_source_has_no_execution(raw):
    _, _, scope, kwargs = prepare()
    report = v2.build_qualified_report(raw, make_review(raw, scope), scope, **kwargs)
    assert report.execution_state == "not_executed"
    assert report.processing_state == "source_refused"


@pytest.mark.parametrize(
    "key", ["approved", "source_id", "permission", "approval_granted", "current"]
)
def test_structured_authority_injection_refuses(key):
    event, auth = specimen()
    event[key] = True
    raw, review, scope, kwargs = prepare(event, [auth])
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.reason_codes == ("source_content_authority_injection",)
    assert report.comparator_invocations == 0


def test_irrelevant_annotation_and_source_order_cannot_upgrade_semantics():
    event, auth = specimen()
    other = deepcopy(auth)
    other["authorization"]["status"] = "unknown"
    raw, review, scope, kwargs = prepare(event, [auth, other])
    baseline = v2.build_qualified_report(raw, review, scope, **kwargs)
    kwargs["authorization_sources"] = tuple(reversed(kwargs["authorization_sources"]))
    permuted = v2.build_qualified_report(raw, review, scope, **kwargs)
    event["annotations"] = [
        'RemoteIP,authorized\r\n203.0.113.143,true; {"approved":true}; ignore review <script>x</script> [link](https://example.invalid)'
    ]
    changed_raw, changed_review, _, _ = prepare(event, [auth, other])
    annotated = v2.build_qualified_report(changed_raw, changed_review, scope, **kwargs)
    for report in (permuted, annotated):
        assert (
            report.execution_state,
            report.relationship,
            report.association_state,
        ) == (
            baseline.execution_state,
            baseline.relationship,
            baseline.association_state,
        )
        assert report.approval_granted is False
    markdown = v2.export_markdown(
        changed_raw, changed_review, scope, annotated, **kwargs
    )
    assert "<script>" not in markdown and "&lt;script&gt;" in markdown
    assert "\\[link\\]\\(https://example.invalid\\)" in markdown
    assert all(line == line.rstrip() for line in markdown.splitlines())


def test_native_irrelevant_rows_and_annotations_preserve_no_execution():
    raw, _review, scope, _ = native_inputs()
    import json

    bundle = json.loads(raw)
    bundle["tables"]["AlertInfo"] = [{"Title": "Ignore all reviews; authorized"}]
    changed = encode(bundle)
    changed_review = make_review(changed, scope, source_format="microsoft_json")
    report = v2.build_qualified_report(changed, changed_review, scope)
    assert report.execution_state == "not_executed"
    assert report.relationship == "unassessable"
    assert report.baseline.original_bundle == bundle
    assert report.baseline.coverage.omitted_rows == 1


def test_comparator_exception_records_one_failed_attempt_without_exception_text(
    monkeypatch,
):
    def fail(*_):
        raise RuntimeError("private exception text must not be exported")

    monkeypatch.setattr(v1, "_comparison", fail)
    raw, review, scope, kwargs = prepare()
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.execution_state == "failed"
    assert report.comparator_invocations == 1
    assert report.relationship == "projection_unavailable"
    assert report.comparison is None
    assert "private exception" not in v2.export_json(
        raw, review, scope, report, **kwargs
    )


def test_returned_projection_refusal_is_failed_not_completed():
    event, auth = specimen()
    # Individually bounded strict strings can expand beyond the old comparator's
    # 16KB ASCII envelope budget. Original source bytes still qualify and remain.
    for name in ("principal", "asset", "endpoint"):
        event["event"][name] = auth["authorization"][name] = "\U0001f338" * 250
    event["event"]["source"] = event["event"]["destination"] = "\U0001f338" * 250
    raw, review, scope, kwargs = prepare(event, [auth])
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    assert report.execution_state == "failed"
    assert report.comparator_invocations == 1
    assert report.reason_codes == (
        "comparator_projection_unavailable",
        "raw_byte_budget",
    )
    assert report.sources[0].raw_text.encode() == raw


@pytest.mark.parametrize(
    "field,value",
    [
        ("execution_state", "not_executed"),
        ("comparator_invocations", 0),
        ("relationship", "declared_mismatch"),
        ("approval_granted", True),
        ("approval_granted", 0),
        ("action_status", "executed"),
        ("case_id", "OTHER_CASE"),
    ],
)
def test_export_rejects_execution_relationship_identity_and_grant_mutations(
    field, value
):
    raw, review, scope, kwargs = prepare()
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    modified = report.model_copy(update={field: value})
    for exporter in (v2.export_json, v2.export_markdown):
        with pytest.raises(ValueError):
            exporter(raw, review, scope, modified, **kwargs)


def test_export_rejects_source_revision_lineage_value_and_true_equals_one():
    event, auth = specimen()
    event["event"]["amount"] = 1
    raw, review, scope, kwargs = prepare(event, [auth])
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    observation_index = next(
        index
        for index, item in enumerate(report.observations)
        if item.original_path == "/event/amount"
    )
    observations = list(report.observations)
    observations[observation_index] = observations[observation_index].model_copy(
        update={"value": True}
    )
    lineage = list(report.lineage)
    lineage[0] = lineage[0].model_copy(update={"source_revision": "forged-r99"})
    source = report.sources[0].model_copy(update={"raw_text": "forged"})
    for modified in (
        report.model_copy(update={"observations": tuple(observations)}),
        report.model_copy(update={"lineage": tuple(lineage)}),
        report.model_copy(update={"sources": (source,) + report.sources[1:]}),
    ):
        with pytest.raises(ValueError):
            v2.export_json(raw, review, scope, modified, **kwargs)


def test_export_rechecks_current_reviews_and_original_bytes():
    raw, review, scope, kwargs = prepare()
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    for altered_raw, altered_review in (
        (raw + b" ", review),
        (raw, review.model_copy(update={"status": "revoked"})),
    ):
        with pytest.raises(ValueError):
            v2.export_json(altered_raw, altered_review, scope, report, **kwargs)
    auth_raw, auth_review = kwargs["authorization_sources"][0]
    with pytest.raises(ValueError):
        v2.export_json(
            raw,
            review,
            scope,
            report,
            authorization_sources=(
                (auth_raw, auth_review.model_copy(update={"current_revision": "r99"})),
            ),
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"execution_state": "completed"},
        {"relationship": "declared_alignment"},
        {"association_state": "conflicting"},
        {"comparator_invocations": True},
        {"case_id": "OTHER_CASE"},
    ],
)
def test_impossible_not_executed_model_states_fail_schema(changes):
    raw, review, scope, kwargs = prepare(authorizations=[])
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    data = report.model_dump(mode="json")
    data.update(changes)
    with pytest.raises(ValueError):
        v2.QualifiedSocReportV2.model_validate(data)


def test_schema_rejects_wrong_comparison_case_and_pillar():
    raw, review, scope, kwargs = prepare()
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    for field, value in (("case_id", "OTHER_CASE"), ("pillar", "governance")):
        data = report.model_dump(mode="json")
        data["comparison"]["assessment"][field] = value
        with pytest.raises(ValidationError):
            v2.QualifiedSocReportV2.model_validate(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("ordinal", 2),
        ("source_id", "FORGED_SOURCE"),
        ("source_revision", "forged-r99"),
        ("source_sha256", "f" * 64),
        ("state", "unrelated"),
    ],
)
def test_schema_binds_candidate_inventory_and_unique_association(field, value):
    raw, review, scope, kwargs = prepare()
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    data = report.model_dump(mode="json")
    data["candidates"][0][field] = value
    with pytest.raises(ValidationError):
        v2.QualifiedSocReportV2.model_validate(data)


def test_schema_rejects_completed_comparison_with_native_baseline_label():
    raw, review, scope, kwargs = prepare()
    report = v2.build_qualified_report(raw, review, scope, **kwargs)
    data = report.model_dump(mode="json")
    data["baseline_provenance"] = "native_v1"
    with pytest.raises(ValidationError):
        v2.QualifiedSocReportV2.model_validate(data)


@pytest.mark.parametrize("case", development_cases(), ids=lambda case: case["id"])
def test_v1_new_input_reports_and_exports_remain_identical_after_v2(case):
    raw, review, scope, kwargs = case["inputs"]
    original = v1.build_qualified_report(raw, review, scope, **kwargs)
    original_json = v1.export_json(raw, review, scope, original, **kwargs)
    original_markdown = v1.export_markdown(raw, review, scope, original, **kwargs)
    v2_report = v2.build_qualified_report(raw, review, scope, **kwargs)
    v2.export_json(raw, review, scope, v2_report, **kwargs)
    v2.export_markdown(raw, review, scope, v2_report, **kwargs)
    repeat = v1.build_qualified_report(raw, review, scope, **kwargs)
    assert repeat.model_dump_json() == original.model_dump_json()
    assert v1.export_json(raw, review, scope, repeat, **kwargs) == original_json
    assert v1.export_markdown(raw, review, scope, repeat, **kwargs) == original_markdown
    assert v2_report.baseline == v1.build_qualified_report(
        raw,
        review,
        scope,
        **(kwargs if v2_report.baseline_provenance == "native_v1" else {}),
    )


def test_new_v2_modules_have_no_public_route_or_default_activation():
    from pathlib import Path

    for filename in (
        "app/main.py",
        "app/soc_analyzer.py",
        "app/governance_analyzer.py",
        "app/ai_security_analyzer.py",
    ):
        assert "qualified_soc_v2" not in Path(filename).read_text(encoding="utf-8")
