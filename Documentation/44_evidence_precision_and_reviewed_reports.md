# Evidence precision and correction-first reports (Mini-Sprint 4.6)

The existing correction workbench now supports individual supplied Microsoft fields
and puts the latest analyst proposals before model conclusions in newly generated
exports. Original AI analysis, submitted telemetry, source authority, correction IDs
and append-only revision chains remain unchanged. No semantic verification or model
accuracy improvement is claimed.

## Field provenance and identity

`SuppliedFieldAnchor` adds value-free metadata to `EvidenceInspectorReport`:
request fingerprint, table, zero-based row index, field name, deterministic evidence
ID, parent observation/row ID and empty/nonempty presence. Its fixed provenance is
supplied field, not independently verified. Unknown authority/value fields are rejected.

The field ID hashes `[request_sha256, table, row_index, field_name,
"supplied-field-v1"]` using the existing fingerprint function. The parent row keeps
its original identity. Tables/fields are traversed deterministically, without changing
canonical row order or the request submitted to qwen. Only existing top-level fields
in canonical Microsoft rows receive anchors; no new parser or nested-field inference.

Absent fields have no anchor. JSON null, empty strings and empty arrays/objects are
marked empty; zero and false are nonempty supplied values. Whitespace-only strings
remain supplied nonempty strings. No raw field value or value hash is stored.
Generic SOC and governance retain their existing inventories without generalized
field anchors.

Report validation binds anchors to this request's existing row inventory and field
names, parent identity and deterministic path ID; duplicate/forged paths and metadata
authority upgrades are rejected. Correction validation revalidates report metadata
and permits eligible reference IDs, existing row IDs or these field IDs. Cross-case,
cross-workflow, missing-row/field and fabricated IDs remain invalid. A field link
records which supplied field was examined, not whether its content is true, malicious
or sufficient for the proposed correction. Hashes are not authentication/signatures.

## Selection and compatibility

The existing correction editor keeps reference/whole-row selection and adds a
separate supplied-field picker. Labels identify field/table/row and presence, never
cell values. The original opt-in selected-value viewer is unchanged; selecting an
anchor does not enable it.

At most 200 matching field options are shown. Coverage states shown/matching/total
counts and explicitly labels incomplete displays. Filter by table, row or field name
to find remaining anchors. Previously linked fields outside the display remain
linked on revision, with an explicit retained count; filter to inspect/remove them.
Filter before drafting: changing filters can discard unsaved form edits.

Old serialized reports default to no field anchors; missing values are not guessed
from field names. Existing row-linked corrections remain valid, with unchanged claim,
correction, revision and predecessor identities. No correction contract field changed.
Session invalidation, workflow prefixes and new-submission clearing remain unchanged.
History is session-local and unauthenticated, not durable audit storage.

## Correction-first JSON and Markdown

With corrections, the optional Inspector export adds versioned
`review_summary` (`analyst-review-summary-v1`): one entry per corrected claim, original
response field and excerpt, latest proposal/category, revision count, unverified
analyst provenance, linked-evidence flag and references to the detailed history.
Original excerpts are capped at 400 characters and explicitly marked when truncated,
including when the Inspector's existing claim excerpt was already incomplete.
Every revision remains in `correction_history`; no proposal is accepted automatically.

Markdown puts **Analyst Correction Summary** before severity, incident characterization
and substantive AI analysis. It distinguishes original AI statements from latest
analyst-proposed corrections, not independently verified. Complete original analysis
and detailed history follow. JSON places the Inspector block and its summary first
when present; the original `analysis` object remains structure-equivalent. Only
field-anchor metadata linked in any revision is exported, to explain historical links.

Without corrections, export shape/order and Markdown stay unchanged, including for
new Microsoft reports that have field anchors. Existing serialized reports and
correction records still parse; no import workflow or automatic reconstruction of
old field metadata is added. Existing old exports without a summary remain readable.

Analyst/model excerpt text uses the existing correction escaping: line breaks are
flattened, HTML/entities encoded and Markdown syntax escaped. Original model fields
retain their existing export formatting. New provenance adds no raw input values,
source excerpts, prompts, rejected generations or diagnostic traces.

Exports are **not redacted**. Existing case identity can contain account/asset names;
original analysis and its bounded summary excerpts can quote supplied information;
analyst wording/rationale can contain sensitive text. The early summary and history
retain sharing warnings. Review the whole file, including old revisions, before sharing.

## Validation and preservation

Start: `feature/analyst-correction-workflow`,
`3b51f9ed2f0ba765fe82b99a50771a5109748feb`. Child branch:
`feature/evidence-precision-reporting`.

- `5c1ab63`: field contracts, binding, legacy row compatibility and focused tests.
- `9fa5a112d93c3fa9e20d79fceea596b10f46e8a9`: bounded field picker, correction-first
  exports and focused UI/report tests.
- Final documentation SHA and exact-SHA hosted CI are recorded in the handoff.

Synthetic tests cover account-attribution field links, unsupported C2 and implemented-
requirement corrections, deterministic identities, empty/missing fields, malformed
metadata/lineage, private-value exclusion, 250-field coverage/filter retention, all
three input paths, no extra calls, latest-only summaries, every revision, bounded
excerpts, Markdown escaping, unchanged analysis and no-correction compatibility.

Final local Windows validation: **1775 passed** (22 added tests), one existing
Starlette/httpx deprecation warning, 67.53 seconds. The full suite ran once at the
final implementation gate. Uncached Ruff, pip check and diff checks passed. Seventy-two
focused compatibility/UI/report checks passed before checkpoint 2; the added narrow
preservation boundary and report checks passed separately. Final exact-SHA hosted CI
and its Linux skip count are verified in the handoff. The closeout commit changes
documentation only.

Exact files changed:

```text
app/evidence_inspector.py
dashboard/evidence_inspector.py
dashboard/exports.py
tests/test_field_anchors.py
tests/test_field_anchor_ui.py
tests/test_reviewed_reports.py
tests/test_correction_preservation.py
tests/test_support_e2e_artifacts.py
Documentation/44_evidence_precision_and_reviewed_reports.md
```

The archived live Inspector replay checks every original field exactly through an
explicit projection excluding only the new additive field-anchor collection. Separate
tests validate that collection. Frozen reports, judgments, cases and scorers are not
modified. Preservation checks constrain this sprint's production diff to the Inspector
contract, Inspector UI and export modules, plus this document; other historical checks
and replay tests remain active. No public analysis schema, prompt, analyzer, retrieval
default, dependency, registry or inference configuration changed.

New Ollama/qwen inference requests: **zero**. No live evaluation, desktop/Computer Use,
browser/headless automation, screenshots, cleanup, installation or system changes.
Protected worktree remnants remain untouched and visibly untracked. Main/peeled
v2.3.0 remain `fde00d0ca5d21eecbc6973cc784550ed453edb7a`. No merge, tag or release.

## User visual testing and next scope

**USER VISUAL QA PENDING**. The bounded workbench is ready for user-led visual testing
after the automated/hosted gates reported in the handoff; this is not release approval.
Check all three paths, readable row/field/reference distinctions, empty-field labels,
long/filter-limited inventories, retained hidden links, opt-in value privacy, revision
history, stale-case clearing, summary-before-analysis downloads, themes and narrow screens.

Next full sprint: **Expansion Sprint 5 — Natural-Language Evidence Support & Policy
Applicability**, with independently reviewed positive/negative controls, trusted source
admission and frozen support/applicability criteria. It is not begun by this sprint.
