# Evidence-linked analyst corrections (Mini-Sprint 4.5)

Analysts can propose and revise corrections to displayed claims inside the existing
Evidence Inspector. Generic SOC, Microsoft SOC and AI System Risk Review share this
session-local feature. It never rewrites the original AI analysis, submitted inputs,
source metadata, evidence eligibility or policy/access scopes. It adds no model call,
reanalysis, semantic verification, automatic action, database or authenticated approval.

## Records, evidence and revisions

`AnalystCorrection` lives alongside the Inspector contracts. Each immutable record
contains Inspector/result identity, claim ID, response field, original claim fingerprint,
category, proposed wording, rationale, selected evidence IDs, stable correction ID,
revision ID/number and predecessor revision ID. Provenance is fixed to analyst-recorded,
verification to not-verified, and reviewer identity to unauthenticated local user entry.
Extra fields cannot introduce authority or verification grants.

Six fixed categories cover unsupported facts, incident inferences, policy/authority,
implementation/compliance, missing/mischaracterized evidence and other clarification.
Wording is nonblank and at most 4096 characters; rationale is nonblank and at most
2000. Evidence is optional: an analyst need not prove absence to flag an unsupported
claim. The UI explicitly says when no linked support is selected. Selecting a source
does not prove entailment, create a mandate or establish implementation.

The correction identity is derived from the Inspector and original claim. The claim
fingerprint binds the exact displayed claim record, whose existing claim ID also
binds the original complete generated text. Corrections are available for displayed
claims only; existing claim-count/excerpt limits remain, and truncated claims require
review of the full original analysis. No source/claim content is reinterpreted.

`append_analyst_correction` validates existing history and returns a new immutable
tuple with one appended revision. Each claim has a sequence starting at 1, increasing
by exactly one and pointing to that claim's immediately preceding revision. Different
claim chains may interleave. Revision fingerprints bind record content. Unknown claims,
wrong results, altered original fields/fingerprints, foreign evidence, duplicate or
skipped revisions and cross-claim predecessors are rejected. These hashes are binding
checks, not digital signatures or authenticated tamper-proof audit evidence.

Only source IDs and supplied observation/inventory IDs already available in this
Inspector can be linked. A shared eligible source ID may legitimately appear in more
than one case; the result and original claim bindings still prevent cross-case history.
No correction text is sent to a model, source loader or policy-authority parser.

## Analyst workflow and session lifetime

In Analyst Review, select a claim and compare **Original AI analysis — unchanged**
with **Analyst-proposed correction — not independently verified**. Enter category,
wording, rationale and optional evidence, then save. The latest proposal is shown
separately. The next editor is prefilled from it; saving appends another revision.
The expandable history retains all prior revisions and their linkage, wording,
rationale and evidence. Text is displayed as plain text. Existing support judgments
remain available and are not replaced by corrections.

History uses the existing per-workspace review state and exact Inspector fingerprint.
A different case/result resets both reviews and corrections. New submissions clear
them even when a repeated deterministic result has the same fingerprint. Microsoft
input/profile changes clear stale review state immediately. Generic/governance inputs
remain inside their existing submission forms: unsent edits do not change the saved
result, which remains explicitly labeled as the result for the submitted input.
Submitting changed input starts fresh. Workspace prefixes prevent workflow inheritance.

Session history is not durable storage or an authenticated enterprise audit trail.
Closing/resetting a session, changing a case or resubmitting can lose history. Export
before doing so when retention is needed. There is no import, persistent store,
approval workflow, undo/delete-history control or automatic application of proposals.

## Compatible exports and privacy

Without corrections, public schemas and existing exports retain their prior shape.
When present, the optional Inspector block adds `correction_history` with format
`analyst-corrections-v1`, a sharing notice and ordered revision records. It includes
original claim identity/field/fingerprint, category, proposed wording, rationale,
evidence IDs, provenance, unverified status and supersession references. The original
analysis remains intact. Export validates the complete history against the Inspector.

