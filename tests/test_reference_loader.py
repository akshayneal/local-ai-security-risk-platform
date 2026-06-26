from app.reference_loader import (
    format_references_for_prompt,
    get_relevant_references,
    load_references,
)


def test_load_soc_references():
    references = load_references("soc_alert")

    assert references
    assert any(reference["source_id"] == "MITRE-TA0006" for reference in references)


def test_load_governance_references():
    references = load_references("governance")

    assert references
    assert any(reference["source_id"] == "AI-RMF-GOVERN" for reference in references)


def test_soc_brute_force_retrieval():
    references = get_relevant_references(
        mode="soc_alert",
        query="SSH brute force followed by successful login",
        limit=4,
    )

    source_ids = [reference["source_id"] for reference in references]

    assert "SOC-BRUTE-FORCE-SUCCESS" in source_ids
    assert "MITRE-TA0006" in source_ids


def test_governance_resume_screening_retrieval():
    references = get_relevant_references(
        mode="governance",
        query="AI resume screening assistant using candidate resumes for hiring decisions",
        limit=6,
    )

    source_ids = [reference["source_id"] for reference in references]

    assert "GRC-HIGH-IMPACT-USE" in source_ids
    assert "AI-RMF-MAP" in source_ids


def test_format_references_for_prompt():
    references = get_relevant_references(
        mode="soc_alert",
        query="Suspicious encoded PowerShell command",
        limit=2,
    )

    formatted = format_references_for_prompt(references)

    assert "Source ID:" in formatted
    assert "Framework:" in formatted
    assert "Content:" in formatted