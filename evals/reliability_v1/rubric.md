# Prospective reliability v1 rubric (before implementation/outcomes)

Six new scheduled submissions, two per workflow. SEC-A/B run first because
technical availability is highest priority. Six GLOBAL raw generation HTTP
attempts include transport/app retries and SOC repair. A timeout with an uncertain
response consumes one attempt. Further submissions are NOT RUN when exhausted.
Never selectively rerun, replace failure with success, or change expectations.

Report separately: scheduled, submitted, reserved/sent, provider responded,
unknown after timeout, API returned, usable technical advisory, insufficient,
withheld, budget-denied and not run. Counts use their explicit denominators.
Provider JSON/schema failures and semantic errors are distinct. Record provider
version/digest/settings, request wall time versus provider total/eval/load times,
exact case/source/output hashes and executing source commit. No warm-up/holdout.

Deterministic checks: response schema and immutable submitted ID, source citation
membership (envelope evidence_id, never logical document identity), technical
graph endpoint/category/source binding, candidate/not_verified/no_actions status,
coverage/findings consistency. Original invalid payloads must remain rejected.
An empty benign advisory is allowed; an insufficient response is not silently
promoted, and all rejected content is withheld from the analyst. These checks
prove structure/identity, not entailment, approval or deployed effectiveness.

Implementation-author review (independent adjudication PENDING): for each of the
18 frozen expected facts, mark retained, omitted, contradicted or unassessable.
Use brief exact synthetic excerpts and reasoning, not word-for-word matching.
Report retained/assessable and omitted/contradicted/assessable separately from
unassessable/scheduled facts. Flag unsupported inventory/reputation/intent,
unknown implementation turned into absence, known absence/implementation/approval
erased as unknown, invented cadence/retention, lost low-impact/proposed-review
context, false verified/executed/approval claims and unsupported benign attack paths.
Missing evidence should be explicit without erasing supplied positive facts.

SEC-A: untrusted OCR -> generated HTML -> caller-declared raw renderer provides
a basis for a conditional unsafe-output hypothesis. Lack of implementation proof
is a gap, not a missing architecture. Preserve IDs and exact allowed guidance.
SEC-B: public/offline translator -> claimed string filter -> human preview gate.
No invented tools, retrieval, sensitive data or publication permissions. Zero
findings can be useful; a real hypothesis must be grounded in this declared graph
and remain conditional. Claimed controls are not independently verified.

SOC-A: retain the lookup, source/answer roles and absent subsequent actions.
No inventory/reputation/intent is supplied. A lookup cannot establish compromise.
SOC-B: retain within-record source inventory match, completed transfer and narrowly
scoped approval. Do not hedge those away solely because external confirmation is
absent; do not turn copy approval into containment authority.

RISK-A: retain low-impact public drafting and proposed curator review; missing
implementation documentation leaves implementation unknown. RISK-B: attribute
the explicit scoped absence/implementation and pilot approval to supplied MT-44/
AP-44 records; preserve them without claiming independent verification, universal
law or unrestricted approval. A proposed review decision is not granted authority.

Useful output requires both contract validity and case-grounded, proportionate
content. No aggregate accuracy/confidence/safety percentage. Six distinct cases
with different paths cannot establish causal improvement over historical totals.
All raw full synthetic outputs stay in the fresh ignored run root. Track only
minimal excerpts, hashes, counts and candid limitations. No qualitative review
here is expert/independent adjudication or a release/visual acceptance decision.
