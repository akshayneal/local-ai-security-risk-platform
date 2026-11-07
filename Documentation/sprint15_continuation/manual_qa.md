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
