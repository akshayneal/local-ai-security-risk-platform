Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:DevelopmentCommands = @{
    api = '-m uvicorn app.main:app --host 127.0.0.1 --port 8235'
    ui = '-m streamlit run dashboard/streamlit_app.py --server.address 127.0.0.1 --server.port 8535 --server.headless true --browser.gatherUsageStats false'
}

function Get-DevelopmentPaths {
    $root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
    [pscustomobject]@{ Root = $root; Python = (Join-Path $root '.venv/Scripts/python.exe')
        Runtime = (Join-Path $root 'logs/development'); State = (Join-Path $root 'logs/development/processes.json') }
}

function Assert-DevelopmentCheckout($Paths) {
    $root = & git -C $Paths.Root rev-parse --show-toplevel
    if ($LASTEXITCODE -ne 0 -or [IO.Path]::GetFullPath($root) -ne $Paths.Root) { throw 'Launcher must be inside the development repository.' }
    & git -C $Paths.Root merge-base --is-ancestor d7348af17f054a0d4d2c96b8f7d1b2265a712d9c HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Checkout does not contain the verified development checkpoint d7348af.' }
    $branch = & git -C $Paths.Root branch --show-current
    if ($branch -eq 'main' -or -not $branch) { throw 'Use an attached development branch, not main or a detached release.' }
    $head = & git -C $Paths.Root rev-parse HEAD
    Write-Host "Development checkout: $branch @ $head ($($Paths.Root))"
    return $head
}

function Assert-DevelopmentPython($Paths) {
    if (-not (Test-Path -LiteralPath $Paths.Python -PathType Leaf)) { throw "Missing existing virtual environment: $($Paths.Python). No dependencies were installed." }
    & $Paths.Python -c 'import fastapi, uvicorn, streamlit, ollama, tenacity, pydantic, pandas, dotenv, requests, plotly, pypdf; import sys; assert sys.prefix != sys.base_prefix'
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment is invalid or a required Python module is missing. See the import error above; install project requirements manually.' }
}

