"""Opt-in local analysis client and session guard for uncertain inference work.

The guard is a local interaction aid, not idempotency, cancellation or a queue.
No result is recovered from the backend's metadata-only status endpoint.
"""

import json
from dataclasses import dataclass
from uuid import UUID, uuid4

import requests
import streamlit as st

from app.inference_lifecycle import (
    ExecutionStatus,
    LifecycleResponse,
    lifecycle_enabled,
    load_config,
)
from app.ui_schemas import GovernanceAnalysisEnvelope, SocAnalysisEnvelope
from dashboard.native_evidence_client import (
    _local_base,
    _reject_constant,
    _unique_pairs,
)

BASE_PATH = "/experimental/analysis-lifecycle/v1"
MAX_WIRE_BYTES = 400_000
MAX_RESPONSE_BYTES = 4_000_000
MAX_STATUS_BYTES = 16_384
GUARD_KEY = "analysis_lifecycle_guard"
UNKNOWN_ERROR = (
    "The analysis outcome is unknown after a request attempt. The provider may still be running. "
    "No automatic retry was made. Check this attempt's status before deciding whether to submit again."
)
BEFORE_DISPATCH_ERROR = (
    "The experimental analysis request was rejected locally before dispatch. "
    "Check the loopback API address, input and process-owned lifecycle configuration."
)
KNOWN_ERROR = "The experimental analysis did not return an analyst result. Its recorded lifecycle status is shown below."
STATUS_ERROR = "The attempt status is unavailable or could not be validated. Missing status does not prove that no inference ran or that it stopped."


@dataclass(frozen=True)
class LifecycleOutcome:
    result: dict | None = None
    execution: dict | None = None
    error: str | None = None
    keep_guard: bool = False


def _attempt_id(value: str) -> str:
    if not isinstance(value, str) or str(UUID(value)) != value:
        raise ValueError("canonical_attempt_uuid_required")
    return value


def _decode(response, limit):
    body = bytearray()
    for chunk in response.iter_content(chunk_size=8192):
        if len(body) + len(chunk) > limit:
            raise ValueError("response_byte_budget")
        body.extend(chunk)
    return json.loads(
        body.decode("utf-8", errors="strict"),
        object_pairs_hook=_unique_pairs,
        parse_constant=_reject_constant,
    )


def _status(value, attempt_id):
    status = ExecutionStatus.model_validate(value)
    if status.attempt_id != attempt_id:
        raise ValueError("attempt_identity_mismatch")
    return status.model_dump(mode="json")


def post_lifecycle_analysis(
    base_url: str, *, soc: bool, payload: dict, attempt_id: str
) -> LifecycleOutcome:
    """One POST only. A transport failure cannot establish provider cancellation."""
    try:
        base = _local_base(base_url)
        attempt_id = _attempt_id(attempt_id)
        config = load_config()
        encoded = json.dumps(payload, ensure_ascii=True, allow_nan=False).encode(
            "utf-8"
        )
        if len(encoded) > MAX_WIRE_BYTES:
            raise ValueError("request_byte_budget")
    except (ValueError, TypeError, AttributeError, UnicodeError, RecursionError):
        return LifecycleOutcome(error=BEFORE_DISPATCH_ERROR)
    endpoint = BASE_PATH + "/analyze/" + ("soc-alert" if soc else "governance")
    try:
        with requests.Session() as transport:
            transport.trust_env = False
            with transport.post(
                base + endpoint,
                data=encoded,
                headers={
                    "Content-Type": "application/json",
                    "X-Analysis-Attempt-ID": attempt_id,
                },
                timeout=(config.connect_seconds, config.ui_timeout),
                stream=True,
                allow_redirects=False,
            ) as response:
                status_code = response.status_code
                body = _decode(response, MAX_RESPONSE_BYTES)
        if status_code == 200:
            response = LifecycleResponse.model_validate(body)
            execution = _status(response.execution, attempt_id)
            if execution["state"] != "completed_validated":
                raise ValueError("completed_response_required")
            model = SocAnalysisEnvelope if soc else GovernanceAnalysisEnvelope
            result = model.model_validate(response.result).model_dump(mode="json")
            return LifecycleOutcome(result=result, execution=execution)
        detail = body.get("detail") if isinstance(body, dict) else None
        if not isinstance(detail, dict) or detail.get("code") not in {
            "analysis_lifecycle_withheld",
            "analysis_attempt_reused",
        }:
            raise ValueError("unrecognized_lifecycle_failure")
        execution = _status(detail.get("execution"), attempt_id)
        keep_guard = detail["code"] == "analysis_attempt_reused" or execution[
            "state"
        ] in {"running", "unknown_post_dispatch", "completed_validated"}
        return LifecycleOutcome(
            execution=execution,
            error=UNKNOWN_ERROR if keep_guard else KNOWN_ERROR,
            keep_guard=keep_guard,
        )
    except (
        requests.RequestException,
        ValueError,
        TypeError,
        AttributeError,
        UnicodeError,
        RecursionError,
    ):
        return LifecycleOutcome(error=UNKNOWN_ERROR, keep_guard=True)


