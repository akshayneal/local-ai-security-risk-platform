"""Portable safety checks plus executable helper tests on Windows (no downloads)."""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "scripts/demo"
COMMON = (DEMO / "Demo.Common.ps1").read_text(encoding="utf-8")
START = (DEMO / "Start-Demo.ps1").read_text(encoding="utf-8")


def run_powershell(code, tmp_path):
    script = tmp_path / "test.ps1"
    script.write_text(
        f". '{DEMO / 'Demo.Common.ps1'}'\n" + code, encoding="utf-8"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-File", str(script)],
        capture_output=True,
        check=False,
        text=True,
        env={**os.environ, "LOCALAPPDATA": str(tmp_path)},
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def test_only_dedicated_clone_can_be_reset():
    assert "Assert-DemoBoundary $Paths" in COMMON
    assert "& git -C $Paths.Repo @Arguments" in COMMON
    assert "@('checkout', 'main')" in COMMON
    assert "@('reset', '--hard', 'origin/main')" in COMMON
    assert "git clean" not in COMMON
    assert "ReparsePoint" in COMMON and "Unexpected demo origin" in COMMON
    assert "dedicated clone, not a worktree" in COMMON


def test_fixed_ports_environment_and_no_development_venv():
    assert "$script:DemoApiPort = 8100" in COMMON
    assert "$script:DemoUiPort = 8510" in COMMON
    assert "$env:API_BASE_URL = 'http://127.0.0.1:8100'" in START
    assert "$env:RETRIEVAL_BACKEND = 'legacy'" in START
    assert ".venv" not in COMMON + START
    assert "py -3.13" in COMMON and "pip check" in COMMON
    assert "Get-FileHash -LiteralPath $direct" in COMMON


def test_stop_verifies_identity_and_never_kills_by_name():
    assert "$live.created -eq $Record.created" in COMMON
    assert "$live.command -ceq $Record.command" in COMMON
    assert "$live.command -match $pythonPattern" in COMMON
    assert "Stop-Process -Id $record.process_id" in COMMON
    assert "Stop-Process -Name" not in COMMON
    assert "Enter-DemoLock" in START
    assert "Stop-DemoOwnedProcesses $paths" in START


def test_shortcuts_use_copied_bootstrap():
    source = (DEMO / "Install-DemoShortcut.ps1").read_text()
    assert "Copy-Item -LiteralPath" in source
    assert "Join-Path $paths.Launcher $item.Script" in source
    assert "WScript.Shell" in source
    assert "GetFolderPath('Desktop')" in source


@pytest.mark.skipif(os.name != "nt", reason="PowerShell helper execution on Windows")
@pytest.mark.parametrize(
    "code",
    [
        """
        $paths = Get-DemoPaths
        Assert-DemoBoundary $paths
        if ($paths.Repo -ne (Join-Path $paths.Root 'repo')) { throw 'bad layout' }
        $paths.Repo = $PSScriptRoot
        try { Assert-DemoBoundary $paths; throw 'accepted unsafe path' }
        catch { if ($_.Exception.Message -eq 'accepted unsafe path') { throw } }
        """,
        """
        $paths = Get-DemoPaths
        Initialize-DemoRoot $paths
        if (-not (Test-Path $paths.Marker)) { throw 'no marker' }
        Initialize-DemoRoot $paths
        """,
        """
        $paths = Get-DemoPaths
        Initialize-DemoRoot $paths
        ConvertTo-Json -InputObject @(@{process_id=1}, @{process_id=2}) | Set-Content (Join-Path $paths.Runtime 'processes.json')
        $records = @(Get-DemoRecords $paths)
        if ($records.Count -ne 2 -or $records[0].process_id -ne 1) { throw 'nested PID records' }
        """,
        """
        $paths = Get-DemoPaths
        New-Item -ItemType Directory $paths.Root | Out-Null
        try { Initialize-DemoRoot $paths; throw 'accepted unmarked' }
        catch { if ($_.Exception.Message -eq 'accepted unmarked') { throw } }
        """,
        """
        $paths = Get-DemoPaths
        Initialize-DemoRoot $paths
        if (Test-DemoFallback $paths) { throw 'accepted no ready checkout' }
        New-Item -ItemType Directory (Join-Path $paths.Repo 'app') -Force | Out-Null
        Set-Content (Join-Path $paths.Repo 'app/main.py') '# fake fixture'
        Set-Content (Join-Path $paths.Runtime 'ready.json') '{"commit":"abc"}'
        function Invoke-DemoGit { return 'abc' }
        if (-not (Test-DemoFallback $paths)) { throw 'no fallback' }
        function Invoke-DemoGit { return 'different' }
        if (Test-DemoFallback $paths) { throw 'accepted different checkout' }
        """,
        """
        $paths = Get-DemoPaths
        Initialize-DemoRoot $paths
        New-Item -ItemType Directory (Join-Path $paths.Repo '.git') -Force | Out-Null
        New-Item -ItemType Directory (Join-Path $paths.Repo 'app') -Force | Out-Null
        Set-Content (Join-Path $paths.Repo 'app/main.py') '# fixture'
        $script:readyCommit = 'a' * 40
        $script:fakeHead = 'b' * 40
        @{commit=$script:readyCommit} | ConvertTo-Json | Set-Content (Join-Path $paths.Runtime 'ready.json')
        function Invoke-DemoGit($Paths, [string[]]$Arguments) {
            Assert-DemoBoundary $Paths
            switch ($Arguments[0]) {
                'remote' { return $script:DemoRemote }
                'fetch' { throw 'simulated offline' }
                'cat-file' { return }
                'checkout' { if ($Arguments[1] -ne 'main') { throw 'wrong branch' }; return }
                'reset' { $script:fakeHead = $Arguments[2]; return }
                'rev-parse' { return $script:fakeHead }
                default { throw 'unexpected command' }
            }
        }
        Sync-DemoRepository $paths
        if ($script:fakeHead -ne $script:readyCommit) { throw 'did not restore last known good release' }
        """,
        """
        $paths = Get-DemoPaths
        Initialize-DemoRoot $paths
        New-Item -ItemType Directory $paths.Repo | Out-Null
        Set-Content (Join-Path $paths.Repo 'requirements.txt') 'a'
        Set-Content (Join-Path $paths.Repo 'requirements-windows-py313.lock.txt') 'b'
        $first = Get-DemoDependencyHash $paths
        Set-Content (Join-Path $paths.Repo 'requirements.txt') 'c'
        if ($first -eq (Get-DemoDependencyHash $paths)) { throw 'missed direct change' }
        """,
        """
        $paths = Get-DemoPaths
        Initialize-DemoRoot $paths
        New-Item -ItemType Directory $paths.Repo | Out-Null
        Set-Content (Join-Path $paths.Repo 'requirements.txt') 'a'
        Set-Content (Join-Path $paths.Repo 'requirements-windows-py313.lock.txt') 'b'
        $plan = Get-DemoEnvironmentPlan $paths
        if (-not $plan.Install -or -not $plan.Python.StartsWith($paths.Venv)) { throw 'bad first plan' }
        New-Item -ItemType Directory (Split-Path $plan.Python) -Force | Out-Null
        Set-Content $plan.Python 'fake executable fixture'
        @{hash=$plan.Hash;python=$plan.Python} | ConvertTo-Json | Set-Content (Join-Path $paths.Runtime 'dependencies.json')
        if ((Get-DemoEnvironmentPlan $paths).Install) { throw 'unchanged snapshot reinstalls' }
        Set-Content (Join-Path $paths.Repo 'requirements-windows-py313.lock.txt') 'changed'
        $next = Get-DemoEnvironmentPlan $paths
        if (-not $next.Install -or $next.Python -eq $plan.Python -or -not (Test-Path $plan.Python)) { throw 'unsafe changed snapshot update' }
        """,
        """
        $paths = Get-DemoPaths
        Initialize-DemoRoot $paths
        $script:killed = @()
        function Get-DemoRecords { return @([pscustomobject]@{process_id=10}, [pscustomobject]@{process_id=11}) }
        function Test-DemoOwnedProcess($Paths, $Record) { return $Record.process_id -eq 10 }
        function Get-CimInstance { return @() }
        function Stop-Process([int]$Id) { $script:killed += $Id }
        Stop-DemoOwnedProcesses $paths
        if ($script:killed.Count -ne 1 -or $script:killed[0] -ne 10) { throw 'stopped unowned process' }
        """,
        """
        $paths = Get-DemoPaths
        $script:fixture = [pscustomobject]@{process_id=42; created='time'; command=(Join-Path $paths.Venv 'Scripts/python.exe') + ' -m uvicorn app.main:app --host 127.0.0.1 --port 8100'}
        function Get-DemoProcessRecord { return $script:fixture }
        $record = $script:fixture.PSObject.Copy()
        if (-not (Test-DemoOwnedProcess $paths $record)) { throw 'not owned' }
        $record.created = 'reused pid'
        if (Test-DemoOwnedProcess $paths $record) { throw 'pid reuse accepted' }
        $record = $script:fixture.PSObject.Copy()
        $record.command = 'unrelated python'
        if (Test-DemoOwnedProcess $paths $record) { throw 'unrelated accepted' }
        """,
        """
        Get-ChildItem '""" + str(DEMO) + """/*.ps1' | ForEach-Object {
            $tokens = $null; $errors = $null
            [System.Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$tokens, [ref]$errors) | Out-Null
            if ($errors.Count) { throw ($errors | Out-String) }
        }
        """,
    ],
)
def test_windows_helpers(code, tmp_path):
    run_powershell(code, tmp_path)
