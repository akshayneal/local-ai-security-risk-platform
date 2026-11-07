# Sprint 14 evidence qualification readout

**Experimental internal capability, off by default. RELEASE NO-GO.**
No public analyzer, endpoint, retrieval default or launcher is activated by this
slice. All committed examples are fictional. Model and embedding sends: **zero**.
INDEPENDENT HUMAN REVIEW PENDING (0 completed). USER VISUAL QA PENDING.

## Starting identity and scope

Started on `feature/adaptive-typed-security-reasoning-sprint13` at
`285a6b5130e849daaea48406e1c9e1d7bc65ddf1`, equal to upstream/live origin.
Exact baseline CI succeeded:
https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/42279803688.
Work continues only on `feature/evidence-qualified-ingestion-sprint14`.
The prospective plan was committed at `e4c8e07`; fresh literals/rubric at
`0ce1305`; the initial source checkpoint is `1a0a879`. Git retains exact full
commit IDs and the final changed-path list. Final push/CI identity is recorded
in the session handoff after the last commit, avoiding a self-referential SHA.

## What the new code does

`app/evidence_qualification.py` checks a strict, versioned data contract before
source content can enter comparison. A schema checks shape and exact types;
qualification additionally checks separately supplied review status, source role,
case/workflow/question, original-byte hash, current revision and explicit-zone
review/effective/expiry times. Those checks establish eligibility within an
internal synthetic demonstration. They do not authenticate an institution or
prove that an event, permission or deployed control is real.

`app/qualified_soc.py` keeps exact original UTF-8 bytes, parsed field values/types,
row/field pointers, full reviewed metadata, scope and coverage in a deterministic
report. Entity resolution means deciding whether two supplied records concern
the same selected event: exact event, process and creation instant, principal,
asset, resource, event instant and question must agree. IP alone is insufficient.
Several plausible records cause abstention, never first-hit selection.

With one eligible, associated synthetic rule, the existing unchanged Sprint 13
comparator checks the declared relationship. Its envelope is visibly derived;
field lineage points separately to event and authorization originals. JSON and
Markdown exports reconstruct the canonical report and compare type-sensitive
serialization, catching nested changes and Python's `True == 1` equality trap.
Markdown escapes supplied text. Model prose cannot enter the interface.

See the [authority matrix](evidence_qualification_v1/authority_matrix.md) for
the actual owner of each authority field and the
[field mapping contract](evidence_qualification_v1/source_mapping.md) for every
supported transformation and refusal boundary. The pure-function caller must
supply a current application review snapshot at each use/export; this is not a
new authenticated registry or revocation discovery service.

## Real-format vertical slice and controlled examples

One selected `DeviceNetworkEvents` row is accepted through the existing bounded
seven-table Microsoft projected JSON/CSV adapter. All original rows/fields remain
retained; omitted-from-comparison and unsupported-for-this-slice rows are counted.
Native ActionType/ResultType remain opaque vendor assertions. Local/remote IPs
stay local/remote. Neither a transfer nor its completion, data-flow direction,
permission or threat technique is invented. The correct native result is
`unassessable`, reason `unsupported_native_operation_outcome`, even when separately
reviewed context is supplied. Invalid optional fields are reported explicitly.

New development situations illustrate three different results:

- A strict synthetic typed event's `inventory_read` matches one separately
  reviewed synthetic authorization for the exact event/process/principal/resource:
  declared alignment of supplied scope. This is not native Microsoft semantics.
- Two equally associated eligible rules remain ambiguous; differing known
  applicable assertions can remain conflicting. No first candidate is selected.
- A body containing a forged source identity/approval, or a stale source revision,
  is unavailable with a stable refusal code; it is never classified as legitimate.

Failed/attempted outcomes remain noncompleted even when allowed operation scope
differs. Missing evidence differs from explicit denial or a safe outcome.
Metamorphic tests change one relevant value at a time and verify which conclusion
must change; irrelevant annotations/rows cannot manufacture a permission or join.

## Evaluation and review status

