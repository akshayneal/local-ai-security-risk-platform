"""Test-only immutable backend replay; never import inherited s4check content."""

import functools
import io
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
END = "e7f61f4e7f8b56e14c6cf0d65fa461aff3e79417"


def snapshot(tmp_path_factory, commit=END):
    return _snapshot(tmp_path_factory.getbasetemp(), commit)


@functools.lru_cache(maxsize=4)
def _snapshot(base, commit):
    """One bounded tracked-only archive and a scratch index, not a Git worktree."""
    directory = base / ("immutable-source-" + commit[:12])
    directory.mkdir()
    data = subprocess.check_output(["git", "archive", "--format=zip", commit], cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = archive.infolist()
        assert len(entries) <= 2000 and sum(x.file_size for x in entries) <= 128_000_000
        for entry in entries:
            path = PurePosixPath(entry.filename)
            assert (
                not path.is_absolute()
                and ".." not in path.parts
                and ".git" not in path.parts
            )
            assert (entry.external_attr >> 16) & 0o170000 != 0o120000
        archive.extractall(directory)
    env = os.environ | {
        "GIT_DIR": subprocess.check_output(
            ["git", "rev-parse", "--absolute-git-dir"], cwd=ROOT, text=True
        ).strip(),
        "GIT_WORK_TREE": str(directory),
        "GIT_INDEX_FILE": str(directory.parent / (directory.name + ".index")),
        "PYTHONPATH": os.pathsep.join((str(directory), str(directory / "tests"))),
        "PYTHON_DOTENV_DISABLED": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    # Only this explicit scratch index is written; the user's index/config is untouched.
    subprocess.run(
        ["git", "read-tree", commit],
        cwd=directory,
        env=env,
        check=True,
        capture_output=True,
    )
    return directory, env


def historical_call(callback, tmp_path_factory):
    allowed = {
        "evals.ai_security_v1.runner": {"evaluate", "verify_freeze"},
        "evals.knowledge_bridge_v1.runner": {"evaluate", "verify_freeze"},
        "evals.cross_pillar_v1.runner": {"verify_freeze"},
    }
    module, name = callback.__module__, callback.__name__
    assert name in allowed.get(module, set())
    commit = (
        "1c4f937f2b067a4a2b0d8ac8cf5db4f552555d00"
        if module == "evals.ai_security_v1.runner"
        else END
    )
    directory, env = snapshot(tmp_path_factory, commit)
    code = f"import json; from {module} import {name}; print(json.dumps({name}()))"
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=directory,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def historical_test(function):
    """Invoke the unchanged original test body against the original source tree."""

    def run(tmp_path_factory):
        directory, env = snapshot(tmp_path_factory)
        target = (
            "tests/"
            + Path(function.__code__.co_filename).name
            + "::"
            + function.__name__
        )
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                target,
            ],
            cwd=directory,
            env=env,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    run.__name__, run.__doc__ = function.__name__, function.__doc__
    return run
