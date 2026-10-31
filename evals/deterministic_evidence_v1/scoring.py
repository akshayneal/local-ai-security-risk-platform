"""Frozen objective label comparison only; prose still needs authored review."""

def decision_check(expected, proposal):
    return {"expected": expected, "actual": proposal.get("decision"), "matches": proposal.get("decision") == expected, "semantic_review": "REQUIRED; label match is not entailment"}
