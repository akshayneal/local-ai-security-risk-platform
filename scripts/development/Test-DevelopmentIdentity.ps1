# Mock-only process lifecycle regressions. No real service/process mutations.
param([string]$Scenario, [string]$Scratch)
. (Join-Path $PSScriptRoot 'Development.Common.ps1')
function Assert($Condition, $Message) { if (-not $Condition) { throw $Message } }
$paths = [pscustomobject]@{ Root = $Scratch; Python = 'C:\checkout with spaces\.venv\Scripts\python.exe'; Runtime = $Scratch; State = (Join-Path $Scratch 'state.json') }
$script:basePython = 'C:\Python313\python.exe'
$script:created = [datetime]::Parse('2026-01-01T00:00:00.1234567Z').ToUniversalTime()
$script:live = @{}
$script:launched = @()
$script:stopped = @()
$script:disposed = @()
$script:queries = 0
$script:clock = [datetime]::Parse('2026-01-01T00:00:00Z')
function Get-DevelopmentInterpreters { param($Paths); return @($Paths.Python, $script:basePython) }
function Assert-DevelopmentPortsFree {}
function Start-Sleep {}
function Get-Date { $script:clock = $script:clock.AddSeconds(1); return $script:clock }
function Get-DevelopmentProcess {
    param($ProcessId)
    $script:queries++
    if ($Scenario -eq 'delayed_metadata' -and $script:queries -lt 4) { return $null }
    return $script:live[[int]$ProcessId]
}
function Get-CimInstance {
    param($Filter)
    foreach ($item in $script:live.Values) {
        if ($Filter -eq "ParentProcessId = $($item.parent)") { [pscustomobject]@{ ProcessId = $item.id } }
    }
}
function Stop-Process { param($Id); $script:stopped += $Id; $script:live.Remove([int]$Id) }
function Start-Process {
    param($FilePath, $ArgumentList, $WorkingDirectory, $WindowStyle, [switch]$PassThru, $RedirectStandardOutput, $RedirectStandardError)
    $service = if ($script:launched.Count -eq 0) { 'api' } else { 'ui' }
    $processId = if ($service -eq 'api') { 100 } else { 200 }
    $script:launched += $processId
    Assert ($FilePath -eq $paths.Python -and $WorkingDirectory -eq $paths.Root) 'wrong launch paths'
    $observed = [pscustomobject]@{ id = $processId; parent = $PID; created = Get-DevelopmentCreationTime $script:created
        executable = $paths.Python; command = ('"' + $paths.Python + '" ' + $ArgumentList + ' ') }
    if ($Scenario -eq 'normalized_start') { $observed.executable = $paths.Python.ToUpperInvariant().Replace('\', '/') }
    # This is the actual observed failure: the executable matches but the
    # command line has the trailing space added by Windows Start-Process.
    Assert (-not $observed.command.EndsWith($ArgumentList)) 'fixture did not reproduce old suffix failure'
    $script:live[$processId] = $observed
    $exit = $Scenario -in @('delegated_exit', 'startup_exit')
    if ($exit) {
        $script:live.Remove($processId)
        if ($Scenario -eq 'delegated_exit') {
            $child = $observed.PSObject.Copy(); $child.id++; $child.parent = $processId; $child.executable = $script:basePython
            $child.created = Get-DevelopmentCreationTime $script:created.AddMilliseconds(20)
            $script:live[$child.id] = $child
        }
    }
    $mock = [pscustomobject]@{ Id = $processId; StartTime = $script:created; HasExited = $exit; ExitTime = $script:created.AddMilliseconds(100) }
    $mock | Add-Member ScriptMethod Dispose { $script:disposed += $this.Id }
    return $mock
}
function Get-DevelopmentListeners {
    param($Port)
    $owner = if ($Port -eq 8235) { 100 } else { 200 }
    if ($Scenario -eq 'delegated_exit') { $owner++ }
    if ($script:live.ContainsKey($owner)) { [pscustomobject]@{ OwningProcess = $owner; LocalAddress = '127.0.0.1' } }
}
function Test-DevelopmentHttp { return ($Scenario -ne 'health_failure') }
switch ($Scenario) {
    { $_ -in @('trailing_space_start', 'normalized_start', 'delayed_metadata', 'delegated_exit', 'health_failure', 'startup_exit') } {
        $failure = $null
        try { Start-DevelopmentServices $paths 'test' } catch { $failure = $_.Exception.Message }
        if ($Scenario -in @('health_failure', 'startup_exit')) {
            Assert ($null -ne $failure) 'startup failure not detected'
            Assert ($script:live.Count -eq 0) 'startup failure left an owned process behind'
            if ($Scenario -eq 'health_failure') { Assert ($script:stopped.Count -eq 2) 'failed readiness did not clean up both services' }
        } else {
            Assert (-not $failure) "unexpected startup failure: $failure"
            $state = Read-DevelopmentState $paths
            Assert (Test-DevelopmentReady $paths $state) 'repeated launch did not recognize owned listeners'
            if ($Scenario -eq 'delegated_exit') { Assert ($state.records.Count -eq 4) 'delegated interpreters not recorded' }
            Stop-DevelopmentOwned $paths $state
            Assert ($script:live.Count -eq 0) 'stop left owned processes behind'
            Assert ($script:stopped.Count -eq 2) 'stop targeted a dead redirector or missed a live interpreter'
        }
        Assert ($script:disposed.Count -eq $script:launched.Count) 'launch handles not disposed'
    }
    command_identity {
        $expected = '"C:\checkout with spaces\.venv\Scripts\python.exe" ' + $script:DevelopmentCommands.api
        Assert (Test-DevelopmentCommand ($expected + ' ') $expected) 'trailing whitespace rejected'
        $quoted = '"c:/checkout with spaces/.venv/Scripts/python.exe" -m "uvicorn" app.main:app   --host 127.0.0.1 --port "8235"'
        Assert (Test-DevelopmentCommand $quoted $expected) 'equivalent quoting/separators rejected'
        foreach ($bad in @(($expected + ' --reload'), ($expected + "`n"), $expected.Replace('8235', '8535'), ('"C:\other\python.exe" ' + $script:DevelopmentCommands.api), $expected.Replace('uvicorn', 'evil'))) {
            Assert (-not (Test-DevelopmentCommand $bad $expected)) 'unexpected interpreter/arguments accepted'
        }
        $ui = '"' + $paths.Python + '" ' + $script:DevelopmentCommands.ui
        Assert (Test-DevelopmentCommand ($ui.Replace('dashboard/streamlit_app.py', '"dashboard\streamlit_app.py"') + ' ') $ui) 'UI path quoting rejected'
        Assert ((Get-DevelopmentCreationTime $script:created) -eq '2026-01-01T00:00:00.1234560Z') 'creation time precision incorrect'
    }
    child_rejection {
        Start-DevelopmentServices $paths 'test'
        $state = Read-DevelopmentState $paths
        $parent = $script:live[100]
        $child = $parent.PSObject.Copy(); $child.id = 999; $child.parent = 100; $child.executable = 'C:\Unrelated\python.exe'
        $script:live[999] = $child
        Update-DevelopmentChildren $paths $state
        Assert ($state.records.Count -eq 2) 'arbitrary Python child adopted'
        $child.executable = $script:basePython; $child.command += ' --reload'
        Update-DevelopmentChildren $paths $state
        Assert ($state.records.Count -eq 2) 'unexpected command child adopted'
        $child.command = $parent.command; $child.created = '2025-01-01T00:00:00.0000000Z'
        Update-DevelopmentChildren $paths $state
        Assert ($state.records.Count -eq 2) 'child predating parent adopted'
        $child.created = $parent.created
        $parent.created = '2027-01-01T00:00:00.0000000Z'
        Update-DevelopmentChildren $paths $state
        Assert ($state.records.Count -eq 2) 'recycled parent PID adopted child'
        $script:live.Remove(100)
        Update-DevelopmentChildren $paths $state
        Assert ($state.records.Count -eq 2) 'missing parent without exit bound adopted child'
        $state.records[0] | Add-Member NoteProperty exited '2025-01-01T00:00:00.0000000Z' -Force
        Update-DevelopmentChildren $paths $state
        Assert ($state.records.Count -eq 2) 'child born after proven exit adopted'
        Stop-DevelopmentOwned $paths $state
        Assert ($script:live.ContainsKey(999) -and 999 -notin $script:stopped) 'unrelated child terminated'
    }
    default { throw "Unknown identity scenario: $Scenario" }
}
Write-Host "PASS: $Scenario"
