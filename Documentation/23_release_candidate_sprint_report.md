# Professional release-candidate sprint report

## Starting point

Repository: `local-ai-security-risk-platform`. Clean synchronized
`feature/portfolio-hardening` at the required starting SHA
`fab6d418b597cbd2ed53caf44dbc622288f47d8f`.
Baseline checks: **1,270 passed**, one existing Starlette/httpx deprecation warning,
**53.16s**; Ruff and `git diff --check HEAD` passed.

This sprint is restricted to professional presentation, release-candidate
documentation and conservative reproduction/CI housekeeping. It does not merge,
tag, implement planned workflows or change semantic analysis behavior.

On resuming the interrupted run, `feature/portfolio-hardening` was synchronized
with the remote at `a20386087861d9dc92a1387f69ab4cd1898a35e5` (the completed
product-experience commit). Four modified files and two new attribute files
contained the Windows checkout correction and its test/documentation. There
were no staged changes. All inherited work was preserved; no reset, clean,
revert, history rewrite or branch recreation was used.

## Changes

- Native `st.navigation` with default Overview, Workflows and Platform groups.
  Six file-backed pages delegate to existing presentation functions.
- Overview uses a native 2×2 product map: two Active workflows with links and two
  Planned informational cards without forms, routes or analysis controls.
- Governance Review becomes AI System Risk Review in current product/exports/
  guides. Evaluation Lab becomes Platform Evaluation with an explicit application
  assurance purpose. Internal API/schema identifiers remain compatible.
- Workflow copy, empty states, source explanation and response-check labels are
  factual and shorter. Sidebar/About slogans and repeated repair reassurance are
  removed. Existing evidence/inference, sample, export and fail-closed behavior
  remains; the UI uses an Analysis withheld message for the known policy code.
- About's Graphviz graphic is removed completely and replaced by native theme-aware
  columns/containers with distinct SOC and risk-review branches. Product scope,
  current release and operational boundaries replace long prose.
- Activity retains filters and hidden internal errors, uses practitioner-facing
  workflow names and clearly identifies its role as platform activity.
- Application version is centralized as `2.3.0rc1` in `app/version.py`; root,
  FastAPI and UI status agree. No evaluation version or release tag changes.
- README is rewritten around current capability, product direction, architectural
  boundaries, meaningful evaluation milestones, clean setup, tests and deep links.
  Product documentation and the five-step demo are updated. Historical reports
  remain historical rather than being renamed retroactively.
- Readable `requirements.txt` stays unchanged. A 79-package exact Windows x64 /
  CPython 3.13.1 snapshot is generated from a fresh environment using the existing
  tested versions as constraints. No package manager or runtime capability is added.
- CI updates to verified official `checkout@v5` / `setup-python@v6` Node 24
  actions, preserving full history and Ubuntu/Python 3.13 checks.

## Files

New: `app/version.py`, `dashboard/navigation.py`, six files under
`dashboard/pages/`, `tests/test_release_candidate.py`,
`requirements-windows-py313.lock.txt`, the release-candidate guide and this report.
Two parent-level `.gitattributes` files preserve frozen V3.2 checkout bytes.

Updated: `app/main.py` naming/version only; Streamlit entrypoint, workflow/product
pages, presentation/error/export helpers and catalog caveat; associated dashboard,
product-helper and UI API tests; `.github/workflows/ci.yml`; README; product guide
20 and demo walkthrough. No analyzer, prompt, source/identity policy, registry,
reference pack, frozen report, suite, scorer or historical manifest is edited.

## Deterministic validation

The first adapted UI/helper/API group passed **78 tests**. New native navigation,
Overview, planned-route exclusion, copy, About structure, renamed exports and
centralized version tests passed **13 tests**. The first full regression passed
**1,284 tests**, one existing warning, **52.56s**; Ruff and whitespace passed.
Documentation-link and dependency-snapshot checks were subsequently added.
The pre-commit gate passed **1,286 tests**, one existing warning, **52.90s**;
full-repository Ruff and whitespace checks also passed. This is a net increase
of 16 deterministic instances from the starting point.

AppTest exercises every page without requiring model inference, with unavailable
backend handling. Original API-envelope, repair/fail-closed, source, sample,
export, Activity-filter and frozen evaluation regression tests remain. Modified
assertions update authorized UI labels, not historical scorer/identity meanings.
No live model generation or historical live evaluation is part of this sprint.

## Reproduction and warning decisions

