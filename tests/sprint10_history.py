"""The sole Sprint 10 historical migration targets immutable Sprint 9 source."""

import subprocess
import sys
from pathlib import Path

from sprint8_history import _snapshot

END = "b6d84530b6eb9dccbb328a8dcffb0f9b532ef7ab"


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
