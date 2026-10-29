[CmdletBinding()]
param([switch]$NoBrowser, [switch]$Status)
. (Join-Path $PSScriptRoot 'Demo.Common.ps1')
$paths = Get-DemoPaths
Assert-DemoBoundary $paths
if ($Status) {
    @(Get-DemoRecords $paths) | ForEach-Object {
        [pscustomobject]@{ ProcessId = $_.process_id; OwnedAndAlive = (Test-DemoOwnedProcess $paths $_) }
    }
    return
}
Initialize-DemoRoot $paths
$lock = Enter-DemoLock $paths
$transcribing = $false
try {
    Start-Transcript -Path (Join-Path $paths.Logs 'launcher.log') -Append | Out-Null
    $transcribing = $true
    $records = @(Get-DemoRecords $paths)
    if ($records.Count -ge 2 -and @($records | Where-Object { -not (Test-DemoOwnedProcess $paths $_) }).Count -eq 0 -and
        (Test-DemoHttp 'http://127.0.0.1:8100/health') -and (Test-DemoHttp 'http://127.0.0.1:8510/_stcore/health')) {
        Write-Host 'Demo is already healthy.'
        if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8510' }
        return
    }
    Stop-DemoOwnedProcesses $paths
    Assert-DemoPortsFree
    Sync-DemoRepository $paths
    $python = Initialize-DemoPython $paths
    Initialize-DemoOllama $paths
    $env:API_BASE_URL = 'http://127.0.0.1:8100'
    $env:PYTHONPATH = $paths.Repo
    # Avoid inheriting experimental retrieval configuration from a developer shell.
    $env:RETRIEVAL_BACKEND = 'legacy'
    $records = @()
    $commands = @(
        @{ Name = 'api'; Arguments = '-m uvicorn app.main:app --host 127.0.0.1 --port 8100' },
        @{ Name = 'ui'; Arguments = '-m streamlit run dashboard/streamlit_app.py --server.address 127.0.0.1 --server.port 8510 --server.headless true --browser.gatherUsageStats false' }
    )
    foreach ($command in $commands) {
        $process = Start-Process -FilePath $python -ArgumentList $command.Arguments -WorkingDirectory $paths.Repo `
            -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $paths.Logs "$($command.Name).out.log") `
            -RedirectStandardError (Join-Path $paths.Logs "$($command.Name).err.log")
        $record = Get-DemoProcessRecord $process.Id
        if (-not $record) { throw "$($command.Name) exited during startup." }
        $records += $record
        ConvertTo-Json -InputObject @($records) | Set-Content -LiteralPath (Join-Path $paths.Runtime 'processes.json')
    }
    Wait-DemoHttp 'http://127.0.0.1:8100/health'
    Wait-DemoHttp 'http://127.0.0.1:8510/_stcore/health'
    # Windows venv launchers may delegate to a child Python process. Record only
    # descendants of our own verified launchers, with the exact command/time.
    foreach ($record in @($records)) {
        Get-CimInstance Win32_Process -Filter "ParentProcessId = $($record.process_id)" | ForEach-Object {
            $child = Get-DemoProcessRecord $_.ProcessId
            if ($child -and (Test-DemoOwnedProcess $paths $child)) { $records += $child }
        }
    }
    ConvertTo-Json -InputObject @($records) | Set-Content -LiteralPath (Join-Path $paths.Runtime 'processes.json')
    $version = Invoke-RestMethod 'http://127.0.0.1:8100/' -TimeoutSec 5
    $ready = @{ commit = (Invoke-DemoGit $paths @('rev-parse', 'HEAD')); version = $version.version }
    $ready | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $paths.Runtime 'ready.json')
    Write-Host "Demo ready: version $($version.version), commit $($ready.commit). Logs: $($paths.Logs)"
    if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8510' }
} catch {
    Stop-DemoOwnedProcesses $paths
    Write-Error "Demo failed. Logs: $($paths.Logs). $($_.Exception.Message)"
} finally {
    if ($transcribing) { Stop-Transcript | Out-Null }
    $lock.Dispose()
}
