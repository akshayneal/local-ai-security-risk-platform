"""Replay the unchanged Sprint 13 scope assertion at its immutable final SHA."""

import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from sprint8_history import _snapshot as historical_snapshot

_snapshot = lru_cache(maxsize=4)(historical_snapshot.__wrapped__)
END = "285a6b5130e849daaea48406e1c9e1d7bc65ddf1"


def historical_test(function):
    def run(tmp_path_factory):
        directory, env = _snapshot(tmp_path_factory.getbasetemp(), END)
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
            timeout=120,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    run.__name__, run.__doc__ = function.__name__, function.__doc__
    return run
