@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Development.ps1" %*
if errorlevel 1 (
  echo Development startup failed. See the message above.
  pause
  exit /b 1
)
