"""Single foreground study: fresh synthetic evidence, no public route changes."""

import argparse
import json
import subprocess
import time
from pathlib import Path

from pydantic import ConfigDict, create_model

from app import evidence_reasoning as reasoning
from app.ai_security_contracts import AiSecurityResponse
from app.schemas import GovernanceRiskResponse, SocAlertResponse
from evals.deterministic_evidence_v1.runner import model_preflight
from evals.evidence_reasoning_v1.transport import (
    PHASES,
    CampaignLedger,
    DiagnosticBudget,
    DiagnosticStop,
    encoded,
    sha,
    track,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
WORK = ROOT / "knowledge_base/workspaces"
LAB = WORK / "spruce-sprint12-development"
HOLDOUT = WORK / "spruce-sprint12-diagnostic"
CAMPAIGN = WORK / "spruce-sprint12-campaign"
RESPONSES = {
    "soc": SocAlertResponse,
    "governance": GovernanceRiskResponse,
    "ai_security": AiSecurityResponse,
}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def read(name):
    return json.loads((HERE / name).read_bytes())


def verify_freeze():
    """Original prospective literals and executable code must be committed."""
    freeze = read("freeze.json")
    original = git(
        "log", "--diff-filter=A", "--format=%H", "--", str(HERE / "freeze.json")
    ).splitlines()
    if (
        not original
        or subprocess.check_output(
            ["git", "show", original[-1] + ":evals/evidence_reasoning_v1/freeze.json"],
            cwd=ROOT,
        )
        != (HERE / "freeze.json").read_bytes()
    ):
        raise ValueError("Prospective freeze identity changed")
    for path, expected in freeze["sha256"].items():
        if (
            sha((ROOT / path).read_bytes()) != expected
            or sha(subprocess.check_output(["git", "show", "HEAD:" + path], cwd=ROOT))
            != expected
        ):
            raise ValueError("Frozen source changed: " + path)
    for path, expected in freeze.get("protected_git_blobs", {}).items():
        if (
            git("rev-parse", "HEAD:" + path) != expected
            or git("hash-object", "--path=" + path, path) != expected
        ):
            raise ValueError("Protected normalized source changed: " + path)
    return freeze


def bundle_type(pillar):
    """Same core judgment plus the current public response contract's burden.

    This is a single-generation schema experiment, not the original analyzer:
    no retrieved guidance, repair, reference sanitizer or operational approval.
    """
    return create_model(
        "AnalysisBundle",
        __config__=ConfigDict(extra="forbid"),
        judgment=(reasoning.ReasoningProposal, ...),
        workflow_report=(RESPONSES[pillar], ...),
    )


def dispatch_spec(case, arm):
    req, selected = reasoning.request(case), reasoning.selection(case)
    mode = "minimal" if arm == "compact" else "full"
    messages = reasoning.build_messages(
        req, selected, question=case["question"], context_mode=mode
    )
    schema = (
        bundle_type(case["pillar"]) if arm == "bundle" else reasoning.ReasoningProposal
    ).model_json_schema()
    return req, selected, messages, schema


def execute(case, arm, budget):
    req, selected, messages, schema = dispatch_spec(case, arm)
    response = budget.chat(
        messages, schema, {"temperature": 0.1, "num_ctx": 32768}, think=False
    )
    raw = json.loads(response["message"]["content"])
    # Preserve a valid core proposal even if the ancillary full report fails.
    # Both validations are reported independently; nothing is repaired.
    ancillary_valid, ancillary_error = None, None
    if arm == "bundle":
        try:
            bundle_type(case["pillar"]).model_validate(raw)
            ancillary_valid = True
        except ValueError as exc:
            ancillary_valid, ancillary_error = False, type(exc).__name__
        raw = raw.get("judgment", {}) if isinstance(raw, dict) else {}
    report = reasoning.project(
        req, selected, raw, context_mode="minimal" if arm == "compact" else "full"
    )
    return {
        "proposal": report.proposal.model_dump(mode="json"),
        "report": json.loads(reasoning.export_json(req, selected, report)),
        "markdown": reasoning.export_markdown(req, selected, report),
        "ancillary_full_schema_valid": ancillary_valid,
        "ancillary_error": ancillary_error,
        "analyzer_available": "NOT INVOKED; single-generation schema experiment",
        "messages_sha256": sha(encoded(messages)),
        "schema_sha256": sha(encoded(schema)),
        "message_bytes": len(encoded(messages)),
        "schema_bytes": len(encoded(schema)),
    }


def phase_cases(phase):
    cases = read("diagnostic_cases.json" if phase == "H1" else "dev_cases.json")
    if phase == "D1":
        # Counterbalance contract ordering; fixed before outcomes.
        return [
            (case, arm)
            for i, case in enumerate(cases)
            for arm in (("bundle", "linked") if i % 2 == 0 else ("linked", "bundle"))
        ]
    if phase == "D2":
        return [(case, "compact") for case in cases]
    if phase == "H1":
        return [(case, "linked") for case in cases]
    raise ValueError("D3 NOT RUN: no second installed completion model")


def stored_result(root, relative):
    """Do not trust an orphaned or changed result when checking phase order."""
    path = root / relative
    data = path.read_bytes()
    rows = [
        json.loads(line) for line in (root / "journal.jsonl").read_bytes().splitlines()
    ]
    matches = [
        r
        for r in rows
        if r.get("event") == "artifact_stored" and r.get("path") == relative
    ]
    if len(matches) != 1 or matches[0]["sha256"] != sha(data):
        raise ValueError("Prior phase result is unjournaled or changed; preserve it")
    return json.loads(data)


def run(phase):
    freeze = verify_freeze()
    preflight = model_preflight()
    current_track = track(phase)
    root = HOLDOUT if current_track == "acceptance" else LAB
    trial = phase.lower()
    if (root / "trials" / trial).exists():
        raise ValueError(
            "Existing phase artifacts: preserve and review; automatic rerun refused"
        )
    for prior in {"D1": (), "D2": ("D1",), "H1": ("D1", "D2")}[phase]:
        summary = stored_result(LAB, f"trials/{prior.lower()}/phase-summary.json")
        if summary.get("safety_stop") or summary["accounting"]["blocked"]:
            raise ValueError(
                "Prior source/protection or UNKNOWN stop blocks generation"
            )
    scheduled = phase_cases(phase)
    # Validate every source/required binding and complete-context bound before
    # any reservation. This reads no rubric or expected outcome.
    for case, arm in scheduled:
        _, _, messages, schema = dispatch_spec(case, arm)
        DiagnosticBudget._request(
            None, messages, schema, {"temperature": 0.1, "num_ctx": 32768}, False
        )
    with (
        CampaignLedger(
            CAMPAIGN,
            lab_journal=LAB / "journal.jsonl",
            acceptance_journal=HOLDOUT / "journal.jsonl",
        ) as umbrella,
        DiagnosticBudget(root, umbrella=umbrella, track=current_track) as budget,
    ):
        records = []
        safety_stop = False
        for case, arm in scheduled:
            output = root / "trials" / trial / (case["id"] + "-" + arm + ".json")
            # Any prior reservation for this identity forbids a fresh send.
            rows = [
                json.loads(line)
                for line in (root / "journal.jsonl").read_bytes().splitlines()
            ]
            if any(
                r.get("event") == "provider_reserved"
                and r.get("sprint12_phase") == phase
                and r.get("case_id") == case["id"]
                and r.get("arm") == arm
                for r in rows
            ):
                raise ValueError(
                    "Prior reserved identity without result; manual preservation review required"
                )
            if budget.blocked or umbrella.blocked:
                raise ValueError("UNKNOWN blocks all further sends")
            budget.begin(
                case["id"],
                trial=trial,
                contrast=PHASES[phase],
                sprint12_phase=phase,
                arm=arm,
                commit=git("rev-parse", "HEAD"),
                case_sha256=sha(encoded(case)),
                freeze_sha256=sha(encoded(freeze)),
                preflight=preflight,
            )
            before, started = budget.count, time.monotonic()
            result = {
                "id": case["id"],
                "pillar": case["pillar"],
                "phase": phase,
                "arm": arm,
                "status": "RETURNED",
            }
            try:
                result.update(execute(case, arm, budget))
            except (ValueError, RuntimeError) as exc:
                result.update(status="WITHHELD", error_type=type(exc).__name__)
                if isinstance(exc, reasoning.proof.ProjectionUnavailable):
                    safety_stop = str(exc) not in {
                        "unavailable_fact_id",
                        "proposal_budget",
                    }
                    result["reason_code"] = str(exc)
                elif isinstance(exc, RuntimeError) and not isinstance(
                    exc, DiagnosticStop
                ):
                    safety_stop = True
                if budget.count == before:
                    safety_stop = True
            result.update(
                raw_sends=budget.count - before,
                seconds=round(time.monotonic() - started, 6),
                accounting=budget.snapshot(),
            )
            budget.store(output.name, result)
            records.append(result)
            print(
                json.dumps(
                    {
                        k: result[k]
                        for k in (
                            "id",
                            "phase",
                            "arm",
                            "status",
                            "raw_sends",
                            "seconds",
                        )
                    }
                ),
                flush=True,
            )
            if budget.blocked or safety_stop:
                break
        budget.store(
            "phase-summary.json",
            {
                "phase": phase,
                "records": records,
                "accounting": budget.snapshot(),
                "campaign": umbrella.snapshot(),
                "preflight": preflight,
                "safety_stop": safety_stop,
                "not_run": len(scheduled) - len(records),
            },
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("D1", "D2", "H1"))
    run(parser.parse_args().phase)