function Enter-DevelopmentLock($Paths) {
    New-Item -ItemType Directory -Force -Path $Paths.Runtime | Out-Null
    try { return [IO.File]::Open((Join-Path $Paths.Runtime 'launcher.lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
    catch { throw 'Another development start/stop is in progress. Retry shortly.' }
}

function Get-DevelopmentProcess([int]$ProcessId) {
    $p = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction Stop
    if ($p) { return [pscustomobject]@{ id = [int]$p.ProcessId; parent = [int]$p.ParentProcessId
        created = $p.CreationDate.ToUniversalTime().ToString('o'); command = $p.CommandLine; executable = $p.ExecutablePath } }
}

function Test-DevelopmentOwned($Record) {
    $live = Get-DevelopmentProcess $Record.id
    return ($null -ne $live -and $live.created -ceq $Record.created -and
        $live.command -ceq $Record.command -and $live.executable -eq $Record.executable)
}

function Read-DevelopmentState($Paths) {
    if (-not (Test-Path -LiteralPath $Paths.State)) { return $null }
    $state = Get-Content -Raw -LiteralPath $Paths.State | ConvertFrom-Json
    if ($state.root -ne $Paths.Root -or $state.format -ne 1) { throw 'Unrecognized development ownership file; refusing process actions.' }
    foreach ($record in $state.records) {
        if ($record.service -notin @('api', 'ui') -or
            -not $record.command.EndsWith($script:DevelopmentCommands[$record.service], [StringComparison]::Ordinal) -or
            [IO.Path]::GetFileName($record.executable) -ne 'python.exe') { throw 'Invalid development process record; refusing process actions.' }
    }
    return $state
}

function Save-DevelopmentState($Paths, $State) {
    $temp = $Paths.State + '.tmp'
    $State | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $temp
    Move-Item -Force -LiteralPath $temp -Destination $Paths.State
}

function Update-DevelopmentChildren($Paths, $State) {
    # Discover only while a recorded parent is still verifiably alive. The Windows
    # venv redirector's child may use the base interpreter executable instead.
    foreach ($record in @($State.records)) {
        if (-not (Test-DevelopmentOwned $record)) { continue }
        $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $($record.id)")
        foreach ($child in $children) {
            $candidate = Get-DevelopmentProcess $child.ProcessId
            if ($candidate -and $candidate.id -notin @($State.records | ForEach-Object { $_.id }) -and
                $candidate.created -ge $record.created -and
                [IO.Path]::GetFileName($candidate.executable) -eq 'python.exe' -and
                $candidate.command.EndsWith($script:DevelopmentCommands[$record.service], [StringComparison]::Ordinal)) {
                $candidate | Add-Member NoteProperty service $record.service
                $State.records += $candidate
            }
        }
    }
    Save-DevelopmentState $Paths $State
}

function Stop-DevelopmentOwned($Paths, $State) {
    if (-not $State) { return }
    Update-DevelopmentChildren $Paths $State
    $refused = $false
    # Children first, then venv redirectors. Never kill a tree or a port owner.
    foreach ($record in @($State.records | Sort-Object created -Descending)) {
        if (Test-DevelopmentOwned $record) { Stop-Process -Id $record.id -ErrorAction Stop }
        elseif (Get-DevelopmentProcess $record.id) {
            Write-Warning "Refusing PID $($record.id): ownership no longer matches."
            $refused = $true
        }
    }
    if ($refused) { throw 'Some process identities could not be verified; ownership file retained.' }
    Remove-Item -LiteralPath $Paths.State -ErrorAction SilentlyContinue
}

function Get-DevelopmentListeners([int]$Port) {
    @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -eq $Port })
}

function Assert-DevelopmentPortsFree {
    foreach ($port in @(8235, 8535)) {
        if (@(Get-DevelopmentListeners $port).Count) { throw "Port $port is occupied. No unrelated process will be reused or terminated." }
    }
}

function Test-DevelopmentHttp([string]$Url) {
    try { return (Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2).StatusCode -eq 200 }
    catch { return $false }
}

function Test-DevelopmentReady($Paths, $State) {
    if (-not $State) { return $false }
    foreach ($service in @('api', 'ui')) {
        $port = if ($service -eq 'api') { 8235 } else { 8535 }
        $listeners = @(Get-DevelopmentListeners $port)
        if (-not $listeners.Count) { return $false }
        foreach ($listener in $listeners) {
            $owned = @($State.records | Where-Object { $_.service -eq $service -and $_.id -eq $listener.OwningProcess -and (Test-DevelopmentOwned $_) })
            if (-not $owned.Count -or $listener.LocalAddress -ne '127.0.0.1') { return $false }
        }
    }
    return ((Test-DevelopmentHttp 'http://127.0.0.1:8235/health') -and (Test-DevelopmentHttp 'http://127.0.0.1:8535/_stcore/health'))
}

function Initialize-DevelopmentEnvironment($Paths) {
    # Parse without executing .env, then prevent application load_dotenv calls
    # from restoring cleared experimental settings (empty values disappear in PS5).
    $settings = & $Paths.Python -c 'import json,sys; from dotenv import dotenv_values; print(json.dumps(dotenv_values(sys.argv[1])))' (Join-Path $Paths.Root '.env')
    if ($LASTEXITCODE -ne 0) { throw 'Could not read project .env settings.' }
    $decoded = $settings | ConvertFrom-Json
    foreach ($property in $decoded.PSObject.Properties) {
        if ($null -ne $property.Value) { [Environment]::SetEnvironmentVariable($property.Name, $property.Value, 'Process') }
    }
    $env:PYTHON_DOTENV_DISABLED = '1'
    Get-ChildItem Env: | Where-Object { $_.Name -like 'RETRIEVAL_*' -or $_.Name -like 'STREAMLIT_*' } | ForEach-Object { Remove-Item -LiteralPath ('Env:' + $_.Name) }
    $env:RETRIEVAL_BACKEND = 'legacy'
    $env:RETRIEVAL_SHADOW_BACKEND = ''
    $env:API_BASE_URL = 'http://127.0.0.1:8235'
    $env:OLLAMA_HOST = 'http://127.0.0.1:11434'
    $env:OLLAMA_MODEL = 'qwen3:8b'
    $env:NO_PROXY = '127.0.0.1,localhost'
}

function Assert-DevelopmentModel($Tags) {
    if ('qwen3:8b' -notin @($Tags.models | ForEach-Object { $_.name })) { throw 'Ollama model qwen3:8b is missing. Install it manually with: ollama pull qwen3:8b. Nothing was downloaded.' }
}

function Initialize-DevelopmentOllama($Paths) {
    $command = Get-Command ollama -ErrorAction SilentlyContinue
    if (-not $command) { throw 'Ollama executable is missing from PATH. Install Ollama locally and retry.' }
    if (-not (Test-DevelopmentHttp 'http://127.0.0.1:11434/api/tags')) {
        if (@(Get-DevelopmentListeners 11434).Count) { throw 'Port 11434 is occupied but Ollama is not healthy. Inspect its owner manually.' }
        $p = Start-Process -FilePath $command.Source -ArgumentList 'serve' -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $Paths.Runtime 'ollama.out.log') -RedirectStandardError (Join-Path $Paths.Runtime 'ollama.err.log')
        $record = Get-DevelopmentProcess $p.Id
        @{ started_by_launcher = $true; process = $record; policy = 'shared; never stopped automatically' } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $Paths.Runtime 'ollama.json')
        $deadline = (Get-Date).AddSeconds(30)
        while (-not (Test-DevelopmentHttp 'http://127.0.0.1:11434/api/tags')) {
            if ((Get-Date) -ge $deadline) { throw 'Local Ollama startup timed out. Inspect ollama.err.log.' }
            Start-Sleep -Milliseconds 500
        }
        Write-Host 'Started Ollama; left running as a shared service, including on failure.'
    } else { Write-Host 'Reusing user-managed/shared Ollama; it will not be stopped.' }
    Assert-DevelopmentModel (Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5)
}

