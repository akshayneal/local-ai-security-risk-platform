[CmdletBinding()]
param()
. (Join-Path $PSScriptRoot 'Demo.Common.ps1')
$paths = Get-DemoPaths
Initialize-DemoRoot $paths
$lock = Enter-DemoLock $paths
try {
    # Copy bootstrap out of development: future shortcut launches never depend on it.
    foreach ($name in @('Demo.Common.ps1', 'Start-Demo.ps1', 'Stop-Demo.ps1')) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $paths.Launcher $name) -Force
    }
    $shell = New-Object -ComObject WScript.Shell
    $desktop = [Environment]::GetFolderPath('Desktop')
    foreach ($item in @(
        @{ Name = 'Local AI Security Risk Platform - Demo'; Script = 'Start-Demo.ps1' },
        @{ Name = 'Stop Local AI Security Demo'; Script = 'Stop-Demo.ps1' }
    )) {
        $shortcut = $shell.CreateShortcut((Join-Path $desktop ($item.Name + '.lnk')))
        $shortcut.TargetPath = Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'
        $shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + (Join-Path $paths.Launcher $item.Script) + '"'
        $shortcut.WorkingDirectory = $paths.Root
        $shortcut.Description = 'Isolated released main demo; development checkout is never synchronized.'
        $shortcut.Save()
    }
    Write-Host "Desktop shortcuts installed. Bootstrap: $($paths.Launcher)"
} finally { $lock.Dispose() }
