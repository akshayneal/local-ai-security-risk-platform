"""Default-off native observation page; supplied values are rendered as data."""

import hashlib
import json
from pathlib import Path

import streamlit as st

from app.native_evidence_config import INVALID_INPUT, WITHHELD, native_evidence_enabled
from app.native_investigation import (
    QUESTION_TEXT,
    NativeInvestigationRequest,
)
from app.native_investigation import (
    validate_response as validate_investigation_response,
)
from app.native_observations import (
    MAX_SOURCE_BYTES,
    NativeObservationRequest,
    validate_response,
)
from app.soc_inputs import SocInputError, parse_csv_bundle, parse_json_bundle
from dashboard.native_evidence_client import (
    post_native_investigation,
    post_native_observations,
)

SAMPLE = (
    Path(__file__).resolve().parents[1]
    / "sample_data/native_evidence/network_observation.json"
)
PAGE = ("pages/native_evidence.py", "Native Evidence (Experimental)")


def navigation_groups(groups: dict, *, enabled: bool) -> dict:
    """Copy navigation rather than mutating the established page definitions."""
    result = {name: tuple(pages) for name, pages in groups.items()}
    if enabled:
        result["Experimental"] = result.get("Experimental", ()) + (PAGE,)
    return result


def _clear_results():
    st.session_state.pop("native_result", None)
    st.session_state.pop("native_error", None)


def _json_text(value):
    # Keep booleans, integers, strings and null visibly distinct in dataframes.
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _preview_rows(source_text, source_format, csv_case_id):
    """Bounded local parsing helps select a row; it never submits a request."""
    try:
        request = NativeObservationRequest(
            source_text=source_text,
            source_format=source_format,
            csv_case_id=csv_case_id,
        )
        raw = request.source_text.encode("utf-8")
        bundle = (
            parse_json_bundle(raw)
            if source_format == "microsoft_json"
            else parse_csv_bundle(raw, request.csv_table, csv_case_id)
        )
    except (ValueError, TypeError, UnicodeError, SocInputError):
        st.caption("Row preview unavailable; review the supported bundle shape.")
        return
    rows = bundle["tables"].get("DeviceNetworkEvents", [])
    with st.expander(f"Choose a subject from {len(rows)} supplied network rows"):
        st.caption(
            "Preview values are clipped after 120 characters. Build shows complete selected values. "
            "Rows remain separate; matching text does not associate events."
        )
        for index, row in enumerate(rows):
            st.text(f"DeviceNetworkEvents[{index}]")
            for name in (
                "Timestamp",
                "DeviceName",
                "InitiatingProcessId",
                "InitiatingProcessCreationTime",
                "ActionType",
                "RemoteIP",
                "RemotePort",
            ):
                value = _json_text(row[name]) if name in row else "not supplied"
                preview = (
                    value if len(value) <= 120 else value[:120] + " [preview clipped]"
                )
                kind = type(row[name]).__name__ if name in row else "absent"
                st.text(f"  {name} ({kind}): {preview}")


