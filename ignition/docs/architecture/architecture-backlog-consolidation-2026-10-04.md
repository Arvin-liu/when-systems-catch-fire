# Architecture Backlog Consolidation — 2026-10-04

Status: planning / handoff consolidation only.

This document consolidates architecture directions discussed across multiple Owner/GPT conversations and compares them with the repository's current architecture. It does **not** promote any candidate to Current, assign a formal task number, authorize Task230, modify Task229 experimental semantics, or claim that an external architecture result transfers to Ignition.

## Status vocabulary

- `ALREADY_CURRENT`: implemented/merged architecture or governance foundation already represented by Current repository authority.
- `RECORDED_CANDIDATE`: candidate has a bounded written design, but is not Current and is not yet authorized for execution.
- `NEEDS_GAP_AUDIT`: prior discussion/design exists, but overlap with Current components and the true missing surface must be re-established before implementation.
- `NEEDS_SYNTHETIC_PILOT`: candidate is defined well enough for a bounded synthetic/offline comparison before any Current registration.
- `DEFERRED`: consciously postponed; not a current implementation target.
- `SUPERSEDED`: an earlier target architecture/assumption has been replaced by a more precise direction; retained only as historical context.

A backlog label is not epistemic acceptance, implementation evidence, Owner approval for execution, or Current capability.

## Consolidated backlog

| ID | Architecture direction | Status | Current overlap / reason | Next gate |
|---|---|---|---|---|
| AB-00 | Existing Ignition OS control spine: Kernel/Runtime, Pack-aware routing, Reasoner Gateway, resource arbitration, bounded scheduler, health lease, queue/backpressure, Operational Memory, External Agent Federation, Durability/Lifecycle, ARN, Operating Method | `ALREADY_CURRENT` | These are the foundations new work should extend rather than duplicate. Current status/claim ceilings remain governed by repository authorities. | Preserve as substrate; do not create second control plane. |
| AB-01 | Reliable Context Construction / Reliable Context Operating Layer | `NEEDS_GAP_AUDIT` | Cross-conversation design exists but is not cleanly represented in the current handoff. Candidate role: select, filter, organize and attribute context from authoritative assets without changing their epistemic status. | Map overlap with Operating Method, Knowledge Experience, REOS LIGHT, ARN and Operational Memory; freeze exact missing interfaces before coding. |
| AB-02 | Query-conditioned Raw Evidence Navigation (`QUERY_CONDITIONED_RAW_EVIDENCE_NAVIGATION_R0`) | `NEEDS_SYNTHETIC_PILOT` | Candidate already recorded from Sirchmunk/LENS: `EvidenceRequirement[]`, query-dependent `EvidenceWindow`, low-cost priors, propose→observe→update, explicit budget/stopping, source revalidation. | Dynamic-corpus A/B test against current deterministic index on freshness, evidence coverage, grounding, stale-answer rate and cost. |
| AB-03 | Versioned Current Scientific Understanding (`CurrentScientificUnderstanding`) | `NEEDS_GAP_AUDIT` | Candidate already recorded, but its exact relationship to claim registry, source evidence, Knowledge Experience, REOS and supersession governance is not yet frozen. | Define schema and authority boundary: as-of time, evidence delta, applicability, consensus/dispute, uncertainty, predecessor/supersession/downgrade. |
| AB-04 | Capability-tiered execution routing (`CAPABILITY_TIERED_EXECUTION_ROUTING_R0`) | `NEEDS_SYNTHETIC_PILOT` | Candidate recorded from MoHGE-inspired cross-layer analogy. Missing layer is explicit capacity matching between task demand and executor selection. | Compare uniform-high-capacity, single-stage routing and two-level tier→executor routing using validated completion, p95 latency, escalation and cost-per-validated-completion. |
| AB-05 | Concurrent heterogeneous multi-Agent orchestration | `NEEDS_GAP_AUDIT` | Current repository has bounded scheduler/resource arbitration, but handoff still explicitly excludes Current multi-Agent concurrency. Recent Task229 overnight lanes provide useful design observations but are not a Current capability. | Identify minimal delta from bounded scheduler to isolated multi-lane DAG execution: write-domain ownership, one-way feedback channels, protocol stop, audit and failure isolation. |
| AB-06 | Cross-contract integrity / reference binding | `NEEDS_GAP_AUDIT` | Earlier design discussions converged on identity/binding consistency across source, object identity, projection, surface, release/admission and action. Current later architecture may already absorb part of this through lifecycle/admission/durability contracts. | Re-audit whether a global invariant is still needed; test bindings such as `(object_id, version, scope, lifecycle_epoch)`, claim→action and approval→action before adding another architecture plane. |
| AB-07 | Provider/runtime execution contract R1 | `RECORDED_CANDIDATE` | Task229-R4 exposed concrete substrate gaps: live backend acceptance, empty model-facing tool surface, hard timeout, transport-vs-successor-payload byte semantics, payload cap and one-request-per-process isolation. A runtime-prereg candidate exists, but R1 is not established. | First reconcile formal control state, then freeze/test a provider runtime preregistration revision before any R4 live unit. This is substrate, not a new truth/knowledge layer. |
| AB-08 | Long-term vector/embedding memory as a required core memory plane | `DEFERRED` | Current architecture explicitly excludes it; LENS-style source-first navigation reduces the need to make vector memory a truth-bearing substrate. | Revisit only after retrieval/context pilots show a repeatable gap not covered by deterministic index + raw-source navigation + bounded Operational Memory. |
| AB-09 | Always-on daemon / autonomous long-running service as a Current architecture target | `DEFERRED` | Current boundaries do not establish a production daemon or unrestricted autonomy. | Revisit only after live provider/runtime, lifecycle/recovery, scheduler and Owner-control obligations are independently established. |
| AB-10 | Universal static-index-only retrieval as the target research architecture | `SUPERSEDED` | Replaced by a hybrid stance: stable/hot material may use indexes/caches, while freshness-sensitive material must be able to return to current raw sources. | Retain indexes as priors/accelerators, not universal current-truth authority. |
| AB-11 | Provider-bound direct task→named-model routing as the desired end state | `SUPERSEDED` | Replaced at candidate level by provider-neutral task-demand→capability-tier→executor routing. | Keep provider/model identity at the executor/admission layer, not as the semantic task-routing ontology. |

