# Analyst Evidence Inspector

SOC Investigation (generic and Microsoft) and AI System Risk Review receive an
expandable Evidence Inspector after a successful submitted analysis. It is a passive
review workbench, not a semantic hardening pass, support certificate or new workflow.
No extra model generation, automatic action, new retrieval backend or default change.

## What analysts can inspect

- Actual retrieved references, including uncited candidates, with source family,
  application-owned authority, scope/applicability, currentness, registry status,
  content fingerprint and bounded plain-text excerpt. Cited status is matched to the
  returned sanitized source identities; it does not establish claim support.
- Supplied table/row and field inventory for Microsoft cases, or supplied field
  inventory for generic SOC/governance. Default metadata contains no raw telemetry
  values. Original submitted inputs remain in that result's local Streamlit session.
- An explicit opt-in selected-value viewer, bound by the request fingerprint. Only
  the selected original field/cell is displayed, capped at 2000 characters with
  coverage labeling. Values are excluded from evidence exports by design.
- Model-authored assertions, their response fields and field-based display kinds.
  They always carry model-proposed/unassessed provenance and require analyst review.
  The kind is not an automatic semantic classifier: summary/gap text can mix facts,
  requirements, implementation claims and uncertainty. No green Verified status or
  reliability/confidence percentage exists.
- Model-proposed evidence gaps, explicitly requiring comparison against the input.
- Local analyst-recorded support/partial/insufficient/conflict/inapplicable judgments,
  selected evidence and bounded notes. User entry is not independently authenticated
  or machine-verified. It changes neither analysis text nor source access rights.

All analyst judgments are bound to the exact submitted request/result fingerprint,
claim identity and current eligible candidate/input-inventory IDs. A different case,
result, claim or forbidden evidence ID is rejected or clears the local review state.
Supported/conflict judgments require an explicit evidence selection. No proof of
entailment is inferred from that selection; it is a recorded human judgment.

## Integration and compatibility

The shared request-local capture in `app/evidence_inspector.py` observes the existing
retrieval result. Public curated legacy cards must match the application catalog;
optional lexical records retain their trusted metadata and are rechecked for current
public workflow eligibility. Unknown/forbidden/ungated document records do not enter
the Inspector. Query text is hashed, never returned. Capture failures are isolated
from generation, and a skipped/unavailable capture is labeled rather than inferred
from model citations. ContextVar scope prevents cross-request/workflow leakage.

Only `/ui/analyze/*` envelopes gain the optional typed metadata field. Existing
`/analyze/*` success schemas and analyzer prompts/validators are unchanged. Both UI
routes still call the original analyzer once, preserve SOC repair/context protection
and audit the analysis once. Governance retains its narrower existing validation;
Inspector metadata does not make it equivalent to SOC factual checks.

After the eight frozen live diagnostics completed, the SOC API boundary was corrected
to bind the response routing `alert_id` to the submitted case ID after full analyzer
validation. Both public and UI routes share this correction. All other validated
fields remain intact; no identifier parser, additional generation or repair was added.
The archived diagnostic's vendor-ID substitution remains a recorded failure. Direct
analyzer behavior and historical experiment replay are unchanged. This correction
does not validate event/account/endpoint claims in ordinary model text.

The UI uses the shared support-assessment contract for unassessed model claims.
The evaluated exact structured-record matcher is available as a reusable library,
but it does not automatically interpret free-form production conclusions. Applying
its synthetic benchmark result to model prose would be unjustified. That automation
remains inactive; human review is the explicit production boundary.

Existing JSON/Markdown exports remain unchanged when Inspector metadata is absent.
New exports add versioned provenance, field inventory, claim status and optional
analyst judgments. They exclude original input values, source excerpts, prompts,
rejected generations, traces and operational diagnostics. Notes/model strings are
escaped in Markdown. Judgments are session-local and exportable; no persistent
review database, backend audit certification or authenticated approval is added.

Governance UI labels control fields as model proposals/stated requirements requiring
applicability review. Two distinctions remain explicit: retrieved guidance is not
binding policy, and a binding requirement is not proof of implementation.

## Bounds and QA

Up to 60 model assertions are displayed, with shown/total counts; omitted assertions
remain unassessed. Individual assertion excerpts are capped at 4096 characters and
reference excerpts at 600. Full analysis remains in its existing display. Microsoft
rows are not selected out of the original request or model context.

AppTest/API/unit checks cover actual retrieved/cited status, both active workflows,
Microsoft row inventory and profile invalidation, explicit private-value opt-in,
empty-row behavior, analyst review binding, stale review clearing, safe exports,
capture isolation, unchanged public analysis, one model call/audit, and absence of
forbidden evidence or raw diagnostics. They use no browser, screenshots or model.

**USER VISUAL QA PENDING**: the user should inspect layout, narrow-screen wrapping,
light/dark themes, long source/claim text, uploads, selected-value privacy and exports.
No graphical or headless browser automation was used. Automated UI success is not a
claim that visual review, semantic correctness or release readiness is complete.
