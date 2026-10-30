"""Launcher safety tests; Windows execution uses mocks, never real services."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts/development"


def test_launcher_scope_and_visible_errors():
    common = (SCRIPTS / "Development.Common.ps1").read_text()
    start = (SCRIPTS / "Start-Development.ps1").read_text()
    stop = (SCRIPTS / "Stop-Development.ps1").read_text()
    for forbidden in ("Stop-Process -Name", "taskkill", "git reset", "ollama pull qwen3:8b\n"):
        assert forbidden not in common + start + stop
    assert "--host 127.0.0.1 --port 8235" in common
    assert "--server.address 127.0.0.1 --server.port 8535" in common
    assert "PYTHON_DOTENV_DISABLED = '1'" in common
    for name in ("Start", "Stop"):
        cmd = (SCRIPTS / f"{name}-Development.cmd").read_text()
        assert '"%~dp0' in cmd and "pause" in cmd and "exit /b 1" in cmd


@pytest.mark.skipif(os.name != "nt", reason="Windows PowerShell and CIM")
@pytest.mark.parametrize(
    "scenario",
    [
        "syntax_paths",
        "missing_venv",
        "missing_ollama",
        "missing_model",
        "port_occupied",
        "ownership_stop",
        "children",
        "repeated_start",
        "partial_failure",
        "environment",
        "shortcut_conflict",
    ],
)
def test_mocked_powershell(scenario, tmp_path):
    fixture = SCRIPTS / "Test-Development.ps1"
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(fixture),
            "-Scenario",
            scenario,
            "-Scratch",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(os.name != "nt", reason="Windows cmd error window behavior")
def test_cmd_failure_is_visible_from_path_with_spaces(tmp_path):
    package = tmp_path / "checkout with spaces" / "scripts" / "development"
    shutil.copytree(SCRIPTS, package)
    result = subprocess.run(
        ["cmd.exe", "/d", "/c", str(package / "Start-Development.cmd")],
        input="\n",
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
        cwd=tmp_path,
    )
    assert result.returncode == 1
    assert "Development startup failed" in result.stdout
    assert "Press any key" in result.stdout


@pytest.mark.skipif(os.name != "nt", reason="Windows command parsing and process mocks")
@pytest.mark.parametrize(
    "scenario",
    [
        "command_identity",
        "trailing_space_start",
        "normalized_start",
        "delayed_metadata",
        "delegated_exit",
        "startup_exit",
        "health_failure",
        "child_rejection",
    ],
)
def test_process_identity_regressions(scenario, tmp_path):
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SCRIPTS / "Test-DevelopmentIdentity.ps1"),
            "-Scenario",
            scenario,
            "-Scratch",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
