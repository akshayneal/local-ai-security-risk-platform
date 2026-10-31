"""Explicit foreground development diagnostics; never resumes historical runs."""

import argparse
import json
import os
import subprocess
import time
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import requests

from evals.model_task_diagnostic_v1.transport import (
    DIGEST,
    HOST,
    MODEL,
    OPTIONS,
    PHASE_CAPS,
    DiagnosticBudget,
    DiagnosticStop,
    encoded,
    plain_path,
    sha,
)
from evals.model_task_diagnostic_v1.umbrella import CampaignLedger

ROOT = Path(__file__).resolve().parents[2]
SUITE = Path(__file__).resolve().parent
WORKSPACES = ROOT / "knowledge_base/workspaces"
LAB = WORKSPACES / "elm-sprint10-lab/accounting"
CAMPAIGN = WORKSPACES / "elm-sprint10-campaign"
ACCEPTANCE_JOURNAL = WORKSPACES / "elm-sprint10-acceptance/accounting/journal.jsonl"
SOURCE_PATHS = (
    "app/ai_security_analyzer.py",
    "app/ai_security_contracts.py",
    "app/ai_security_sources.py",
    "app/ollama_client.py",
    "app/inference_context.py",
    "app/evidence_ledger.py",
    "app/prompts.py",
    "app/soc_analyzer.py",
    "app/governance_analyzer.py",
    "app/output_policy.py",
    "app/schemas.py",
    "evals/model_task_diagnostic_v1/runner.py",
    "evals/model_task_diagnostic_v1/transport.py",
    "evals/model_task_diagnostic_v1/umbrella.py",
    "evals/model_task_diagnostic_v1/narrow.py",
)
MODES = {"default": None, "off": False, "on": True}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def read(name):
    return json.loads((SUITE / name).read_bytes())


def verify_plan():
    """Prospective literal cases/rubric/options must exist in the current commit."""
    freeze = read("freeze.json")
    for name, digest in freeze["sha256"].items():
        actual = (ROOT / name).read_bytes()
        committed = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=ROOT)
        if sha(actual) != digest or sha(committed) != digest:
            raise ValueError("Prospective development identity changed: " + name)
    if read("plan.json")["options"] != OPTIONS:
        raise ValueError("Prospective runtime settings changed")
    if git("diff", "HEAD", "--", *SOURCE_PATHS):
        raise ValueError("Commit experimental source changes before live inference")
    return freeze


def preflight():
    """Read-only bounded metadata; no model warm-up, proxy, redirect or retry."""
    result = {}
    with requests.Session() as session:
        session.trust_env = False
        for path, payload in (
            ("/api/version", None),
            ("/api/tags", None),
            ("/api/show", {"model": MODEL}),
            ("/api/ps", None),
        ):
            response = session.request(
                "GET" if payload is None else "POST",
                HOST + path,
                json=payload,
                stream=True,
                timeout=10,
                allow_redirects=False,
            )
            body = bytearray()
            try:
                if response.status_code != 200:
                    raise ValueError("Read-only provider metadata unavailable")
                for chunk in response.iter_content(8192):
                    if len(body) + len(chunk) > 256_000:
                        raise ValueError("Read-only provider metadata exceeds limit")
                    body.extend(chunk)
            finally:
                response.close()
            result[path] = json.loads(body)
    model = next(
        (m for m in result["/api/tags"].get("models", []) if m.get("name") == MODEL),
        None,
    )
    capabilities = result["/api/show"].get("capabilities", [])
    if (
        not model
        or model.get("digest") != DIGEST
        or result["/api/version"].get("version") != "0.40.13"
        or "thinking" not in capabilities
        or "completion" not in capabilities
    ):
        raise ValueError("Exact supported local runtime unavailable")
    return {
        "version": "0.40.13",
        "model": MODEL,
        "digest": DIGEST,
        "capabilities": capabilities,
        "show_sha256": sha(encoded(result["/api/show"])),
        "loaded_models": [m.get("name") for m in result["/api/ps"].get("models", [])],
        "generation_attempts": 0,
    }


