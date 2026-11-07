"""New offline v2 study; no historical diagnostic replay or model transport."""

import argparse
import hashlib
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from html import escape
from pathlib import Path
from unittest.mock import patch

from app import qualified_soc as v1
from app import qualified_soc_v2 as v2
from app.evidence_qualification import QualificationScope, SourceReview
from app.soc_inputs import parse_csv_bundle

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "evals/qualified_soc_contract_v2"
DOCS = ROOT / "Documentation/qualified_soc_contract_v2"


def read(path):
    return json.loads(path.read_bytes())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def write_once(path, value):
    with path.open("x", encoding="utf8", newline="\n") as target:
        json.dump(value, target, ensure_ascii=True, indent=2)
        target.write("\n")
        target.flush()
        os.fsync(target.fileno())


def verify_hashes(value):
    for name, expected in value["sha256"].items():
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or ":" in name:
            raise ValueError("Frozen paths must be repository relative")
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError("Frozen source/input mismatch: " + name)


def verify_inputs():
    portable = read(SUITE / "input_freeze_portable.json")
    original = read(SUITE / "input_freeze.json")
    if portable["original_freeze_sha256"] != sha((SUITE / "input_freeze.json").read_bytes()):
        raise ValueError("Original prospective freeze changed")
    normalized = {}
    for name, expected in original["sha256"].items():
        suffix = "evals/qualified_soc_contract_v2/" + name.rsplit("/", 1)[-1]
        if not name.endswith("/" + suffix):
            raise ValueError("Unexpected original authoring path")
        normalized[suffix] = expected
    if normalized != portable["sha256"]:
        raise ValueError("Portable freeze must retain identical source/input hashes")
    verify_hashes(portable)


def source_integrity(report, raw, review, scope, options):
    supplied = [(raw, review), *options.get("authorization_sources", ())]
    snapshots = [(s.source_id, s.revision, s.raw_sha256, s.raw_text, s.review.model_dump(mode="json")) for s in report.sources]
    expected_sources = [(r.source_id, r.revision, sha(value), value.decode("utf8"), r.model_dump(mode="json")) for value, r in supplied]
    if Counter(map(canonical, snapshots)) != Counter(map(canonical, expected_sources)):
        return False
    expected_observations = []
    for value, metadata in supplied:
        if metadata.source_format == "microsoft_csv":
            body = parse_csv_bundle(value, options.get("csv_table", "DeviceNetworkEvents"), options.get("csv_case_id") or scope.case_id)
        else:
            body = json.loads(value.decode("utf-8-sig"))
        if metadata.source_format.startswith("microsoft_"):
            items = [(f"{table}[{index}].{field}", item) for table, rows in body["tables"].items() for index, row in enumerate(rows) for field, item in row.items()]
        else:
            items = []
            for field, item in body.items():
                if field == "event":
                    items.extend(("/event/" + key, child) for key, child in item.items())
                else:
                    items.append(("/" + field, item))
        expected_observations += [(metadata.source_id, metadata.revision, path, type(item).__name__, item) for path, item in items]
    actual = [(o.source_id, o.source_revision, o.original_path, o.original_type, o.value) for o in report.observations]
    return Counter(map(canonical, actual)) == Counter(map(canonical, expected_observations))


def lineage_integrity(report, raw, review, options):
    if report.comparison is None:
        return True
    original = {r.source_id: (r, json.loads(value.decode("utf-8-sig"))) for value, r in [(raw, review), *options.get("authorization_sources", ())]}
    derived = json.loads(report.comparison.assessment.raw)["data"]
    expected = {f"/data/{kind}/{name}": value for kind, fields in derived.items() for name, value in fields.items()}
    actual = {item.target_path: item for item in report.lineage}
    if len(actual) != len(report.lineage) or set(actual) != set(expected):
        return False
    for target, value in expected.items():
        item = actual[target]
        metadata, body = original[item.source_id]
        if item.source_revision != metadata.revision or not item.original_path:
            return False
        for token in item.original_path.lstrip("/").split("/"):
            body = body[token.replace("~1", "/").replace("~0", "~")]
        if canonical(body) != canonical(value):
            return False
    return True


def inspect_inputs(raw, review, scope, options):
    # A spy observes actual calls for this derivation only. Export recomputations
    # are separate derivations and never counted as model sends.
    with patch.object(v1, "_comparison", wraps=v1._comparison) as comparator:
        report = v2.build_qualified_report(raw, review, scope, **options)
        calls = comparator.call_count
    encoded = v2.export_json(raw, review, scope, report, **options)
    markdown = v2.export_markdown(raw, review, scope, report, **options)
    data = report.model_dump(mode="json")

    def safe(value):
        return re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", escape(str(value))).replace("\n", " ").replace("\r", " ").rstrip()

    return {
        "processing_state": report.processing_state, "execution_state": report.execution_state,
        "comparator_invocations": report.comparator_invocations, "observed_comparator_calls": calls,
        "relationship": report.relationship, "association_state": report.association_state,
        "reason_codes": list(report.reason_codes),
        "qualification": "refused" if report.processing_state == "source_refused" else "eligible",
        "source_integrity": None if report.processing_state == "source_refused" else source_integrity(report, raw, review, scope, options),
        "lineage_integrity": None if report.processing_state == "source_refused" else lineage_integrity(report, raw, review, options),
        "export_integrity": canonical(json.loads(encoded)) == canonical(data)
            and all(safe(s.raw_text) in markdown for s in report.sources)
            and not re.search(r"<(?:script|iframe|img)\b", markdown, re.IGNORECASE),
        "no_grant": type(report.approval_granted) is bool and report.approval_granted is False and report.action_status == "no_actions_executed",
        "report": data, "json_sha256": sha(encoded.encode()), "markdown_sha256": sha(markdown.encode()),
    }


