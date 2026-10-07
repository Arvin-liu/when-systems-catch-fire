# Ignition Research Operating System Architecture Roadmap R0

> Status: `PROPOSED_ARCHITECTURE_ROADMAP`
>
> Date: 2026-10-07
>
> Authority ceiling: this document records the next architecture direction only. It does **not** promote any component to Current, does not alter the active Codex task, does not authorize a merge, does not start Task230, and does not change scientific or governance contracts. Implementation resumes only after the currently running Codex task has finished and Owner/Chat review its result.

## 1. Direction

Ignition should evolve from a system that mainly selects and executes thinking operations into a higher-throughput **Research Operating System**:

```text
Frame
  -> Monitor
  -> Portfolio allocation
  -> Bounded attempts
  -> Candidate compression
  -> Machine-verifiable checks
  -> Independent review
  -> Typed transition proposal
  -> Owner / Chat architecture adjudication
  -> Accepted state change with lineage
```

The governing principle is:

```text
Generation authority != Verification authority != Adjudication authority != Promotion authority
```

A stronger executor is not sufficient by itself. As generation throughput rises, verification and adjudication bandwidth become first-class scarce resources.

## 2. Portfolio-level metacognition

AB-16 should eventually extend beyond operation-level selection.

Current question:

```text
What thinking operation should happen next?
```

Target questions:

```text
How many independent attempts are worth opening?
Which attempts should continue receiving budget?
Which attempts should be killed early?
When should the whole portfolio stop?
Is another candidate worth the verification debt it creates?
```

The controller should treat at least these budgets as explicit dimensions:

- compute budget;
- read/retrieval budget;
- verification budget;
- reviewer/adjudication budget;
- Owner attention budget.

A candidate is not valuable merely because it can be generated cheaply. Routing should consider expected value, usefulness, verifiability, and total generation + verification cost.

### Related operating rule

Long-running work may use:

```text
BOUNDED_BACKLOG_UNBOUNDED_WALL_CLOCK
```

with:

```text
CHILD_TASK_MUST_BIND_TO_EXISTING_PARENT_GOAL
```

Removing a wall-clock ceiling must not become permission to invent new goals. New directions discovered during execution remain `PROPOSED_FUTURE_WORK` unless explicitly admitted.

## 3. Independent Delegated Review Gate

Ignition needs a reviewer role that is independent from the executor's completion pressure.

### Executor role

The Executor / Work / Codex instance:

- implements;
- searches;
- runs experiments;
- produces evidence;
- creates artifacts;
- proposes state transitions.

It does **not** gain authority merely because it completed the work.

### Reviewer role

A separate reviewer receives a narrow, auditable `ReviewPacket`, for example:

```text
stage / goal
exact before-state digest
proposed after-state digest
requested transition
evidence manifest
mandatory gates
claim ceiling
frozen policy digest
rollback / failure handling
```

The reviewer returns only a typed result such as:

```text
APPROVE_BOUNDED
REJECT
REVISE
ESCALATE_OWNER
UNDERDETERMINED
```

The reviewer must be able to deny progress without being pressured to complete the executor's task.

### Reviewer hard boundaries

```text
REVIEWER_IS_NOT_TRUTH_AUTHORITY
REVIEWER_CANNOT_APPROVE_ITS_OWN_POLICY_CHANGE
APPROVAL_IS_ACTION_SCOPED_AND_STATE_BOUND
REVIEWER_CONTEXT_IS_SEPARATE_FROM_EXECUTOR
DENIAL_MAY_REDIRECT_BUT_NOT_EXPAND_SCOPE
UNRESOLVED_SCIENTIFIC_RULE_ESCALATES_OWNER
```

The reviewer may adjudicate compliance with already frozen rules. It must not define the scientific question, enlarge a claim ceiling, choose a new architecture doctrine, merge into public Current, or start a new major task on its own.

## 4. Approval receipts

Natural-language "looks good" approval is insufficient for long-running autonomous work.

A successful delegated review should eventually emit a machine-checkable `ApprovalReceipt` bound to exact artifacts:

```text
subject_digest
transition_type
review_policy_digest
evidence_manifest_digest
decision
approved_claim_ceiling
conditions
unresolved_assumptions
reviewer_identity
sequence / timestamp
```

A later stage may proceed only if the approval receipt binds the exact proposal and exact evidence it reviewed.

This should integrate with Typed Transition Integrity rather than become an unrelated second control plane.

## 5. Machine-verifiable witness layer

Ignition cannot formalize every architecture judgment, but it should continuously convert language-only assertions into machine-checkable witnesses where possible.

Priority witness types include:

- schema validation;
- digest binding;
- transition binding;
- expected-class manifests;
- deterministic replay;
- exact-head CI;
- typed outcomes;
- frozen scorers;
- explicit invariants;
- provenance lineage.

This is Ignition's practical "Lean-lite" layer: not a truth oracle, but a way to keep verification throughput from collapsing as executor throughput increases.

## 6. Human-review compression and curation

A successful episode should produce two distinct artifacts:

### Machine-review artifact

Contains exact state, hashes, manifests, gates, CI, receipts, lineage and reproducibility material.

### Human-review artifact

Answers only:

