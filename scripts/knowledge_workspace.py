"""Trusted local CLI; never an unauthenticated file-upload/read endpoint."""

import argparse
import json

from app.knowledge_workspace import (
    initialize_workspace,
    load_workspace,
    register_workspace,
    select_knowledge,
    workspace_query,
)
from app.retrieval.contracts import Workflow
from app.retrieval.serialization import metadata


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Experimental reviewed local knowledge workspace"
    )
    parser.add_argument(
        "action", choices=["init", "register", "build", "status", "query"]
    )
    parser.add_argument(
        "workspace", help="Simple name under knowledge_base/workspaces/"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="init only: copy frozen synthetic Northstar inputs",
    )
    parser.add_argument(
        "--workflow",
        choices=[Workflow.SOC.value, Workflow.AI_RISK.value],
        default=Workflow.SOC.value,
    )
    parser.add_argument("--text", default="incident approval RAG review")
    args = parser.parse_args()
    try:
        if args.demo and args.action != "init":
            raise ValueError("--demo is only valid for init")
        if args.action == "init":
            result = initialize_workspace(args.workspace, demo=args.demo)
        elif args.action == "register":
            result = register_workspace(args.workspace)
        else:
            workspace = load_workspace(args.workspace)
            hits, coverage, _ = select_knowledge(
                workspace,
                workspace_query(workspace, Workflow(args.workflow), args.text),
            )
            result = {
                "status": "validated",
                "coverage": coverage.model_dump(mode="json"),
            }
            if args.action == "query":
                # Metadata only; no full text, paths, hidden grants or sensitive payloads.
                result["selected_sources"] = [metadata(h) for h in hits]
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, RuntimeError):
        parser.exit(
            2,
            "Workspace operation refused. Check the named local workspace, exact-version reviews and registry; no analysis was run.\n",
        )


if __name__ == "__main__":
    main()
