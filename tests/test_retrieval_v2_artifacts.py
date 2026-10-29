import json
from pathlib import Path

from app.retrieval.embeddings import CachedEmbeddingProvider
from app.retrieval.storage import canonical_value
from evals.retrieval_v2.runner import load_suite, run, suite_identity

DIRECTORY = (
    Path(__file__).resolve().parents[1] / "Documentation/retrieval_evaluation_v2"
)


def test_v2_exact_offline_replay_and_zero_declared_violations():
    original = json.loads((DIRECTORY / "comparison.json").read_bytes())
    assert not original["git_dirty"]
    assert {k: original[k] for k in suite_identity(*load_suite())} == suite_identity(
        *load_suite()
    )
    replay = canonical_value(
        run(
            tuple(original["candidates"]),
            lambda name: CachedEmbeddingProvider(
                DIRECTORY / "vectors" / f"{name}.json"
            ),
        )
    )
    for name, candidate in original["candidates"].items():
        for old, new in zip(
            candidate["results"], replay["candidates"][name]["results"], strict=True
        ):
            for key in ("ranking", "metrics", "violations"):
                assert old[key] == new[key]
        assert not any(candidate["summary"]["violations"].values())
        assert candidate["summary"]["no_answer_cases"] == 10
        assert candidate["summary"]["correct_abstention_count"] == 0


def test_v2_recorded_code_identity_at_experiment_commit():
    import hashlib
    import subprocess

    report = json.loads((DIRECTORY / "comparison.json").read_bytes())
    for path, expected in report["source_sha256"].items():
        value = subprocess.check_output(
            ["git", "show", f"{report['git_commit']}:{path}"]
        )
        assert hashlib.sha256(value.replace(b"\r\n", b"\n")).hexdigest() == expected
