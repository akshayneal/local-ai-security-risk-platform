# Early Sprint 15 native observation workflow

**Scoped early milestone implemented; experimental and disabled by default.**
RELEASE NO-GO. INDEPENDENT HUMAN REVIEW PENDING (0 verified).
USER VISUAL QA PENDING. Model/embedding sends: zero. No inference performance or
model reasoning accuracy was measured.

## Branch and milestone boundary

This branch, `feature/native-evidence-workflow-sprint15`, starts from finalized14B
`a9af4bdc63478c63f10ee4a194d8fe07bec0886f`. It retains all14B work in history.
14B is COMPLETE:2924 fulltests,322-fileRuff,dependency/diff/preservation checks,
one ten-case mini-diagnostic matching10/10 authored expectations, and exact-SHA CI
[42347233153](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/42347233153)
succeeded with test/Ruff steps. Original Sprint14N2A6 remains11/12; neither old
diagnostic was rerun or rescored. New authored matches are not independent review.

Early15 prospective plan: `07562f9`; typed native core: `78a4be8`; actual gated
API/UI integration: `4b67025`. Final commit/origin/CI identity is resolved in the
session handoff after the final normal push. Git retains exact full commit IDs.
Main, v2.3.0, released demo, existing gateway/navigation definitions and both
launcher source trees remain unchanged.

## Native progress and honest semantic boundary

The new useful result is a typed, traceable native observation, not an invented
operation/outcome mapping. It accepts one selected DeviceNetworkEvents row in
the existing supported projected JSON/CSV profile, retains the whole supplied
bundle and reports what is known about each selected field's representation.