Fifteen new development situations and twelve separately frozen diagnostic cases
were committed before diagnostic execution. Scorer-only authored outcomes never
enter application input. Exact input hashes, prospective rubric, candidate
identity and a create-once barrier separate development iteration from the sole
offline diagnostic. A durable per-case journal retains progress/failures through
interruption. Saved diagnostic results must be inspected, never regenerated.

Diagnostic result and final verification: **pending in this checkpoint**. The
final version of this readout will record the actual observations without
changing the scored candidate or authored key.

The unchanged Sprint 13 60-output masked packet now has a printable reviewer
guide and a separate hash-bound blank adjudication template. No semantic verdict,
human identity/role/date or reviewer confidence was invented. A real independent
person should review exact sources before outputs and before opening the separate
concealed key, recording disagreements separately from authored gold.

## Timeout and runtime findings

Gate D takes the permitted evidence-backed deferral. The independent frontend
and Ollama 300s inactivity timeouts are unchanged. Transport can retry uncertain
requests; the SOC repair path can permit up to four raw sends. Timeout/disconnect
does not prove cancellation. Check Activity/local services before considering
resubmission; missing Activity does not prove no send occurred. Full findings and
the minimal future deadline/request-identity design are in
[timeout_deferral.md](evidence_qualification_v1/timeout_deferral.md).

Read-only runtime inspection observed Ollama **0.40.14**, differing from the
historical 0.40.13; no upgrade was performed. The qwen3:8b Q4_K_M digest remains
`500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
No model was loaded. RTX 3060 Laptop GPU reported 6144 MiB total VRAM and 1082 MiB
used at one idle snapshot. Offload, KV-cache use and inference latency were NOT
MEASURED. System RAM is separate from VRAM. No models, packages, services or
system settings were changed.

## Preservation and reproducibility

Gate Zero verified the expected 405 untracked s4check files and 185 ignored cache
files without opening/executing private source. All 911 earlier raw files and
79 Willow files remain hash-bound (990 total). The original 25 saved artifacts,
masked packet/key, raw outputs, historical verdicts and Birch9 UNKNOWN remain
unchanged. No historical experiment or diagnostic was rerun. Immutable source
guard replay and deliberate negative mutation tests are deterministic software
checks, not new historical experimental outcomes.

Use the existing CPython 3.13.1 Windows venv:

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/test_evidence_qualification.py tests/test_qualified_soc.py tests/test_evidence_qualification_study.py tests/test_sprint14_preservation.py -q
.\.venv\Scripts\python.exe -B -m evals.evidence_qualification_v1.preservation
.\.venv\Scripts\python.exe -B -m evals.evidence_qualification_v1.runner development
```

The development command is deterministic and requires no Ollama. Inspect
`diagnostic_results.json` and `diagnostic_journal.jsonl` read-only for the official
diagnostic; do not dispatch it again. Frozen source/input hashes and reservations
remain in the new study directories. An absent local raw archive in CI cannot be
claimed preserved by that hosted job; local hash checks supply that evidence.

The only existing-source migrations are narrowly documented historical source
guards, with their unchanged assertions replayed at the immutable Sprint 13 SHA.
No main/tag/release, production analyzer/repair contract, Inspector/corrections,
retrieval path or launcher changed. Complete validation commands/counts and file
inventory are retained in `validation.json` and `artifact_manifest.json`.

## Remaining limits and Sprint 15

Native telemetry does not yet establish a comparator operation/outcome. A future
semantic allowlist needs vendor-source justification and fresh counterexamples.
Synthetic application review is not organizational authentication or enterprise
authorization. Collection completeness, live event truth and deployed controls
remain unverified. Independent analyst usefulness and semantic adjudication are
pending. New synthetic matches cannot establish population accuracy or model safety.

Next: obtain genuine independent review of the prepared packet; define the
smallest application-owned review/currentness lifecycle and action applicability
contract; then freeze new source-qualified cases before expanding any mapping.
Resolve timeout unknown/duplicate lifecycle behavior before increasing waits.
UI integration needs a separately scoped opt-in design and actual user visual QA.
No release, general detector or broader policy authority should be claimed from
this internal slice.
