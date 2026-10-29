# Safety boundary: ONLY the marked, dedicated %LOCALAPPDATA% demo clone may be
# synchronized destructively. Never run checkout/reset/clean in the development repo.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:DemoRemote = 'https://github.com/akshayneal/local-ai-security-risk-platform.git'
$script:DemoApiPort = 8100
$script:DemoUiPort = 8510

function Get-DemoPaths {
    if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA is required on Windows.' }
    $root = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'LocalAISecurityRiskPlatformDemo'))
    [pscustomobject]@{
        Root = $root; Repo = (Join-Path $root 'repo'); Venv = (Join-Path $root 'venv')
        Logs = (Join-Path $root 'logs'); Runtime = (Join-Path $root 'runtime')
        Launcher = (Join-Path $root 'launcher'); Marker = (Join-Path $root 'demo-owned.txt')
    }
}

function Assert-DemoBoundary($Paths) {
    $expected = Get-DemoPaths
    foreach ($key in @('Root', 'Repo', 'Venv', 'Logs', 'Runtime', 'Launcher', 'Marker')) {
        if ($Paths.$key -cne $expected.$key) { throw "Unsafe demo path: $key" }
    }
    # Resolve every existing ancestor; junctions/symlinks must never redirect reset.
    $cursor = $Paths.Root
    while ($cursor) {
        if ((Test-Path -LiteralPath $cursor) -and
            ((Get-Item -Force -LiteralPath $cursor).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Demo path traverses a junction or symbolic link: $cursor"
        }
        $parent = Split-Path -Parent $cursor
        if ($parent -eq $cursor) { break }
        $cursor = $parent
    }
    foreach ($child in @($Paths.Repo, $Paths.Venv, $Paths.Runtime, $Paths.Logs, $Paths.Launcher)) {
        if ((Test-Path -LiteralPath $child) -and
            ((Get-Item -Force -LiteralPath $child).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Redirected demo directory: $child"
        }
    }
    $development = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')).TrimEnd('\')
    if ((Test-Path -LiteralPath (Join-Path $development '.git')) -and
        ($development -eq $Paths.Repo -or $development.StartsWith($Paths.Repo + '\', [StringComparison]::OrdinalIgnoreCase) -or
        $Paths.Repo.StartsWith($development + '\', [StringComparison]::OrdinalIgnoreCase))) {
        throw 'Demo and development checkout must be separate.'
    }
}

function Initialize-DemoRoot($Paths) {
    Assert-DemoBoundary $Paths
    if ((Test-Path -LiteralPath $Paths.Root) -and -not (Test-Path -LiteralPath $Paths.Marker)) {
        throw "Existing unmarked demo root; inspect it manually: $($Paths.Root)"
    }
    New-Item -ItemType Directory -Force -Path $Paths.Root | Out-Null
    if (-not (Test-Path -LiteralPath $Paths.Marker)) {
        Set-Content -LiteralPath $Paths.Marker -Value $script:DemoRemote
    }
    if ((Get-Content -Raw -LiteralPath $Paths.Marker).Trim() -ne $script:DemoRemote) {
        throw 'Demo ownership marker does not match this repository.'
    }
    foreach ($path in @($Paths.Logs, $Paths.Runtime, $Paths.Launcher)) {
        New-Item -ItemType Directory -Force -Path $path | Out-Null
    }
}

function Invoke-DemoGit($Paths, [string[]]$Arguments) {
    Assert-DemoBoundary $Paths
    $ErrorActionPreference = 'Continue' # Git progress on stderr is not a PowerShell exception.
    $output = & git -C $Paths.Repo @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($exitCode -ne 0) { throw "Demo Git failed: $output" }
    return @($output | ForEach-Object { $_.ToString() })
}

function Test-DemoFallback($Paths) {
    $ready = Join-Path $Paths.Runtime 'ready.json'
    if (-not (Test-Path -LiteralPath $ready)) { return $false }
    $state = Get-Content -Raw -LiteralPath $ready | ConvertFrom-Json
    $head = Invoke-DemoGit $Paths @('rev-parse', 'HEAD')
    return ($head -eq $state.commit -and (Test-Path (Join-Path $Paths.Repo 'app/main.py')))
}

function Sync-DemoRepository($Paths) {
    Get-Command git -ErrorAction Stop | Out-Null
    if (-not (Test-Path -LiteralPath $Paths.Repo)) {
        # Clone only main, directly into the verified dedicated destination.
        & git clone --branch main --single-branch $script:DemoRemote $Paths.Repo
        if ($LASTEXITCODE -ne 0) { throw 'First demo clone failed. Check GitHub access and retry.' }
    }
    $gitPath = Join-Path $Paths.Repo '.git'
    if (-not (Test-Path -LiteralPath $gitPath -PathType Container) -or
        ((Get-Item -Force -LiteralPath $gitPath).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'Demo must be a dedicated clone, not a worktree or redirected Git directory.'
    }
    if ((Invoke-DemoGit $Paths @('remote', 'get-url', 'origin')) -ne $script:DemoRemote) {
        throw 'Unexpected demo origin; synchronization refused.'
    }
    try {
        Invoke-DemoGit $Paths @('fetch', 'origin', 'main') | Out-Host
    } catch {
        if (-not (Test-DemoFallback $Paths)) { throw 'GitHub unavailable and no previously ready demo checkout exists.' }
        Write-Warning 'GitHub unavailable: using the last successfully synchronized and started demo.'
        return
    }
    # DESTRUCTIVE operations below are restricted to the marked dedicated clone.
    Invoke-DemoGit $Paths @('checkout', 'main') | Out-Host
    Invoke-DemoGit $Paths @('reset', '--hard', 'origin/main') | Out-Host
}

function Get-DemoDependencyHash($Paths) {
    $lock = Join-Path $Paths.Repo 'requirements-windows-py313.lock.txt'
    $direct = Join-Path $Paths.Repo 'requirements.txt'
    if (-not (Test-Path -LiteralPath $lock)) { throw 'Released Python 3.13 Windows snapshot is missing.' }
    return ((Get-FileHash -LiteralPath $lock -Algorithm SHA256).Hash + ':' +
        (Get-FileHash -LiteralPath $direct -Algorithm SHA256).Hash)
}

function Initialize-DemoPython($Paths) {
    Get-Command py -ErrorAction Stop | Out-Null
    $version = & py -3.13 -c 'import sys; print(sys.version_info.major,sys.version_info.minor,sep=chr(46))'
    if ($LASTEXITCODE -ne 0 -or $version -ne '3.13') { throw 'Install CPython 3.13 with the Windows py launcher, then retry.' }
    $python = Join-Path $Paths.Venv 'Scripts/python.exe'
    if (-not (Test-Path -LiteralPath $python)) {
        & py -3.13 -m venv $Paths.Venv
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the dedicated demo virtual environment.' }
    }
    $version = & $python -c 'import sys; print(sys.version_info.major,sys.version_info.minor,sep=chr(46))'
    if ($LASTEXITCODE -ne 0 -or $version -ne '3.13') { throw 'Demo venv is incompatible; inspect it before recreating it.' }
    $hash = Get-DemoDependencyHash $Paths
    $sentinel = Join-Path $Paths.Runtime 'dependencies.txt'
    if (-not (Test-Path -LiteralPath $sentinel) -or (Get-Content -Raw -LiteralPath $sentinel).Trim() -ne $hash) {
        & $python -m pip install -r (Join-Path $Paths.Repo 'requirements-windows-py313.lock.txt') | Out-Host
        if ($LASTEXITCODE -ne 0) { throw 'Demo dependency install failed; retry with network access. Logs are preserved.' }
        & $python -m pip check | Out-Host
        if ($LASTEXITCODE -ne 0) { throw 'Demo dependency validation failed.' }
        Set-Content -LiteralPath $sentinel -Value $hash
    }
    return $python
}

function Test-DemoHttp([string]$Url) {
    try { return (Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2).StatusCode -eq 200 }
    catch { return $false }
}

function Wait-DemoHttp([string]$Url, [int]$Seconds = 60) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        if (Test-DemoHttp $Url) { return }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    throw "Readiness timed out: $Url"
}

function Initialize-DemoOllama($Paths) {
    Get-Command ollama -ErrorAction Stop | Out-Null
    # Demo uses released defaults, independently of development environment variables.
    $env:OLLAMA_HOST = 'http://127.0.0.1:11434'
    $env:OLLAMA_MODEL = 'qwen3:8b'
    if (-not (Test-DemoHttp "$env:OLLAMA_HOST/api/tags")) {
        Write-Host 'Starting the shared local Ollama service (left running by Stop-Demo).'
        Start-Process ollama -ArgumentList 'serve' -WindowStyle Hidden `
            -RedirectStandardOutput (Join-Path $Paths.Logs 'ollama.out.log') `
            -RedirectStandardError (Join-Path $Paths.Logs 'ollama.err.log') | Out-Null
        Wait-DemoHttp "$env:OLLAMA_HOST/api/tags" 30
    }
    $tags = Invoke-RestMethod "$env:OLLAMA_HOST/api/tags" -TimeoutSec 5
    if ('qwen3:8b' -notin @($tags.models | ForEach-Object { $_.name })) {
        Write-Host 'First setup: pulling the released generation model qwen3:8b.'
        & ollama pull qwen3:8b
        if ($LASTEXITCODE -ne 0) { throw 'Could not pull qwen3:8b. Check Ollama/network access and retry.' }
    }
}

function Get-DemoProcessRecord([int]$ProcessId) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
    if (-not $process) { return $null }
    return [pscustomobject]@{
        process_id = $ProcessId; created = $process.CreationDate.ToUniversalTime().ToString('o')
        command = $process.CommandLine
    }
}

function Test-DemoOwnedProcess($Paths, $Record) {
    $live = Get-DemoProcessRecord $Record.process_id
    if (-not $live) { return $false }
    $python = Join-Path $Paths.Venv 'Scripts/python.exe'
    return ($live.created -eq $Record.created -and $live.command -ceq $Record.command -and
        $live.command.Contains($python) -and
        ($live.command -match '-m uvicorn app\.main:app .*--port 8100' -or
         $live.command -match '-m streamlit run dashboard/streamlit_app\.py .*--server.port 8510'))
}

function Get-DemoRecords($Paths) {
    $file = Join-Path $Paths.Runtime 'processes.json'
    if (-not (Test-Path -LiteralPath $file)) { return @() }
    return @(Get-Content -Raw -LiteralPath $file | ConvertFrom-Json)
}

function Stop-DemoOwnedProcesses($Paths) {
    Assert-DemoBoundary $Paths
    $records = @(Get-DemoRecords $Paths)
    foreach ($record in @($records)) {
        if (Test-DemoOwnedProcess $Paths $record) {
            Get-CimInstance Win32_Process -Filter "ParentProcessId = $($record.process_id)" | ForEach-Object {
                $child = Get-DemoProcessRecord $_.ProcessId
                if ($child -and (Test-DemoOwnedProcess $Paths $child)) { $records += $child }
            }
        }
    }
    foreach ($record in $records) {
        if (Test-DemoOwnedProcess $Paths $record) {
            Stop-Process -Id $record.process_id -ErrorAction SilentlyContinue
        }
    }
    $file = Join-Path $Paths.Runtime 'processes.json'
    if (Test-Path -LiteralPath $file) { Remove-Item -LiteralPath $file }
}

function Assert-DemoPortsFree {
    foreach ($port in @($script:DemoApiPort, $script:DemoUiPort)) {
        $listener = New-Object Net.Sockets.TcpListener ([Net.IPAddress]::Loopback), $port
        try { $listener.Start() } catch { throw "Port $port is occupied. Stop its owner or the demo; no unrelated process will be killed." }
        finally { $listener.Stop() }
    }
}

function Enter-DemoLock($Paths) {
    # FileShare.None is released by the OS even if a launcher crashes.
    try {
        return [IO.File]::Open((Join-Path $Paths.Runtime 'launcher.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
    } catch { throw 'Another demo start/stop is in progress. Retry shortly.' }
}
