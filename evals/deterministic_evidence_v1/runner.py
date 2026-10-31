"""Counted foreground benchmark; no server, GUI, real data, retries or defaults change."""

import argparse
import hashlib
import json
import subprocess
import time
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from app import deterministic_evidence as proof
from app.ai_security_contracts import AiSecurityRequest
from app.analysis_trace import AnalysisTrace
from app.schemas import GovernanceRiskRequest, SocAlertRequest
from evals.deterministic_evidence_v1.transport import (
    CAPS,
    DIGEST,
    MODEL,
    OPTIONS,
    CampaignLedger,
    DiagnosticBudget,
    DiagnosticStop,
    encoded,
    sha,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
WORKSPACES = ROOT / "knowledge_base/workspaces"
LAB = WORKSPACES / "larch-sprint11-lab"
ACCEPTANCE = WORKSPACES / "juniper-sprint11-acceptance"
CAMPAIGN = WORKSPACES / "larch-sprint11-campaign"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def verify_freeze():
    freeze = json.loads((HERE / "freeze.json").read_bytes())
    for path, expected in freeze["sha256"].items():
        if (
            sha((ROOT / path).read_bytes()) != expected
            or sha(subprocess.check_output(["git", "show", "HEAD:" + path], cwd=ROOT))
            != expected
        ):
            raise ValueError("Frozen benchmark identity changed: " + path)
    if json.loads((HERE / "plan.json").read_bytes())["options"] != OPTIONS:
        raise ValueError("Frozen options changed")
    sources = [
        "app/deterministic_evidence.py",
        *[p.relative_to(ROOT).as_posix() for p in HERE.glob("*.py")],
    ]
    if git("diff", "HEAD", "--", *sources) or any(
        git("ls-files", "--error-unmatch", p) != p for p in sources
    ):
        raise ValueError("Commit source before inference")
    return freeze


def model_preflight():
    # Audited Sprint10 read-only metadata function, no generation/journal access.
    from evals.model_task_diagnostic_v1.runner import preflight

    return preflight()


def request(case):
    return {
        "soc": SocAlertRequest,
        "governance": GovernanceRiskRequest,
        "ai_security": AiSecurityRequest,
    }[case["pillar"]].model_validate(case["input"])


def selection(case):
    return proof.select(
        request(case),
        case_id=case["id"],
        required_paths=tuple(f["path"] for f in case["expected_facts"]),
        classification="public_synthetic",
    )


def plain_schema():
    schema = proof.ReasoningProposal.model_json_schema()
    for key in ("fact_ids", "actions_executed", "approval_granted"):
        schema["properties"].pop(key)
    schema["required"] = ["decision", "explanation", "unknowns", "validation"]
    return schema


def execute(case, formulation, budget):
    """Returns actual experiment objects, never changes semantic labels to match gold."""
    from app import (
        ai_security_analyzer,
        governance_analyzer,
        ollama_client,
        soc_analyzer,
    )
    from app.evidence_ledger import evidence_ledger_mode
    from app.prompts import SYSTEM_PROMPT

    trace = AnalysisTrace()

    def counted(messages, schema, options):
        answer = budget.chat(messages, schema, options, think=False)
        return json.loads(answer["message"]["content"])

    if formulation == "F1":
        payload = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": proof.encode(
                    {
                        "question": case["question"],
                        "application_decision_rule": case["rule"],
                        "untrusted_original_request": case["input"],
                        "scope": "one supplied question, other areas unassessed; do not recite all evidence",
                    }
                ),
            },
        ]
        raw = counted(payload, plain_schema(), {"temperature": 0.1, "num_ctx": 32768})
        proposal = proof.ReasoningProposal.model_validate(raw)
        return {
            "proposal": proposal.model_dump(mode="json"),
            "canonical_panel": "not supplied by this formulation",
        }
    if formulation == "F3":
        selected = selection(case)
        report = proof.run(
            request(case),
            selected,
            question=case["question"],
            rule=case["rule"],
            client=counted,
        )
        # These are the real serialization functions, no GUI or production export substitution.
        panel = json.loads(proof.export_json(request(case), selected, report))
        return {
            "report": panel,
            "markdown_export": proof.export_markdown(request(case), selected, report),
            "required_bindings": len(selected.required_paths),
            "required_omissions": 0,
            "proposal": report.proposal.model_dump(mode="json"),
        }
    if formulation != "F2":
        raise ValueError("Unknown formulation")

    class NoSDK:
        def chat(self, **kwargs):
            raise DiagnosticStop()

    once = ollama_client.call_model_json.__wrapped__
    with ExitStack() as stack:
        stack.enter_context(
            patch.object(
                ollama_client,
                "_complete_context_chat",
                lambda m, s, o: budget.chat(m, s, o, think=False),
            )
        )
        stack.enter_context(
            patch.object(ollama_client, "complete_context_required", lambda: True)
        )
        stack.enter_context(patch.object(ollama_client, "client", NoSDK()))
        # Evaluation-only runtime override; old metric helper admits only 4K/8K.
        # Durable transport journal owns actual options/usage for every format.
        stack.enter_context(
            patch.object(ollama_client, "configured_context", lambda: 32768)
        )
        for module in (ai_security_analyzer, governance_analyzer, soc_analyzer):
            stack.enter_context(patch.object(module, "call_model_json", once))
        stack.enter_context(evidence_ledger_mode(False))
        stack.enter_context(ai_security_analyzer.candidate_protocol(True))
        try:
            if case["pillar"] == "soc":
                result = soc_analyzer.analyze_soc_alert(request(case), trace=trace)
            elif case["pillar"] == "governance":
                result = governance_analyzer.analyze_governance_risk(
                    request(case), trace=trace
                )
            else:
                result = ai_security_analyzer.analyze_ai_security(request(case))
            return {
                "analysis": result.model_dump(mode="json"),
                "trace": trace.stages,
                "repair_attempted": trace.repair_attempted,
            }
        except (RuntimeError, ValueError, TypeError, KeyError) as exc:
            return {
                "withheld": type(exc).__name__,
                "trace": trace.stages,
                "repair_attempted": trace.repair_attempted,
            }


