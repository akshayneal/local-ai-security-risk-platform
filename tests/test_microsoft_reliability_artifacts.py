"""Offline replay and identity checks for the new experiment's official artifacts."""

import hashlib
import json
import subprocess

from evals.microsoft_reliability.cases import load_cases
from evals.microsoft_reliability.runner import (
    ROOT,
    aggregate,
    compare,
    digest,
    identity,
    request_for,
)

DIRECTORY = ROOT / "Documentation/microsoft_reliability"


def test_baseline_complete_exact_schedule_provenance_and_replay():
    report = json.loads((DIRECTORY / "baseline.json").read_bytes())
    manifest = json.loads((DIRECTORY / "baseline_provenance.json").read_bytes())
    assert (
        hashlib.sha256((DIRECTORY / "baseline.json").read_bytes()).hexdigest()
        == manifest["baseline_sha256"]
    )
    assert report["identity"] == identity() == manifest["suite_identity"]
    for name, expected_hash in report["identity"]["source_lf_sha256"].items():
        assert (
            hashlib.sha256(
                (ROOT / "evals/microsoft_reliability" / name).read_bytes()
            ).hexdigest()
            == expected_hash
        )
    expected = [
        (c["case_id"], trial, digest(request_for(c).model_dump(mode="json")))
        for c in load_cases()
        for trial in range(1, c["trials"] + 1)
    ]
    assert [
        (r["case_id"], r["trial"], r["request_sha256"]) for r in report["records"]
    ] == expected
    assert report["metrics"] == aggregate(report["records"])
    assert report["metrics"]["attempts"] == 32
    assert report["metrics"]["returned"] == 29
    assert report["runtime"]["git_commit"] == "3f33cca014ff7865981afcedacdc69107bb5f6d2"
    assert not report["runtime"]["git_dirty"]
    assert all(
        a["configured_num_ctx"] is None
        for r in report["records"]
        for a in r["model_attempts"]
    )
    snapshot = json.loads((DIRECTORY / "recovery_snapshot.json").read_bytes())
    for old, row in zip(
        snapshot["completed_schedule_prefix"], report["records"], strict=False
    ):
        assert old["record_sha256"] == digest(row)


def test_manual_review_complete_quotes_bound_and_prior_judgments_preserved():
    report = json.loads((DIRECTORY / "baseline.json").read_bytes())
    review = json.loads((DIRECTORY / "baseline_manual_review.json").read_bytes())
    assert len(review["reviews"]) == len(report["records"]) == 32
    for item, row in zip(review["reviews"], report["records"], strict=True):
        assert (item["case_id"], item["trial"]) == (row["case_id"], row["trial"])
        assert review["baseline_record_sha256"][
            f"{row['case_id']}/{row['trial']}"
        ] == digest(row)
        for quote in item["quotes"]:
            assert quote["text"] in str(row["result"][quote["field"]])
        if row["result"] is None:
            assert all(
                item[k] == "unassessable"
                for k in (
                    "material_omission",
                    "unsupported_factual_claim",
                    "unsupported_authority_claim",
                    "overclaiming",
                    "source_applicability",
                )
            )
    prior = json.loads(
        subprocess.check_output(
            [
                "git",
                "show",
                "58304d0:Documentation/microsoft_reliability/baseline_manual_review.json",
            ],
            cwd=ROOT,
        )
    )
    assert review["reviews"][: len(prior["reviews"])] == prior["reviews"]
    assert review["judgment_revisions"] == []


def test_context_and_native_contract_artifacts_are_exact_and_separate():
    manifest = json.loads((DIRECTORY / "context_provenance.json").read_bytes())
    for name, expected in manifest.items():
        assert hashlib.sha256((DIRECTORY / name).read_bytes()).hexdigest() == expected
    report = json.loads((DIRECTORY / "context.json").read_bytes())
    assert report["identity"] == identity()
    assert [(r["case_id"], r["trial"]) for r in report["records"]] == [
        (key, trial)
        for trial in (1, 2)
        for key in ("REL-SOC-006", "REL-SOC-013", "REL-SOC-014")
    ]
    assert [
        r["model_attempts"][0]["configured_num_ctx"] for r in report["records"]
    ] == [4096] * 3 + [8192] * 3
    assert not report["runtime"]["git_dirty"]
    contract = json.loads((DIRECTORY / "context_contract.json").read_bytes())
    assert [r["probe"] for r in contract["records"]] == contract["plan"]["probes"]
    assert [r["http_status"] for r in contract["records"]] == [200, 200, 400, 400, 200]
    assert [r["status"] for r in contract["records"]][2:4] == ["other_server_error"] * 2
    pressure = contract["records"][-1]
    assert pressure["done_reason"] == "length"
    assert (
        pressure["usage"]["prompt_eval_count"] + pressure["usage"]["eval_count"] == 4096
    )


