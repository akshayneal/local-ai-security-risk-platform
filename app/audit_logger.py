import json
from datetime import datetime, timezone
from pathlib import Path

from app.ollama_client import OLLAMA_MODEL

LOG_PATH = Path("logs/audit_log.jsonl")


def write_audit_log(
    mode: str,
    input_summary: str,
    result_summary: str,
    success: bool,
    error: str | None = None,
) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "model": OLLAMA_MODEL,
        "input_summary": input_summary,
        "result_summary": result_summary,
        "success": success,
        "error": error,
    }

    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry) + "\n")


def read_audit_logs(limit: int = 50) -> list[dict]:
    if not LOG_PATH.exists():
        return []

    lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    logs = []

    for line in lines[-limit:]:
        try:
            logs.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return list(reversed(logs))