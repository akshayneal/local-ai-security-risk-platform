@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Stop-Development.ps1"
if errorlevel 1 (
  echo Development stop failed. See the message above.
  pause
  exit /b 1
)
