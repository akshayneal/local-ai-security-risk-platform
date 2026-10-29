"""Single predeclared MSFT-003 reproduction; only safe codes leave the analyzer."""

import argparse
import json
import subprocess
from pathlib import Path

from app.local_diagnostics import LocalDiagnosticTrace
from app.soc_analyzer import analyze_soc_alert
from app.soc_inputs import MicrosoftSocAdapter, parse_json_bundle
from evals.provenance import collect_provenance

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", required=True)
    args = parser.parse_args()
    assert args.live
    path = next((ROOT / "sample_data/microsoft").glob("MSFT-003*.json"))
    request = (
        MicrosoftSocAdapter().normalize(parse_json_bundle(path.read_bytes())).request
    )
    trace = LocalDiagnosticTrace(request.alert_id)
    report = {
        "planned_trials": 1,
        "purpose": "controlled diagnostic reproduction; historical cause remains unobservable",
        "runtime": collect_provenance().model_dump(mode="json"),
    }
    try:
        analyze_soc_alert(request, trace=trace)
        report["outcome"] = "returned"
    except Exception:  # noqa: BLE001 -- no exception messages or payloads.
        report["outcome"] = "withheld"
    report["diagnostics"] = trace.report()
    report["application_sha"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    target = ROOT / "evals/results/microsoft_port_diagnosis.json"
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
