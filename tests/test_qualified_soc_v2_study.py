"""Study accounting properties with temporary mock runs; never dispatch holdout."""

import hashlib
import json

import pytest

from app import qualified_soc_v2 as v2
from evals.qualified_soc_contract_v2 import runner
from evals.qualified_soc_contract_v2.development import (
    development_cases,
    native_inputs,
    prepare,
)


def test_original_and_portable_frozen_input_hashes():
    runner.verify_inputs()
    original = runner.read(runner.SUITE / "input_freeze.json")
    assert original["cases"] == 10 and original["model_sends"] == 0


def test_new_development_matrix_has_exact_source_export_and_dispatch_evidence():
    output = runner.development()
    assert output["model_sends"] == 0
    for row in output["cases"]:
        observed = row["observed"]
        assert all(observed[name] == value for name, value in row["authored_expected"].items())
        assert observed["source_integrity"] is not False
        assert observed["lineage_integrity"] is not False
        assert observed["export_integrity"] and observed["no_grant"]
        assert observed["observed_comparator_calls"] == observed["comparator_invocations"]


def test_source_observation_omission_and_revision_mutation_are_detected():
    raw, review, scope, options = native_inputs()
    report = v2.build_qualified_report(raw, review, scope, **options)
    assert runner.source_integrity(report, raw, review, scope, options)
    assert not runner.source_integrity(report.model_copy(update={"observations": ()}), raw, review, scope, options)
    altered = report.observations[0].model_copy(update={"source_revision": "forged"})
    modified = report.model_copy(update={"observations": (altered, *report.observations[1:])})
    assert not runner.source_integrity(modified, raw, review, scope, options)


def test_changed_lineage_is_detected_against_original_bytes():
    raw, review, scope, options = prepare()
    report = v2.build_qualified_report(raw, review, scope, **options)
    assert runner.lineage_integrity(report, raw, review, options)
    bad = report.lineage[0].model_copy(update={"source_revision": "forged"})
    report = report.model_copy(update={"lineage": (bad, *report.lineage[1:])})
    assert not runner.lineage_integrity(report, raw, review, options)


def test_exclusive_artifact_write_never_overwrites(tmp_path):
    path = tmp_path / "reservation.json"
    runner.write_once(path, {"state": "RESERVED"})
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        runner.write_once(path, {"state": "COMPLETED"})
    assert path.read_bytes() == original


def test_duplicate_reservation_precedes_diagnostic_input_read(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "DOCS", tmp_path)
    runner.write_once(tmp_path / "diagnostic_reservation.json", {"state": "RESERVED"})
    monkeypatch.setattr(runner, "git", lambda *args: "candidate" if args == ("rev-parse", "HEAD") else "")
    monkeypatch.setattr(runner, "verify_inputs", lambda: None)

    def only_metadata(path):
        assert path.name not in {"cases.json", "key.json"}
        return {"source_commit": "candidate", "sha256": {}}

    monkeypatch.setattr(runner, "read", only_metadata)
    with pytest.raises(FileExistsError):
        runner.diagnostic()


def test_input_failure_preserves_barrier_and_journal(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "DOCS", tmp_path)
    monkeypatch.setattr(runner, "git", lambda *args: "candidate" if args == ("rev-parse", "HEAD") else "")
    monkeypatch.setattr(runner, "verify_inputs", lambda: None)

    def empty_input(path):
        return {"cases": []} if path.name == "cases.json" else {"authored_expectations": {}} if path.name == "key.json" else {"source_commit": "candidate", "sha256": {}}

    monkeypatch.setattr(runner, "read", empty_input)
    with pytest.raises(ValueError, match="inventory"):
        runner.diagnostic()
    assert (tmp_path / "diagnostic_reservation.json").exists()
    assert "input_load_failed" in (tmp_path / "diagnostic_journal.jsonl").read_text(encoding="utf8")


def test_hash_drift_and_external_paths_are_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    path = tmp_path / "module.py"
    path.write_bytes(b"original")
    frozen = {"sha256": {"module.py": hashlib.sha256(path.read_bytes()).hexdigest()}}
    runner.verify_hashes(frozen)
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="mismatch"):
        runner.verify_hashes(frozen)
    with pytest.raises(ValueError, match="repository relative"):
        runner.verify_hashes({"sha256": {"../outside": "0" * 64}})


def test_type_sensitive_canonical_values_and_disjoint_case_identities():
    assert runner.canonical(True) != runner.canonical(1)
    assert runner.canonical("1") != runner.canonical(1)
    # Identity-only overlap check, never a diagnostic execution or gold review.
    diagnostic = json.loads((runner.SUITE / "cases.json").read_bytes())
    assert not {case["id"] for case in diagnostic["cases"]} & {case["id"] for case in development_cases()}
