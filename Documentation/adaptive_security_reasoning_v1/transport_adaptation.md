# Sprint 13 bounded transport adaptation

Status: experimental evaluation support, **off the production path**. No provider
or model requests were made while implementing or testing this adaptation.
`acceptance` is a retained internal accounting name for Sprint 13's diagnostic
holdout; it does **not** mean release acceptance.

## Audited source and exact modifications

The new `evals/adaptive_security_reasoning_v1/transport.py` began as an exact copy
of `evals/deterministic_evidence_v1/transport.py` at Sprint 12 endpoint
`95fdfbe1d5f5cacf0d814e7c3a67bb56ce18f57a`. Original source SHA-256:
`4bcca2b9d07b2ad2949284d2a4c55d7ec2b292a57290ae42074aac27b781b001`.
The original file is unchanged. The new file imports no historical evaluation
runner, budget, output root or campaign. There is no default output directory.
The transport requires exact new Willow namespace leaf names; the runner also
restricts their full parent to the selected Sprint 13 workspace.

These are the complete behavioral/textual adaptations:

| Location | Sprint 13 change and purpose |
| --- | --- |
| Module/class docstrings | Name Sprint 13 and distinguish legacy diagnostic accounting from release acceptance; state runner responsibility for full workspace parent and per-send read-only model/provider identity preflight. |
| Constants | `LAB_CAP=84`; `PHASE_CAPS={D0:24,D1:24,D3:36,A:24}`; diagnostic cap `24`; `CAPS={lab:84,acceptance:24}`; `MAX_ATTEMPTS=108`. Caps are nontransferable and raw reservations are not completions. |
| Runtime/size constants | Wall per request `600s`, campaign `14400s`, prompt `48000` bytes and retained track data+journal `64000000` bytes. Connect `10s`, idle `120s`, raw wire `1000000` bytes and campaign journal `256000` bytes remain separately bounded. Retention is a per-track ceiling; two tracks and the separate campaign journal are not advertised as one 64 MB aggregate allocation. |
| `DiagnosticBudget.__init__` | Select new 84/24 caps. Check the journal leaf with existing `plain_path()` before replay/open so a linked leaf cannot redirect journal access despite an ordinary root. |
| New `ROOT_NAMES/named_root` and constructor gates | Before metadata/read/open/mkdir, require exact `willow-sprint13-development`, `willow-sprint13-diagnostic`, `willow-sprint13-campaign` leaves, literal `journal.jsonl` and a common parent; reject `..`. Budget construction additionally requires an open actual `CampaignLedger`, the same parent and the exact declared manifest track journal. An old Spruce/Birch root is rejected before it can be read. Arbitrary temporary parents remain usable for offline tests. |
| `DiagnosticBudget._replay` | Require `s13-d-NNNN` sequence and a phase owned by the selected track (`D0/D1/D3` for development, `A` for diagnostic). Reject absent/foreign phases instead of replaying a less restrictive history. Replay now verifies every stored artifact rather than only counting its bytes. |
| New `artifact_bytes` | Permit only unique `trials/<bounded-trial>/<bounded-file>` relative paths; refuse traversal, duplicate paths, missing files, symlinks/junctions, size/hash changes and oversized reads. Read at most the raw-wire cap plus one byte. Equal-length edited content fails the hash check. |
| `DiagnosticBudget.chat` | Use `s13-d-NNNN`; consult shared campaign `check_dispatch()` before writing a track reservation. Existing store/reserve/fsync -> global reserve/fsync -> one raw send ordering is retained. |
| `CampaignLedger.__init__` | New manifest format `adaptive-security-reasoning-v1-campaign`, declared `campaign_seconds`, and fsynced first-start monotonic/wall timestamps. Reopen checks exact manifest keys/static identity and finite numeric starts, restores original starts and rejects clock rollback. Add `math` only for finite checks and injectable clocks for offline tests. |
| `CampaignLedger.reserve` | Check global elapsed budget before every global reservation, even when a caller switches tracks. |
| `CampaignLedger._apply/_reconcile_tracks` | Retain global outcomes in memory during replay, then reconcile all declared new-root track journals against global reservations and finishes before opening for new work. A local-before-global reservation crash gap, unknown/pending track work, deleted/changed track history, mismatched outcome or altered stored artifact stops reopening without repairing evidence. A header-only track with no reservations is allowed; it represents no raw send. |
| `CampaignLedger.elapsed_seconds/check_dispatch` | Use `max(monotonic elapsed, wall elapsed)` from persisted first start; any rollback/nonfinite value fails closed. Require room for a full 600-second request before dispatch; reopening cannot reset the 14400-second allowance. A reboot that resets the monotonic counter below its stored value requires stopping, never resetting history. |
| `CampaignLedger.snapshot` | Expose persisted start, aggregate elapsed and remaining campaign seconds alongside original counts/pending/blocked fields. |

