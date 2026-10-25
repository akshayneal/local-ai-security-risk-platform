import pytest

from evals.compare import compare_reports
from evals.runner import build_report, load_suite
from evals.schemas import EvaluationResult


def make_report(outcomes):
    cases = load_suite()[0].cases[: len(outcomes)]
    return build_report(
        [
            EvaluationResult(
                test_id=c.test_id,
                category=c.category,
                severity=c.severity,
                mode=c.mode,
                passed=passed,
                duration_seconds=0,
            )
            for c, passed in zip(cases, outcomes)
        ],
        "same-hash",
    )


def test_all_transitions_and_category_delta():
    result = compare_reports(
        make_report([False, False, True, True]), make_report([True, False, False, True])
    )
    assert result["newly_passing"] == ["SOC-DPI-001"]
    assert result["still_failing"] == ["GOV-DPI-001"]
    assert result["regressions"] == ["SOC-IPI-001"]
    assert result["unchanged_passing"] == ["GOV-IPI-001"]
    assert result["percentage_point_change"] == 0
    assert result["category_changes"]["direct_prompt_injection"] == {
        "baseline": 0,
        "hardened": 50,
    }


def test_hash_mismatch_refused():
    before = make_report([True])
    after = before.model_copy(update={"suite_hash": "different"})
    with pytest.raises(ValueError, match="hashes differ"):
        compare_reports(before, after)


def test_filtered_case_sets_cannot_be_compared():
    with pytest.raises(ValueError, match="case sets differ"):
        compare_reports(make_report([True]), make_report([True, True]))


def test_comparison_cli_writes_machine_readable_output(tmp_path):
    import json

    from evals.compare import main

    before, after = tmp_path / "before.json", tmp_path / "after.json"
    output = tmp_path / "comparison.json"
    before.write_text(make_report([False]).model_dump_json(), encoding="utf-8")
    after.write_text(make_report([True]).model_dump_json(), encoding="utf-8")
    assert main([str(before), str(after), "--output", str(output)]) == 0
    assert json.loads(output.read_text())["percentage_point_change"] == 100
