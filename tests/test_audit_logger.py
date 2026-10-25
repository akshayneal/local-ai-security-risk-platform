import json

from app import audit_logger
from app.audit_logger import write_audit_log


def test_write_audit_log_accepts_source_ids(monkeypatch, tmp_path):
    log_file = tmp_path / "audit_log.jsonl"
    monkeypatch.setattr(audit_logger, "LOG_DIR", tmp_path)
    monkeypatch.setattr(audit_logger, "LOG_FILE", log_file)
    write_audit_log(
        mode="test",
        input_summary="test input",
        result_summary="test result",
        success=True,
        source_ids=["TEST-SOURCE-1", "TEST-SOURCE-2"],
    )

    entry = json.loads(log_file.read_text(encoding="utf-8"))
    assert entry["source_ids"] == ["TEST-SOURCE-1", "TEST-SOURCE-2"]