def _render_investigation(request, response):
    response = validate_investigation_response(request, response)
    report, observation = response.report, response.report.observation
    st.subheader("Native Evidence Investigation")
    st.caption(
        "Experimental · deterministic · zero model calls · human review required"
    )
    st.text("Investigation question: " + report.question_text)
    st.text("Case label supplied by input: " + observation.case_id)
    st.text("Selected row locator: " + observation.row_identity)
    st.subheader("Observation")
    st.caption(
        "Reported values from one selected row. Valid shape checks representation only; "
        "absent and invalid values remain unknown. Local/remote labels retain their original roles."
    )
    fields = {field.name: field for field in report.snapshot}
    for label, names in (
        ("Reported event", ("Timestamp", "ActionType", "ResultType")),
        ("Device", ("DeviceId", "DeviceName")),
        (
            "Initiating process",
            (
                "InitiatingProcessId",
                "InitiatingProcessCreationTime",
                "InitiatingProcessFileName",
            ),
        ),
        (
            "Reported account",
            (
                "InitiatingProcessAccountUpn",
                "InitiatingProcessAccountName",
                "InitiatingProcessAccountDomain",
            ),
        ),
        ("Local endpoint", ("LocalIP", "LocalPort")),
        ("Remote endpoint / reported protocol", ("RemoteIP", "RemotePort", "Protocol")),
    ):
        values = []
        for name in names:
            field = fields[name]
            value = _json_text(field.original_value) if field.present else "unknown"
            state = field.status
            if state == "invalid_shape":
                state += "; unknown"
            values.append(name + "=" + value + " [" + state + "]")
        st.text(label + ": " + "; ".join(values))
    with st.expander("Field values, shapes and provenance"):
        st.caption(
            "Every field below belongs to the selected row locator shown above. Original values are complete JSON literals."
        )
        st.dataframe(
            [
                {
                    "Source field": field.expected_path,
                    "State": field.status,
                    "Original value (JSON)": _json_text(field.original_value),
                    "Original type": field.original_type or "not supplied",
                    "Normalized value (JSON)": _json_text(field.normalized_value),
                    "Transformation": field.normalization,
                    "Limitation": field.reason_code,
                }
                for field in report.snapshot
            ],
            hide_index=True,
        )
    st.text(
        f"Rows retained: {observation.coverage.total_rows}; selected: 1; "
        f"outside the selected row: {observation.coverage.omitted_rows}; "
        f"repeated network representations: {observation.coverage.duplicate_network_rows}."
    )
    st.dataframe(
        [
            {
                "Supplied table": table.table,
                "Rows": table.row_count,
                "Selected for this view": table.selected_for_view,
            }
            for table in report.tables
        ],
        hide_index=True,
    )
    st.caption(
        "Supplied coverage does not establish collection completeness or absence of activity."
    )
    st.subheader("Supported comparison")
    st.caption(
        "Literal, type-sensitive field representations across supplied rows; no causal join or outcome comparison."
    )
    counts = {
        state: sum(comparison.state == state for comparison in report.comparisons)
        for state in (
            "same_representation",
            "different_representation",
            "not_comparable",
        )
    }
    st.text(
        f"Compared field representations: {counts['same_representation']} same; "
        f"{counts['different_representation']} different; {counts['not_comparable']} not comparable."
    )
    with st.expander("Representation comparison details and row paths"):
        if not report.comparisons:
            st.text("No other network row was supplied for representation comparison.")
        for comparison in report.comparisons:
            st.text(comparison.field + ": " + comparison.state)
            st.text(comparison.explanation)
            st.text("Selected: " + comparison.selected_path)
            st.text(
                "Other supplied paths: " + (", ".join(comparison.other_paths) or "none")
            )
    st.subheader("Insufficient evidence")
    st.text("Semantic decision: " + report.semantic_decision)
    st.text("Comparator: not executed (0 calls). Association: not assessed.")
    st.text("Relationship: unassessable. Native event semantics remain unverified.")
    for gap in report.gaps:
        st.text(gap.evidence_kind + ": " + gap.statement)
        st.text(
            "Source/gap paths: "
            + (", ".join(gap.paths) or "question-level evidence gap")
        )
    st.subheader("Suggested next investigation")
    st.caption(
        "Evidence questions to consider; these sources have not been queried or independently checked by this workflow."
    )
    for item in report.next_evidence:
        st.text(item.question)
        st.text(
            "Basis: "
            + (", ".join(item.basis_paths) or "selected investigation question")
        )
    st.subheader("Unverified analyst notes")
    st.text(
        "Not collected by this view; no analyst assertion or reviewer identity is added to the report."
    )
    with st.expander("Source integrity and complete original evidence"):
        st.text("Original byte SHA-256: " + observation.source_sha256)
        st.text("Source revision: " + observation.source_revision)
        st.text("Request fingerprint: " + report.request_fingerprint)
        st.text("Currentness: submitted snapshot only; external currentness unchecked.")
        st.text(
            "Authority: observation only. Review: not reviewed for policy or permission."
        )
        st.caption(
            "Hashes and upload locators correlate bytes; they do not authenticate or anonymize a source."
        )
        for warning in observation.warnings:
            st.text(warning)
        st.text(observation.original_source_text)
    st.caption(
        "No actions executed. No approval granted. Independent human review PENDING. "
        "Exports include the original source; review before sharing."
    )
    st.download_button(
        "Download investigation JSON",
        response.json_export,
        file_name="native_investigation.json",
        mime="application/json",
    )
    st.download_button(
        "Download investigation Markdown",
        response.markdown_export,
        file_name="native_investigation.md",
        mime="text/markdown",
    )