- what changed;
- why the change is currently credible;
- what remains unknown;
- which claim ceiling applies;
- whether Owner / Chat attention is actually needed.

The system should optimize not only for result production but for **review compression**. Producing evidence no human or reviewer can realistically absorb is adjudication debt.

## 7. Method extraction

Long research runs should not end with only `result + receipt`.

They should also attempt:

```text
reusable method extraction
```

Repeatedly useful mechanisms should be proposed for the thinking-operation library rather than rediscovered in each episode.

External reasoning summaries, when legally and operationally available, should be mined primarily for reusable operation patterns, not merely summarized for domain conclusions.

Possible targets include:

- bounded portfolio search;
- early branch elimination;
- evidence-first freezing;
- exact-state successor binding;
- deterministic admission;
- verification-aware stopping;
- failure-class separation;
- independent review routing.

Any extracted method remains candidate-level until independently tested inside Ignition.

## 8. Relationship to existing control responsibilities

The long-term division of responsibility is approximately:

```text
AB-16
  -> whether to continue thinking
  -> which operation to use
  -> how many attempts to open
  -> which branches receive more budget
  -> when the portfolio stops

AB-04
  -> what capability / model tier should be used

AB-02
  -> when raw evidence is worth rereading or retrieving

AB-06
  -> whether a state transition is correctly and completely bound

AB-19
  -> whether the work produced real R&D gain rather than activity

Delegated Review Gate
  -> whether an executor's proposed transition satisfies already-frozen rules

Owner / Chat
  -> scientific definition
  -> architecture choice
  -> claim-ceiling changes
  -> policy changes
  -> public Current / merge / major-task promotion
```

These labels describe intended architectural responsibility, not proof that every referenced AB already implements the target behavior.

## 9. Security approval is separate from epistemic approval

Codex product-level permission modes and Ignition epistemic review are different layers.

```text
Product permission / sandbox review:
"Is this action allowed to execute?"

Ignition delegated epistemic review:
"Does the frozen evidence and policy permit this state transition?"
```

Codex built-in Auto-review may be useful as a security / permission reviewer when that product mode is used, but it must not be treated as Ignition's scientific or architecture reviewer.

Likewise, running Codex with Full Access does not grant epistemic authority. Full Access can reduce permission interruptions; it does not answer whether evidence is sufficient, whether a result may freeze, or whether a scientific contract may change.

## 10. Adoption sequence

### R0 — Roadmap and authority freeze

- define the role split;
- define ReviewPacket and ApprovalReceipt candidates;
- enumerate transitions that are mechanical versus Owner-reserved;
- define reviewer failure and escalation semantics;
- make no runtime authority change.

### R1 — Shadow reviewer

- reviewer is read-only;
- reviewer decisions have no execution authority;
- compare reviewer decisions against existing Owner/Chat adjudications;
- measure false approvals, false denials, underdetermined cases and review cost.

### R2 — Bounded delegated approval

Only clearly mechanical transitions may be delegated, such as contract-complete deterministic continuation whose policy was frozen before execution.

Scientific definition changes, architecture choices, claim-ceiling expansion, merge/public-Current promotion and major-task start remain Owner/Chat reserved.

### R3 — Portfolio budget controller

Extend AB-16 with attempt allocation and explicit verification/adjudication budgets.

Measure whether extra generation produces usable information or merely creates review debt.

### R4 — Long-running research operation

Permit long or multi-stage execution against a bounded backlog, with:

- checkpoint/resume;
- independent reviewer gates;
- machine verification;
- typed receipts;
- escalation only when frozen rules cannot decide;
- no autonomous goal expansion.

## 11. Acceptance criteria

This direction should not be promoted merely because it sounds cleaner.

At minimum, later implementation should demonstrate:

1. executor and reviewer authority are technically separable;
2. reviewer cannot silently change its own policy or expand scope;
3. approvals bind exact proposal/evidence digests;
4. deterministic checks remain independently reproducible;
5. human review load decreases without increasing unsupported promotions;
6. reviewer disagreement and underdetermination remain visible;
7. long-running tasks stop less often for mechanical ambiguity;
8. scientific and architecture ambiguities still escalate rather than being guessed through;
9. portfolio control improves useful-result / verification-cost ratio;
10. failure attempts remain lineage-preserved and are not rewritten as success.

## 12. Failure / rollback criteria

Pause or roll back delegated review if any of the following occurs:

- reviewer approves an unbound or stale proposal;
- executor can influence reviewer policy during the same approval;
- review receipts cannot be deterministically tied to exact artifacts;
- automated approval expands claim ceiling or scientific scope;
- review compression hides material unresolved assumptions;
- throughput rises while verification debt grows faster;
- Owner / Chat receives fewer interruptions only because uncertainty is being silently suppressed.

## 13. Immediate execution boundary

As of 2026-10-07, this roadmap is documentation only.

The currently running Codex task is left untouched. No new architecture implementation task, reviewer pilot, merge, Current promotion, or Task230 start is authorized by this document.

Next action after the active Codex run completes:

```text
inspect its final marker + receipt + exact-head evidence
-> reconcile against this roadmap
-> decide whether R0 should become an admitted implementation task
```
