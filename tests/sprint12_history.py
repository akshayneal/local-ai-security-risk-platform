"""Replay the unchanged Sprint 11 guard against its immutable final source."""

import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from sprint8_history import _snapshot as historical_snapshot

# Each generation has its own cache. Preserve the original bounded archive body
# without evicting entries still used by earlier historical guards.
_snapshot = lru_cache(maxsize=4)(historical_snapshot.__wrapped__)

END = "430f20b93836584acc7719a9ed7c946781cdb3d1"


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
