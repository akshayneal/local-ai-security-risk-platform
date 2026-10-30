"""Reproduce the recorded local experiment offline and verify its provenance."""

import hashlib
import json
import subprocess

import pytest

from app.retrieval.embeddings import CachedEmbeddingProvider
from app.retrieval.storage import canonical_value, fingerprint
from evals.retrieval.runner import FIXTURES, ROOT, load_suite, run_benchmark

ARTIFACTS = ROOT / "Documentation/retrieval_evaluation"


@pytest.fixture(scope="module")
def comparison():
    return json.loads((ARTIFACTS / "comparison.json").read_bytes())


def test_report_suite_hashes_and_denominators(comparison):
    records, cases = load_suite()
    assert comparison["corpus_records"] == len(records) == 74
    assert comparison["synthetic_records"] == 48
    assert comparison["chunk_records"] == 36
    assert comparison["case_count"] == len(cases) == 48
    assert comparison["corpus_sha256"] == fingerprint(records)
    assert comparison["cases_sha256"] == fingerprint(cases)
    for name, expected in comparison["fixture_bytes_sha256"].items():
        assert hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest() == expected
    checkpoint = json.loads((ARTIFACTS / "lexical_checkpoint.json").read_bytes())
    assert checkpoint["corpus_sha256"] == comparison["corpus_sha256"]
    assert checkpoint["cases_sha256"] == comparison["cases_sha256"]


def test_recorded_source_identity_at_experiment_commit(comparison):
    for name, expected in comparison["source_sha256"].items():
        source = subprocess.check_output(
            ["git", "show", f"{comparison['git_commit']}:{name}"], cwd=ROOT
        )
        assert hashlib.sha256(source.replace(b"\r\n", b"\n")).hexdigest() == expected, (
            name
        )


def test_full_dense_hybrid_replay_without_ollama(comparison):
    provider = CachedEmbeddingProvider(ARTIFACTS / "vectors.json")
    replay = canonical_value(
        run_benchmark(("legacy", "lexical", "dense", "hybrid"), provider)
    )
    for name, original in comparison["candidates"].items():
        for row, rerun in zip(
            original["results"], replay["candidates"][name]["results"], strict=True
        ):
            assert row["ranking"] == rerun["ranking"]
            assert row["metrics"] == rerun["metrics"]
            assert row["violations"] == rerun["violations"]
        assert not any(original["summary"]["violations"].values())
    assert provider.provenance()["digest"] == comparison["embedding_provider"]["digest"]


def test_release_implementation_and_frozen_evidence_preserved():
    protected = [
        "app",
        "dashboard",
        "reference_material",
        "evals/cases",
        "AGENTS.md",
        "README.md",
        "requirements.txt",
        "requirements-windows-py313.lock.txt",
        ".gitattributes",
    ]
    names = subprocess.check_output(
        [
            "git",
            "diff",
            "v2.3.0",
            "6be3887617dfac1b95c09d672f5fa5acaabb9e08",
            "--name-only",
            "--",
            *protected,
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    # Explicit expansion integration and machine-only diagnostic instrumentation.
    # Prior implementation identities stay checked at the foundation checkpoint.
    from historical_identity import expansion_blob

    integration = {
        "app/soc_analyzer.py",
        "app/governance_analyzer.py",
        "dashboard/workflows.py",
        "dashboard/sample_loader.py",
        "app/ollama_client.py",
        "app/output_policy.py",
        "app/prompts.py",
        "app/main.py",
        "dashboard/api_client.py",
        "app/ui_schemas.py",
        "dashboard/exports.py",
    }
    additions = {
        "app/soc_inputs.py",
        "dashboard/microsoft_input.py",
        "app/local_diagnostics.py",
        "app/model_metrics.py",
        "app/microsoft_evidence.py",
        "app/inference_context.py",
        "app/soc_query.py",
        "app/reference_authority.py",
        "app/support_contracts.py",
        "app/support_assessor.py",
        "app/evidence_inspector.py",
        "dashboard/evidence_inspector.py",
    }
    assert all(
        name.startswith("app/retrieval/") or name in integration | additions
        for name in names
    ), names
    for name in integration:
        assert (
            expansion_blob(name)
            == subprocess.check_output(
                ["git", "rev-parse", f"v2.3.0:{name}"], cwd=ROOT, text=True
            ).strip()
        )
    # Frozen output-evaluation directories and standalone scorers/runners are
    # still checked against the actual released tree, not relaxed manifests.
    names = subprocess.check_output(
        [
            "git",
            "diff",
            "v2.3.0",
            "--name-only",
            "--",
            "Documentation/evaluation*",
            ":(glob)evals/*.py",
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    assert names == []


def test_new_attributes_preserve_fixture_bytes_without_root_changes():
    names = [
        str((FIXTURES / name).relative_to(ROOT))
        for name in ("corpus.json", "cases.json")
    ]
    attributes = subprocess.check_output(
        ["git", "check-attr", "eol", "--", *names], cwd=ROOT, text=True
    ).splitlines()
    assert all(line.endswith(": eol: lf") for line in attributes)
