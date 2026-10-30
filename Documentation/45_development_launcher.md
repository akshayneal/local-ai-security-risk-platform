# Current development launcher (Windows)

Double-click **Local AI Security Platform - Development** on your Desktop.
The launcher runs this checkout's current development source, including the
SOC/Microsoft telemetry workflows, AI System Risk Review, experimental AI Security Assessment, Evidence Inspector,
corrections/history, field anchors and correction-first exports. It prints the
branch and Git SHA; the application may still display version 2.3.0.
It never updates Git or uses the separate released v2.3.0 demo clone.
The canonical development ASGI entrypoint is `app.ai_security_api:app`, which
composes the original routes with `/ui/analyze/ai-security`. `app.main:app` remains
the compatible two-workflow backend; the released demo launcher is unchanged.

- Application: http://127.0.0.1:8535
- FastAPI: http://127.0.0.1:8235
- Ollama: http://127.0.0.1:11434 (model `qwen3:8b`)

Prerequisites: Windows PowerShell 5.1, Git, this development checkout containing
checkpoint `d7348af`, an existing `.venv` with the project requirements installed,
and Ollama on PATH with `qwen3:8b` already installed. Nothing is installed or
downloaded automatically. Existing `.env` settings load normally; process-local
overrides enforce loopback connections, `qwen3:8b`, legacy retrieval and no shadow
retrieval. No persistent environment settings are changed.

Use **Stop Local AI Security Platform - Development** to stop verified launcher
API/UI processes. Ollama is shared and remains running, even if this launcher
started it. Closing the browser does not stop services. Repeated Start reuses
healthy owned services; after changing source, use Stop then Start.
Unrelated port owners are never reused or terminated. Changed/unverifiable
process identities cause refusal, with an explanation.

After upgrading from the two-workflow launcher, Start refuses legacy ownership
state before stopping or reusing any process. Use the existing Stop shortcut
(or the command below), then Start. Stop accepts only the exact old known API
command or the current gateway command, with the same recorded/live executable,
creation time, parent and argument checks. An unrelated port owner or changed
identity is refused; inspect it manually rather than deleting ownership records.
Neither shortcut target nor development port changed. This migration was tested
with mocks; actual shortcut/workflow acceptance remains user-only.

```powershell
.\scripts\development\Stop-Development.cmd
.\scripts\development\Start-Development.cmd
```

Logs and ownership files are under `logs/development/` (ignored by Git).
Startup logs append to `launcher.log`; service output/error logs are replaced on
the next service start. Failed double-click launches keep the terminal open with
a readable error. Read the relevant `*.err.log` for dependency/startup failures.
Health waits are bounded; partially started owned API/UI processes are stopped.

Recreate the two shortcuts from a repository PowerShell terminal:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\development\Install-DesktopShortcuts.ps1
```

The installer uses the Windows Desktop known folder (including OneDrive
redirection) and refuses to replace shortcuts targeting unrelated files.
For a manual terminal launch without opening a browser, pass `-NoBrowser` to
`Start-Development.ps1`. Automated tests use mocks and start no real services.
**USER VISUAL QA PENDING:** perform the final Start/Stop double-click test locally.
See [Sprint 7 readout and acceptance steps](51_cross_pillar_rc_readout.md).
