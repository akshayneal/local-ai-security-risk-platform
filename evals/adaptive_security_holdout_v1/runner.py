"""One offline diagnostic for a committed deterministic candidate, never tuning.

Inputs/key are deliberately outside the development package. This command is
invoked only after development selection; it has no model client or provider API.
"""

import hashlib
import json
import os
import subprocess
import time
from collections import Counter
from pathlib import Path

from app.adaptive_reports import build_report, export_json, export_markdown
from app.adaptive_semantics import ReviewedContext
from evals.adaptive_security_reasoning_v1.preservation import verify_raw, verify_scope

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DOCS = ROOT / "Documentation/adaptive_security_reasoning_v1"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def verify():
    freeze_path = HERE / "freeze.json"
    first = git(
        "log", "--diff-filter=A", "--format=%H", "--", str(freeze_path)
    ).splitlines()
    if not first or freeze_path.read_bytes() != subprocess.check_output(
        ["git", "show", first[-1] + ":evals/adaptive_security_holdout_v1/freeze.json"],
        cwd=ROOT,
    ):
        raise ValueError("Diagnostic freeze changed or was never committed")
    freeze = json.loads(freeze_path.read_bytes())
    for path, expected in freeze["sha256"].items():
        if digest((ROOT / path).read_bytes()) != expected:
            raise ValueError("Frozen diagnostic literal changed: " + path)
        if (
            digest(subprocess.check_output(["git", "show", "HEAD:" + path], cwd=ROOT))
            != expected
        ):
            raise ValueError("Commit frozen diagnostic literals: " + path)
    selection_path = DOCS / "selection.json"
    selected = json.loads(selection_path.read_bytes())
    if selection_path.read_bytes() != subprocess.check_output(
        [
            "git",
            "show",
            "HEAD:Documentation/adaptive_security_reasoning_v1/selection.json",
        ],
        cwd=ROOT,
    ):
        raise ValueError("Commit candidate selection before opening diagnostic inputs")
    if selected["arm"] != "D" or selected["diagnostic_model_sends"] != 0:
        raise ValueError(
            "This offline runner supports only a deterministic selected candidate"
        )
    for path, blob in selected["source_git_blobs"].items():
        if (
            git("rev-parse", "HEAD:" + path) != blob
            or git("hash-object", "--path=" + path, path) != blob
        ):
            raise ValueError("Selected candidate source changed: " + path)
    required = {
        "app/adaptive_semantics.py",
        "app/adaptive_reports.py",
        "evals/adaptive_security_holdout_v1/runner.py",
    }
    if set(selected["source_git_blobs"]) != required:
        raise ValueError("Incomplete candidate source identity")
    return first[-1], selected


def execute_case(case):
    started = time.perf_counter()
    context = ReviewedContext.model_validate(case["context"])
    report = build_report(case["raw"], context)
    exported = json.loads(export_json(case["raw"], context, report))
    markdown = export_markdown(case["raw"], context, report)
    assessment = report.assessment
    original = json.loads(case["raw"])
    exact = (
        assessment.raw == case["raw"] and assessment.raw_sha256 == context.raw_sha256
    )
    pointers = {p.pointer: p for p in assessment.premises}
    bindings = []
    for pointer, premise in pointers.items():
        value = original
        for token in pointer.strip("/").split("/"):
            key = token.replace("~1", "/").replace("~0", "~")
            value = value[int(key)] if isinstance(value, list) else value[key]
        bindings.append(
            json.dumps(premise.value, ensure_ascii=True)
            == json.dumps(value, ensure_ascii=True)
            and premise.input_path == context.input_path
        )
    integrity = (
        exact
        and all(bindings)
        and exported["assessment"] == assessment.model_dump(mode="json")
        and assessment.approval_granted is False
        and assessment.action_status == "no_actions_executed"
    )
    return {
        "case_id": case["id"],
        "pillar": case["pillar"],
        "outcome": assessment.outcome,
        "report": exported,
        "markdown": markdown,
        "integrity": integrity,
        "premise_bindings": len(bindings),
        "model_sends": 0,
        "wall_seconds": time.perf_counter() - started,
        "semantic_review": "implementation-authored only; independent review PENDING",
    }


def run():
    preregistration, selected = verify()
    verify_scope()
    verify_raw()
    outputs_path = DOCS / "diagnostic_outputs.json"
    reservation_path = DOCS / "diagnostic_run.json"
    if outputs_path.exists() or reservation_path.exists():
        raise ValueError(
            "Diagnostic already attempted; preserve existing outputs and refuse rerun"
        )
    write_new(
        reservation_path,
        {
            "source_commit": git("rev-parse", "HEAD"),
            "status": "reserved_not_completion",
            "model_sends": 0,
            "selection": selected,
        },
    )
    # No authored key is read until EVERY output is durably saved.
    cases = json.loads((HERE / "cases.json").read_bytes())
    if (
        Counter(c["pillar"] for c in cases)
        != {"soc": 8, "governance": 8, "ai_security": 8}
        or len({c["id"] for c in cases}) != 24
    ):
        raise ValueError("Wrong diagnostic inventory")
    outputs = {
        "source_commit": git("rev-parse", "HEAD"),
        "preregistration_commit": preregistration,
        "selection": selected,
        "model_sends": 0,
        "outputs": [execute_case(case) for case in cases],
        "independent_review": "PENDING",
    }
    write_new(outputs_path, outputs)
    key = {k["id"]: k for k in json.loads((HERE / "author_key.json").read_bytes())}
    scored = [
        {
            "case_id": r["case_id"],
            "pillar": r["pillar"],
            "expected": key[r["case_id"]]["outcome"],
            "actual": r["outcome"],
            "typed_match": r["outcome"] == key[r["case_id"]]["outcome"],
            "integrity": r["integrity"],
            "authored_mechanism": key[r["case_id"]]["mechanism"],
        }
        for r in outputs["outputs"]
    ]
    scores = {
        "source_commit": outputs["source_commit"],
        "outcomes_sha256": digest(outputs_path.read_bytes()),
        "typed_matches": sum(r["typed_match"] for r in scored),
        "denominator": 24,
        "integrity_matches": sum(r["integrity"] for r in scored),
        "per_pillar": {
            pillar: {
                "typed_matches": sum(
                    r["typed_match"] for r in scored if r["pillar"] == pillar
                ),
                "denominator": 8,
            }
            for pillar in ("soc", "governance", "ai_security")
        },
        "model_sends": 0,
        "records": scored,
        "independent_review": "PENDING",
        "release": "NO-GO",
    }
    write_new(DOCS / "diagnostic_scores.json", scores)
    return scores


if __name__ == "__main__":
    result = run()
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "typed_matches",
                    "denominator",
                    "integrity_matches",
                    "per_pillar",
                    "model_sends",
                )
            },
            indent=2,
        )
    )
