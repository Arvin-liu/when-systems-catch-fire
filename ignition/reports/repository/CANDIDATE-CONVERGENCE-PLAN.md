# Candidate Convergence Plan — Line D

This plan describes how the four campaign lines and the pre-existing open candidate surface could converge. Everything here is `RECOMMENDATION_ONLY`; no step merges, marks Ready, closes, deletes or re-bases anything.

## Line relations

```text
main (cac043d4, iteration 114 accepted)
├── #190 Line A  Task 115 Checkpoint C recovery      [Draft -> main]
│        parent tip: f56edf33 (Task 115 Checkpoint B, WorkBuddy branch untouched)
├── #189 Zhiyuan writing editorial revision           [Draft -> main, pre-existing]
│        └── #191 Line B  independent review + CI repair [Draft -> #189 branch]
├── research/eight-track-...-r2                        [research, not formal knowledge]
│        └── #192 Line C  auditability/reproduction repair [Draft -> R2 branch]
└── Line D (this branch)  state ledger + invariants    [Draft -> main, absorbs none of A–C]
```

Line D observes Lines A–C as candidates only. It must not and does not cherry-pick them; its ledger and invariants are independent of their acceptance.

## Independent-review safety

- Lines A, B, C, D each live on isolated branches built from locked tips with ordinary commits and non-forced pushes; any one can be reviewed or discarded without touching the others.
- Line B's changes are canonical-generator outputs plus one review document; Line C's stay inside the R2 campaign root + validator/test paths; Line A's are Task 115-scoped; Line D's are governance/tooling/report surfaces.

## Ordering where dependency exists

1. #191 (Line B) can only land into the #189 branch; #189 itself then proceeds solely by owner adjudication.
2. #192 (Line C) can only land into the R2 research branch; R2 acceptance is a separate owner/GPT decision.
3. #190 (Line A) targets main but is gated by `R2_EMPIRICAL_CALIBRATION_PENDING` and Task 115's non-terminal phase.
4. Line D targets main and is safe to review independently of A–C; if accepted, it gives the owner a durable state ledger + invariant gate.

## No-merge decision graph for GPT/owner

```text
For each Draft PR P in {#190, #191, #192, #189, Line D PR}:
  Q1 Is the evidence in the PR body + review packet sufficient?  (owner reads)
     no  -> leave Draft, request changes. (no other action)
     yes -> Q2
  Q2 Does P depend on another candidate (stacked)?
     yes -> the parent must be adjudicated first; do not merge child ahead of parent.
     no  -> Q3
  Q3 Is P a research candidate (R2 line)?
     yes -> it can land only into its research branch; never promotes to formal knowledge here.
     no  -> Q4
  Q4 Owner explicitly authorizes merge AND marks Ready?
     yes -> merge by owner.   no -> remain Draft.
Terminal actions (tag / terminalize Task 115 / Task 116 / alter Task 114) are OUTSIDE this campaign entirely.
```

## Recommended sequence (RECOMMENDATION_ONLY)

1. Review Line B (#191) first — it repairs deterministic CI, unblocking human review of #189's substance.
2. Review Line C (#192) — restores R2 metadata trustworthiness before anyone judges R2 results.
3. Review Line A (#190) — recovered Task 115 work, with its recovery manifest and replay evidence.
4. Review Line D (this PR) — installs the state ledger and invariant gate.
5. Adjudicate #189 substance, R2 acceptance, and Task 115 continuation as separate owner decisions, each after its repair line has landed.

## Explicit non-actions

No merge, no Ready, no auto-merge, no tag creation/movement, no closing of old PRs, no deletion of branches, no rebase/squash/amend/force-push, no R2 promotion, no Task 115 terminalization, no Task 116, no alteration of Task 114 terminal history.
