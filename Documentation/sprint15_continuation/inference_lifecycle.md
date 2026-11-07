# Experimental analysis request lifecycle

Implemented, default off. This is a bounded safety improvement for the original
SOC and AI System Risk analyzers, not a queue, cancellation API, result recovery
service or durable exactly-once guarantee. Native Evidence Investigation remains
deterministic and makes zero model/embedding sends. Actual local inference sends
for this continuation: **0**; all lifecycle tests use synthetic mocked transport
and clocks. Historical one-use evaluations were not rerun or rescored.

## Causal review of existing execution

The reviewed source is the early Sprint 15 tip
`9be773070f2176d40e3e80beccf65feaefdc03c0`. Relevant sources are
`app/ollama_client.py`, `app/inference_context.py`, `app/model_metrics.py`,
`app/main.py`, both analyzers, `app/ai_security_api.py`, and
`dashboard/api_client.py`. The existing focused/frozen tests in
`test_complete_context.py`, `test_product_helpers.py`, `test_io_boundary.py`,
`test_controlled_inference_evaluation.py` and `test_cross_pillar_evaluation.py`
remain intact.

| Path | Dispatch, failure and retry behavior | Maximum generation POSTs |
| --- | --- | --- |
| Legacy complete-context HTTP | Version GET (10-second inactivity timeout), then chat POST (300-second inactivity timeout), local/no proxies/no redirects. Tenacity permits two attempts for ordinary runtime/transport/JSON errors. Version GET repeats on retry and repair. `EvidenceBudgetError` stops retry for unsupported runtime, explicit request rejection, incomplete generation and length stop. | SOC 4; governance 2; AI Security 2 |
| Legacy generic SDK | `Client.chat`; installed Ollama SDK's `BaseClient` defaults are `timeout=None` and `follow_redirects=True`. No explicit SDK timeout is set here. Tenacity permits two attempts for ordinary errors. | SOC 4; governance 2; AI Security normally uses protected complete-context mode, maximum 2 |
| Legacy UI | One POST with 300-second inactivity timeout; no client retry. Timeout does not cancel backend work. Connection errors cannot establish whether a dispatch happened. | Does not change provider maxima |
| New lifecycle HTTP | One dispatch per logical generation, bounded response bytes, no automatic transport/parse/callback retry. Complete-context mode retains version preflight plus `truncate=False`, `shift=False`, configured context and trusted workflow instructions. Generic lifecycle mode deliberately uses this HTTP transport instead of SDK. | SOC 2 (initial + existing one repair); governance 1 |

An HTTP attempt is a conservative dispatch reservation made immediately before
`session.post`; a connection error after reservation counts one raw send and
remains uncertain. A version GET is not an inference send. Existing model metrics
still record logical attempts/usage without prompts; they are not a replacement
for the explicit raw-send counter. A completed invalid JSON object may receive the
existing SOC schema/policy repair. Transport failure, malformed JSON text,
incomplete output, a callback error or an exhausted elapsed budget never triggers
an automatic retry. No AI Security lifecycle route or UI opt-in is implemented;
its existing path remains unchanged.

## Contract and budget

The separate foreground composition is `app.lifecycle_api:app`; it mounts the
existing native gateway and original public routes. It adds these routes only
when `ENABLE_INFERENCE_LIFECYCLE=1`:

- POST `/experimental/analysis-lifecycle/v1/analyze/soc-alert`
- POST `/experimental/analysis-lifecycle/v1/analyze/governance`
- GET `/experimental/analysis-lifecycle/v1/status/{attempt_id}`

POST bodies are the unchanged `UiSocRequest` / `UiGovernanceRequest`. Extra fields
cannot grant budgets, source authority or policy permission. Each POST requires
`X-Analysis-Attempt-ID`, a canonical UUID generated before the client dispatch.
It is a correlation identifier, not authentication. A success is
`analysis-lifecycle-response/1`, containing `execution` metadata and the original
validated UI envelope under `result`. Withholding returns fixed errors and
execution metadata without a result. Existing Inspector collection, source
sanitization, correction-first UI exports, audit and bounded SOC repair remain in
their original functions. The validated original result is serialized and capped
at 4,000,000 bytes before completion is recorded. Provider-envelope and model JSON
reject duplicate keys/nonfinite numbers on the new transport. No production route
was rewritten.