def get_lifecycle_status(
    base_url: str, attempt_id: str
) -> tuple[dict | None, str | None]:
    """Metadata-only lookup. A missing record is an unknown outcome."""
    try:
        base, attempt_id = _local_base(base_url), _attempt_id(attempt_id)
        with requests.Session() as transport:
            transport.trust_env = False
            with transport.get(
                base + BASE_PATH + "/status/" + attempt_id,
                timeout=(3, 10),
                stream=True,
                allow_redirects=False,
            ) as response:
                if response.status_code != 200:
                    return None, STATUS_ERROR
                body = _decode(response, MAX_STATUS_BYTES)
        return _status(body, attempt_id), None
    except (
        requests.RequestException,
        ValueError,
        TypeError,
        AttributeError,
        UnicodeError,
        RecursionError,
    ):
        return None, STATUS_ERROR


def submit_lifecycle_analysis(base_url: str, *, soc: bool, payload: dict):
    """Reserve the UI guard before sending so an interrupted render retains it."""
    if st.session_state.get(GUARD_KEY):
        return None, UNKNOWN_ERROR
    attempt_id = str(uuid4())
    st.session_state[GUARD_KEY] = {
        "attempt_id": attempt_id,
        "base_url": base_url,
        "workflow": "SOC Investigation" if soc else "AI System Risk Review",
        "state": "running",
    }
    st.text("Attempt ID: " + attempt_id)
    st.caption(
        "Record this correlation ID before waiting. A full browser reload, new session or tab, "
        "or server restart can lose this session's guard; the ID does not guarantee cancellation or idempotency."
    )
    try:
        outcome = post_lifecycle_analysis(
            base_url, soc=soc, payload=payload, attempt_id=attempt_id
        )
    except Exception:  # noqa: BLE001 -- retain the guard on an interrupted client callback
        outcome = LifecycleOutcome(error=UNKNOWN_ERROR, keep_guard=True)
    if outcome.execution is not None:
        st.session_state["analysis_lifecycle_last_status"] = outcome.execution
    if outcome.keep_guard:
        guard = st.session_state[GUARD_KEY]
        guard["state"] = "unknown_post_dispatch"
        if outcome.execution is not None:
            guard["execution"] = outcome.execution
        st.session_state[GUARD_KEY] = guard
    else:
        st.session_state.pop(GUARD_KEY, None)
    return outcome.result, outcome.error


def _release_guard(attempt_id: str):
    guard = st.session_state.get(GUARD_KEY)
    if (
        guard
        and guard["attempt_id"] == attempt_id
        and st.session_state.get("lifecycle_ack_" + attempt_id) is True
    ):
        st.session_state.pop(GUARD_KEY, None)


def lifecycle_panel() -> bool:
    """Render explicit status/acknowledgment controls; never submit automatically."""
    guard = st.session_state.get(GUARD_KEY)
    if not lifecycle_enabled() and not guard:
        return False
    st.info(
        "Experimental inference lifecycle: generic SOC and AI System Risk use the separate "
        "app.lifecycle_api:app backend when ENABLE_INFERENCE_LIFECYCLE=1. "
        "Microsoft uploads and AI Security retain legacy transport and timeout/duplicate limitations."
    )
    st.caption(
        "Process-owned time budgets check elapsed monotonic time between stages; network timeouts are inactivity limits. "
        "A timeout does not cancel provider work. Attempt IDs do not guarantee idempotency or once-only execution."
    )
    if not guard:
        status = st.session_state.get("analysis_lifecycle_last_status")
        if status:
            st.text(
                f"Last lifecycle attempt: {status['attempt_id']}; state: {status['state']}; "
                f"raw inference sends: {status['raw_sends']}."
            )
        return False
    st.warning(
        "An earlier analysis attempt needs an explicit decision before another analysis in the protected SOC and AI System Risk workspaces. "
        "Editing inputs, loading a sample or rerunning this page within the active session does not release this guard."
    )
    st.text("Attempt ID: " + guard["attempt_id"])
    st.text("Workflow: " + guard["workflow"])
    if st.button("Check analysis attempt status", key="lifecycle_check_status"):
        status, error = get_lifecycle_status(guard["base_url"], guard["attempt_id"])
        if error:
            guard["status_error"] = error
        else:
            guard["execution"] = status
            guard.pop("status_error", None)
        st.session_state[GUARD_KEY] = guard
    if guard.get("status_error"):
        st.warning(guard["status_error"])
    if execution := guard.get("execution"):
        st.text(
            f"Recorded state: {execution['state']}; raw inference sends: {execution['raw_sends']}; "
            f"reason: {execution['reason_code']}."
        )
        if execution["state"] == "completed_validated":
            st.info(
                "The backend recorded completion, but this lookup stores metadata only. "
                "The lost analyst result cannot be recovered here."
            )
    st.caption(
        "Status is process-local and bounded to 64 records; restart or eviction can remove it. "
        "Missing status or Activity does not prove no dispatch. Releasing this guard does not stop or cancel any provider request."
    )
    st.caption(
        "This guard applies to these protected workspaces in this Streamlit session. "
        "A full browser reload, new session or tab, or server restart can lose it. "
        "Record the attempt ID for a manual status lookup. It does not coordinate other sessions, browser tabs or the legacy AI Security page."
    )
    acknowledged = st.checkbox(
        "I understand the earlier request may still run and a fresh analysis may overlap it.",
        key="lifecycle_ack_" + guard["attempt_id"],
    )
    st.button(
        "Acknowledge and allow a fresh analysis",
        key="lifecycle_release_guard",
        disabled=not acknowledged,
        on_click=_release_guard,
        args=(guard["attempt_id"],),
    )
    return True
