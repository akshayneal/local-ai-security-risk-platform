"""Replay unchanged Sprint 8 tests against their immutable tracked-only source."""

import functools
import inspect
import subprocess
import sys
from pathlib import Path

from sprint8_history import _snapshot

END = "f85e67fbd224fa020d0d904b62b6f8d7fd0b5e24"


def historical_test(function):
    """Retain assertions and parameter cases when the raw internal protocol changes."""

    @functools.wraps(function)
    def run(**fixtures):
        directory, env = _snapshot(fixtures["tmp_path_factory"].getbasetemp(), END)
        request = fixtures["request"]
        target = "tests/" + Path(function.__code__.co_filename).name
        target += "::" + function.__name__
        if hasattr(request.node, "callspec"):
            target += "[" + request.node.callspec.id + "]"
        result = subprocess.run(
            [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", target],
            cwd=directory,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    parameters = list(inspect.signature(function).parameters.values())
    names = {p.name for p in parameters}
    parameters += [
        inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        for name in ("tmp_path_factory", "request")
        if name not in names
    ]
    run.__signature__ = inspect.Signature(parameters)
    return run
