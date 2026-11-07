"""Offline study accounting and freeze checks; never run the real diagnostic."""

import hashlib
import json

import pytest

from app.evidence_qualification import QualificationScope, SourceReview
from app.qualified_soc import build_qualified_report
from evals.evidence_qualification_v1 import runner


def test_prospective_literal_hashes_and_development_separation():
    freeze = runner.read(runner.SUITE / "input_freeze.json")
    runner.verify_hashes(freeze)
    assert freeze["model_sends"] == freeze["diagnostic_run_count"] == 0
    development = runner.read(runner.SUITE / "development_cases.json")["cases"]
    # Only identities are inspected here; no diagnostic execution or key judgment.
    diagnostic_ids = {
        row["id"] for row in runner.read(runner.SUITE / "diagnostic_cases.json")["cases"]
    }
    assert len(development) == 15 and len(diagnostic_ids) == 12
    assert not diagnostic_ids & {row["id"] for row in development}
    assert all(not {"expected", "class", "rubric"} & set(row) for row in development)


def test_development_only_all_applicable_integrity_checks():
    result = runner.development()
    assert result["model_sends"] == 0
    assert len(result["cases"]) == 15
    assert all(row["boundary_integrity"] for row in result["cases"])
    assert all(row["extraction_integrity"] is not False for row in result["cases"])
    assert all(row["export_integrity"] is not False for row in result["cases"])


def test_reservation_is_durable_and_never_overwritten(tmp_path):
    path = tmp_path / "reservation.json"
    runner.write_exclusive(path, {"state": "RESERVED"})
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        runner.write_exclusive(path, {"state": "COMPLETED"})
    assert path.read_bytes() == original


def test_diagnostic_duplicate_stops_before_case_or_key_read(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "ARTIFACTS", tmp_path)
    runner.write_exclusive(tmp_path / "diagnostic_reservation.json", {"state": "RESERVED"})
    (tmp_path / "candidate_freeze.json").write_text("{}", encoding="utf8")
    monkeypatch.setattr(runner, "SUITE", tmp_path)
    monkeypatch.setattr(runner, "git", lambda *args: "candidate" if args == ("rev-parse", "HEAD") else "")

    def metadata_only(path):
        assert path.name not in {"diagnostic_cases.json", "diagnostic_key.json"}
        return {"source_commit": "candidate", "sha256": {}}

    monkeypatch.setattr(runner, "read", metadata_only)
    with pytest.raises(FileExistsError):
        runner.diagnostic()


def test_changed_candidate_stops_before_reserving(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "ARTIFACTS", tmp_path)
    monkeypatch.setattr(runner, "read", lambda path: {"source_commit": "original", "sha256": {}})
    monkeypatch.setattr(runner, "git", lambda *args: "changed")
    with pytest.raises(ValueError, match="frozen candidate"):
        runner.diagnostic()
    assert not (tmp_path / "diagnostic_reservation.json").exists()


def test_changed_frozen_file_is_rejected(tmp_path, monkeypatch):
    path = tmp_path / "source.py"
    path.write_bytes(b"original")
    frozen = {"sha256": {"source.py": hashlib.sha256(path.read_bytes()).hexdigest()}}
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    runner.verify_hashes(frozen)
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="Frozen source/input bytes changed"):
        runner.verify_hashes(frozen)


def test_type_sensitive_extraction_comparison():
    assert runner.same_value({"port": 443}, {"port": 443})
    assert not runner.same_value({"port": True}, {"port": 1})
    assert not runner.same_value({"port": "443"}, {"port": 443})


def test_omitted_observation_or_changed_revision_fails_inventory():
    case = runner.read(runner.SUITE / "development_cases.json")["cases"][0]
    raw = case["source"]["raw"].encode()
    review = SourceReview.model_validate(case["source"]["review"])
    scope = QualificationScope.model_validate(case["scope"])
    report = build_qualified_report(raw, review, scope)
    args = ({review.source_id: raw}, {review.source_id: review}, scope, {})
    assert runner.observation_integrity(report, *args)
    assert not runner.observation_integrity(report.model_copy(update={"observations": ()}), *args)
    observation = report.observations[0].model_copy(update={"source_revision": "forged"})
    altered = report.model_copy(update={"observations": (observation, *report.observations[1:])})
    assert not runner.observation_integrity(altered, *args)


def test_input_load_failure_retains_reservation_and_failure_journal(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "ARTIFACTS", tmp_path)
    monkeypatch.setattr(runner, "SUITE", tmp_path)
    (tmp_path / "candidate_freeze.json").write_text("{}", encoding="utf8")
    monkeypatch.setattr(runner, "git", lambda *args: "candidate" if args == ("rev-parse", "HEAD") else "")

    def empty_cases(path):
        if path.name == "diagnostic_cases.json":
            return {"cases": []}
        if path.name == "diagnostic_key.json":
            return {"authored_expectations": {}}
        return {"source_commit": "candidate", "sha256": {}}

    monkeypatch.setattr(runner, "read", empty_cases)
    with pytest.raises(ValueError, match="identity inventory"):
        runner.diagnostic()
    assert (tmp_path / "diagnostic_reservation.json").exists()
    journal = (tmp_path / "diagnostic_journal.jsonl").read_text(encoding="utf8")
    assert "input_load_failed" in journal and "ValueError" in journal
    assert not (tmp_path / "diagnostic_results.json").exists()


def test_invalid_review_is_unavailable_with_unassessed_layers():
    case = runner.read(runner.SUITE / "development_cases.json")["cases"][0]
    case = json.loads(json.dumps(case))
    case["source"]["review"]["approved"] = "true"
    result = runner.execute_case(case)
    assert result["status"] == "unavailable"
    assert result["unavailability_stage"] == "review_contract_validation"
    assert result["export_integrity"] is result["extraction_integrity"] is None
    assert result["report"] is None


def test_malformed_scorer_entry_is_refused_before_dispatch():
    cases = [{"id": f"OPAQUE_{index}"} for index in range(12)]
    key = {row["id"]: {} for row in cases}
    with pytest.raises(ValueError, match="Malformed diagnostic scorer contract"):
        runner.validate_inventory(cases, key)
