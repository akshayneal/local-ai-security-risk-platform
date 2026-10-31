"""Frozen one-run heldout method; never used as a development input."""

from pathlib import Path


def run(readiness):
    from evals.deterministic_evidence_v1.runner import run_suite, verify_freeze

    verify_freeze()
    required = {"all_pillars_viable", "bindings_exact", "no_material_contradictions", "no_pending", "protected_pass", "compatible", "committed"}
    if set(readiness) != required or not all(v is True for v in readiness.values()):
        raise ValueError("Acceptance NOT RUN: viability or identity gate failed")
    root = Path("knowledge_base/workspaces/juniper-sprint11-acceptance")
    if root.exists():
        raise ValueError("Acceptance is exclusive and must never replay")
    return run_suite(track="acceptance", formulation="F3", root=root, phase="A")
