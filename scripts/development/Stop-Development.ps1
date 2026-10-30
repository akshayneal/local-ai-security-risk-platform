[CmdletBinding()]
param()
. (Join-Path $PSScriptRoot 'Development.Common.ps1')
$lock = $null
try {
    $paths = Get-DevelopmentPaths
    $lock = Enter-DevelopmentLock $paths
    Stop-DevelopmentOwned $paths (Read-DevelopmentState $paths)
    Write-Host 'Stopped verified development API/UI processes. Shared Ollama remains running.'
} catch {
    Write-Host "Development stop failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally { if ($lock) { $lock.Dispose() } }
