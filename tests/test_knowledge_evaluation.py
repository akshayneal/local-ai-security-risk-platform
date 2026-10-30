"""Frozen authored-case replay; original failed attempt and all limits stay visible."""

import hashlib
import json

import pytest

from evals.knowledge_bridge_v1.runner import ROOT, SUITE, evaluate, verify_freeze


@pytest.fixture(scope="module")
def recorded_and_replay():
    recorded = json.loads(
        (ROOT / "Documentation/knowledge_bridge_v1/results.json").read_bytes()
    )
    return recorded, evaluate()


def test_frozen_source_cases_rubric_and_implementation_identity():
    freeze = verify_freeze()
    assert len(json.loads((SUITE / "cases.json").read_bytes())) == 26
    assert freeze["implementation_source_git_blobs"]
    original = json.loads((SUITE / "implementation_freeze.json").read_bytes())
    assert (
        original["source_git_blobs"]["evals/knowledge_bridge_v1/runner.py"]
        == freeze["execution_fix"]["original_runner_git_blob"]
    )
    # The failed execution remains a failure, not a manufactured partial score.
    failure = json.loads(
        (
            ROOT / "Documentation/knowledge_bridge_v1/attempt_001_failure.json"
        ).read_bytes()
    )
    assert (
        failure["status"].startswith("incomplete")
        and failure["real_model_requests"] == 0
    )
    assert "unavailable" in failure["case_results"]


def test_exact_offline_replay_rankings_metrics_and_fixed_denominators(
    recorded_and_replay,
):
    recorded, replay = recorded_and_replay
    assert recorded["cases"] == replay["cases"] == 26
    assert recorded["metrics"] == replay["metrics"]
    assert recorded["freeze"] == replay["freeze"]
    for first, again in zip(recorded["results"], replay["results"], strict=True):
        assert {k: v for k, v in first.items() if k != "elapsed_ms"} == {
            k: v for k, v in again.items() if k != "elapsed_ms"
        }
    metrics = recorded["metrics"]
    assert metrics["relevant_recall_at_8"]["total"] == 13
    assert metrics["relevant_recall_at_8"]["positive_cases"] == 11
    assert metrics["required_group_coverage"]["total"] == 2
    assert metrics["no_answer_nonempty_retrieval"]["total"] == 2
    assert metrics["false_eligible_exposure"]["negative_cases"] == 10
    assert metrics["expected_safe_refusals"]["total"] == 3


def test_counterexample_and_unassessed_status_are_not_erased(recorded_and_replay):
    recorded, _ = recorded_and_replay
    rows = {r["id"]: r for r in recorded["results"]}
    assert rows["related-no-deadline"]["nonempty_retrieval"]
    assert rows["related-no-deadline"]["support_unassessed"]
    assert not rows["true-no-answer"]["nonempty_retrieval"]
    assert recorded["metrics"]["unsupported_generation_tendency"].startswith(
        "NOT MEASURED"
    )
    assert recorded["metrics"]["positive_generation_loss"].startswith("NOT MEASURED")
    assert (
        recorded["metrics"]["model_requests"]
        == recorded["metrics"]["network_requests"]
        == 0
    )
    for name in (
        "expired",
        "inactive",
        "wrong-workflow",
        "wrong-unit",
        "wrong-policy",
        "restricted",
        "poison-unapproved",
        "spoofed-id",
    ):
        assert rows[name]["passed"]


def test_official_new_report_identity():
    manifest = json.loads(
        (ROOT / "Documentation/knowledge_bridge_v1/result_identity.json").read_bytes()
    )
    for name, expected in manifest["sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
