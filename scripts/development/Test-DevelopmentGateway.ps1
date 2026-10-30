# Sprint 7 mock-only migration contracts. Never launch services or browsers.
param([string]$Scenario, [string]$Scratch)
. (Join-Path $PSScriptRoot 'Development.Common.ps1')
function Assert($Condition, $Message) { if (-not $Condition) { throw $Message } }
function Expect-Failure([scriptblock]$Action, [string]$Pattern) {
    $caught = $false
    try { & $Action } catch { $caught = $true; Assert ($_.Exception.Message -like $Pattern) $_.Exception.Message }
    Assert $caught "Expected failure: $Pattern"
}
$paths = [pscustomobject]@{ Root = $Scratch; Python = 'C:\checkout\.venv\Scripts\python.exe'; Runtime = $Scratch; State = (Join-Path $Scratch 'state.json') }
$old = '-m uvicorn app.main:app --host 127.0.0.1 --port 8235'
$new = '-m uvicorn app.ai_security_api:app --host 127.0.0.1 --port 8235'
$command = if ($Scenario -eq 'new_reuse') { $new } else { $old }
$record = [pscustomobject]@{ id = 100; parent = 50; created = '2026-01-01T00:00:00.0000000Z'; command = ('"' + $paths.Python + '" ' + $command); executable = $paths.Python; service = 'api' }
$ui = $record.PSObject.Copy(); $ui.id = 200; $ui.service = 'ui'; $ui.command = '"' + $paths.Python + '" ' + $script:DevelopmentCommands.ui
$state = [pscustomobject]@{ format = 1; root = $Scratch; commit = 'same-commit'; records = @($record, $ui); interpreters = @($paths.Python) }
$script:live = @{ 100 = $record.PSObject.Copy(); 200 = $ui.PSObject.Copy() }
$script:stopped = @(); $script:launches = @()
function Get-DevelopmentProcess { param($ProcessId); return $script:live[[int]$ProcessId] }
function Get-CimInstance { return @() }
function Stop-Process { param($Id); $script:stopped += $Id; $script:live.Remove([int]$Id) }
function Start-Process { throw 'Must never start a process or browser in this harness' }
function Get-DevelopmentListeners {
    param($Port)
    [pscustomobject]@{ OwningProcess = $(if ($Port -eq 8235) { 100 } else { 200 }); LocalAddress = '127.0.0.1' }
}
function Test-DevelopmentHttp { return $true }
Save-DevelopmentState $paths $state
switch ($Scenario) {
    canonical_command {
        Assert ($script:DevelopmentCommands.api -ceq $new) 'new launches do not use the composed gateway'
        Assert ($script:DevelopmentCommands.ui -like '*--server.port 8535*') 'UI port changed'
    }
    legacy_stop {
        # Old venv redirector children keep the old exact command. A sibling
        # with an unrelated executable must never be adopted or terminated.
        $child = $record.PSObject.Copy(); $child.id = 101; $child.parent = 100
        $child.created = '2026-01-01T00:00:00.1000000Z'
        $child.PSObject.Properties.Remove('service')
        $script:live[101] = $child
        $unrelated = $child.PSObject.Copy(); $unrelated.id = 999; $unrelated.executable = 'C:\unrelated\python.exe'
        $script:live[999] = $unrelated
        function Get-CimInstance {
            param($Filter)
            if ($Filter -eq 'ParentProcessId = 100') {
                [pscustomobject]@{ ProcessId = 101 }
                [pscustomobject]@{ ProcessId = 999 }
            }
        }
        $loaded = Read-DevelopmentState $paths
        Assert (-not (Test-DevelopmentReady $paths $loaded)) 'legacy service advertised as the new gateway'
        Stop-DevelopmentOwned $paths $loaded
        Assert ($script:stopped.Count -eq 3 -and $script:stopped[0] -eq 101) 'strict legacy child-first stop failed'
        Assert ($script:live.Count -eq 1 -and $script:live.ContainsKey(999) -and 999 -notin $script:stopped) 'unrelated legacy-command child terminated'
        Assert (-not (Test-Path $paths.State)) 'successful stop retained state'
    }
    legacy_start {
        # Drive the real Start script with only infrastructure effects mocked.
        function Get-DevelopmentPaths { return $paths }
        function Assert-DevelopmentCheckout { return 'same-commit' }
        function Enter-DevelopmentLock { return $null }
        function Start-Transcript {}
        function Stop-Transcript {}
        function Assert-DevelopmentPython {}
        function Initialize-DevelopmentEnvironment {}
        function Initialize-DevelopmentOllama { throw 'legacy start touched shared Ollama' }
        function Update-DevelopmentChildren { throw 'legacy start rewrote ownership state' }
        $before = [IO.File]::ReadAllBytes($paths.State)
        $source = Get-Content -Raw (Join-Path $PSScriptRoot 'Start-Development.ps1')
        $source = $source.Replace(". (Join-Path `$PSScriptRoot 'Development.Common.ps1')", '').Replace('exit 1', 'throw')
        Expect-Failure { & ([scriptblock]::Create($source)) -NoBrowser } '*Legacy*Stop*Start*'
        Assert ($script:stopped.Count -eq 0 -and $script:live.Count -eq 2) 'legacy start terminated a process'
        Assert ([Convert]::ToBase64String($before) -ceq [Convert]::ToBase64String([IO.File]::ReadAllBytes($paths.State))) 'legacy start changed state'
    }
    new_reuse {
        $loaded = Read-DevelopmentState $paths
        Assert (Test-DevelopmentReady $paths $loaded) 'healthy gateway not reusable'
        Assert-DevelopmentCurrentGateway $paths $loaded
        Stop-DevelopmentOwned $paths $loaded
        Assert ($script:stopped.Count -eq 2) 'new gateway stop failed'
    }
    altered_record {
        foreach ($bad in @(($old + ' --reload'), $old.Replace('app.main:app', 'app.arbitrary:app'), $old.Replace('127.0.0.1', '0.0.0.0'), $new.Replace('8235', '9999'))) {
            $state.records[0].command = '"' + $paths.Python + '" ' + $bad
            Save-DevelopmentState $paths $state
            Expect-Failure { Read-DevelopmentState $paths } '*Invalid development process record*'
        }
        Assert ($script:stopped.Count -eq 0) 'invalid recorded command stopped a process'
    }
    changed_identity {
        foreach ($field in @('created', 'parent', 'command', 'executable')) {
            $script:live[100] = $record.PSObject.Copy()
            if ($field -eq 'parent') { $script:live[100].parent = 999 }
            elseif ($field -eq 'executable') { $script:live[100].executable = 'C:\other\python.exe' }
            else { $script:live[100].$field += ' altered' }
            Save-DevelopmentState $paths $state
            Expect-Failure { Stop-DevelopmentOwned $paths (Read-DevelopmentState $paths) } '*could not be verified*'
            Assert (100 -notin $script:stopped -and (Test-Path $paths.State)) 'changed legacy identity stopped or state lost'
        }
    }
    port_conflict {
        function Get-DevelopmentListeners { [pscustomobject]@{ OwningProcess = 999; LocalAddress = '127.0.0.1' } }
        Expect-Failure { Assert-DevelopmentPortsFree } '*Port 8235 is occupied*'
        Assert ($script:stopped.Count -eq 0) 'port occupant terminated'
    }
    default { throw "Unknown gateway scenario: $Scenario" }
}
Write-Host "PASS: $Scenario"
