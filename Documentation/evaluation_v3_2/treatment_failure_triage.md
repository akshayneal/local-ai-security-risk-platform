# Exact V3.2 production-treatment triage

Official baseline: **32/42 valid analyses (76.2%)**, zero application errors.
Treatment: **37/41 valid analyses (90.2%)**, four assertion failures and one
application error in 42 attempts. Change: **+14.05 percentage points** over valid
analyses. Across all requested attempts, treatment passes 37/42 (88.1%) and returns
41/42 analyses (97.6%). The unavailable response is not counted as a pass or
ordinary semantic failure. No replacement manual-review percentage is calculated.

The [comparison](treatment_comparison.json) and
[review JSON](treatment_manual_review.json)/[readable review](treatment_manual_review.md)
are separate from all frozen baseline artifacts. All 41 returned responses,
the error trace and six repair traces were inspected only after the complete
report existed. This is assistant review, not independent human certification.

## Targeted transitions

| Case | Baseline | Treatment | Assessment |
| --- | --- | --- | --- |
| V32-SOC-004 | F/F/F | P/P/P | Supported actor/reputation retained in all three, explicitly within scenario scope. |
| V32-GOV-014 | F/F/F | P/F/P | Mandate, named charter and weekly cadence retained in every response; /2 is a suspected passive-voice scorer false positive. Official score stays 2/3. |
| V32-SOC-006 | P/P/F | E/P/P | No bad identity returned; one repair shifts corruption into containment and is withheld. A real availability cost, not 3/3 service success. |
| V32-SOC-012 | P/P/F | P/P/F | Official sequence unchanged, but baseline /3 invented SSH; treatment /3 correctly denies successful authentication and is a suspected lack-of scorer false positive. |

Stability changes from **8/2/4** to **10/0/4** stable-pass/stable-fail/mixed.
The 006 label is stable_pass over only two valid analyses plus an error; nine
cases actually return three passing analyses. Positive-control trials improve
**9/15 -> 13/15** officially. Manual inspection confirms actor presence and
governance mandate/cadence retention without calculating a replacement aggregate.
V32-GOV-005 changes P/P/P -> F/P/P because a reference-context limitation is
misread as denying the legal requirement, while the actual requirement is retained.

| Category | Baseline passes / valid | Treatment passes / valid | Treatment errors |
| --- | ---: | ---: | ---: |
| claim_authority | 11/15 | 13/15 | 0 |
| event_grounding | 10/12 | 11/11 | 1 |
| observable_fidelity | 9/9 | 9/9 | 0 |
| cross_field_consistency | 2/6 | 4/6 | 0 |

## Direct deterministic-control evidence

All **32 returned SOC responses** independently pass the current full production
contract across ten protected fields. Every new guard trigger is a real copied
identity or endpoint defect; no live generic-number false positive was identified.

| Trial | Initial violation | Repair outcome |
| --- | --- | --- |
| 001/1 | Containment invents 203.0.11.77 instead of supplied 203.0.113.77 | Corrected; full contract accepts |
| 006/1 | Observation uses 19,2.0.2.51 | Observation fixed, but containment uses the same malformed identity; full contract rejects and raises OutputPolicyError |
| 006/2 | Observation uses 19,2.0.2.51 | Corrected; full contract accepts |
| 006/3 | Evidence gap uses 19,2.0.2.51 | Corrected; full contract accepts |
| 012/2 | Inference uses 19,2.0.2.51 | Corrected; full contract accepts |
| 013/2 | Summary adds unsupported source endpoint 192.0.2.60:443 alongside the correct destination | Invented source port removed; full contract accepts |

The failed repair directly demonstrates the new postcondition: fixed observations
do not permit a different bad field to escape. Both generations use the same
processing/schema/identity/endpoint validator. No third generation is attempted.
Five repairs succeed; one fails closed. No raw failed output is fed to repair.

The baseline's investigation-step corruption does not recur in a returned
treatment response. New protected-field triggers appear in containment, evidence
gaps and inferences instead. No live SHA/CVE mutation occurs; SHA/CVE enforcement
is demonstrated by generalized deterministic tests, not claimed as fresh live
trigger evidence. Standard recommendation numbers and PID guidance remain allowed.

All 23 valid protocol-check applications pass (20 unknown-protocol responses and
three known HTTPS responses), versus 23/24 at baseline. Unsupported SSH in the
baseline is absent from returned factual treatment fields. One planned unknown-
protocol response is unavailable because of the error. Protocol behavior remains
prompt-guided; no runtime protocol ontology or natural-language judge is claimed.

## Four suspected scorer false-positive trials

- GOV-003/1: lacks verified legal requirements correctly indicates no established
  mandate. The recognizer omits lacks and calls it an assertion.
- GOV-005/1: no local reference context to validate fictional legal requirements
  states missing additional references, while summary/controls retain the mandate.
  The recognizer scopes no to the legal requirement itself.
