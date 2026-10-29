"""Pure formatting/filtering helpers with explicit trust boundaries."""

from app.ui_schemas import COMMON_CHECKS, SOC_CHECKS

TRUST_CAVEAT = (
    "These checks enforce specific application contracts. They do not independently "
    "verify every analytical conclusion."
)
SOURCE_CAVEAT = "Sources provide context; retrieval does not establish claim authority."


def integrity_rows(metadata: dict, *, soc: bool) -> list[dict[str, str]]:
    checks = metadata.get("checks", [])
    rows = []
    labels = {
        "schema validation": "Schema",
        "source-reference sanitization": "Source references",
        "critical identity integrity": "Critical identifiers",
        "endpoint integrity": "Endpoint relationships",
        "observed-evidence contract": "Nonempty observations",
    }
    if soc:
        rows.append(
            {
                "Check": "Final contract",
                "Status": "Passed"
                if metadata.get("integrity_status") == "passed"
                else "Unavailable",
            }
        )
    for check in SOC_CHECKS if soc else COMMON_CHECKS:
        rows.append(
            {
                "Check": labels[check],
                "Status": (
                    "Validated"
                    if check == "source-reference sanitization"
                    else "Passed"
                )
                if check in checks
                else "Unavailable",
            }
        )
    if soc:
        repair = "Unavailable"
        if metadata.get("repair_attempted") is False:
            repair = "Not required"
        elif (
            metadata.get("repair_attempted") is True
            and metadata.get("repair_succeeded") is True
        ):
            repair = "Successful repair"
        rows.append({"Check": "Repair", "Status": repair})
    rows.append({"Check": "Human review", "Status": "Required"})
    return rows


def audit_rows(
    logs: list[dict], workflow: str = "All", outcome: str = "All"
) -> list[dict]:
    """Project only normal analyst fields; stored errors never reach the UI."""
    rows = []
    for log in logs:
        if workflow != "All" and log.get("mode") != workflow:
            continue
        success = log.get("success") is True
        if outcome != "All" and success != (outcome == "Success"):
            continue
        rows.append(
            {
                "Timestamp": log.get("timestamp", ""),
                "Workflow": {
                    "soc_alert": "SOC Investigation",
                    "governance": "AI System Risk Review",
                }.get(log.get("mode", ""), log.get("mode", "")),
                "Model": log.get("model", ""),
                "Input": log.get("input_summary", ""),
                "Result": log.get("result_summary", "")
                if success
                else "Analysis failed; no result returned",
                "Outcome": "Success" if success else "Failure",
                "Source IDs": ", ".join(log.get("source_ids") or []),
            }
        )
    return rows
