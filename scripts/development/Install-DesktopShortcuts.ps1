[CmdletBinding()]
param()
. (Join-Path $PSScriptRoot 'Development.Common.ps1')
$paths = Get-DevelopmentPaths
Assert-DevelopmentCheckout $paths | Out-Null
$desktop = [Environment]::GetFolderPath('DesktopDirectory')
if (-not $desktop -or -not (Test-Path -LiteralPath $desktop -PathType Container)) { throw 'Windows Desktop known-folder path is unavailable.' }
$shell = New-Object -ComObject WScript.Shell
$plans = @(
    @{ Name = 'Local AI Security Platform - Development'; File = 'Start-Development.cmd' },
    @{ Name = 'Stop Local AI Security Platform - Development'; File = 'Stop-Development.cmd' }
)
# Validate both existing targets before writing either shortcut.
foreach ($plan in $plans) {
    $plan.Path = Join-Path $desktop ($plan.Name + '.lnk')
    $plan.Target = Join-Path $PSScriptRoot $plan.File
    if (-not (Test-Path -LiteralPath $plan.Target -PathType Leaf)) { throw "Missing launcher: $($plan.Target)" }
    if (Test-Path -LiteralPath $plan.Path) {
        $existing = $shell.CreateShortcut($plan.Path)
        if ($existing.TargetPath -ne $plan.Target -or $existing.Arguments) { throw "Refusing to overwrite unrelated shortcut: $($plan.Path)" }
    }
}
foreach ($plan in $plans) {
    $shortcut = $shell.CreateShortcut($plan.Path)
    $shortcut.TargetPath = $plan.Target
    $shortcut.WorkingDirectory = $paths.Root
    $shortcut.Description = $plan.Name
    $shortcut.Save()
    $verified = $shell.CreateShortcut($plan.Path)
    if (-not (Test-Path -LiteralPath $plan.Path) -or $verified.TargetPath -ne $plan.Target -or $verified.WorkingDirectory -ne $paths.Root) { throw "Shortcut verification failed: $($plan.Path)" }
    Write-Host "$($plan.Path) -> $($verified.TargetPath)"
}
