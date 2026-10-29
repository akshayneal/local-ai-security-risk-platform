# Isolated released demo (Windows)

Install CPython 3.13 including the `py` launcher, Git and Ollama first. No admin
rights, global Python packages or development virtual environment are used.

From the expansion checkout, install the desktop shortcuts once:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo/Install-DemoShortcut.ps1
```

Click **Local AI Security Risk Platform - Demo**. First startup clones remote
`main`, creates its own environment using the released Windows snapshot, runs
`pip check`, checks Ollama and pulls only `qwen3:8b` if missing. The UI opens after
bounded API/UI readiness checks. First setup needs network access. No analysis is
submitted automatically. **Stop Local AI Security Demo** stops verified owned
API/UI processes; shared Ollama is intentionally left available for development.

Layout: `%LOCALAPPDATA%\LocalAISecurityRiskPlatformDemo\` contains `repo`, `venv`,
`logs`, `runtime`, `launcher` and `demo-owned.txt`. The copied launcher is independent
of the development checkout and survives branch changes. Reinstall shortcuts to
update launcher scripts; application code always comes from remote `main`, never
from this experimental branch. Version remains 2.3.0 for the current release.

**Only the ownership-marked dedicated clone is disposable.** The launcher validates
fixed paths, checks Git origin, rejects worktrees/junctions/symlinks and restricts
checkout/reset to that clone. It never resets, switches or cleans the development
checkout. Do not put personal files or make edits inside the demo clone.

Each fresh launch fetches `origin/main`; a fetch failure may use the exact commit
recorded after a previous successful startup. Without that ready checkout startup
fails with an actionable message. Dependency hashes cover both manifests; unchanged
hashes reuse the environment without pip/network. Changed hashes trigger installation
into a separate `venv/environments/<dependency-key>` and `pip check`; failed updates
never advance the selected-environment sentinel or modify the prior environment. The
original smoke-created `venv` is reused while its hashes match. An incompatible
venv is refused. Changed dependencies cannot be installed offline unless cached.

Ports are loopback-only API **8100**, UI **8510**, Ollama **11434**. The Streamlit
process receives `API_BASE_URL=http://127.0.0.1:8100`. Two clicks open an existing
healthy demo, and a launch lock prevents concurrent bootstrap/stop races. Occupied
ports never cause unrelated processes to be killed. PID records include creation
time and exact command line; stop rechecks both plus the demo Python/module/port.
This is local process ownership protection, not an authentication boundary against
another process running as the same Windows user.

Inspect logs under `logs` (`launcher.log`, `api.*.log`, `ui.*.log`). A failed startup
stops verified partial services and preserves logs. Run status without starting:

```powershell
powershell -NoProfile -File scripts/demo/Start-Demo.ps1 -Status
powershell -NoProfile -File scripts/demo/Start-Demo.ps1 -NoBrowser
powershell -NoProfile -File scripts/demo/Stop-Demo.ps1
```

The demo sets the released generation defaults explicitly and does not require any
experimental embedding model. Ollama must be installed already; if needed its shared
local service is started in a hidden window. No privileged installation is attempted.

## Sprint smoke evidence

On 2026-10-28, one Windows startup/stop smoke created the dedicated clone and
CPython 3.13 environment, installed the exact released snapshot, passed `pip check`,
and reached both readiness endpoints at release commit `fde00d0` / version 2.3.0.
An initial bootstrap quoting defect was corrected before services started. A second
click reused the healthy services. Status verified owned processes, and stop removed
both listening ports. No qwen inference was performed. The smoke used `-NoBrowser`
to avoid opening an interactive tab during automation; automatic browser launch is
implemented but was not visually inspected. Offline fallback is helper-tested,
not validated by deliberately disconnecting this computer from its network.
