# REOS vNext LIGHT

Status: `OWNER_ACCEPTED_WITH_EXPLICIT_RESIDUALS`  
Runtime disposition: `KEEP_LIGHT_ONLY`

REOS is a research-execution control system. It records recoverable research obligations, bounded case state, references, review work and typed handoff. It is not a second knowledge-truth system and it does not decide whether a proposition is true.

## When to use it

Use `DIRECT_RESEARCH` when ordinary notes, a source ledger and a human review are sufficient.

Use `REOS_LIGHT` when a bounded question benefits from explicit obligations, dependency checks, source-family/access references, measurement boundaries, independent review and committed case reload. LIGHT adds process control; it does not add epistemic authority.

There is no available `REOS_FULL` runtime. No recovery layer is implied by this document.

## Minimal persisted kernel

One REOS case document contains:

- an embedded `ActivationDecision`;
- `ResearchCase` identity and operational state;
- a `QuestionContract` with an external preregistration reference/digest, an immutable compact frozen validation summary, a current compact summary, and append-only amendments;
- one acyclic `ResearchObligation` ledger;
- thin `ArtifactRef` rows;
- minimal `EvidenceRequest` retrieval/access states;
- explicitly `NONCANONICAL` `ClaimCandidate` annotations;
- typed `ReviewRequest` / `ReviewDecision` rows.

The compact validation summary contains only the question, scope, estimand, measurement boundaries, claim ceiling and stop conditions. The full preregistration, source bodies, evidence records and canonical claim registry remain external.

`HandoffBundle` is a deterministic projection. It names the receiving authority, object references, bounded allowed claims, scope, residuals and prohibited inferences. It is not a publication, acceptance, truth or claim-promotion state.

The standard-library CLI/API exposes only case initialization, validation, status, typed record append, review recording and projection-only handoff. Validators fail closed for malformed state, cycles, unknown references, authority upgrades, non-finite values, provider/model hard dependencies and generic `SUCCESS`.

## What REOS does not decide

REOS does not decide:

- source, claim, evidence, proof or claim-ceiling authority;
- epistemic status, no-upgrade relationships or federated governance;
- normative permission or action authorization;
- language/thought semantics;
- public Results Book publication;
- truth, causality, external validity, Owner acceptance or `EPISTEMICALLY_ACCEPTED`.

Those authorities remain in the existing Foundation, Epistemic Governance Kernel/Federated Planes, Charter, Language–Thought Logic Plane and Results Book/publication surfaces. Git, CI and iteration machinery remain the exact-state and history authority.

## Pilot result

The first real LIGHT pilot compared a blinded ordinary-research baseline with REOS_LIGHT on the same adult factual-item learning question. The public synthesis is [REOS vNext LIGHT pilot R1](../../reports/research/reos-vnext-light-pilot-r1.md).

The scientific result remained `NOT_IDENTIFIABLE_WITH_AVAILABLE_EVIDENCE`. The process result was `MIXED_VALUE_WITH_COST`. External validity is `NOT_ESTABLISHED` and `EPISTEMICALLY_ACCEPTED=0`. Source-change updateability was not exercised, and information gain versus bureaucracy remains `UNDERDETERMINED`.

## Deliberately absent

R1 does not implement or expose `ExecutionPacket`, `ExecutorLease`, `ResumeCapsule`, runtime idempotency, continuous supervision, executor substitution, distributed queues, broad evidence adapters, automatic budget optimization, UI/dashboard, provider/model lock-in, a second canonical store or an automatic acceptance route.

A future recovery round may be proposed only if a future real research task records a concrete LIGHT failure. `DEFER` is not authorization or a roadmap promise.

## Navigation boundary

The current system map is unchanged in R1. The map already represents the receiving authorities and adding a separate REOS node would create a new formal/public topology surface not required by this bounded capability. This page is the human-readable capability entry point; it does not add an L7 or truth layer.