def run_suite(*, track, formulation, root, phase):
    verify_freeze()
    if (track, formulation, phase) not in {
        ("lab", "paired", "D0"),
        ("lab", "F2", "D1"),
        ("acceptance", "F3", "A"),
    }:
        raise ValueError("Only preregistered blocks may run")
    expected_root = LAB if track == "lab" else ACCEPTANCE
    if Path(root).resolve() != expected_root.resolve():
        raise ValueError("Unapproved or historical output root")
    provider = model_preflight()
    # A loaded idle model is allowed only between this campaign's known blocks.
    if provider["loaded_models"] and not (LAB / "journal.jsonl").exists():
        raise ValueError("Unexpected loaded provider; preserve and inspect")
    cases = json.loads(
        (
            HERE / ("dev_cases.json" if track == "lab" else "acceptance_cases.json")
        ).read_bytes()
    )
    rows = []
    with (
        CampaignLedger(
            CAMPAIGN,
            lab_journal=LAB / "journal.jsonl",
            acceptance_journal=ACCEPTANCE / "journal.jsonl",
        ) as campaign,
        DiagnosticBudget(expected_root, umbrella=campaign, track=track) as budget,
    ):
        trial = phase.lower() + "-" + formulation.lower()
        if (expected_root / "trials" / trial).exists():
            raise ValueError("No block reruns")
        for case in cases:
            for form in ("F1", "F3") if formulation == "paired" else (formulation,):
                if budget.blocked:
                    raise DiagnosticStop()
                budget.begin(
                    case["id"],
                    trial=trial,
                    contrast=phase,
                    formulation=form,
                    pillar=case["pillar"],
                    commit=git("rev-parse", "HEAD"),
                    input_sha256=sha(encoded(case["input"])),
                    source_sha256={
                        p.relative_to(ROOT).as_posix(): hashlib.sha256(
                            p.read_bytes()
                        ).hexdigest()
                        for p in [
                            ROOT / "app/deterministic_evidence.py",
                            HERE / "runner.py",
                            HERE / "transport.py",
                        ]
                    },
                )
                before = budget.count
                started = time.monotonic()
                try:
                    output = execute(case, form, budget)
                    state = "WITHHELD" if "withheld" in output else "RETURNED"
                except (RuntimeError, ValueError, TypeError, KeyError) as exc:
                    output, state = {"withheld": type(exc).__name__}, "WITHHELD"
                row = {
                    "case_id": case["id"],
                    "pillar": case["pillar"],
                    "formulation": form,
                    "state": state,
                    "raw_sends": budget.count - before,
                    "seconds": round(time.monotonic() - started, 6),
                    "semantic_review": "PENDING",
                }
                budget.store(
                    case["id"] + "-" + form + ".json",
                    {"result": row, "output": output},
                )
                rows.append(row)
                print(json.dumps(row), flush=True)
        budget.store(
            "block-summary.json",
            {
                "rows": rows,
                "budget": budget.snapshot(),
                "campaign": campaign.snapshot(),
                "model": MODEL,
                "digest": DIGEST,
                "caps": CAPS,
            },
        )
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["D0", "D1"])
    args = parser.parse_args()
    run_suite(
        track="lab",
        formulation="paired" if args.phase == "D0" else "F2",
        root=LAB,
        phase=args.phase,
    )
