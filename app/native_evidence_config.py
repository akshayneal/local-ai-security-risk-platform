"""Process-owned opt-in for the experimental no-model observation workflow."""

import os

ENABLE_FLAG = "ENABLE_NATIVE_EVIDENCE_WORKFLOW"
ENDPOINT = "/experimental/native-evidence"
MAX_WIRE_BYTES = 400_000
INVALID_INPUT = "Invalid or oversized native telemetry. Review the supported JSON/CSV input and selected row."
WITHHELD = "Native observations were withheld because the source-bound result could not be validated."


def native_evidence_enabled() -> bool:
    """Only explicit process configuration enables the route or navigation."""
    return os.getenv(ENABLE_FLAG, "") == "1"