## AB-01 — Reliable Context Construction / Operating Layer

Candidate pipeline:

`Repository / Registry → Knowledge Experience → Reliable Context Layer → Agent / Generator → Answer Audit`

The candidate layer should be a **derived projection**, not a second truth store.

Minimum candidate responsibilities discussed across Owner/GPT sessions:

- support/evidence filtering;
- epistemic gate before context admission;
- context organizer and structured context packet;
- claim/source attribution;
- explicit `CONTEXT_GAP` detection;
- targeted re-retrieval when context is insufficient;
- anti-self-ingestion: model output or generated context cannot silently become new evidence for itself;
- source/version/freshness binding;
- uncertainty and unresolved-residue preservation.

Non-negotiable boundary:

> Context may select and organize authoritative material; it may not promote, rewrite or manufacture the epistemic status of that material.

Relationship to AB-02:

`Question → Reliable Context → detect Context Gap → EvidenceRequirement → Raw Evidence Navigation → reassemble Context`

Therefore AB-01 is the context control plane; AB-02 is a candidate gap-repair/retrieval mechanism beneath it.

## AB-02 — Query-conditioned Raw Evidence Navigation

Candidate invariant:

`MEMORY_IS_RETRIEVAL_HINT_NOT_CURRENT_AUTHORITY`

Historical retrieval experience, deterministic indexes, ARN relations and aliases may supply priors. The answer must still be grounded against the current source when freshness or factual validity matters.

Candidate loop:

`EvidenceRequirement → prior narrowing → propose → observe raw source → update → sufficiency/budget stop`

Successful searches may be stored as `RetrievalExperience` / `EvidenceCluster` with status:

`NONCANONICAL_RETRIEVAL_PRIOR`

Reuse frequency or similarity must not promote a result into canonical truth.

## AB-03 — CurrentScientificUnderstanding

Candidate invariant:

`CURRENT_SCIENTIFIC_UNDERSTANDING_IS_VERSIONED_NOT_ETERNAL_TRUTH`

The view should represent the best supported synthesis **as of a stated time**, not “the newest paper”.

Required future fields should include at least:

- `as_of`;
- applicability/population/system boundary;
- evidence set and evidence level;
- consensus / dispute structure;
- predecessor;
- `evidence_delta`;
- `change_reason`;
- uncertainty;
- supersession / downgrade / split conditions.

Two directional constraints:

1. old understanding changes only when the evidence delta is sufficient;
2. the new Current understanding must itself remain explicitly revisable.

Relationship:

- raw source = evidence anchor / factual verification;
- CurrentScientificUnderstanding = interpretation calibration;
- historical knowledge = navigation prior;
- claim governance remains the authority boundary over all three.

## AB-04 — Capability-tiered execution routing

Candidate chain:

`Operation / QuestionContract → TaskDemandProfile → ExecutionGroup → Executor → Validator`

`TaskDemandProfile` should prefer observable requirements over a model's unsupported self-report of difficulty. Candidate dimensions include:

- input/context scale;
- tool/network requirement;
- DAG width/depth;
- permission/externality;
- freshness requirement;
- proof/validation obligation;
- failure cost;
- estimated token/tool/wall-clock budget;
- independent-review requirement.

`ExecutionGroup` should be provider-neutral (for example LIGHT/STANDARD/DEEP/REVIEW only if later preregistered), with declared capability, cost/latency envelope, context/tool ceiling, validation obligation and escalation policy.

Candidate routing principles:

- two-level routing: capability tier first, executor second;
- smallest-sufficient executor under hard safety/permission/validation floors;
- explicit escalation with preserved first-failure history;
- capability group decoupled from provider/host placement;
- health/queue/backpressure only choose within an already adequate tier;
- optimize cost-per-validated-completion, not raw cheapness.

