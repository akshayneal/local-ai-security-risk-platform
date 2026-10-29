# Interrupted-session recovery

The continuation recovered a clean local `feature/microsoft-evidence-reliability`
at `06a7c4d2dcf7102dc0a4ae429ec4d9a0c99a5de7`, identical to origin. There was no
uncommitted work to discard, stash or reconstruct. Five inherited checkpoints:

| Commit | Inherited work |
| --- | --- |
| f8159d2 | Bounded local diagnostic trace and single port reproduction plan |
| 6f97939 | Opt-in model metrics, safe JSON error message and preservation identities |
| 3f33cca | Frozen 24-case/32-attempt suite, rubric, scorer and six context probes |
| 10d1542 | Deterministic endpoint compatibility probes and release preservation tests |
| 06a7c4d | API/Activity diagnostic non-exposure regression tests |

Hosted CI for the inherited exact SHA was independently verified successful:
[run 40829675214](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/40829675214).
Earlier local full validation reported 1,522 passes and one failure in the old
release-authorized-path inventory. The subsequent preservation adjustment passed
its targeted tests; it did not alter frozen artifacts. Later targeted groups passed
23 and 25 tests. These are inherited results, not a claimed new full-suite pass.

At recovery the original baseline Python process was still alive, launched at
02:24:27 local time on October 29, 2026. Its journal contained ten complete JSON
records: SOC-001/1-3, SOC-002/1, SOC-003/1, SOC-004/1, SOC-005/1 and SOC-006/1-3.
Every canonical request hash matched the exact frozen schedule prefix; no duplicate,
partial or corrupt line was found. Nine responses returned and one was withheld.
The next scheduled attempt was still in flight. No attempt was restarted, copied
into a fabricated completion, or counted from mere process existence.

The original process continues. No continuation utility is needed while it remains
alive. Its parent command schedules the six context probes after the baseline.
The frozen runner refuses existing journals; no journal was deleted or overwritten.
Raw rejected generations are unavailable by design. The safe port-diagnostic JSON
also exists under ignored results and is not promoted into a raw-output artifact.

`git diff 3f33cca HEAD -- app evals/microsoft_reliability reference_material
requirements.txt` was empty. Only documentation and tests changed after baseline
launch. Thus the executing application and frozen experiment source remain identical
to the launch checkpoint. The eventual completed report's launch-time provenance,
the schedule/request verification and this source comparison must all agree before
calling the baseline complete. No production/evaluator files will change while
the inherited baseline or context process is running.

Main and the peeled v2.3.0 tag remain
`fde00d0ca5d21eecbc6973cc784550ed453edb7a` locally and remotely. The annotated tag
object is `22e5e1704940c41284d6b29e393fd51958f3ba34`; this is not a different release
commit. No branch recreation, reset, clean, rebase, force push, merge or tag occurred.

The continuation uses terminal, repository and test tools only. No Computer Use,
browser automation, screenshot or desktop interaction is authorized. An inherited
task-owned Streamlit QA server was stopped through its original terminal session;
the evaluation process was left running. The earlier session's browser attempt was
blocked by the tool's Windows URL-policy limitation and did not complete visual QA.
Visual/dark-light inspection remains **USER VISUAL QA PENDING**. The continuation
does not repeat or work around that interaction.

## Second continuation

Recovered local and origin HEAD were both `58304d0e81562156b2d9ae7db3bf1da1c613daaa`.
The sole uncommitted file was the manual-review ledger: formatting changes plus
four additional SOC reviews. Existing judgments were preserved exactly as JSON
objects; no review revision was hidden. Application, model-call, reference and
frozen experiment source still had an empty diff from launch `3f33cca`.

The original process had finished. Its final report contains all 32 scheduled
attempts in exact order, with exact request hashes and no duplicates. Every record
equals the append-only journal; the earlier recorded byte prefix and record hashes
still match. Launch-time provenance is clean at `3f33cca`, qwen3:8b identifier
`500a1f067a9f`, temperature 0.1, no seed and no explicit context override. All
32 after-runtime snapshots show context 4096. No trials were resumed or rerun.

Baseline: 29 returned first-pass analyses, three withheld after one failed repair
each, zero transport/JSON retries. The completed report is preserved byte-for-byte
as `baseline.json`; provenance and offline replay tests verify it. All 32 attempts
have separate manual review, including three unassessable withheld outputs.

The parent shell attempted the context phase after baseline completion. It failed
the clean-worktree precondition because the review ledger was uncommitted, before
creating any context artifact or making any context call. Thus zero of six probes
had run at second recovery. After the review/artifact checkpoint is clean, the
six predeclared probes can run once through the unchanged frozen runner. This is
the pending experiment, not a restart or a duplicate.

The first continuation's full Windows test gate passed **1,534 tests**, with the
existing Starlette/httpx deprecation warning. No desktop-control capability was
invoked during either continuation. Visual QA remains **USER VISUAL QA PENDING**.
