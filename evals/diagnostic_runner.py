"""One opt-in staged diagnostic per selected case; not an official benchmark."""

import argparse
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from app.analysis_trace import AnalysisTrace
from evals.reliability_runner import preflight
from evals.runner import run_case


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", required=True, dest="case_ids")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    _, cases, hashes, provenance = preflight(trials=1)
    if set(args.case_ids) - {case.test_id for case in cases}:
        parser.error("Unknown case ID")
    records = []
    for case in cases:
        if case.test_id not in args.case_ids:
            continue
        print(f"[DIAGNOSTIC] {case.test_id}", flush=True)
        trace = AnalysisTrace()
        result = run_case(case, trace=trace)
        records.append(
            {"result": result.model_dump(mode="json"), "trace": asdict(trace)}
        )
        print(
            f"[{case.test_id}] passed={result.passed}, error={result.error}", flush=True
        )
        # Save incrementally so completed diagnostic evidence survives interruption.
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(
                {
                    "purpose": "targeted diagnostic, not official benchmark",
                    "timestamp_utc": datetime.now(UTC).isoformat(),
                    "suite_byte_sha256": hashes[0],
                    "suite_semantic_sha256": hashes[1],
                    "provenance": provenance.model_dump(mode="json"),
                    "records": records,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return int(any(record["result"]["error"] for record in records))


if __name__ == "__main__":
    raise SystemExit(main())
