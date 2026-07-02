from app.audit_logger import write_audit_log


def test_write_audit_log_accepts_source_ids():
    write_audit_log(
        mode="test",
        input_summary="test input",
        result_summary="test result",
        success=True,
        source_ids=["TEST-SOURCE-1", "TEST-SOURCE-2"],
    )