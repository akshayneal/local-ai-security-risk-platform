# Manual native observation workflow QA

Status: **USER VISUAL QA PENDING**. Automated tests use TestClient and Streamlit's
in-process harness; no GUI inspection or service start was performed by Codex.
This development workflow is experimental and disabled by default. It sends no
model/embedding requests and performs no security action.

The existing development launcher still selects its original backend. The release
demo shortcut is unchanged. To use this separate experimental entrypoint, choose
unused local ports in two terminals at this checkout. Do not replace or stop an
existing service merely to reuse its port. These commands are user-run steps:

```powershell
$env:ENABLE_NATIVE_EVIDENCE_WORKFLOW = '1'
.\.venv\Scripts\python.exe -m uvicorn app.native_evidence_api:app --host 127.0.0.1 --port 8245
```

```powershell
$env:ENABLE_NATIVE_EVIDENCE_WORKFLOW = '1'
$env:API_BASE_URL = 'http://127.0.0.1:8245'
.\.venv\Scripts\python.exe -m streamlit run dashboard/streamlit_app.py --server.address 127.0.0.1 --server.port 8545
```

Open the displayed local Streamlit URL manually. Select **Native Evidence
(Experimental)**, load the synthetic network example, then select **Build native
observations**. Confirm the view shows the selected source row, original types,
SHA-256/revision, submitted-snapshot currentness, coverage and missing fields.
The comparator must show not executed, association not assessed and relationship
unassessable. A valid shape or ConnectionSuccess label is not completed access,
policy approval, transferred data or safety.

Download JSON and Markdown. Confirm both preserve the source and limitations;
Markdown must show annotation/HTML text as data. Change the selected row or source:
old downloads should disappear until a new explicit build. Refreshing or using a
download must not automatically submit a new request. Try a synthetic CSV upload
with leading-zero numeric text and confirm its original type remains string.

Repeat with the flag absent in both processes. The page should be absent and the
experimental POST route should return 404; established gateway routes retain
their behavior. If the page points to the original gateway, building must show
fixed experimental-endpoint guidance rather than a model result. Only HTTP(S)
loopback IP API addresses are accepted; redirects and environment proxies are
disabled by the observation client.

Uploads are unreviewed supplied observations. No request can grant source review,
current policy, authentication or permission. No actual source-review lifecycle
or synthetic authorization comparison is exposed here. Exports include the
original source; review them before sharing. Independent human semantic review
remains PENDING; RELEASE NO-GO.
