# SOC Policy & Governance Review: design only

No runnable prototype, endpoint, feature flag, navigation entry or model generation
is implemented. The released two-workflow selection is unchanged. This is the
authorized alternative when the conditional prototype gates are not sufficiently met.

## Go/no-go assessment

| Gate | Disposition |
| --- | --- |
| Mini-Sprint 3.5 closed and checkpointed | Yes, 47f0386 with successful exact-SHA CI. |
| Support experiment informs implementation | Yes, 43 frozen cases and explicit false-abstention cost. |
| Policy authority/applicability validated for a runnable reasoning workflow | Partial: exact reviewed structured fixtures are validated, but natural policy text and applicability to incident/action language remain unassessed; one valid prose answer is lost. |
| Shared Inspector/contracts stable | Automated current-workflow checks pass; user visual QA remains pending. |
| Existing workflow regression checks | Passing checkpoint; final gate reported in sprint closeout. |
| Capacity can deliver a defensible full vertical slice | Prioritize actual current-workflow inspection, provenance, evaluation and preservation rather than imply policy reasoning is solved. |

The authority/applicability gate is not satisfied for a general runnable policy
reasoner. A fixture-only demo could run, but would not resolve this evidence gap.
Current model body-level C2, mandatory-control and implementation overclaims must
remain visible. The third workflow is therefore not activated by this sprint.

## Draft architecture and trust boundaries

Incident context and proposed action remain untrusted case data. Application-reviewed
policy fixtures/sidecar metadata establish source identity, scenario scope, current
version, workflow and explicit access eligibility. User notes and document content
cannot grant access, create organizational authority or change the current version.
All eligibility precedes ranking and support assessment.

The shared contract then separates a scoped policy requirement from implementation
evidence, proposed escalation and actual approval. A requirement to obtain an approval
does not mean approval was granted. Any local model output would remain a proposed
review aid, not authorization or an executed containment action. Model prose cannot
rewrite application-owned authority/provenance. Conflicts remain explicit.

The isolated draft request/proposal contracts live in
`evals/soc_policy_design/contracts.py`. They accept only two synthetic scenario names,
bounded incident/action/notes and no access/policy grants. Proposal metadata fixes
application approval to not granted/verified, human review to required and scope to
synthetic fixture only. These are design shapes, not public API schemas or a claim
that model prose is validated. They are not imported by the application.

[Synthetic fixtures](policy_review_design/scenarios.json) define two distinct units
with different approval roles and retention requirements. Their labels simulate
reviewed application metadata; they are not real organizational policies or an
independent human adjudication. Tests use the existing retriever/assessor contracts
to prove unit separation, unchanged source authority and requirement-versus-approval
distinction. No real registry, SSO, organization repository or connector is added.

## Requirements for a separately authorized prototype

Freeze policy/action applicability judgments and adversarial positives before model
outputs; provide a reviewed policy trust path and explicit current-version gate;
measure prose support and missed obligations; keep source grants out of user/model
text; add source sanitation and bounded local reasoning; integrate API and Streamlit
behind one disabled-by-default experimental flag. Flag-off behavior must preserve
the existing workflow selector and endpoints. Approval metadata must never be model
controlled. Test false approval claims, wrong-unit scope, conflicting policy, mission
continuity and source injection. No automatic actions or release-ready label.

Do not broaden this design into automatic authorization to implement or release a
third workflow. **USER VISUAL QA PENDING** for the current Inspector; no browser or
desktop control was used.