def execute_case(case):
    raw = case["source"]["raw"].encode("utf8")
    review = SourceReview.model_validate(case["source"]["review"])
    scope = QualificationScope.model_validate(case["scope"])
    options = {**case["options"], "authorization_sources": tuple((s["raw"].encode("utf8"), SourceReview.model_validate(s["review"])) for s in case["authorizations"])}
    return inspect_inputs(raw, review, scope, options)


def development():
    from evals.qualified_soc_contract_v2.development import development_cases

    return {"kind": "new_development_only", "source_commit": git("rev-parse", "HEAD"), "model_sends": 0,
        "cases": [{"id": c["id"], "authored_expected": c["expected"], "observed": inspect_inputs(*c["inputs"][:3], c["inputs"][3])} for c in development_cases()]}


def diagnostic():
    freeze = read(SUITE / "candidate_freeze.json")
    verify_hashes(freeze)
    verify_inputs()
    head = git("rev-parse", "HEAD")
    if head != freeze["source_commit"]:
        git("merge-base", "--is-ancestor", freeze["source_commit"], head)
        if set(git("diff", freeze["source_commit"], head, "--name-only").splitlines()) != {"evals/qualified_soc_contract_v2/candidate_freeze.json"}:
            raise ValueError("Candidate changed beyond its freeze-only manifest")
    if git("diff", "--name-only") or git("diff", "--cached", "--name-only"):
        raise ValueError("Candidate must be committed before diagnostic")
    write_once(DOCS / "diagnostic_reservation.json", {"source_commit": head, "candidate_source_commit": freeze["source_commit"], "state": "RESERVED, not proof of completion", "model_sends": 0, "recovery": "Never rerun; inspect journal/results read-only"})
    journal = DOCS / "diagnostic_journal.jsonl"
    with journal.open("x", encoding="utf8"):
        pass

    def record(value):
        with journal.open("a", encoding="utf8", newline="\n") as target:
            target.write(json.dumps(value, ensure_ascii=True) + "\n")
            target.flush()
            os.fsync(target.fileno())

    try:
        cases = read(SUITE / "cases.json")["cases"]
        key = read(SUITE / "key.json")["authored_expectations"]
        if len(cases) != 10 or len({c["id"] for c in cases}) != 10 or {c["id"] for c in cases} != set(key):
            raise ValueError("Mini-diagnostic identity inventory mismatch")
        fields = ("processing_state", "execution_state", "comparator_invocations", "relationship", "association_state")
        if any(not ((set(fields) | {"class"}) <= set(entry)) for entry in key.values()):
            raise ValueError("Malformed scorer-only contract")
    except Exception as exc:
        record({"stage": "input_load_failed", "error_type": type(exc).__name__})
        raise
    output = []
    for case in cases:
        record({"stage": "case_started", "id": case["id"]})
        try:
            observed = execute_case(case)
            expected = key[case["id"]]
            checks = {name: canonical(observed[name]) == canonical(expected[name]) for name in fields}
            checks.update(
                qualification=(observed["qualification"] == "refused") == (expected["processing_state"] == "source_refused"),
                actual_comparator_calls=observed["observed_comparator_calls"] == expected["comparator_invocations"],
                source_integrity=observed["source_integrity"], lineage_integrity=observed["lineage_integrity"], export_integrity=observed["export_integrity"], no_grant=observed["no_grant"],
            )
        except Exception as exc:  # noqa: BLE001 - preserve every unexpected case failure without retry
            observed, checks = {"error_type": type(exc).__name__}, {"unexpected_execution_failure": False}
        row = {"id": case["id"], "class": key[case["id"]]["class"], "authored_expected": key[case["id"]], "observed": observed, "checks": checks, "passed": all(v is not False for v in checks.values())}
        output.append(row)
        record({"stage": "case_finished", "result": row})
    classes = defaultdict(list)
    for row in output:
        classes[row["class"]].append(row)
    names = sorted({name for row in output for name in row["checks"]})
    layers = {name: {"passed": sum(r["checks"].get(name) is True for r in output), "assessed": sum(r["checks"].get(name) is not None for r in output), "not_evaluated": sum(r["checks"].get(name) is None for r in output)} for name in names}
    result = {"format": "qualified-soc-v2-mini-diagnostic/1", "source_commit": head, "candidate_source_commit": freeze["source_commit"], "runs": 1, "model_sends": 0, "completed_cases": len(output), "matching_cases": sum(row["passed"] for row in output), "layers": layers, "cases": output, "per_class": {name: {"passed": sum(r["passed"] for r in rows), "cases": len(rows)} for name, rows in classes.items()}, "historical_sprint14": "unchanged: one run,11/12; not rerun/rescored", "independent_human_review": "PENDING (0 completed)", "release": "NO-GO"}
    write_once(DOCS / "diagnostic_results.json", result)
    record({"stage": "run_completed", "case_count": len(output), "model_sends": 0})
    return {name: result[name] for name in ("source_commit", "completed_cases", "matching_cases", "layers", "model_sends")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("development", "diagnostic"))
    print(json.dumps(development() if parser.parse_args().mode == "development" else diagnostic(), indent=2))
