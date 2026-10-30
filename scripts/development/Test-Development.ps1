# Mock-only harness invoked by pytest; does not launch services or browsers.
param([string]$Scenario, [string]$Scratch)
. (Join-Path $PSScriptRoot 'Development.Common.ps1')
function Assert($Condition, $Message) { if (-not $Condition) { throw $Message } }
function Expect-Failure([scriptblock]$Action, [string]$Pattern) {
    $caught = $false
    try { & $Action } catch { $caught = $true; Assert ($_.Exception.Message -like $Pattern) $_.Exception.Message }
    Assert $caught "Expected failure: $Pattern"
}
$paths = [pscustomobject]@{ Root = $Scratch; Python = (Join-Path $Scratch 'missing python.exe'); Runtime = $Scratch; State = (Join-Path $Scratch 'state.json') }
$record = [pscustomobject]@{ id = 100; parent = 1; created = '2026-01-01T00:00:00.0000000Z'; command = ('python.exe ' + $script:DevelopmentCommands.api); executable = 'C:\Python\python.exe'; service = 'api' }
$script:fixtureRecord = $record
$state = [pscustomobject]@{ format = 1; root = $Scratch; commit = 'test'; records = @($record) }
switch ($Scenario) {
    syntax_paths {
        foreach ($file in Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.ps1') {
            $tokens = $null; $errors = $null
            [Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$errors) | Out-Null
            Assert ($errors.Count -eq 0) "Syntax errors: $errors"
        }
        Push-Location $Scratch
        try { $actual = Get-DevelopmentPaths; Assert ([IO.Path]::IsPathRooted($actual.Root)) 'relative root'; Assert (Test-Path (Join-Path $actual.Root 'app/main.py')) 'wrong root' } finally { Pop-Location }
        $lock = Enter-DevelopmentLock $paths
        try { Expect-Failure { Enter-DevelopmentLock $paths } '*in progress*' } finally { $lock.Dispose() }
    }
    missing_venv { Expect-Failure { Assert-DevelopmentPython $paths } '*Missing existing virtual environment*' }
    missing_ollama {
        function Get-Command { return $null }
        Expect-Failure { Initialize-DevelopmentOllama $paths } '*missing from PATH*'
    }
    missing_model {
        Expect-Failure { Assert-DevelopmentModel ([pscustomobject]@{ models = @() }) } '*model qwen3:8b is missing*'
        Assert-DevelopmentModel ([pscustomobject]@{ models = @([pscustomobject]@{ name = 'qwen3:8b' }) })
    }
    port_occupied {
        function Get-DevelopmentListeners { return [pscustomobject]@{ OwningProcess = 999 } }
        function Stop-Process { throw 'Must never stop port owner' }
        Expect-Failure { Assert-DevelopmentPortsFree } '*Port 8235 is occupied*'
        Assert (-not (Test-DevelopmentReady $paths $state)) 'unrelated owner accepted'
    }
    ownership_stop {
        Save-DevelopmentState $paths $state
        function Get-DevelopmentProcess { return $script:fixtureRecord }
        Assert (Test-DevelopmentOwned $record) 'owned identity rejected'
        $changed = $record.PSObject.Copy(); $changed.created = 'different'
        Assert (-not (Test-DevelopmentOwned $changed)) 'recycled PID accepted'
        $changed = $record.PSObject.Copy(); $changed.command = 'unrelated'
        Assert (-not (Test-DevelopmentOwned $changed)) 'changed command accepted'
        function Get-CimInstance { return @() }
        $script:stopped = @()
        function Stop-Process { param($Id); $script:stopped += $Id }
        Stop-DevelopmentOwned $paths $state
        Assert ($script:stopped.Count -eq 1 -and $script:stopped[0] -eq 100) 'wrong process stopped'
        Assert (-not (Test-Path $paths.State)) 'state retained after successful stop'
        $changed = $record.PSObject.Copy(); $changed.created = 'different'
        $state.records = @($changed)
        Expect-Failure { Stop-DevelopmentOwned $paths $state } '*could not be verified*'
        Assert ($script:stopped.Count -eq 1) 'unrelated process stopped'
        Assert (Test-Path $paths.State) 'refusal lost state'
        $state.root = 'different'
        Save-DevelopmentState $paths $state
        Expect-Failure { Read-DevelopmentState $paths } '*Unrecognized*'
    }
    children {
        $child = $record.PSObject.Copy(); $child.id = 101; $child.parent = 100; $child.created = '2026-01-01T00:00:01.0000000Z'
        $script:fixtureChild = $child
        $script:fixtureChild.PSObject.Properties.Remove('service')
        function Get-DevelopmentProcess { param($ProcessId); if ($ProcessId -eq 100) { return $script:fixtureRecord }; return $script:fixtureChild }
        function Get-CimInstance { param($Filter); if ($Filter -eq 'ParentProcessId = 100') { return [pscustomobject]@{ ProcessId = 101 } } }
        Update-DevelopmentChildren $paths $state
        Assert ($state.records.Count -eq 2) 'venv child not recorded'
        $script:stopped = @()
        function Stop-Process { param($Id); $script:stopped += $Id }
        Stop-DevelopmentOwned $paths $state
        Assert ($script:stopped.Count -eq 2 -and $script:stopped[0] -eq 101) 'child stop order incorrect'
    }
    repeated_start {
        function Get-DevelopmentProcess { return $script:fixtureRecord }
        function Get-DevelopmentListeners { param($Port); return [pscustomobject]@{ OwningProcess = $(if ($Port -eq 8235) { 100 } else { 101 }); LocalAddress = '127.0.0.1' } }
        $ui = $record.PSObject.Copy(); $ui.id = 101; $ui.service = 'ui'
        $state.records += $ui
        function Test-DevelopmentOwned { return $true }
        function Test-DevelopmentHttp { return $true }
        Assert (Test-DevelopmentReady $paths $state) 'healthy owned services not reusable'
        function Assert-DevelopmentCheckout { return 'test' }
        function Get-DevelopmentPaths { return $paths }
        function Assert-DevelopmentPython {}
        function Initialize-DevelopmentEnvironment {}
        function Read-DevelopmentState { return $state }
        function Update-DevelopmentChildren {}
        function Initialize-DevelopmentOllama {}
        function Start-Process { throw 'Repeated start launched a process/browser' }
        function Start-DevelopmentServices { throw 'Repeated start launched services' }
        $source = Get-Content -Raw (Join-Path $PSScriptRoot 'Start-Development.ps1')
        $source = $source.Replace(". (Join-Path `$PSScriptRoot 'Development.Common.ps1')", '')
        & ([scriptblock]::Create($source)) -NoBrowser
    }
    partial_failure {
        function Assert-DevelopmentPortsFree {}
        $paths.Python = $record.executable
        $script:fixtureRecord = $record.PSObject.Copy()
        $script:fixtureRecord.PSObject.Properties.Remove('service')
        $script:launches = 0; $script:stopped = @()
        function Start-Process { $script:launches++; if ($script:launches -eq 2) { throw 'mock UI failure' }; return [pscustomobject]@{ Id = 100 } }
        function Get-DevelopmentProcess { return $script:fixtureRecord }
        function Get-CimInstance { return @() }
        function Stop-Process { param($Id); $script:stopped += $Id }
        Expect-Failure { Start-DevelopmentServices $paths 'test' } '*mock UI failure*'
        Assert ($script:stopped.Count -eq 1 -and $script:stopped[0] -eq 100) 'partial failure cleanup wrong'
    }
    environment {
        $paths.Python = (Get-DevelopmentPaths).Python
        Set-Content -LiteralPath (Join-Path $Scratch '.env') -Value "RETRIEVAL_BACKEND=lexical`nRETRIEVAL_SHADOW_BACKEND=lexical`nAPI_BASE_URL=http://remote`nOLLAMA_HOST=http://remote`nLAUNCHER_FIXTURE=loaded"
        $env:RETRIEVAL_SHADOW_BACKEND = 'lexical'; $env:STREAMLIT_SERVER_ADDRESS = '0.0.0.0'
        Initialize-DevelopmentEnvironment $paths
        Assert ($env:RETRIEVAL_BACKEND -eq 'legacy' -and -not $env:RETRIEVAL_SHADOW_BACKEND) 'experimental settings inherited'
        Assert ($env:API_BASE_URL -eq 'http://127.0.0.1:8235' -and $env:OLLAMA_HOST -eq 'http://127.0.0.1:11434') 'remote settings inherited'
        Assert ($env:LAUNCHER_FIXTURE -eq 'loaded' -and $env:PYTHON_DOTENV_DISABLED -eq '1') 'dotenv configuration incorrect'
        Assert (-not $env:STREAMLIT_SERVER_ADDRESS) 'Streamlit inherited setting'
    }
    shortcut_conflict {
        # Test installer refusal entirely with mocked COM and a scratch Desktop.
        $source = Get-Content -Raw (Join-Path $PSScriptRoot 'Install-DesktopShortcuts.ps1')
        $source = $source.Replace(". (Join-Path `$PSScriptRoot 'Development.Common.ps1')", '')
        $source = $source.Replace('$PSScriptRoot', ("'" + $PSScriptRoot.Replace("'", "''") + "'"))
        $source = $source.Replace("[Environment]::GetFolderPath('DesktopDirectory')", "'$($Scratch.Replace("'", "''"))'")
        Set-Content -LiteralPath (Join-Path $Scratch 'Local AI Security Platform - Development.lnk') 'unrelated'
        function Assert-DevelopmentCheckout {}
        function New-Object {
            $mock = [pscustomobject]@{}
            $mock | Add-Member ScriptMethod CreateShortcut { param($Path); return [pscustomobject]@{ TargetPath = 'unrelated.cmd'; Arguments = '' } }
            return $mock
        }
        Expect-Failure { & ([scriptblock]::Create($source)) } '*Refusing to overwrite unrelated shortcut*'
        Assert ((Get-Content (Join-Path $Scratch 'Local AI Security Platform - Development.lnk')) -eq 'unrelated') 'shortcut overwritten'
    }
    default { throw "Unknown scenario: $Scenario" }
}
Write-Host "PASS: $Scenario"