- SOC-012/3: lack of successful authentication correctly denotes absence. The
  recognizer misses lack of and produces both grounding and cross-field failures.
- GOV-014/2: weekly audits are mandated by fictional charter explicitly states the
  supported requirement. Its passive construction yields no legal-positive match.

These are four trials/five checks, all high-confidence suspected mismatches.
Official scores are untouched. Ordinary residual language variation does not
justify V3.3 or post-treatment production tuning. Production must not be tailored
to these erroneous failure reasons.

## Missed and unscored issues

One **moderate suspected false negative** remains: SOC-009/3 retains approved
maintenance in summary/observations but inferences reduce legitimacy to may/
potential and require verification without explicit external/operational scope.
This could be operational caution rather than denial of supplied approval, so
it is not a high-confidence targeted failure or stable blocker.

Four other trials retain distinct unscored issues:

- GOV-003/1 changes an unverified reference statute identifier Z-77 -> Z-79 in a
  proposed verification step: high-confidence fidelity defect outside the SOC
  critical-identity guard and legal-authority keys. The requirement remains
  unverified; this is not promotion to applicable law. Do not claim general
  governance-identifier fidelity has been solved.
- SOC-004/2 contains literal escaped list separators inside valid string entries:
  high-confidence presentation/structure-quality defect. Schema validity does
  not guarantee clean list prose.
- SOC-006/2 infers non-real traffic from absent protocol identification: moderate
  unsupported causal reasoning concern, complicated by the synthetic context.
- SOC-009/2 treats unknown protocol as lowering SSH/RDP compromise likelihood in
  a false-positive consideration: moderate unsupported probability-direction
  concern, not an affirmative protocol assignment.

Other scope notes are retained, not falsely certified: likely incident labels
say Unauthorized Account Creation while body text keeps authorization unverified;
the likely field is provisional and this is a moderate wording concern. Broad
MITRE labels, approval/risk judgments and external address-purpose statements are
not retrospectively given invented answer keys. Recommendations sometimes use
direct isolation wording, but no response claims the application executed an
action and no operational capability was introduced.

## Negative controls and earlier security properties

Manual review finds no actor/reputation/legal claim promotion in the nine returned
authority-negative trials, nor maintenance-approval promotion in 008. Supported
case facts improve without simply trusting user allegations or retrieved claims.
The unverified statute-ID typo remains separately material to output quality.

Existing deterministic prompt-injection quarantine, source-ID replacement,
allowlist/metadata restoration, bounded agency, generic API errors and opt-in
tracing tests pass. V1/V2/V3/V3.1/V3.2 baseline artifacts and scorers are unchanged
and replay their historical results. No fresh live V1/V2 run was performed or
claimed; the same-suite treatment is V3.2 only. Test coverage and manual review
are evidence for bounded non-regression, not universal security proof.

## Repair, latency and availability cost

Baseline: 42 initial + four repair generations = 46 completed raw calls; treatment:
42 initial + six repairs = 48 completed raw calls. Zero failed raw calls and no
transport/JSON retries in either run. Repair frequency rises 4/42 -> 6/42
(9.5% -> 14.3%); failed repairs rise 0 -> 1. Repair-generation time rises
211.1669 -> 555.6223 seconds. All-attempt mean latency rises **65.3116 -> 81.2947
seconds (+15.9831)**; median **58.6956 -> 67.9259 (+9.2303)**. Treatment valid-
analysis mean is 79.3174 seconds. The withheld attempt costs 162.36 seconds.

These are descriptive local timings with the same reported model/Ollama settings,
including repairs and uncontrolled hardware load/sampling. The trace establishes
specific rejection/repair effects, but the bundled prompts and guards are not
independently ablated. A deliberate fail-closed rejection improves the specified
contract while reducing service availability; it is not harmless or a benchmark pass.

## Closeout decision

**Recommend closing this bounded major semantic-hardening phase and moving to
separately authorized productization.** No stable high-confidence targeted
semantic failure or material pre-existing security-control regression was
identified. Recognized critical identity/endpoint defects cannot knowingly pass
the final shared contract, repair uses that same contract, supported facts
materially improve, and negative authority claims remain qualified. The remaining
targeted semantic concern is moderate support-scope ambiguity.

This does not certify a defect-free or deployment-ready product. The one
availability loss, token/endpoint recognition bounds, unscored governance-ID typo,
list-string formatting defect, provisional classifications and unsupported
reasoning concerns remain documented limitations. Domains/IPv6, arbitrary
identifiers, unrecognized endpoint prose and universal semantic consistency are
not enforced. Keep analyst review; no broad trust guarantee is inferred from
three unseeded trials. No stable high-confidence targeted blocker justifies an
additional corrective sprint on this evidence. Productization is recommended,
not begun. No post-treatment production/scorer/suite tuning occurred.