Markdown gives corrections a separate, explicitly unverified section. Analyst text
has line breaks flattened, HTML/entities encoded and Markdown syntax escaped, so
entered links, headings and HTML do not become active or deceptive markup. JSON
preserves the entered strings as data. Evidence-selection values are identities,
not automatic copies of telemetry or excerpts.

The correction block automatically includes no original input values, full source
excerpts, prompts, rejected generations or diagnostic traces. Existing analysis can
quote telemetry, and correction wording/rationale can contain sensitive user-entered
text. Exports explicitly require review before sharing: they are not redacted or
safe-to-publish certificates. Linking policy guidance does not independently verify
the proposed correction or authorize a consequential decision.

## Validation, checkpoints and preservation

Starting branch/SHA: `feature/evidence-support-workbench`,
`4f7009ec198710f0495e8c5f2e5dce9a19593496`. Development branch:
`feature/analyst-correction-workflow`.

- `501481f`: typed binding, immutable revisions and focused validation tests.
- `b5423526730d87b98ade1dd3eaf801edf5dd3ded`: UI/editor, all three input paths,
  append-only history, compatible exports and focused AppTest/API tests.
- Final documentation checkpoint and exact-final-SHA hosted CI are reported in the
  handoff; this document cannot contain its own final commit identity.

Focused synthetic tests exercise unsupported C2 and requirement-as-implemented
correction examples, valid revisions, evidence/identity rejection, malformed lineage,
text bounds, original/history preservation, stale-state clearing, existing judgments,
export compatibility/escaping/privacy and editing without additional API/model calls.
These are feature tests, not reliability experiments or evidence of model improvement.

Final local Windows validation: **1753 passed** (32 added tests), one existing
Starlette/httpx deprecation warning, 67.49 seconds. The full suite was run once at
the final implementation gate. Uncached Ruff, pip check and diff checks passed;
48 focused correction/Inspector/preservation checks also passed before checkpoint 2.
The final documentation commit changes no application code or tests. Exact-final-SHA
hosted CI, including Linux's Windows-only skips, is verified in the handoff.

Exact files changed:

```text
app/evidence_inspector.py
dashboard/evidence_inspector.py
dashboard/exports.py
dashboard/microsoft_input.py
dashboard/workflows.py
tests/test_analyst_corrections.py
tests/test_analyst_correction_ui.py
tests/test_analyst_correction_exports.py
tests/test_correction_preservation.py
Documentation/43_analyst_corrections.md
```

Preservation checks constrain the entire app/dashboard/reference/evaluation/doc diff
to the five authorized integration modules and this document. Existing historical
artifact identity/replay tests remain unchanged. No benchmark case, scorer, report,
manual judgment, prompt, analyzer, retrieval backend/default or dependency is edited.
Maximum and actual new Ollama/qwen inference requests: **zero**.

No desktop, Computer Use, browser/headless automation, screenshots, cleanup, system
changes, new worktree, merge, tag or release. Existing protected remnants under
`evals/results/s4check/` and `.git/worktrees/s4check/` are left untouched; the former
remains visible as untracked rather than being deleted or concealed. Main and peeled
v2.3.0 remain `fde00d0ca5d21eecbc6973cc784550ed453edb7a`.

## User visual QA and next prerequisites

**USER VISUAL QA PENDING**. Manually inspect:

- All three input paths: original/proposed distinction and long text wrapping.
- First save and second revision, editor prefilling and readable prior history.
- Linked versus no-linked-support labeling and separate existing judgments.
- New submissions, Microsoft input/profile changes and workflow isolation.
- JSON/Markdown downloads, escaped user content and privacy review before sharing.
- Light/dark themes and narrow-screen form/history layout.

The next full sprint should address **natural-language policy applicability and
evidence support, with independently reviewed positive and negative controls**.
Prerequisites are reviewed source admission/applicability rules, independent human
judgments, frozen evaluation criteria and explicit positive-loss measurements. This
mini-sprint does not begin that work or activate SOC Policy & Governance Review.
