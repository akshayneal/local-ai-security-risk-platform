"""Non-secret CLI provenance and exact working-file hashes; no model generations."""

import hashlib
import json
import platform
import re
import subprocess
from pathlib import Path
from typing import Any

from app.ollama_client import OLLAMA_MODEL, OLLAMA_TEMPERATURE
from evals.reliability_schemas import RepeatedEvaluationReport, RuntimeProvenance

ROOT = Path(__file__).resolve().parents[1]
BEHAVIOR_FILES = (
    "evals/cases/adversarial_v2.json",
    "app/prompts.py",
    "app/schemas.py",
    "app/ollama_client.py",
    "app/reference_loader.py",
    "app/soc_analyzer.py",
    "app/governance_analyzer.py",
    "app/analysis_trace.py",
    "app/untrusted_content.py",
    "app/output_policy.py",
    "app/observables.py",
    "reference_material/soc_references.json",
    "reference_material/governance_references.json",
    "reference_material/local_checklists.json",
    "requirements.txt",
    "evals/schemas.py",
    "evals/validators.py",
    "evals/observables.py",
    "evals/runner.py",
    "evals/reliability_runner.py",
    "evals/reliability_schemas.py",
    "evals/provenance.py",
    "evals/response_contracts.py",
    "evals/reliability_compare.py",
    "evals/diagnostic_runner.py",
    ".gitattributes",
)
V1_FILES = (
    "Documentation/evaluation_results/baseline.json",
    "Documentation/evaluation_results/hardened.json",
    "Documentation/evaluation_results/comparison.json",
    "evals/cases/adversarial.json",
)


def byte_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def suite_hashes(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    canonical = json.dumps(
        json.loads(raw),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest(), hashlib.sha256(canonical).hexdigest()


def cli_output(args: list[str]) -> str | None:
    try:
        return subprocess.run(
            args, cwd=ROOT, check=True, capture_output=True, text=True, timeout=15
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def collect_provenance() -> RuntimeProvenance:
    version = cli_output(["ollama", "--version"])
    listing = cli_output(["ollama", "ls"])
    digest = None
    for line in (listing or "").splitlines():
        columns = line.split()
        if (
            len(columns) >= 2
            and columns[0] == OLLAMA_MODEL
            and re.fullmatch(r"[a-f0-9]{12,64}", columns[1])
        ):
            digest = columns[1]
            break
    commit = cli_output(["git", "rev-parse", "HEAD"])
    status = cli_output(["git", "status", "--porcelain"])
    unavailable = []
    if version is None:
        unavailable.append("Ollama version CLI unavailable")
    if digest is None:
        unavailable.append("No reliably parsed configured-model ID from ollama ls")
    if commit is None or status is None:
        unavailable.append("Git provenance unavailable")
    return RuntimeProvenance(
        python_version=platform.python_version(),
        ollama_version=version,
        model=OLLAMA_MODEL,
        model_digest=digest,
        model_digest_kind="ollama_ls_short_id" if digest else None,
        git_commit=commit,
        git_dirty=None if status is None else bool(status),
        temperature=OLLAMA_TEMPERATURE,
        unavailable=unavailable,
    )


def build_manifest(
    report: RepeatedEvaluationReport, report_filename: str, *, root: Path = ROOT
) -> dict[str, Any]:
    """No absolute paths or file contents; raw bytes describe this experiment's checkout."""
    return {
        "manifest_version": "2.0",
        "official_report": report_filename,
        "official_report_sha256": byte_hash(root / report_filename),
        "runtime": report.provenance.model_dump(mode="json"),
        "suite_byte_sha256": report.suite_byte_sha256,
        "suite_semantic_sha256": report.suite_semantic_sha256,
        "hash_scope": "Exact working-file bytes used by this local run; checkout line endings can affect hashes.",
        "file_sha256": {
            name: byte_hash(root / name)
            for name in BEHAVIOR_FILES
            if (root / name).is_file()
        },
        "frozen_v1_sha256": {
            name: byte_hash(root / name) for name in V1_FILES if (root / name).is_file()
        },
    }


def verify_manifest(manifest: dict[str, Any], *, root: Path = ROOT) -> None:
    for name, expected in {
        **manifest["file_sha256"],
        **manifest["frozen_v1_sha256"],
        manifest["official_report"]: manifest["official_report_sha256"],
    }.items():
        path = root / name
        if path.is_absolute() and not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Manifest path escapes repository")
        if byte_hash(path) != expected:
            raise ValueError(f"Manifest hash mismatch: {name}")