A temporary full local clone and fresh virtual environment were created outside
the primary checkout. Installing the direct manifest constrained to the existing
tested package set succeeded; `pip check` reported no broken requirements.
`pip freeze` from that clean environment produced 79 exact package versions.
This avoids manufacturing versions or upgrading packages for freshness. The
primary `.venv`, `.env`, logs and model configuration were not changed.

The independent snapshot replay and hosted CI results are recorded below.
The snapshot is explicitly Windows/CPython scoped; no cross-platform or artifact
hash lock is claimed. Ubuntu CI uses the unchanged readable direct manifest.

The Node 20 action warning is addressed by the two Node 24 action updates.
Both action steps succeeded in hosted CI; no Node 20 deprecation warning was
found in the retrieved job logs. The independent Starlette/httpx Python warning
is documented, not suppressed or fixed through a new transport dependency.

## Clean-checkout correction and validation

The first independent replay at `a20386087861d9dc92a1387f69ab4cd1898a35e5`
installed the snapshot successfully and matched all 79 package pins exactly.
Full pytest then reported **1,280 passed, six failed**, one warning, **53.94s**;
Ruff passed and Git status was clean. This was an objective Windows checkout
defect: `core.autocrlf=true` changed the frozen V3.2 suite and four Markdown
review/triage files from LF to CRLF. The suite byte hash changed from recorded
`b55be3f59c6cce919f489d3fadbf72663d35c58c6b701ae76293e73e72c396f5`
to checkout-only `3400375d68a1568c760455beea2974a833c4ffaa575e854115f85a68445a8bce`.
Recorded review hashes also mismatched solely through newline conversion.

This was reported before correction. Two new parent-level `.gitattributes` files
set LF for the affected paths; no existing frozen suite, report, review,
historical attribute file, manifest or hash is edited. A deterministic effective
attribute regression check was added, bringing the suite to **1,287 tests**.
Commit `b09112a7f17cd4820af70879444222821074ec9c` records this correction.
A new full clone was checked out at that exact commit with local
`core.autocrlf=true`. It reused the independently created snapshot environment
from the first replay, without installing or changing packages. All 79 installed
pins matched the snapshot, `pip check` passed, and the suite's original byte
hash was restored. Full pytest passed **1,287 tests**, one existing warning,
**49.77s**; Ruff and whitespace checks passed and Git status was clean.

On resume, the primary checkout also passed **1,287 tests** in **46.98s**, with
the same warning, and Ruff/whitespace checks passed. The final copy audit found
three stray question marks in an evaluation caption, request-flow description
and analysis spinner. These were corrected with plain punctuation; the 29
dashboard/release tests passed in **6.20s**. No workflow behavior changed.

Hosted Ubuntu/Python 3.13 CI passed for both the product implementation
([run 40792634598](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/40792634598),
1,286 tests) and the checkout correction
([run 40794514940](https://github.com/akshayneal/local-ai-security-risk-platform/actions/runs/40794514940),
1,287 tests in 7.64s). Retrieved correction-job logs contained no Node 20
deprecation or Starlette warning. The Windows snapshot's existing Starlette
warning remains documented; no dependency upgrade was made to suppress it.

The final packaging commit contains the copy corrections and this closeout.
Its exact SHA, final local gate and hosted run are reported in the delivery
message rather than embedding a self-referential commit hash here.

## Visual inspection and remaining issues

Browser inventory reported **The browser access host is unavailable**, with no
available browser surface. The existing Windows Firefox path was already known
to lack supported URL-policy enforcement, so no bypass was attempted. No new
pixel-level visual inspection, screenshots or dark/light visual approval is
claimed. AppTest confirms structure/execution only.

The white architecture graphic is gone. About and Overview use theme-inheriting
native components without fixed graphic backgrounds, custom colors or HTML/CSS
layout. Desktop/narrow viewport layout, overflow, clipping, spacing and actual
dark/light appearance remain for the user's visual inspection. Browser access
was checked again after resuming and was still unavailable. The reproducibility
defect above is fixed; no test failures remain in the completed checks.

Existing product limits remain: finite identifier grammar, prompt-guided risk
semantics, provisional model classifications, residual support/formatting issues,
local inference latency, repair/withholding availability cost, timeout without
backend cancellation, no authentication and no live threat verification.

## Release recommendation

Ready for final human visual approval, subject to the final packaging gate
reported in the delivery message.
This is not visual approval or an operational safety claim. The remaining steps
are human desktop/narrow and dark/light review, any specifically requested visual
corrections, optional screenshots/demo capture, then separately authorized merge
and tag/version-finalization decisions. Planned workflows remain nonfunctional
presentation only. No merge to `main`, tag or deployment is performed.
