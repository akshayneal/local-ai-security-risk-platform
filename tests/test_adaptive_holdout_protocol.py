"""Frozen identities/inventory only; never execute diagnostic semantic cases here."""

import ast
import json
from collections import Counter
from pathlib import Path

from evals.adaptive_security_holdout_v1 import runner

HERE = Path("evals/adaptive_security_holdout_v1")


def test_diagnostic_inventory_is_disjoint_balanced_and_neutrally_worded():
    cases = json.loads((HERE / "cases.json").read_bytes())
    development = json.loads(
        Path("evals/adaptive_security_reasoning_v1/dev_cases.json").read_bytes()
    )
    assert Counter(c["pillar"] for c in cases) == {
        "soc": 8,
        "governance": 8,
        "ai_security": 8,
    }
    assert len({c["id"] for c in cases}) == 24
    assert not {c["id"] for c in cases} & {c["id"] for c in development}
    assert len({c["question"] for c in cases}) == 1
    for case in cases:
        assert {"outcome", "mechanism", "forbidden_claims", "gold"}.isdisjoint(
            json.loads(case["raw"])
        )


def test_locked_key_has_positive_legitimate_unknown_and_conflict_controls():
    cases = json.loads((HERE / "cases.json").read_bytes())
    key = json.loads((HERE / "author_key.json").read_bytes())
    assert {k["id"] for k in key} == {c["id"] for c in cases}
    pillars = {c["id"]: c["pillar"] for c in cases}
    for pillar in ("soc", "governance", "ai_security"):
        outcomes = {k["outcome"] for k in key if pillars[k["id"]] == pillar}
        assert {
            "declared_mismatch",
            "underdetermined",
            "conflicting_claims",
        } <= outcomes
        assert outcomes & {"declared_alignment", "not_applicable"}
    assert all(
        k["review_status"] == "implementation_authored; independent review PENDING"
        for k in key
    )


def test_offline_runner_has_no_generation_dependency():
    tree = ast.parse(Path(runner.__file__).read_text(encoding="utf-8"))
    imports = [
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    ]
    assert not any(
        any(
            name in (module or "")
            for name in ("transport", "ollama_client", "requests")
        )
        for module in imports
    )
    calls = [node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)]
    assert "chat" not in calls


def test_locked_source_identities_match_preregistered_hashes():
    path = HERE / "freeze.json"
    assert path.exists(), "Prospective holdout freeze is required"
    freeze = json.loads(path.read_bytes())
    for relative, expected in freeze["sha256"].items():
        assert runner.digest(Path(relative).read_bytes()) == expected
