[CmdletBinding()]
param([switch]$NoBrowser)
. (Join-Path $PSScriptRoot 'Development.Common.ps1')
$lock = $null
$transcribing = $false
try {
    $paths = Get-DevelopmentPaths
    $head = Assert-DevelopmentCheckout $paths
    $lock = Enter-DevelopmentLock $paths
    Start-Transcript -Path (Join-Path $paths.Runtime 'launcher.log') -Append | Out-Null
    $transcribing = $true
    Assert-DevelopmentPython $paths
    Initialize-DevelopmentEnvironment $paths
    $env:PYTHONPATH = $paths.Root
    $state = Read-DevelopmentState $paths
    if ($state) { Update-DevelopmentChildren $paths $state }
    if ($state -and (Test-DevelopmentReady $paths $state)) {
        if ($state.commit -ne $head) { throw 'Running services use a different commit. Use Stop, then Start to load this checkout.' }
        Write-Host 'Development services are already healthy. Uncommitted edits require Stop then Start.'
        Initialize-DevelopmentOllama $paths
    } else {
        Stop-DevelopmentOwned $paths $state
        Assert-DevelopmentPortsFree
        Initialize-DevelopmentOllama $paths
        Start-DevelopmentServices $paths $head
    }
    Write-Host "API: http://127.0.0.1:8235 | Application: http://127.0.0.1:8535 | Ollama: http://127.0.0.1:11434"
    Write-Host "Logs: $($paths.Runtime)"
    if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8535' }
} catch {
    Write-Host "Development startup failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Inspect logs/development in the repository. No installation or model download was attempted.'
    exit 1
} finally {
    if ($transcribing) { Stop-Transcript | Out-Null }
    if ($lock) { $lock.Dispose() }
}
