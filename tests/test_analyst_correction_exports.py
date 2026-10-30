from copy import deepcopy

import pytest
from test_analyst_corrections import correction
from test_evidence_inspector import report_for

from app.evidence_inspector import AnalystEvidenceReview, inspector_export
from dashboard.exports import export_document, json_export, markdown_export


@pytest.mark.parametrize("soc", [True, False])
def test_optional_history_export_compatibility_privacy_and_markdown_escaping(soc):
    request, analysis, report = report_for(soc)
    document = export_document(
        request, analysis, generated_at="fixed", evidence_inspector=report
    )
    original = deepcopy(document)
    assert inspector_export(report) == inspector_export(report, corrections=())
    assert "correction_history" not in document["evidence_inspector"]
    text = "[click](javascript:alert(1))\r\n# forged\n<script>evil</script> &lt;b&gt; **verified**"
    revisions = correction(report, proposed_text=text, rationale=text)
    revisions = correction(report, revisions, proposed_text="Revised proposal.")
    review = AnalystEvidenceReview(
        inspector_id=report.inspector_id,
        claim_id=report.claims[0].claim_id,
        relationship="unassessed",
        note="Existing judgment remains compatible.",
    )
    document["evidence_inspector"] = inspector_export(
        report, [review], corrections=revisions
    )
    assert document["analysis"] == original["analysis"]
    history = document["evidence_inspector"]["correction_history"]
    assert (
        history["format"] == "analyst-corrections-v1" and len(history["revisions"]) == 2
    )
    assert history["revisions"][0]["proposed_text"] == text
    assert document["evidence_inspector"]["analyst_reviews"][0]["note"] == review.note
    assert "not redacted" in history["notice"] and "user-entered" in history["notice"]
    md = markdown_export(document)
    assert "[click](" not in md and "<script>" not in md and "\n# forged" not in md
    assert "&amp;lt;b&amp;gt;" in md and r"\*\*verified\*\*" in md
    assert "Supersedes revision" in md and r"not\_verified" in md
    assert revisions[0].revision_id in md
    for forbidden in (
        "PRIVATE-INPUT-VALUE",
        "raw_model",
        "user_prompt",
        "diagnostic_trace",
    ):
        assert forbidden not in json_export(document) and forbidden not in md
    assert "excerpt" not in document["evidence_inspector"]["sources"][0]
