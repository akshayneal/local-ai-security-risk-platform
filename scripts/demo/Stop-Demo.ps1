[CmdletBinding()]
param()
. (Join-Path $PSScriptRoot 'Demo.Common.ps1')
$paths = Get-DemoPaths
Assert-DemoBoundary $paths
if (-not (Test-Path -LiteralPath $paths.Runtime)) { return }
$lock = Enter-DemoLock $paths
try {
    Stop-DemoOwnedProcesses $paths
    Write-Host 'Stopped verified demo API/UI processes. Shared Ollama service remains available.'
} finally { $lock.Dispose() }