Public [Microsoft table documentation](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-devicenetworkevents-table)
describes network telemetry and literal fields, while detailed ActionType values
are delegated to portal documentation. Microsoft also describes a
[ConnectionSuccess event before handshake completion and subsequent blocking](https://learn.microsoft.com/en-us/defender-endpoint/network-protection#network-protection-and-the-tcp-three-way-handshake).
These public sources were rechecked November7 without login/GUI. They do not
justify transfer completion, permission, compromise or control effectiveness.

Decision remains **MORE_EVIDENCE_REQUIRED** for stronger native semantics.
`reported_event_class=supplied_DeviceNetworkEvents_row` names the supplied table
shape. ActionType and ResultType remain literal unverified vendor assertions.
LocalIP/RemoteIP retain their roles; port443 does not become HTTPS. No cross-row
process association, ATT&CK mapping, severity assessment or security action occurs.

The [mapping contract](native_evidence_workflow_v1/source_mapping.md) defines:

- Original UTF8/BOM/CRLF, all rows/fields/types, separate canonical bundle and
  table/row/field pointers retained. Selected and other-row coverage are explicit.
- Shape states valid/absent/invalid/unverified, with originals beside explicit
  UTC/IP/numeric normalization. Shape validity never means source truth.
- Duplicate rows and reused PID observations retained; no deduplicated causal join.
- Unknown labels, opaque ResultType, misleading Severity and authority-like source
  fields retained as data. They cannot supply approval/currentness or permission.
- Malformed/absent timestamps, timezone normalization overflow, strict boolean/
  integer distinctions, CSV leading zeroes and invalid selected rows handled
  without silent correction or fallback.

## Source identity and authority

An upload receives application-derived byte-hash locators and a request binding
that includes format, selected row and CSV context. These are correlation aids,
not authenticated source/event identity or anonymization. Currentness is only
`submitted_snapshot_only`; external currentness is unchecked. Authority is
`observation_only`, review status `not_reviewed`, source `supplied_unverified`.

An ordinary request cannot provide SourceReview, approved/current flags, source ID,
policy scope or permission metadata. No fake public_synthetic approved review is
manufactured. This observation-only path stays below the eligibility boundary for
the separate synthetic authorization comparator. It does not establish enterprise
IAM, an institutional policy review or a real operator's approval.

Every report fixes comparator execution to **not_executed,0calls**, association to
**not_assessed**, relationship to **unassessable**, and the reason to
**native_semantics_unverified**. Approval is false; no actions execute. The14B
internal contract separately represents completed comparison plus underdetermined;
this native upload cannot force that computation by claiming it was authorized.

## Actual development API and UI

New explicit ASGI entrypoint: `app.native_evidence_api:app`. With process-owned
`ENABLE_NATIVE_EVIDENCE_WORKFLOW=1`, it exposes POST
`/experimental/native-evidence`; otherwise that path is404, even before parsing
its body. It mounts the unchanged prior gateway, preserving existing routes/docs.
No request/query can enable the feature. This flag is feature exposure, not IAM.

The same flag adds **Native Evidence (Experimental)** to a copied Streamlit
navigation map. The page offers a synthetic sample, paste/uploadJSON/CSV, row
selection, explicit Build button, source-linked typed observations, limitations,
coverage and two downloads. Source content is rendered as text/JSON, never HTML
instructions. Old results/downloads disappear when current input changes or fails.
Rerunning or downloading does not automatically submit a new request.

The standard development launcher still selects its existing backend; it does
not automatically enable this experimental composition. The release demo shortcut
is untouched. [Manual QA instructions](native_evidence_workflow_v1/manual_qa.md)
give two explicit foreground commands on unused local ports8245/8545. Codex did
not start those services, open a browser or inspect the visible UI.

The route enforces400,000 outer wire bytes,64,000 original UTF8 bytes and existing
parser row/field/depth/canonical limits. Duplicate keys, malformed encodings,
request-owned review metadata and unsafe types receive fixed sanitized errors.
The complete encoded response is capped at4,000,000bytes. No raw telemetry is
written to audit logs by this new route.

The dedicated client accepts literal loopback IP HTTP(S) addresses, disables
environment proxies/netrc and redirects, streams a bounded response and retries
zero times. Its3s connect/15s read settings are inactivity limits, not a total
deadline or cancellation guarantee. Before display/download it reconstructs the
report and both exports from the exact request. Saved session data is revalidated
again against current widgets on every render.

## Acceptance and validation

The actual selected ASGI route was exercised through FastAPI TestClient with the
synthetic sample. It returned200, retained both original rows and source hash,
selected one row, showed comparator not executed and produced JSON/escapedMarkdown.
The [saved acceptance record](native_evidence_workflow_v1/acceptance_result.json)
and adjacent example files retain that source-bound output.

Tests also forward the actual client through TestClient into Streamlit AppTest:
load sample→Build→render→two downloads, with no automatic repeat, and CSV strings
preserved. Forged report/export/session snapshots are withheld. A request cannot
grant review metadata; source-body permission/injection text stays untrusted data.
This is executable software evidence, not completed human visual QA.

Focused final new-core/API/UI/product/preservation checks: **146passed,1existing
warning,19.31seconds**. Existing dashboard/Microsoft/API compatibility:41passed.
Ruff passes336trackedPython files; pip check passes. Final full-suite result:
**3070passed,1existingwarning,325.79seconds** on the existing CPython3.13.1venv.
Complete-feature diffcheck and795original-blob/990raw-file preservation pass.
No Python source changed after the tested integration commit4b67025.

Broader ECS/OCSF normalization was considered as a design alternative and deferred;
renaming fields would not supply the missing vendor action semantics. No framework
conformance or cross-schema semantic mapping is claimed.

No new frozen diagnostic was needed for this software integration. Both earlier
one-run diagnostics remain unchanged. No independent reviewer identities,
judgments or confidence percentages were invented.

The new baseline freezes final14B source/data. **795original blobs and990rawfiles**
remain protected, with two exact authorized existing paths: functional default-off
Streamlit entrypoint addition and the immediate14Bscope-test import/decorator.
The original assertion replays at immutable14B; actual mutation proofs distinguish
old-guard protected main from the new guard's protection of v2. Both v1/v2 modules,
frozen cases/keys/scorers/journals/results and all405 visible/185ignored private
s4check files are preserved. Private source was never opened or executed.

## Code-level teaching and remaining work

`NativeObservationRequest` uses strict Pydantic fields and validators to bound
shape/bytes and reject caller-owned authority. `build_report` preserves originals
beside normalized representations. A content hash identifies bytes; the request
fingerprint additionally identifies which row/context was selected. These contracts
make accidental type changes and stale response reuse detectable, not sources true.

`export_json`, `export_markdown` and `validate_response` recompute deterministic
results and compare type-sensitive serialized values. `create_app` gates a new
route without changing the old app; `navigation_groups` copies existing page
definitions. This keeps an experiment usable while preserving default behavior.

Supporting model-request lifecycle work is **DEFERRED after audit**. Existing
frontend/model300s inactivity limits, uncertain post-send retry and possible SOC
repair remain unchanged. There is no request identity/completion lookup or provider
cancellation guarantee in those old routes. A real monotonic budget plus unknown
outcome/nonretry contract would need a separately scoped transport change preserving
historical send accounting. Raising literals or adding a speculative queue would
not establish it. No scheduler, worker or service change was introduced.

Next fullSprint15 priorities: actual user visual QA of the documented page; genuine
independent semantic review; reviewed vendor/version/protocol evidence before any
native completion predicate; application-owned review/currentness lifecycle before
real permission comparison; then a bounded model request-ID/deadline/unknown-outcome
design with mocked transport. Release remains NO-GO.
