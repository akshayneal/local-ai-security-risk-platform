# Sprint 15 continuation plan — November 7, 2026

Experimental development only. RELEASE NO-GO. Independent human review: zero
verified. USER VISUAL QA PENDING. Planned model/embedding sends: zero.

Baseline: `feature/native-evidence-workflow-sprint15`,
`9be773070f2176d40e3e80beccf65feaefdc03c0`, equal to the live origin ref.
Tracked/index diffs empty; 405 inherited untracked s4check files retained.
Read-only process inspection found shared Ollama, no Python evaluation.
A temporary hash-only inventory records all inherited untracked files and 452
non-venv/non-bytecode ignored files; this broader inventory includes caches,
and is not comparable to the previous sprint's 185-file private subset.
No inherited journal is reserved or rerun. Original 14 11/12 and 14B 10/10 stay
unchanged. Existing 795-blob/990-raw preservation guards will be replayed at their
immutable historical tip before a narrowly listed continuation guard is added.

Working branch: `feature/sprint15-analyst-utility-and-request-lifecycle` (new,
absent locally/remotely before creation). Main/tag/launchers stay untouched.

Operator questions:

1. What exactly does this selected network row report, which representations are
   invalid/missing, and what other supplied rows might need separate inspection?
2. What additional evidence would answer application access, blocking or policy
   authorization without treating a network label as that conclusion?

Smallest implementation: a versioned investigation companion to the existing
native report/route. Reuse exact-byte observations; add deterministic coverage,
same-field representation comparisons, explicit insufficient-evidence statements,
and question/presence-driven next-evidence templates. Keep the old observation
route/export intact. Expose a deliberate report-view choice on the existing page,
with explicit Build and source/row/question-bound JSON/Markdown downloads.
An alternative was extending the v1 schema in place; a companion avoids contract
drift and preserves the existing source-bound viewer.

Trust boundary: uploads/labels are unverified data; hashes locate bytes and do
not authenticate them. Local/remote retain their roles. Other-row comparisons
only describe literal/type differences, never associate events. No source,
note, model or title creates permission. No model, scan, action, policy comparison,
new table ingestion, dependency, worker, service or authenticated review system.
Disable the existing native flag to remove the companion route/page capability.

Prospective deterministic acceptance (implementation-authored, not independent
validation; no new scored diagnostic):

| Transformation | Required property |
| --- | --- |
| Select another row | New facts/paths/request binding; same original bytes/hash |
| Add unrelated row | Coverage/hash change; selected facts and unknown conclusions stable |
| Swap local/remote | Exact roles swap; no direction inference |
| Equivalent timestamp offset | Same normalized instant; original spelling/hash differ |
| Replace numeric shape with bool/list | Invalid representation; no numeric fallback |
| Forge approval/current/source ID | Original retained; authority unchanged; zero comparison |
| Duplicate row / reuse PID | All candidates retained; ambiguity visible; no automatic join |
| Change source revision, report or either export | Response/download withheld |
| Remove field | Absent/unknown plus specific evidence question; no absence-of-event claim |
| Refresh/download/change question or row | Zero implicit POST; stale downloads removed |
| Timeout/disconnect after dispatch | Unknown outcome; no automatic inference retry |
| Exhaust monotonic budget | No next dispatch/repair; no cancellation claim |

Sequence: commit plan; implement/test/commit A; qualify at most two native
semantic hypotheses with official sources; then implement a default-off bounded
request-lifecycle safety subset with mocked time/transport, preserving legacy
runner seams. Finally challenge API/client/AppTest/exports, full deterministic
suite, tracked/new Python Ruff, pip/diff/preservation checks, normal feature push
and exact-SHA CI. Document all failures and limits. No live inference is needed;
the optional six-send allowance is unreserved and unused.
