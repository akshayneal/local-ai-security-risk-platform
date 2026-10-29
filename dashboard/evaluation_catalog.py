"""Read-only projections of tracked frozen evidence; no evaluator/model imports."""

import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

ROOT = Path(__file__).resolve().parents[1] / "Documentation"
CROSS_VERSION_CAVEAT = (
    "Results from different evaluation versions measure different properties "
    "and are not directly comparable."
)
CATALOG = (
    (
        "V1 adversarial evaluation",
        "evaluation_results/baseline.json",
        "Initial adversarial measurement",
        "Prompt controls alone left substantial failures.",
    ),
    (
        "V1 adversarial treatment",
        "evaluation_results/hardened.json",
        "Same-suite prompt/source treatment",
        "7/12 remained 7/12: one gain and one regression.",
    ),
    (
        "V2 repeated reliability baseline",
        "evaluation_v2/current_state_3trial.json",
        "Repeated trials and exact evidence fidelity",
        "Empty observed evidence caused fidelity failures.",
    ),
    (
        "V2 deterministic I/O treatment",
        "evaluation_v2/post_hardening_3trial.json",
        "Same-suite deterministic boundary treatment",
        "Better bounded contracts; poisoned claims and unscored mutations remained.",
    ),
    (
        "V3 semantic grounding baseline",
        "evaluation_v3/semantic_baseline_3trial.json",
        "Measure authority, events and consistency",
        "Manual review found scorer false positives and missed defects.",
    ),
    (
        "V3.1 calibrated semantic evaluation",
        "evaluation_v3_1/semantic_baseline_3trial.json",
        "Calibrate semantic measurement",
        "High official scores still missed scope/consistency defects.",
    ),
    (
        "V3.2 final semantic baseline",
        "evaluation_v3_2/semantic_baseline_3trial.json",
        "Final calibrated semantic ruler",
        "Actor/mandate omissions motivated a scoped treatment.",
    ),
    (
        "V3.2 production treatment",
        "evaluation_v3_2/semantic_treatment_3trial.json",
        "Exact-suite production comparison",
        "Improved support retention with a real availability and latency cost.",
    ),
)
COMPARISON_PATH = "evaluation_v3_2/treatment_comparison.json"


class ArtifactUnavailable(ValueError):
    pass


class Totals(BaseModel):
    trials_attempted: int = Field(ge=0, strict=True)
    trials_completed: int = Field(ge=0, strict=True)
    trials_passed: int = Field(ge=0, strict=True)
    application_error_count: int = Field(ge=0, strict=True)


class RepeatedReport(BaseModel):
    total_cases: int = Field(ge=1, strict=True)
    totals: Totals
    stability_counts: dict[str, int]


def _read(root: Path, path: str) -> dict:
    try:
        value = json.loads((root / path).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise TypeError("expected object")
        return value
    except (OSError, ValueError, TypeError) as exc:
        raise ArtifactUnavailable(
            "Frozen evaluation evidence is unavailable or invalid."
        ) from exc


def catalog_rows(root: Path = ROOT) -> tuple[list[dict], list[str]]:
    rows, errors = [], []
    for label, path, purpose, lesson in CATALOG:
        try:
            report = _read(root, path)
            if path.startswith("evaluation_results/"):
                cases = report["total_cases"]
                passed = report["passed"]
                if (
                    type(cases) is not int
                    or type(passed) is not int
                    or not 0 <= passed <= cases
                    or cases < 1
                ):
                    raise ValueError("invalid counts")
                attempted = completed = cases
                results = report["results"]
                if not isinstance(results, list) or any(
                    not isinstance(r, dict) for r in results
                ):
                    raise ValueError("invalid results")
                error_count = sum(bool(r.get("error")) for r in results)
                stability = "Single trial per case"
            else:
                # Semantic reports encode case count through cases, V2 also has total_cases.
                parsed = RepeatedReport.model_validate(
                    {
                        **report,
                        "total_cases": report.get(
                            "total_cases", len(report.get("cases", []))
                        ),
                    }
                )
                cases = parsed.total_cases
                totals = parsed.totals
                passed, completed = totals.trials_passed, totals.trials_completed
                attempted, error_count = (
                    totals.trials_attempted,
                    totals.application_error_count,
                )
                if (
                    not 0 <= passed <= completed <= attempted
                    or completed + error_count != attempted
                ):
                    raise ValueError("inconsistent totals")
                counts = parsed.stability_counts
                stability = f"{counts['stable_pass']} stable-pass / {counts['stable_fail']} stable-fail / {counts['mixed']} mixed"
            rows.append(
                {
                    "Evaluation": label,
                    "Purpose": purpose,
                    "Cases": cases,
                    "Attempts": attempted,
                    "Official passes / valid": f"{passed}/{completed}",
                    "Passes / attempts": f"{passed}/{attempted}",
                    "Application errors": error_count,
                    "Stability": stability,
                    "Major lesson": lesson,
                }
            )
        except (ArtifactUnavailable, ValidationError, KeyError, TypeError, ValueError):
            errors.append(f"{label}: frozen summary unavailable.")
    return rows, errors


def same_suite_comparison(root: Path = ROOT) -> dict:
    """Return bounded aggregate/case outcomes only, never responses or traces."""
    try:
        comparison = _read(root, COMPARISON_PATH)
        baseline = _read(root, "evaluation_v3_2/semantic_baseline_3trial.json")
        treatment = _read(root, "evaluation_v3_2/semantic_treatment_3trial.json")
        for field in ("suite_byte_sha256", "suite_semantic_sha256", "scorer_version"):
            if (
                not comparison[field]
                or not comparison[field] == baseline[field] == treatment[field]
            ):
                raise ValueError("incompatible evidence")
        metrics = []
        for side, report in (("before", baseline), ("after", treatment)):
            section = comparison[side]
            totals = Totals.model_validate(section["totals"])
            if (
                section["totals"] != report["totals"]
                or section["stability"] != report["stability_counts"]
            ):
                raise ValueError("inconsistent evidence")
            positive = Totals.model_validate(section["positive_controls"])
            metrics.append(
                {
                    "Run": "Baseline" if side == "before" else "Treatment",
                    "Passes / valid": f"{totals.trials_passed}/{totals.trials_completed}",
                    "Passes / attempts": f"{totals.trials_passed}/{totals.trials_attempted}",
                    "Application errors": totals.application_error_count,
                    "Stable-fail cases": int(section["stability"]["stable_fail"]),
                    "Positive controls": f"{positive.trials_passed}/{positive.trials_attempted}",
                    "Repair generations": int(section["repair_generations"]),
                    "Mean attempt seconds": round(
                        float(section["mean_trial_seconds"]), 2
                    ),
                }
            )
        cases = []
        for row in comparison["case_transitions"]:
            before, after = row["before_outcomes"], row["after_outcomes"]
            if (
                not before
                or not after
                or any(v not in {"pass", "fail", "error"} for v in before + after)
            ):
                raise ValueError("invalid outcome")
            cases.append(
                {
                    "Case ID": str(row["case_id"]),
                    "Baseline outcomes": " / ".join(before),
                    "Treatment outcomes": " / ".join(after),
                    "Stability transition": f"{row['before']} → {row['after']}",
                }
            )
        if len(cases) != len(baseline["cases"]) or len(cases) != len(
            treatment["cases"]
        ):
            raise ValueError("missing case")
        return {"metrics": metrics, "cases": cases}
    except (
        ArtifactUnavailable,
        ValidationError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise ArtifactUnavailable(
            "Frozen same-suite comparison is unavailable or invalid."
        ) from exc
