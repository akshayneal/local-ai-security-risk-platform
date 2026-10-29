import json
from copy import deepcopy

import pytest

from evals.grounding_stabilization.comparison import compare_reports, compare_reviews
from evals.provenance import ROOT

FOLDER = ROOT / "Documentation/grounding_stabilization"


def reports():
    baseline = json.loads((FOLDER / "baseline.json").read_bytes())
    treatment = deepcopy(baseline)
    treatment["phase"] = "treatment"
    return baseline, treatment


def test_comparison_keeps_withholding_and_model_requests_separate():
    baseline, treatment = reports()
    treatment["records"][0].update(
        result=None, error="EvidenceBudgetError", checks=None
    )
    result = compare_reports(baseline, treatment)
    assert result["baseline"]["returned"] == 8
    assert result["treatment"]["returned"] == 7
    assert result["treatment"]["withheld"] == 1
    assert result["treatment"]["model_requests"] == result["baseline"]["model_requests"]
    assert result["baseline"]["machine_check_failures"] == {"case_identity_exact": 1}
    assert result["availability_transitions"] == {
        "returned -> returned": 7,
        "returned -> withheld": 1,
    }


@pytest.mark.parametrize(
    "mutation", ["suite", "order", "request", "model", "temperature", "phase"]
)
def test_comparison_rejects_incomparable_experiments(mutation):
    baseline, treatment = reports()
    if mutation == "suite":
        treatment["identity"]["semantic_case_sha256"] = "changed"
    elif mutation == "order":
        treatment["records"].reverse()
    elif mutation == "request":
        treatment["records"][0]["request_sha256"] = "changed"
    elif mutation in {"model", "temperature"}:
        treatment["runtime"][mutation] = "changed"
    else:
        treatment["phase"] = "baseline"
    with pytest.raises(ValueError):
        compare_reports(baseline, treatment)


def test_manual_ambiguity_and_unassessable_labels_are_not_passes():
    baseline = json.loads((FOLDER / "baseline_manual_review.json").read_bytes())
    treatment = deepcopy(baseline)
    treatment["reviews"][0]["unsupported_factual_claim"] = "unassessable"
    result = compare_reviews(baseline, treatment)
    assert result["baseline_labels"]["unsupported_factual_claim"]["ambiguous"] > 0
    assert result["treatment_labels"]["unsupported_factual_claim"]["unassessable"] == 1
    assert (
        sum(result["common_returned_transitions"]["unsupported_factual_claim"].values())
        == 7
    )