Cross-layer warning:

MoHGE token→expert routing is inspiration only. `token complexity ≠ Agent task complexity`; load balance does not imply correctness; executor capacity does not imply truth authority.

## AB-05 — Concurrent heterogeneous multi-Agent orchestration

Do not infer Current capability from Task229's temporary overnight multi-lane execution.

Candidate future pattern should preserve:

- dependency DAG and bounded concurrency;
- one writer per worktree/write domain;
- isolated live-experiment lane where required;
- validator/audit lanes as one-way consumers unless a preregistered hard-stop channel fires;
- append-only event/receipt trail;
- backpressure and health lease;
- explicit global/protocol stop;
- failure isolation;
- no implicit permission or scope expansion through delegation.

The design should reuse OS Control Plane records rather than add a second scheduler/control plane.

## AB-06 — Cross-contract integrity / reference binding

This is intentionally a gap audit, not an implementation commitment.

Questions to re-establish against the current repository:

- Is one object represented consistently across identity, version, scope and lifecycle epoch?
- Are Current projections bound to the exact canonical object/version they summarize?
- Can release/admission/surface projections silently refer to stale or differently scoped objects?
- Are claim→action and approval→action bindings exact and replayable?
- Do provenance records include the claim ceiling and accountable actor/authority, rather than only a complete-looking history?

Historical diagnostic phrases such as `PROVENANCE_WITHOUT_CEILING` and `COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY` should be treated as leads to re-test, not automatically-current defects.

## AB-07 — Runtime/provider execution substrate

The Task229-R4 runtime block is architecture-relevant evidence because it exposed a missing verified live-execution boundary.

Required distinction for any revised runtime contract:

- provider `transport_response_bytes`;
- exact `successor_payload_bytes`;
- decoded successor object.

A payload limit must specify which layer it constrains.

Future preregistration should also solve the backend-acceptance paradox: if model/effort acceptance must be known before the first scientific unit, either preregister a target-blind synthetic infrastructure canary or explicitly let the first matrix unit carry that risk.

This runtime substrate is a dependency for later live capability-tier routing and multi-Agent orchestration; it does not itself establish either.

## Dependency view

`AB-00 Current foundations`
→ `AB-07 live runtime substrate`
→ `AB-04 capability-tier routing`
→ `AB-05 concurrent heterogeneous orchestration`

`AB-00 Current foundations`
→ `AB-01 reliable context`
→ `AB-02 raw evidence navigation`
→ `AB-03 current scientific understanding`

`AB-06 cross-contract integrity` is a horizontal audit across both chains and should be performed before broad architectural promotion.

## Recommended implementation order

### Wave 0 — unblock the live substrate

- reconcile the formal relay/control-state mismatch currently blocking the Runtime R1 task;
- establish the new runtime preregistration without running R4 scientific units;
- independently review before any live matrix execution.

### Wave 1 — architecture gap audits

Run read-only audits for:

- AB-01 Reliable Context;
- AB-03 CurrentScientificUnderstanding integration;
- AB-05 multi-Agent scheduler delta;
- AB-06 cross-contract integrity.

The output should be “already covered / true gap / duplicate / conflict / superseded”, not code by default.

### Wave 2 — bounded synthetic pilots

- AB-02 raw evidence navigation;
- AB-04 capability-tier routing;
- AB-01 context construction only after its gap audit identifies a real missing plane.

No pilot result automatically registers a Current capability.

### Wave 3 — compose only validated deltas

Only after separate pilots establish repeatable net value should Ignition consider composing:

`Reliable Context + Evidence Navigation + CurrentScientificUnderstanding`

and

`Runtime Substrate + Capability Routing + Concurrent Orchestration`

Each composition still requires its own formal iteration, claim ceiling, propagation closure, exact-head validation and receipt.

## Consolidated long-term pipeline

Candidate long-term request path:

`Owner Intent / Question`
→ `QuestionContract`
→ `Reliable Context Construction`
→ `Context sufficient?`
→ if no: `EvidenceRequirement / Raw Evidence Navigation`
→ for science: `CurrentScientificUnderstanding calibration`
→ `Context reassembly`
→ `TaskDemandProfile`
→ `Capability Tier`
→ `Executor Selection`
→ `Bounded Concurrent Orchestration`
→ `Validator`
→ `Receipt / Provenance / Audit`
→ bounded retrieval/routing experience as prior.

The return path must not create automatic truth escalation.

## Backlog governance rule

Future architecture discussions that materially propose a new plane, router, memory, executor class, authority, scheduler or evidence lifecycle should be entered here or in a successor canonical backlog with:

- candidate name;
- current overlap;
- primary status from this vocabulary;
- source/conversation or external inspiration;
- claim ceiling;
- dependency;
- next gate;
- supersession relation if any.

No conversation-only architecture direction should be treated as safely handed off until it appears in this backlog or a later canonical successor.
