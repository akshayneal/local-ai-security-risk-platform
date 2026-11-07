"""Replay the unchanged early Sprint 15 scope assertion at its final source tip."""

import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from sprint8_history import _snapshot as historical_snapshot

_snapshot = lru_cache(maxsize=4)(historical_snapshot.__wrapped__)
END = "9be773070f2176d40e3e80beccf65feaefdc03c0"


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
