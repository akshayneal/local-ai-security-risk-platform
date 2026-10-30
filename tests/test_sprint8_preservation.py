"""Active scope/byte guards and narrow historical endpoint AST proofs."""

import ast
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = "e7f61f4e7f8b56e14c6cf0d65fa461aff3e79417"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def plan():
    return json.loads((ROOT / "Documentation/sprint8_preservation.json").read_bytes())


def assert_scope(names, allowed):
    assert not set(names) - set(allowed), "Unauthorized Sprint 8 path"


def test_current_paths_and_every_other_base_blob():
    manifest = plan()
    assert manifest["base_commit"] == BASE
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE, "HEAD"], cwd=ROOT, check=True
    )
    allowed = set(manifest["authorized_existing"]) | set(manifest["authorized_new"])
    untracked = [
        p
        for p in git("ls-files", "--others", "--exclude-standard").splitlines()
        if not p.startswith("evals/results/s4check/")
    ]
    assert_scope(git("diff", BASE, "--name-only").splitlines() + untracked, allowed)
    blobs = {
        line.split("\t")[1]: line.split()[2]
        for line in git("ls-tree", "-r", BASE).splitlines()
    }
    protected = {
        p: h for p, h in blobs.items() if p not in manifest["authorized_existing"]
    }
    actual = subprocess.check_output(
        ["git", "hash-object", "--stdin-paths"],
        cwd=ROOT,
        text=True,
        input="\n".join(protected) + "\n",
    ).splitlines()
    assert dict(zip(protected, actual, strict=True)) == protected
    assert set(manifest["allowed_app_changes"]) == {
        "app/prompts.py",
        "app/ai_security_contracts.py",
        "app/ai_security_analyzer.py",
    }


def test_protected_inherited_sets_and_original_live_run():
    manifest = plan()
    s5, s6, s7 = [
        json.loads((ROOT / p).read_bytes()) for p in manifest["inherited_manifests"]
    ]
    live = json.loads((ROOT / manifest["protected_live_manifest"]).read_bytes())
    sets = [
        (
            "evals/results/s4check",
            s5["preexisting_untracked_sha256"] | s7["protected_inherited_cache_sha256"],
            False,
        ),
        (
            "knowledge_base/workspaces/northstar-sprint5",
            s6["protected_workspace_sha256"],
            False,
        ),
        (live["ignored_run_root"], live["artifact_sha256"], True),
    ]
    for directory, hashes, relative in sets:
        root = ROOT / directory
        if not root.exists():
            continue  # Fresh clone absence is not an integrity claim.
        actual = {
            p.relative_to(root if relative else ROOT).as_posix()
            for p in root.rglob("*")
            if p.is_file()
        }
        assert actual == set(hashes)
        for name, digest in hashes.items():
            assert (
                hashlib.sha256(
                    (root / name if relative else ROOT / name).read_bytes()
                ).hexdigest()
                == digest
            ), name
    if (ROOT / "evals/results/s4check").exists():
        assert (
            hashlib.sha256((ROOT / "AGENTS.md").read_bytes()).hexdigest()
            == manifest["installed_agents_sha256"]
        )
    assert not git("ls-files", "--", "evals/results/s4check").strip()
    assert "evals/results/s4check/" not in git("diff", "--cached", "--name-only")


def expected_tree(name):
    tree = ast.parse(git("show", BASE + ":" + name))
    if name.endswith("test_ai_security_evaluation.py"):
        old = next(
            n
            for n in tree.body
            if isinstance(n, ast.ImportFrom) and n.module == "test_sprint7_preservation"
        )
        old.module, old.names = (
            "sprint8_history",
            [ast.alias("historical_call", "historical_ai_security_call")],
        )
        return tree
    helper = "historical_test" if "preservation" in name else "historical_call"
    tree.body.append(
        ast.ImportFrom(module="sprint8_history", names=[ast.alias(helper)], level=0)
    )
    targets = (
        {"test_prior_mini_sprint_and_unmodified_source_are_preserved"}
        if "sprint4" in name
        else {
            "test_current_scope_and_protected_base_blobs",
            "test_historical_replay_call_sites_only_pin_the_source_root",
            "test_original_runner_still_rejects_corrupt_snapshot",
        }
    )
    if helper == "historical_test":
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in targets:
                node.decorator_list.append(ast.Name(id=helper, ctx=ast.Load()))
        return tree
    if "knowledge_evaluation" in name:
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in {
                "recorded_and_replay",
                "test_frozen_source_cases_rubric_and_implementation_identity",
            }:
                node.args.args.append(ast.arg(arg="tmp_path_factory"))

        class Calls(ast.NodeTransformer):
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id in {
                    "evaluate",
                    "verify_freeze",
                }:
                    return ast.Call(
                        func=ast.Name(id=helper, ctx=ast.Load()),
                        args=[
                            node.func,
                            ast.Name(id="tmp_path_factory", ctx=ast.Load()),
                        ],
                        keywords=[],
                    )
                return self.generic_visit(node)

        return Calls().visit(tree)
    node = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef)
        and n.name == "test_frozen_matrix_and_fresh_reviewed_workspace"
    )
    node.args.args.append(ast.arg(arg="tmp_path_factory"))
    statement = next(
        n
        for n in node.body
        if isinstance(n, ast.Expr)
        and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Attribute)
        and n.value.func.attr == "verify_freeze"
    )
    statement.value = ast.Call(
        func=ast.Name(id=helper, ctx=ast.Load()),
        args=[statement.value.func, ast.Name(id="tmp_path_factory", ctx=ast.Load())],
        keywords=[],
    )
    return tree


def canonical(tree):
    imports = sorted(
        ast.dump(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
    )
    body = [
        ast.dump(n)
        for n in tree.body
        if not isinstance(n, (ast.Import, ast.ImportFrom))
    ]
    return imports, body


@pytest.mark.parametrize(
    "name",
    [
        "tests/test_sprint4_preservation.py",
        "tests/test_sprint7_preservation.py",
        "tests/test_ai_security_evaluation.py",
        "tests/test_knowledge_evaluation.py",
        "tests/test_cross_pillar_evaluation.py",
    ],
)
def test_historical_changes_are_only_snapshot_call_sites(name):
    assert canonical(ast.parse((ROOT / name).read_text())) == canonical(
        expected_tree(name)
    )
    source = git("show", BASE + ":" + name)
    assert canonical(
        ast.parse(source.replace("assert ", "assert True or ", 1))
    ) != canonical(ast.parse(source))


def test_current_scope_and_byte_mutation_negatives():
    with pytest.raises(AssertionError, match="Unauthorized"):
        assert_scope(["app/ollama_client.py"], plan()["authorized_existing"])
    data = subprocess.check_output(
        ["git", "show", BASE + ":app/ollama_client.py"], cwd=ROOT
    )

    def blob(value):
        return hashlib.sha1(f"blob {len(value)}\0".encode() + value).hexdigest()

    assert blob(data) == git("rev-parse", BASE + ":app/ollama_client.py").strip()
    assert blob(data + b"\n# mutation") != blob(data)
