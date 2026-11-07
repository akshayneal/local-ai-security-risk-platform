# Gate D: timeout lifecycle change deferred

Status: **evidence-backed deferral**. Production frontend and model transport
source, timeout values, retry policy, SOC repair cap and historical evaluation
accounting remain unchanged. Sprint 14 dispatches zero inference calls. This
document describes an existing reliability limit, not a completed timeout fix.

## Source findings at immutable Sprint 13 baseline

Baseline: `285a6b5130e849daaea48406e1c9e1d7bc65ddf1`. Paths/lines below refer to
that source and remain protected by Sprint 14 preservation checks.

| Boundary | Evidence | Consequence |
| --- | --- | --- |
| Frontend wait | `dashboard/api_client.py:49`, POST `timeout=300` | Requests uses connect/read inactivity timeouts; this is not a total wall-clock request deadline. |
| Model preflight | `app/ollama_client.py:72`, version GET `timeout=10` | An additional request occurs before generation. |
| Protected model request | `app/ollama_client.py:96`, chat POST `timeout=300` | Its budget competes with the frontend's independently started 300-second wait. |
| Retry | `app/ollama_client.py:115`, two Tenacity attempts and one-second wait; `:111`, RequestException becomes RuntimeError | A read timeout or post-send disconnect can trigger another inference while the original completion is uncertain. EvidenceBudgetError alone is excluded. |
| Generic SDK | `app/ollama_client.py:27`, `Client(host=OLLAMA_HOST)` | No explicit application timeout or lifecycle deadline is assigned here. |
| SOC repair | `app/soc_analyzer.py:65`, two policy generations, each invoking the retrying client | Up to four raw sends are possible. One allowed policy repair differs from one transport retry. A transport exception leaves this repair loop. |
| UI progress | `dashboard/workflows.py:244`, `dashboard/microsoft_input.py:118` | A static spinner says analysis is running; it does not measure token progress or elapsed budget. |
| API lifecycle | `app/main.py:104`, synchronous SOC entry; `app/ai_security_api.py:76`, synchronous AI Security entry | These routes expose no durable request ID, completion lookup, cancellation guarantee or idempotent resubmission contract. |

The client already gives a safe timeout warning at `dashboard/api_client.py:64`:
backend work may still finish and be audited. The more general connection-error
path cannot establish whether failure happened before or after dispatch. Failed
or absent UI output is not proof that the provider stopped or never received it.

## Safe user guidance

After an analysis timeout or disconnect, completion is **UNKNOWN / possibly
running**. Check Activity and the local services before considering resubmission.
An absent Activity result does not prove no inference occurred. Do not repeatedly
click Analyze or treat page refresh as cancellation/resumption. There is no
cancellation guarantee and no new duplicate-submission guard in this sprint.
Returned validated results and completed audit entries differ from partial or
unobserved generation. Never display raw transport exceptions or partial output.

## Why a scalar increase is insufficient

Changing both 300s settings to 1,200s would leave independent inactivity timers,
version lookup, transport retries and policy repair without a coherent lifecycle
budget. A page disconnect could still leave work running, and automatic retry
could still duplicate it. Existing deterministic tests also assert legacy retry
and frontend behavior; historical runners wrap both HTTP stacks to count sends.
Changing global retry semantics during the P0 qualification study risks changing
that accounting without establishing truthful request completion.

This choice follows the sprint's Gate D deferral option. It does not assert that
the existing transport avoids duplicate inference. No real 20-minute wait, model
measurement, service restart, scheduler or persistent process was introduced.

## Minimal prospective follow-up

Define a separate opt-in request-budget contract before changing production:
bounded frontend wait, bounded model connect/read settings, maximum attempts and
repair budget, plus an explicit monotonic total deadline propagated through
preflight/initial generation/repair. Require the frontend wait to exceed the
allowed backend lifecycle with a documented margin. A read timeout alone must
never be described as that total deadline.

Classify uncertain post-dispatch failures and prevent automatic inference retry
for them. Add a request identity and pending/unknown/completed lookup so a user
can check an existing submission instead of silently issuing another. Define
what cancellation can and cannot guarantee. Historical evaluation entrypoints
must retain their frozen accounting. A durable job queue or worker is outside
the minimal design until a concrete lifecycle requirement justifies it.

Before activation, use mocked clocks and transports for slow responses,
disconnect-after-send, timeout with uncertain completion, invalid budget/type
boundaries, policy repair, exact raw-send counts and duplicate submission/page
refresh. No long real sleeps or raw model calls are needed. Existing relevant
checks live in `tests/test_complete_context.py`, `tests/test_product_helpers.py`,
`tests/test_io_boundary.py`, `tests/test_controlled_inference_evaluation.py` and
`tests/test_cross_pillar_evaluation.py`; these checks are software evidence and
do not complete user visual QA or prove cancellation.
