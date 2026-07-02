from app.reference_loader import (
    get_reference_ids,
    get_reference_lookup,
    sanitize_source_references,
    clean_inline_source_citations,
    remove_inline_source_citations
)


def test_get_reference_ids():
    references = [
        {
            "source_id": "SOC-BRUTE-FORCE-SUCCESS",
            "title": "SOC Checklist - Brute Force Followed by Successful Login",
        },
        {
            "source_id": "MITRE-TA0006",
            "title": "MITRE ATT&CK - Credential Access",
        },
    ]

    source_ids = get_reference_ids(references)

    assert source_ids == {"SOC-BRUTE-FORCE-SUCCESS", "MITRE-TA0006"}


def test_get_reference_lookup():
    references = [
        {
            "source_id": "GRC-HIGH-IMPACT-USE",
            "title": "AI Governance Checklist - High-Impact Use",
            "framework": "Local AI Governance Checklist",
        }
    ]

    lookup = get_reference_lookup(references)

    assert "GRC-HIGH-IMPACT-USE" in lookup
    assert lookup["GRC-HIGH-IMPACT-USE"]["framework"] == "Local AI Governance Checklist"


def test_sanitize_source_references_removes_fake_sources():
    retrieved_references = [
        {
            "source_id": "SOC-BRUTE-FORCE-SUCCESS",
            "title": "SOC Checklist - Brute Force Followed by Successful Login",
            "framework": "Local SOC Checklist",
        },
        {
            "source_id": "MITRE-TA0006",
            "title": "MITRE ATT&CK - Credential Access",
            "framework": "MITRE ATT&CK",
        },
    ]

    returned_sources = [
        {
            "source_id": "SOC-BRUTE-FORCE-SUCCESS",
            "title": "Wrong model-generated title",
            "framework": "Wrong framework",
            "relevance": "Matched the pattern of failed logins followed by success.",
        },
        {
            "source_id": "FAKE-SOURCE",
            "title": "Fake Source",
            "framework": "Fake Framework",
            "relevance": "This should be removed.",
        },
    ]

    sanitized = sanitize_source_references(
        returned_sources=returned_sources,
        retrieved_references=retrieved_references,
    )

    assert len(sanitized) == 1
    assert sanitized[0]["source_id"] == "SOC-BRUTE-FORCE-SUCCESS"
    assert sanitized[0]["title"] == "SOC Checklist - Brute Force Followed by Successful Login"
    assert sanitized[0]["framework"] == "Local SOC Checklist"
    assert sanitized[0]["relevance"] == "Matched the pattern of failed logins followed by success."


def test_sanitize_source_references_handles_empty_sources():
    sanitized = sanitize_source_references(
        returned_sources=[],
        retrieved_references=[
            {
                "source_id": "AI-RMF-GOVERN",
                "title": "NIST AI RMF - Govern Function",
                "framework": "NIST AI RMF",
            }
        ],
    )

    assert sanitized == []


def test_sanitize_source_references_handles_missing_relevance():
    retrieved_references = [
        {
            "source_id": "AI-RMF-GOVERN",
            "title": "NIST AI RMF - Govern Function",
            "framework": "NIST AI RMF",
        }
    ]

    returned_sources = [
        {
            "source_id": "AI-RMF-GOVERN",
            "title": "Model title",
            "framework": "Model framework",
        }
    ]

    sanitized = sanitize_source_references(
        returned_sources=returned_sources,
        retrieved_references=retrieved_references,
    )

    assert len(sanitized) == 1
    assert sanitized[0]["source_id"] == "AI-RMF-GOVERN"
    assert sanitized[0]["title"] == "NIST AI RMF - Govern Function"
    assert sanitized[0]["framework"] == "NIST AI RMF"
    assert sanitized[0]["relevance"] == (
        "The model identified this retrieved local reference as relevant."
    )

def test_remove_inline_source_citations_removes_per_source_id():
    cleaned = remove_inline_source_citations(
        text="Implement data minimization (per GRC-DATA-MINIMIZATION).",
        source_ids={"GRC-DATA-MINIMIZATION"},
    )

    assert cleaned == "Implement data minimization."


def test_remove_inline_source_citations_removes_parenthetical_source_id():
    cleaned = remove_inline_source_citations(
        text="Document governance policies (AI-RMF-GOVERN).",
        source_ids={"AI-RMF-GOVERN"},
    )

    assert cleaned == "Document governance policies."


def test_clean_inline_source_citations_cleans_list_fields():
    raw_result = {
        "required_controls": [
            "Implement data minimization (per GRC-DATA-MINIMIZATION).",
            "Document governance roles (AI-RMF-GOVERN).",
        ],
        "source_references": [
            {
                "source_id": "GRC-DATA-MINIMIZATION",
                "title": "AI Governance Checklist - Data Minimization",
                "framework": "Local AI Governance Checklist",
                "relevance": "Relevant to personal data handling.",
            }
        ],
    }

    cleaned = clean_inline_source_citations(
        raw_result=raw_result,
        source_ids={"GRC-DATA-MINIMIZATION", "AI-RMF-GOVERN"},
        fields_to_clean=["required_controls"],
    )

    assert cleaned["required_controls"] == [
        "Implement data minimization.",
        "Document governance roles.",
    ]

    assert cleaned["source_references"][0]["source_id"] == "GRC-DATA-MINIMIZATION"