def _render(request, response):
    response = validate_response(request, response)
    report = response.report
    st.subheader("Submitted native observations")
    st.caption(
        "Unreviewed source assertions · human review required · zero model calls"
    )
    st.text("Source format: " + report.source_format)
    st.text("Input profile: " + report.source_profile)
    st.text("Case label supplied by input: " + report.case_id)
    st.text("Upload locator: " + report.upload_id)
    st.text("Original byte SHA-256: " + report.source_sha256)
    st.text("Source revision: " + report.source_revision)
    st.text("Currentness: submitted snapshot only; external currentness unchecked.")
    st.text(
        "Authority: observation only. Review: not reviewed for policy or permission."
    )
    st.text("Comparator: not executed (0 calls). Association: not assessed.")
    st.text("Relationship: unassessable. Native event semantics remain unverified.")
    st.text("Selected row locator: " + report.row_identity)
    st.caption(
        "Upload IDs and hashes locate supplied bytes; they do not authenticate an event or source."
    )
    st.subheader("Selected fields and original types")
    st.dataframe(
        [
            {
                "Source field": field.expected_path,
                "State": field.status,
                "Original value (JSON)": _json_text(field.original_value),
                "Original type": field.original_type or "not supplied",
                "Normalized value (JSON)": _json_text(field.normalized_value),
                "Transformation": field.normalization,
                "Limitation": field.reason_code,
            }
            for field in report.selected_fields
        ],
        hide_index=True,
    )
    st.caption(
        "Valid shape means a value has the expected representation. It does not prove the event occurred or was authorized."
    )
    st.subheader("Coverage and missing evidence")
    st.text(
        f"Rows retained: {report.coverage.total_rows}; selected for this view: {report.coverage.selected_rows}; "
        f"outside the selected row: {report.coverage.omitted_rows}; other table rows: {report.coverage.unsupported_rows}."
    )
    st.text(
        f"Repeated network rows retained: {report.coverage.duplicate_network_rows}."
    )
    st.caption(
        "These counts describe the submitted bundle and this view, not collection completeness."
    )
    for label, values in (
        ("Absent selected fields", report.coverage.absent_fields),
        ("Invalid field shapes", report.coverage.invalid_fields),
        ("Unverified field semantics", report.coverage.unverified_fields),
        ("Unknown vendor fields retained", report.coverage.unknown_vendor_fields),
    ):
        st.text(label + ": " + (", ".join(values) or "None in this submitted view"))
    st.subheader("Unsupported conclusions")
    st.write(
        "This view cannot establish completed access or transfer, permission, causal process identity, compromise, ATT&CK technique or security control effectiveness."
    )
    for warning in report.warnings:
        st.text(warning)
    with st.expander("All original field observations"):
        st.dataframe(
            [
                {
                    "Original path": item.original_path,
                    "Original value (JSON)": _json_text(item.value),
                    "Original type": item.original_type,
                }
                for item in report.observations
            ],
            hide_index=True,
        )
    with st.expander("Exact submitted source"):
        st.text(report.original_source_text)
    st.caption(
        "No actions executed. No approval granted. Independent human review PENDING. Exports contain original source text; review them before sharing."
    )
    st.download_button(
        "Download native observation JSON",
        response.json_export,
        file_name="native_observations.json",
        mime="application/json",
    )
    st.download_button(
        "Download native observation Markdown",
        response.markdown_export,
        file_name="native_observations.md",
        mime="text/markdown",
    )


