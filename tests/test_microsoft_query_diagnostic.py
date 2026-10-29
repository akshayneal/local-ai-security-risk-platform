import json

from evals.microsoft_diagnostics.query_terms import collect
from evals.provenance import ROOT


def test_query_diagnostic_replays_without_inference_or_default_changes():
    expected = json.loads(
        (
            ROOT / "Documentation/microsoft_reliability/query_diagnostic.json"
        ).read_bytes()
    )
    assert collect() == expected
    for record in expected["records"][:3]:
        full, without = (
            record["query_variants"]["full_request"],
            record["query_variants"]["without_adapter_behavior"],
        )
        assert (
            full["authentication_card_score"] == 6
            and without["authentication_card_score"] == 1
        )
        assert "SOC-BRUTE-FORCE-SUCCESS" in full["top5_ids"]
        assert "SOC-BRUTE-FORCE-SUCCESS" not in without["top5_ids"]
    assert (
        "SOC-BRUTE-FORCE-SUCCESS"
        in expected["records"][-1]["query_variants"]["raw_evidence_only"]["top5_ids"]
    )