function Start-DevelopmentServices($Paths, $Head) {
    $state = [pscustomobject]@{ format = 1; root = $Paths.Root; commit = $Head; records = @() }
    try {
        Assert-DevelopmentPortsFree
        foreach ($service in @('api', 'ui')) {
            $p = Start-Process -FilePath $Paths.Python -ArgumentList $script:DevelopmentCommands[$service] -WorkingDirectory $Paths.Root -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $Paths.Runtime "$service.out.log") -RedirectStandardError (Join-Path $Paths.Runtime "$service.err.log")
            $record = Get-DevelopmentProcess $p.Id
            if (-not $record) { throw "$service exited immediately. Inspect $service.err.log." }
            if ($record.executable -ne $Paths.Python -or -not $record.command.EndsWith($script:DevelopmentCommands[$service], [StringComparison]::Ordinal)) { throw "Cannot verify newly started $service process; refusing process actions." }
            $record | Add-Member NoteProperty service $service
            $state.records += $record
            Save-DevelopmentState $Paths $state
        }
        $deadline = (Get-Date).AddSeconds(60)
        do {
            Update-DevelopmentChildren $Paths $state
            if (Test-DevelopmentReady $Paths $state) { return }
            if ((Get-Date) -ge $deadline) { throw 'Application readiness timed out; inspect api.err.log and ui.err.log.' }
            Start-Sleep -Milliseconds 500
        } while ($true)
    } catch {
        $failure = $_
        Stop-DevelopmentOwned $Paths $state
        throw $failure
    }
}