The shared first-start change corrects a scope problem in the copied design:
independent per-track clocks alone could grant a later-starting track a fresh
wall-time allowance. A track still retains its own original conservative clock;
the shared guard additionally bounds the whole Sprint 13 campaign.

Pre-generation review identified three additional weaknesses in the original
copy: arbitrary constructor roots could be read before their identity failed;
global replay did not reconcile an interrupted local reservation; and artifact
replay counted recorded bytes without checking present contents. The namespace,
reconciliation and artifact gates above address these before the first frozen
Sprint 13 generation. No old transport, journal or artifact was modified.

The low-level socket connection, deadline reader, deadline socket, NDJSON stream
parser, secret/path screening and request builder are unchanged at the Python AST
level. Tests compare them directly to the original source. Sampling remains
temperature `0.1`, `num_ctx=32768`, `num_predict=4096`; model/tag and expected
digest are unchanged. Runner preflight must verify actual installed provider and
model digest before each raw send. Transport stream frames also reject model-name
drift; that check is not a replacement for provider identity preflight.

## Integrity properties and limits

The transport creates an exclusive active lock, stores bounded request bytes,
then durably reserves the track and global attempt **before** its sole loopback
`POST /api/chat`. It never retries, repairs, follows redirects, reads proxy
configuration, launches/stops a service, downloads a model or issues cloud calls.
A partial/unknown/error outcome remains counted and blocks later sends and
reopening. Known length/empty completions are counted but withheld, not relabeled
as completed useful answers. Durability failure before raw dispatch creates
conservative unresolved reservations and stops; it does not imply a send occurred.

Complete-context byte/token upper bounds include prompt, JSON schema, output
budget and template allowance. Wire always sets `truncate=false`, `shift=false`,
and streaming. Deadlines govern send, headers, NDJSON/chunk framing and reads
through the socket itself; no watchdog, timer thread or background worker is used.

Hidden `thinking` fields and inline think blocks are counted and hashed, with
raw wire bytes/hash and usage metadata recorded. Their text is discarded; only
allowlisted final visible answer/usage are retained. Hashes correlate snapshots,
not truth or authority. Source classification, immutable schema/prompt freeze,
fresh-case uniqueness, full workspace-parent selection, source/report integrity, provider preflight and foreign
evaluation-process checks belong to the runner/application gates, not this
socket/accounting component. No transport test proves security reasoning quality.

## Offline verification

`tests/test_adaptive_transport.py` uses fake sockets/responses, temporary journals
and clocks. It covers durable reservation before send, fsync failure with zero
raw sends, zero hidden retries, model-name drift, malformed/partial/timeout output,
UNKNOWN blocking, known withheld output, track/phase/global caps (84+24=108),
exclusive artifacts/locks, replay, wrong-track replay, shared campaign expiry
across reopening, clock rollback, strict context bounds, thinking byte/hash
accounting without retained hidden content, and real `http.client` chunk framing
over a fake fixed-loopback socket with proxy environment variables ignored.
The new negative tests also prove old/mismatched roots cause no filesystem
operation, local/global crash gaps block another track on reopening, missing or
changed track journals block, and missing/unsafe/duplicated or equal-length
tampered stored artifacts block before any fresh campaign or budget dispatch.

Executed on the existing Windows environment:

- Initial transport-only stabilization: **43 passed**.
- After pre-generation namespace/reconciliation/artifact hardening,
  `python -m pytest -q tests/test_adaptive_transport.py`: **59 passed in 7.41s**.
- `python -m ruff check evals/adaptive_security_reasoning_v1/transport.py tests/test_adaptive_transport.py`: **PASS**.

Initial test development exposed one fixture assertion that looked for a duplicate
artifact in a different trial directory after phase iteration; the assertion was
corrected to the actual current-trial artifact. The initial run was 31 passed,
1 failed. No provider call occurred, no implementation failure was substituted
for a success, and temporary test journals were not campaign evidence. Scoped
Ruff also identified nested context-manager style and formatting issues, fixed
within this new test file. During hardening, the two earlier tests that wrote
only global ledger entries were updated to create real paired track journals;
the stricter reconciliation correctly rejected those incomplete fixtures. A
new tamper test initially asserted an internal error string/code, while the
inherited `EvidenceBudgetError` intentionally normalizes it to the public generic
failure. Its assertion now checks rejection before a second raw send. These
were offline test-development failures, not omitted provider outcomes. Full
repository verification belongs to the root Sprint 13 handoff.