def native_evidence_page(base_url: str) -> None:
    if not native_evidence_enabled():
        _clear_results()
        st.info("The experimental native evidence workflow is disabled.")
        return
    st.title("Native Evidence (Experimental)")
    st.write(
        "Inspect a supplied Microsoft-format network row without a model or authorization comparison."
    )
    st.caption(
        "Development only · unreviewed local JSON/CSV · no Microsoft connection · no actions"
    )
    st.info(
        "This page requires the ENABLE_NATIVE_EVIDENCE_WORKFLOW=1 process flag and the manual app.native_evidence_api:app backend. The standard development launcher and release demo are unchanged."
    )
    view = st.selectbox(
        "Report view",
        ["Source observations", "Native Evidence Investigation"],
        key="native_view",
    )
    investigation = view == "Native Evidence Investigation"
    st.caption(
        "Choose Native Evidence Investigation for a reported event snapshot, evidence gaps and next-evidence questions."
    )
    question = "reported_event"
    if investigation:
        question = st.selectbox(
            "Investigation question",
            list(QUESTION_TEXT),
            key="native_question",
            format_func=lambda value: QUESTION_TEXT[value],
        )
    sample_error = None
    if st.button("Load synthetic network example"):
        _clear_results()
        try:
            if SAMPLE.stat().st_size > MAX_SOURCE_BYTES:
                raise ValueError("sample_byte_budget")
            st.session_state["native_source_text"] = SAMPLE.read_bytes().decode(
                "utf-8", errors="strict"
            )
            st.session_state["native_mode"] = "Paste JSON"
            st.session_state["native_row"] = 0
        except (OSError, ValueError, UnicodeError):
            sample_error = "The synthetic example is unavailable."
    mode = st.selectbox(
        "Native input", ["Paste JSON", "Upload JSON", "Upload CSV"], key="native_mode"
    )
    source_text, upload_error, upload_marker = "", None, ""
    if mode == "Paste JSON":
        source_text = st.text_area(
            "Native Microsoft JSON bundle",
            key="native_source_text",
            height=240,
            max_chars=MAX_SOURCE_BYTES,
        )
    else:
        upload = st.file_uploader(
            "Native telemetry file",
            type=["csv" if mode == "Upload CSV" else "json"],
            key="native_upload_" + mode,
        )
        if upload is not None:
            size = getattr(upload, "size", None)
            if type(size) is not int or not 0 < size <= MAX_SOURCE_BYTES:
                upload_error, upload_marker = INVALID_INPUT, "invalid_upload_size"
            else:
                raw = upload.getvalue()
                upload_marker = hashlib.sha256(raw).hexdigest()
                try:
                    if len(raw) != size or len(raw) > MAX_SOURCE_BYTES:
                        raise ValueError("upload_byte_budget")
                    source_text = raw.decode("utf-8", errors="strict")
                except (ValueError, UnicodeError):
                    upload_error = INVALID_INPUT
    csv_case_id = None
    if mode == "Upload CSV":
        st.caption("CSV source table: DeviceNetworkEvents. Cells remain strings.")
        csv_case_id = st.text_input(
            "Native CSV case label (unverified)",
            value="SYN-NATIVE-CSV",
            max_chars=256,
            key="native_csv_case",
        )
    row_index = st.number_input(
        "Selected network row (zero based)",
        min_value=0,
        max_value=49,
        value=0,
        step=1,
        key="native_row",
    )
    source_format = "microsoft_csv" if mode == "Upload CSV" else "microsoft_json"
    payload = {
        "source_text": source_text,
        "source_format": source_format,
        "row_index": row_index,
        "csv_case_id": csv_case_id,
    }
    if investigation:
        payload["question"] = question
        if source_text and upload_error is None:
            _preview_rows(source_text, source_format, csv_case_id)
    request_model = (
        NativeInvestigationRequest if investigation else NativeObservationRequest
    )
    validate = validate_investigation_response if investigation else validate_response
    post = post_native_investigation if investigation else post_native_observations
    # Invalidate even when a new input cannot form a valid request. No previous
    # report/download may survive an oversized or undecodable replacement.
    fingerprint = hashlib.sha256(
        json.dumps(
            [view, mode, payload, upload_marker, upload_error, base_url],
            ensure_ascii=True,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    if st.session_state.get("native_input_fingerprint") != fingerprint:
        _clear_results()
        st.session_state["native_input_fingerprint"] = fingerprint
    if upload_error:
        st.error(upload_error)
    if sample_error:
        st.error(sample_error)
    if st.button(
        "Build investigation report" if investigation else "Build native observations",
        type="primary",
        disabled=not source_text or upload_error is not None,
    ):
        _clear_results()
        try:
            request = request_model(**payload)
            with st.spinner("Building source-bound observations..."):
                response, error = post(base_url, request)
            if error:
                st.session_state["native_error"] = error
            else:
                response = validate(request, response)
                st.session_state["native_result"] = {
                    "request": request.model_dump(mode="json"),
                    "response": response.model_dump(mode="json"),
                }
        except (ValueError, TypeError, AttributeError, UnicodeError, RecursionError):
            st.session_state["native_error"] = INVALID_INPUT
    if st.session_state.get("native_error"):
        st.error(st.session_state["native_error"])
    if saved := st.session_state.get("native_result"):
        try:
            # Revalidate against both the saved submission and current widgets on
            # every render/download rerun, rather than trusting a stored envelope.
            request = request_model(**payload)
            saved_request = request_model.model_validate(saved["request"])
            if request.model_dump_json() != saved_request.model_dump_json():
                raise ValueError("current_request_changed")
            render = _render_investigation if investigation else _render
            render(request, saved["response"])
        except (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            UnicodeError,
            RecursionError,
        ):
            _clear_results()
            st.error(WITHHELD)