def selected_cases(contrast, formulation, case_ids, reason):
    cases = read("cases.json")
    if contrast in {"D1", "D2"}:
        if case_ids or (contrast == "D1" and formulation != "full"):
            raise ValueError("D1/D2 require the complete same technical pair")
        return cases[:2]
    if contrast == "D3":
        if case_ids or formulation != "full":
            raise ValueError("D3 requires the complete SOC/governance pair")
        return cases[2:]
    if contrast != "D4" or not reason.strip() or len(case_ids) != 1:
        raise ValueError(
            "D4 needs one explicit case and a documented diagnostic reason"
        )
    selected = [case for case in cases if case["id"] in case_ids]
    if len(selected) != 1:
        raise ValueError("Unknown diagnostic case")
    return selected


def execute(
    cases,
    budget,
    *,
    trial,
    contrast,
    mode,
    formulation,
    ledger,
    reason,
    decision_rule="v1",
):
    from app import (
        ai_security_analyzer,
        governance_analyzer,
        ollama_client,
        soc_analyzer,
    )
    from app.ai_security_contracts import AiSecurityRequest
    from app.evidence_ledger import evidence_ledger_mode
    from app.model_metrics import local_model_metrics
    from app.schemas import GovernanceRiskRequest, SocAlertRequest
    from evals.model_task_diagnostic_v1 import narrow

    source = {p: sha((ROOT / p).read_bytes()) for p in SOURCE_PATHS}
    commit = git("rev-parse", "HEAD")
    results = []
    call_once = ollama_client.call_model_json.__wrapped__

    class NoSdk:
        def chat(self, **kwargs):
            raise DiagnosticStop()

    with ExitStack() as stack:
        stack.enter_context(
            patch.object(
                ollama_client,
                "_complete_context_chat",
                lambda messages, schema, options: budget.chat(
                    messages, schema, options, think=MODES[mode]
                ),
            )
        )
        # Evaluation-only strict dispatch, including generic SOC/governance.
        stack.enter_context(
            patch.object(ollama_client, "complete_context_required", lambda: True)
        )
        stack.enter_context(patch.object(ollama_client, "client", NoSdk()))
        for module in (ai_security_analyzer, soc_analyzer, governance_analyzer):
            stack.enter_context(patch.object(module, "call_model_json", call_once))
        stack.enter_context(ai_security_analyzer.candidate_protocol(True))
        stack.enter_context(evidence_ledger_mode(ledger))
        for case in cases:
            if budget.blocked or budget.phase_counts[contrast] >= PHASE_CAPS[contrast]:
                results.append(
                    {
                        "id": case["id"],
                        "state": "NOT RUN",
                        "reason": "phase cap or unknown provider work",
                    }
                )
                continue
            budget.begin(
                case["id"],
                trial=trial,
                contrast=contrast,
                formulation=formulation,
                decision_rule=decision_rule,
                ledger=ledger,
                mode=mode,
                reason=reason,
                input_sha256=sha(encoded(case["input"])),
                case_sha256=sha(encoded(case)),
                commit=commit,
                source_sha256=source,
            )
            before, started = budget.count, time.monotonic()
            body, error_type, state = None, None, "RETURNED"
            with local_model_metrics(num_ctx=8192) as metrics:
                try:
                    if case["pillar"] == "ai_security":
                        request = AiSecurityRequest.model_validate(case["input"])
                        if formulation == "narrow":
                            task = narrow.build(request, decision_rule=decision_rule)
                            raw = call_once(task.prompt, task.response_schema)
                            body = narrow.evaluate(raw, task)
                        else:
                            body = ai_security_analyzer.analyze_ai_security(
                                request
                            ).model_dump(mode="json")
                    elif case["pillar"] == "soc":
                        body = soc_analyzer.analyze_soc_alert(
                            SocAlertRequest.model_validate(case["input"])
                        ).model_dump(mode="json")
                    else:
                        body = governance_analyzer.analyze_governance_risk(
                            GovernanceRiskRequest.model_validate(case["input"])
                        ).model_dump(mode="json")
                except (RuntimeError, ValueError, TypeError, KeyError) as exc:
                    state, error_type = "WITHHELD", type(exc).__name__
            row = {
                "id": case["id"],
                "pillar": case["pillar"],
                "control": case["control"],
                "contrast": contrast,
                "mode": mode,
                "formulation": formulation,
                "decision_rule": decision_rule,
                "ledger": ledger,
                "state": state,
                "error_type": error_type,
                "raw_attempts": budget.count - before,
                "wall_seconds": round(time.monotonic() - started, 6),
                "metrics": metrics.attempts,
                "semantic_judgment": "PENDING",
                "api_status": "not invoked; actual analyzer/internal contract exercised",
            }
            budget.store(case["id"] + ".json", {"result": row, "analysis": body})
            results.append(row)
            print(json.dumps(row), flush=True)
    return results


