"""Explicit local-development diagnostics; no payloads, filesystem or API hooks."""

import hashlib
import time
from typing import Any

from app.analysis_trace import AnalysisTrace
from app.output_policy import SOC_FACTUAL_FIELDS

_FIXED = {
    "response failed source/citation processing contract": ("SOURCE_PROCESSING", None),
    "response failed schema validation": ("SCHEMA", None),
    "observed_evidence must be a nonempty list of supported observations": (
        "OBSERVATIONS_REQUIRED",
        "observed_evidence",
    ),
    "observed_evidence items must be nonblank strings": (
        "OBSERVATIONS_BLANK",
        "observed_evidence",
    ),
}
_SUFFIXES = {
    " contains malformed IPv4-like tokens": "IP_SHAPE",
    " contains a malformed near-input SHA-256 token": "SHA_SHAPE",
    " contains an endpoint relationship absent from the original request": "ENDPOINT_PAIR",
    " contradicts an explicit input endpoint role": "ENDPOINT_ROLE",
    " changes a supplied destination port": "ENDPOINT_PORT",
    **{
        f" contains {kind} values absent from the original request": code
        for kind, code in (
            ("ipv4", "IP_MEMBERSHIP"),
            ("sha256", "SHA_MEMBERSHIP"),
            ("cve", "CVE_MEMBERSHIP"),
        )
    },
}


def violation_code(value: Any) -> dict:
    """Exact allowlist matching, never exception parsing or arbitrary field echo."""
    if isinstance(value, str):
        if value in _FIXED:
            code, field = _FIXED[value]
            return {"code": code, "field": field}
        for field in SOC_FACTUAL_FIELDS:
            for suffix, code in _SUFFIXES.items():
                if value == field + suffix:
                    return {"code": code, "field": field}
    return {"code": "UNCLASSIFIED", "field": None}


class LocalDiagnosticTrace(AnalysisTrace):
    """Pass explicitly to an analyzer in local experiments only.

    Unlike AnalysisTrace, stage values are never copied. Unlike ProductTrace,
    fixed rejection codes are retained. No automatic persistence or env enablement.
    """

    def __init__(self, identity: str) -> None:
        super().__init__()
        self.identity_sha256 = hashlib.sha256(identity.encode()).hexdigest()
        self._started = time.perf_counter()

    def capture(self, stage: str, value: Any, *, generation: int = 0) -> None:
        if generation not in (0, 1) or len(self.stages) >= 16:
            return
        event = {"generation": generation}
        if stage == "generation_started":
            event.update(stage="generation", status="started")
        elif stage == "policy_violations":
            codes = (
                [violation_code(v) for v in value[:40]]
                if isinstance(value, list)
                else [violation_code(None)]
            )
            names = {v["code"] for v in codes}
            event.update(
                stage="validation",
                violations=codes,
                schema="failed"
                if "SCHEMA" in names
                else "passed"
                if "SOURCE_PROCESSING" not in names
                else "not_checked",
                sources="failed" if "SOURCE_PROCESSING" in names else "processed",
                observables="failed"
                if names
                & {
                    "IP_SHAPE",
                    "SHA_SHAPE",
                    "IP_MEMBERSHIP",
                    "SHA_MEMBERSHIP",
                    "CVE_MEMBERSHIP",
                }
                else "passed"
                if "SOURCE_PROCESSING" not in names
                else "not_checked",
                endpoints="failed"
                if names & {"ENDPOINT_PAIR", "ENDPOINT_ROLE", "ENDPOINT_PORT"}
                else "passed"
                if "SOURCE_PROCESSING" not in names
                else "not_checked",
                observations="failed"
                if names & {"OBSERVATIONS_REQUIRED", "OBSERVATIONS_BLANK"}
                else "passed"
                if "SOURCE_PROCESSING" not in names
                else "not_checked",
            )
        elif stage == "contract_accepted":
            event.update(stage="outcome", status="accepted")
        elif stage == "final_failure":
            event.update(stage="outcome", status="withheld")
        else:
            return  # raw_model, final_response, unknown stages: never retained.
        event["elapsed_ms"] = round((time.perf_counter() - self._started) * 1000, 3)
        self.stages.append(event)

    def report(self) -> dict:
        return {
            "format": "local-machine-diagnostics-v1",
            "identity_sha256": self.identity_sha256,
            "events": self.stages,
            "repair_attempted": self.repair_attempted,
            "repair_failed": self.repair_failed,
        }
