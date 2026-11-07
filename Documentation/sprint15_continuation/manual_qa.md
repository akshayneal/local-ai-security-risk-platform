# User-only investigation walkthrough

**USER VISUAL QA PENDING.** Automated TestClient/AppTest checks do not complete
visual or independent human review. This development slice is experimental,
default off, zero inference, and RELEASE NO-GO. Do not use the release demo or
change either launcher to try it.

From this checkout, use two foreground PowerShell terminals. First check the
suggested ports without stopping any owner:

```powershell
Get-NetTCPConnection -State Listen -LocalPort 8245,8545 -ErrorAction SilentlyContinue
```

If occupied, choose two unused loopback ports and adjust both commands. Terminal 1:

```powershell
$env:ENABLE_NATIVE_EVIDENCE_WORKFLOW = '1'
.\.venv\Scripts\python.exe -m uvicorn app.native_evidence_api:app --host 127.0.0.1 --port 8245
```

Terminal 2:

```powershell
$env:ENABLE_NATIVE_EVIDENCE_WORKFLOW = '1'
$env:API_BASE_URL = 'http://127.0.0.1:8245'
.\.venv\Scripts\python.exe -m streamlit run dashboard/streamlit_app.py --server.address 127.0.0.1 --server.port 8545
```

Open the displayed UI URL manually. Ollama can be unavailable for all native
checks. Do not stop a shared Ollama/service to demonstrate independence.

1. Open **Native Evidence (Experimental)**. Original **Source observations**
   remains available. Choose **Native Evidence Investigation**, load the synthetic
   network example, and inspect the subject-row preview. Nothing is sent until
   **Build investigation report**.
2. Build row 0 for the reported-event question. The snapshot reports the original
   timestamp, device, process, account and local/remote endpoint fields. Expand
   field details for exact JSON types, normalized values, shape states and paths.
   A familiar ActionType remains an unverified label; port 443 does not mean HTTPS.
3. Compare row representations. The two supplied rows reuse a PID with different
   creation times. No process/event join, threat determination or contradiction
   about one real event is established. Missing data stays unknown.
4. Choose the application-access question; old downloads disappear. Build again.
   Read the application/server-record question and explicit insufficient-evidence
   statement. Repeat for blocking: ConnectionSuccess is not protection allow;
   seek relevant disposition records separately. DeviceEvents is not an accepted
   table in this profile. Policy authorization must remain unavailable.
5. Download investigation JSON and Markdown. Compare their selected row, question,
   source SHA-256 and exact source with the input. The JSON retains original bytes
   as UTF-8 source text, all rows, fields and types. Markdown is readable and
   escaped, with the original observation appendix. Review exports before sharing.
6. Refresh, expand details and download again: no automatic build should occur.
   Change selected row, source, question or report view: old downloads disappear
   until another explicit build. Invalid replacements must withhold old reports.
7. Try a synthetic CSV with CRLF rows and `RemotePort` cell `00443`: original type
   stays string and normalized port is 443. Try a malformed timestamp and a JSON
   boolean port: they remain invalid/unknown, without borrowing another row's field.
8. Add synthetic duplicate rows and a source-body `approved: true` or HTML annotation.
   Duplicates remain visible; annotations display as data; approval stays false,
   comparator not executed, association not assessed. Inspect light/dark themes,
   small windows, section hierarchy and download readability yourself.

Stop only the two foreground processes you started (Ctrl+C in those terminals).
For default-off QA, remove the native flag in those terminals before restarting:
`Remove-Item Env:ENABLE_NATIVE_EVIDENCE_WORKFLOW -ErrorAction SilentlyContinue`.
The page should be absent and both experimental POST routes return 404. Original
gateway routes remain available. Record your observations separately using the
blank reviewer form; no automated result certifies the telemetry or model safety.

## Optional lifecycle QA (separate, bounded user procedure)

Codex used **zero model sends**. The automated mocked lifecycle tests are the
first check; they need no provider, long sleep or service change:

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/test_inference_lifecycle.py tests/test_lifecycle_dashboard.py -q
```

To inspect the opt-in UI yourself, use unused ports and the same two foreground
terminals as above, replacing the API entrypoint with `app.lifecycle_api:app`.
Set these process variables in **both** terminals before starting them:

```powershell
$env:ENABLE_INFERENCE_LIFECYCLE = '1'
$env:ANALYSIS_BUDGET_SECONDS = '900'
$env:ANALYSIS_CONNECT_SECONDS = '5'
$env:ANALYSIS_READ_SECONDS = '900'
$env:ANALYSIS_UI_MARGIN_SECONDS = '30'
```

Keep the native flag if checking native reports too. The lifecycle gateway mounts
the native gateway and the original routes; the launchers remain unchanged.
Use one API worker: metadata/duplicate suppression are process-local.

The lifecycle notice should appear on **generic SOC** and **AI System Risk
Review**. Microsoft upload and AI Security UI retain legacy transport; the notice
states that limitation. These pages do not gain cancellation or durable recovery.
No model call is needed merely to inspect navigation, input forms and notices.

If deliberately choosing a runtime smoke check later, use **one fictional generic
SOC sample, one click, at most two raw generations including repair**. Verify no
inherited evaluation is active and use the existing provider without any restart,
pull or configuration change. Do not test by repeatedly submitting while a prior
request might still run. This is a future user-run check, not a completed sprint
evaluation or automatic diagnostic.

After a timeout/disconnect, inspect the attempt ID and use **Check analysis attempt
status**. Rerun within the same active Streamlit session, change inputs, load a
sample and switch SOC/AI Risk pages: the guard in those workspaces must remain
until an explicit decision. Full browser reload, a new session/tab or server
restart can lose session state; record the attempt ID before leaving. There is
no cross-session duplicate prevention. A completed
status with a lost reply cannot recover the result. Missing status/Activity does
not prove no dispatch. Read the warning before explicitly acknowledging a fresh
request; that acknowledgment does not stop the old request. Prefer recording the
finding and ending the check rather than generating overlapping work.

The default is a 900-second cooperative elapsed budget and 30-second UI margin.
Socket timeouts limit inactivity; they cannot guarantee a hard wall-clock stop or
provider cancellation. Slow reads may outlive the target. Status records contain
metadata only and at most 64 retained entries; restart/eviction loses history,
and unresolved running/unknown records can fill the registry. Do not clear status
or restart a process as proof that provider work has stopped.

Stop only your own foreground processes when finished. Remove the lifecycle flag
before restarting to verify the extra routes are absent. Report actual runtime
send counts and visual findings separately; preparing these instructions is not
successful runtime or visual validation.
