"""CLI for rebuildable curated-card/registered-document evidence snapshots."""

import argparse
import json
import time
from pathlib import Path

from app.retrieval.importers import load_curated_records, load_registered_records
from app.retrieval.storage import canonical_json, read_snapshot, write_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build", "status"])
    parser.add_argument(
        "--path", type=Path, default=Path("knowledge_base/registry/retrieval.db")
    )
    parser.add_argument("--raw-docs", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument(
        "--metadata",
        type=Path,
        help="Trusted JSON mapping document IDs to retrieval metadata",
    )
    args = parser.parse_args()
    if args.action == "status":
        records = read_snapshot(args.path)
        print(
            canonical_json({"records": len(records), "bytes": args.path.stat().st_size})
        )
        return
    if any((args.raw_docs, args.registry, args.metadata)) and not all(
        (args.raw_docs, args.registry, args.metadata)
    ):
        parser.error("--raw-docs, --registry and --metadata must be supplied together")
    started = time.perf_counter()
    records = list(load_curated_records())
    if args.raw_docs:
        metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
        records.extend(load_registered_records(args.raw_docs, args.registry, metadata))
    result = write_snapshot(args.path, records)
    result["build_ms"] = (time.perf_counter() - started) * 1000
    print(canonical_json(result))


if __name__ == "__main__":
    main()