def run(
    *,
    trial,
    contrast,
    mode="default",
    formulation="full",
    ledger=False,
    case_ids=(),
    reason="",
    decision_rule="v1",
):
    if (
        not trial
        or len(trial) > 80
        or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in trial)
    ):
        raise ValueError("Explicit unique trial ID required")
    if mode not in MODES or (contrast in {"D1", "D2"} and ledger):
        raise ValueError("Invalid fixed diagnostic treatment")
    if decision_rule != "v1" and (
        contrast != "D4" or formulation != "narrow" or decision_rule != "explicit-v2"
    ):
        raise ValueError(
            "Explicit decision-rule diagnostic is limited to D4 narrow tasks"
        )
    os.environ.update(
        PYTHONDONTWRITEBYTECODE="1",
        PYTHON_DOTENV_DISABLED="1",
        OLLAMA_HOST=HOST,
        OLLAMA_MODEL=MODEL,
        RETRIEVAL_BACKEND="legacy",
        RETRIEVAL_SHADOW_BACKEND="",
        LOCAL_KNOWLEDGE_WORKSPACE="",
    )
    verify_plan()
    cases = selected_cases(contrast, formulation, case_ids, reason)
    provider = preflight()
    directory = LAB / "trials" / trial
    plain_path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    with (
        CampaignLedger(
            CAMPAIGN,
            lab_journal=LAB / "journal.jsonl",
            acceptance_journal=ACCEPTANCE_JOURNAL,
        ) as umbrella,
        DiagnosticBudget(LAB, umbrella=umbrella) as budget,
    ):
        budget.begin("TRIAL", trial=trial)
        report = {
            "trial": trial,
            "contrast": contrast,
            "mode": mode,
            "formulation": formulation,
            "decision_rule": decision_rule,
            "ledger": ledger,
            "implementation_commit": git("rev-parse", "HEAD"),
            "provider": provider,
            "scheduled": len(cases),
        }
        budget.store("preflight.json", report)
        report["results"] = execute(
            cases,
            budget,
            trial=trial,
            contrast=contrast,
            mode=mode,
            formulation=formulation,
            ledger=ledger,
            reason=reason,
            decision_rule=decision_rule,
        )
        report["lab_budget"] = budget.snapshot()
        report["campaign_budget"] = umbrella.snapshot()
        budget.store("report.json", report)
        return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trial", required=True)
    parser.add_argument("--contrast", choices=tuple(PHASE_CAPS), required=True)
    parser.add_argument("--mode", choices=tuple(MODES), default="default")
    parser.add_argument("--formulation", choices=("full", "narrow"), default="full")
    parser.add_argument("--ledger", choices=("off", "on"), default="off")
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--reason", default="")
    parser.add_argument("--decision-rule", choices=("v1", "explicit-v2"), default="v1")
    args = parser.parse_args()
    run(
        trial=args.trial,
        contrast=args.contrast,
        mode=args.mode,
        formulation=args.formulation,
        ledger=args.ledger == "on",
        case_ids=args.case,
        reason=args.reason,
        decision_rule=args.decision_rule,
    )


if __name__ == "__main__":
    main()
