"""Frozen AI Security software evidence replay, never real model inference."""

import hashlib
import json

import pytest

from evals.ai_security_v1.runner import ROOT, SUITE, evaluate, verify_freeze


@pytest.fixture(scope="module")
def recorded_and_replay():
    recorded = json.loads(
        (ROOT / "Documentation/ai_security_v1/results.json").read_bytes()
    )
    return recorded, evaluate()


def test_new_freeze_and_predeclared_group_denominators():
    assert verify_freeze()["implementation_source_git_blobs"]
    cases = json.loads((SUITE / "cases.json").read_bytes())
    assert len(cases) == 24 and len({c["id"] for c in cases}) == 24
    for group in {c["group"] for c in cases}:
        assert sum(c["group"] == group for c in cases) == 6
    assert sum(c["expected"] == "input_rejected" for c in cases) == 3
    assert sum(c["expected"] == "output_rejected" for c in cases) == 4


def test_exact_api_replay_without_ollama(recorded_and_replay):
    recorded, replay = recorded_and_replay
    assert recorded["metrics"] == replay["metrics"]
    assert recorded["groups"] == replay["groups"]
    assert recorded["freeze"] == replay["freeze"]
    for first, again in zip(recorded["results"], replay["results"], strict=True):
        assert {k: v for k, v in first.items() if k != "elapsed_ms"} == {
            k: v for k, v in again.items() if k != "elapsed_ms"
        }


def test_software_properties_are_not_model_effectiveness_claims(recorded_and_replay):
    recorded, _ = recorded_and_replay
    assert recorded["passed"] == recorded["cases"] == 24
    assert recorded["metrics"]["semantic_accuracy"] == "NOT MEASURED"
    assert recorded["metrics"]["live_injection_resistance"] == "NOT MEASURED"
    assert recorded["metrics"]["real_model_attempts"] == 0
    assert recorded["metrics"]["unassessed_unverified_status"] == {
        "count": 17,
        "total": 17,
    }
    assert recorded["metrics"]["category_source_consistency"] == {
        "count": 9,
        "total": 9,
    }
    row = next(r for r in recorded["results"] if r["id"] == "BOUNDARY-5")
    assert (
        row["stub_calls"] == 0
        and row["response"]["analysis"]["coverage_status"] == "insufficient_information"
    )


def test_new_official_artifact_hashes_are_not_rewritten():
    manifest = json.loads(
        (ROOT / "Documentation/ai_security_v1/result_identity.json").read_bytes()
    )
    for name, expected in manifest["sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