def test_treatment_complete_unchanged_schedule_and_comparison_replay():
    baseline = json.loads((DIRECTORY / "baseline.json").read_bytes())
    report = json.loads((DIRECTORY / "treatment.json").read_bytes())
    provenance = json.loads((DIRECTORY / "treatment_provenance.json").read_bytes())
    for name, expected in provenance["official_artifact_sha256"].items():
        assert hashlib.sha256((DIRECTORY / name).read_bytes()).hexdigest() == expected
    assert report["identity"] == baseline["identity"] == identity()
    assert len(report["records"]) == 32
    assert report["metrics"] == aggregate(report["records"])
    assert json.loads((DIRECTORY / "comparison.json").read_bytes()) == compare(
        baseline, report
    )
    assert report["runtime"]["git_commit"] == "92e8ee3038715071389b8ff95c4b6f65f7ce7da8"
    assert not report["runtime"]["git_dirty"]
    snapshot = json.loads((DIRECTORY / "treatment_recovery_snapshot.json").read_bytes())
    for prior, row in zip(snapshot["completed_prefix"], report["records"], strict=False):
        assert prior["record_sha256"] == digest(row)
    assert provenance["journal_records_equal_final_report"] is True
    assert provenance["recovery_prefix_verified"] is True
    assert provenance["executing_source_changes_during_treatment"] == []
    for row in report["records"]:
        microsoft = row["case_id"].startswith("REL-SOC")
        for attempt in row["model_attempts"]:
            assert attempt["complete_context_required"] is microsoft
            assert attempt["configured_num_ctx"] == (8192 if microsoft else None)
    large = next(r for r in report["records"] if r["case_id"] == "REL-SOC-014")
    assert large["result"] is None
    assert large["error"] == "EvidenceBudgetError"
    assert not large["diagnostics"]["repair_attempted"]
    assert large["model_attempts"][0]["context_status"] == "request_rejected"


def test_treatment_manual_review_complete_and_paired_counts_replay():
    from collections import Counter

    baseline = json.loads((DIRECTORY / "baseline_manual_review.json").read_bytes())
    review = json.loads((DIRECTORY / "treatment_manual_review.json").read_bytes())
    report = json.loads((DIRECTORY / "treatment.json").read_bytes())
    summary = json.loads((DIRECTORY / "manual_comparison.json").read_bytes())
    dimensions = (
        "material_omission",
        "unsupported_factual_claim",
        "unsupported_authority_claim",
        "overclaiming",
        "source_applicability",
    )
    assert len(review["reviews"]) == len(report["records"]) == 32
    assert review["status"] == "complete; all 32 scheduled attempts reviewed"
    for item, row in zip(review["reviews"], report["records"], strict=True):
        assert (item["case_id"], item["trial"]) == (row["case_id"], row["trial"])
        assert item["record_sha256"] == digest(row)
        for quote in item["quotes"]:
            assert quote["text"] in str(row["result"][quote["field"]])
        for key in dimensions:
            assert item[key] in {"absent", "present", "ambiguous", "unassessable"}
            assert (item[key] == "unassessable") is (row["result"] is None)
    previous = json.loads(
        subprocess.check_output(
            [
                "git",
                "show",
                "6060d49:Documentation/microsoft_reliability/treatment_manual_review.json",
            ],
            cwd=ROOT,
        )
    )
    assert review["reviews"][: len(previous["reviews"])] == previous["reviews"]
    assert review["judgment_revisions"] == []
    for key in dimensions:
        assert summary["baseline_all_attempts"][key] == dict(
            Counter(item[key] for item in baseline["reviews"])
        )
        assert summary["treatment_all_attempts"][key] == dict(
            Counter(item[key] for item in review["reviews"])
        )
        paired = Counter(
            f"{before[key]} -> {after[key]}"
            for before, after in zip(baseline["reviews"], review["reviews"], strict=True)
            if before[key] != "unassessable" and after[key] != "unassessable"
        )
        assert summary["common_returned_transitions"][key] == dict(paired)
        assert sum(paired.values()) == summary["common_returned_attempts"]


def test_entity_identifier_observations_bound_to_original_outputs():
    supplement = json.loads((DIRECTORY / "entity_identifier_review.json").read_bytes())
    records = {
        phase: json.loads((DIRECTORY / f"{phase}.json").read_bytes())["records"]
        for phase in ("baseline", "treatment")
    }
    assert len(supplement["entries"]) == 4
    for entry in supplement["entries"]:
        for phase, phase_records in records.items():
            row = next(
                row
                for row in phase_records
                if (row["case_id"], row["trial"]) == (entry["case_id"], entry["trial"])
            )
            observation = entry[phase]
            assert observation["record_sha256"] == digest(row)
            if row["result"] is None:
                assert observation["status"] == "unassessable"
                assert observation["value"] is None
            else:
                assert observation["value"] == row["result"][observation["field"]]