| Local-process environment variable | Default | Allowed integer seconds |
| --- | --- | --- |
| `ANALYSIS_BUDGET_SECONDS` | 900 | 30–1200 |
| `ANALYSIS_CONNECT_SECONDS` | 5 | 1–30, at most total budget |
| `ANALYSIS_READ_SECONDS` | 900 | 1–1200, at most total budget |
| `ANALYSIS_UI_MARGIN_SECONDS` | 30 | 5–120 |

The default UI wait is 930 seconds (total budget plus margin). Each provider
connect/read limit is also capped at the remaining monotonic budget. Preflight
read inactivity is capped at ten seconds. Monotonic time measures elapsed time
without depending on wall-clock adjustments. The budget is checked before
preflight, dispatch, repair, between response reads, after decoding and before
returning validated output. A response arriving after the budget is withheld.

**These are cooperative elapsed checks and socket inactivity timeouts.** They
cannot interrupt a blocked read, prevent a slow stream/header from exceeding the
elapsed target, or cancel already-dispatched Ollama work. A full late response
that was not decoded before expiry remains conservatively unknown; a previously
confirmed complete response whose later validation exhausts the budget fails
known with no result. The UI wait margin reduces accidental early timeout; it is
not a hard wall-clock guarantee and does not create cancellation.

## States, duplicate suppression and retention

| State | Meaning |
| --- | --- |
| `running` | The gateway has reserved this ID and has not finished its synchronous call. |
| `completed_validated` | The original UI result passed its application contracts within budget; semantic truth is not established. |
| `rejected_before_dispatch` | No provider POST reservation occurred on this attempt. |
| `failed_known` | A complete response or explicit provider rejection was observed, but the application withheld the final result. |
| `unknown_post_dispatch` | A POST was attempted and completion could not be confirmed. Timeout/disconnect does not establish that work stopped. |

The process-local registry holds at most 64 metadata entries: UUID, state,
raw-send count, reason, elapsed time and configured budget. It stores no raw
telemetry, prompt, model output or recoverable result. Existing audit behavior
remains separate. A retained UUID cannot dispatch twice, including across the two
new routes. Running and uncertain entries are not evicted. Completed/known-failed/
predispatch entries may be evicted in insertion order. If all entries are running
or uncertain, new requests fail closed before dispatch. No automatic clearing,
worker, scheduler or service restart occurs.

Missing status, eviction, a different process, multiple server workers or restart
remove this limited duplicate-suppression evidence. They never prove that earlier
inference did not run. Use a single explicitly started foreground API process.
The registry is not persistent idempotency, authentication or cancellation. If
it saturates with unresolved attempts, the user must investigate the existing
provider work and decide how to manage their own foreground processes. Resetting
the application cannot prove provider completion.

The UI retains an uncertain submission through script reruns within the same
active Streamlit session and blocks another send until an explicit user decision.
A browser/WebSocket reload, new tab or UI restart may lose that session guard;
there is no cross-session duplicate prevention. Manual status lookup does not
rerun inference or recover a lost result. A completed status still requires an
explicit decision before another send because its result may have been lost.

## Validation and remaining limits

`tests/test_inference_lifecycle.py` covers mocked slow completion, preflight and
POST failure, cooperative elapsed exhaustion, complete-output repair, raw-send
caps, callback failures, unsupported runtimes, malformed/oversized output,
loopback/credential/redirect boundaries, context reset, actual route→analyzer
execution, result revalidation, duplicate IDs, status lookup, eviction/restart,
registry saturation, hostile request bodies and default-off route composition.
Legacy retry/accounting tests separately demonstrate that historical behavior
remains unchanged when no lifecycle context is active. These authored software
tests are not independent expert review or measured local inference performance.

The route is synchronous and cannot resume or cancel a request. Status is advisory
process-local metadata; no result can be retrieved after disconnection. Budget
configuration must match between the manually started API and UI processes.
Microsoft upload and AI Security UI paths remain explicitly legacy. User visual
QA and independent human semantic review remain PENDING; release NO-GO.
