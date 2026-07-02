import json
from datetime import UTC, datetime
from pathlib import Path

from app.ollama_client import OLLAMA_MODEL


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "audit_log.jsonl"


def write_audit_log(
    mode: str,
    input_summary: str,
    result_summary: str,
    success: bool,
    error: str | None = None,
    source_ids: list[str] | None = None,
) -> None:
    """
    Writes one audit log entry as a JSON line.
    """
    LOG_DIR.mkdir(exist_ok=True)

    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "mode": mode,
        "model": OLLAMA_MODEL,
        "input_summary": input_summary,
        "result_summary": result_summary,
        "success": success,
        "error": error,
        "source_ids": source_ids or [],
    }

    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry) + "\n")


def read_audit_logs(limit: int = 50) -> list[dict]:
    """
    Reads recent audit log entries.
    """
    if not LOG_FILE.exists():
        return []

    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    recent_lines = lines[-limit:]

    logs = []

    for line in recent_lines:
        try:
            logs.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return list(reversed(logs))