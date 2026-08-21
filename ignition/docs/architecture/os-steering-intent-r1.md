# OS Steering, Intent, and Obligation R1

This document describes the repository-local steering plane introduced by IGNITION-129. It is a control-plane contract for durable direction, Goal state, obligations, arbitration, and human-readable next-work explanations. It is not a claim that the repository knows an actual Owner preference, has completed a real-world objective, or has established production or external truth.

## Authority boundary

The canonical chain is explicit:

`OWNER_DECLARED` or `OWNER_APPROVED_DERIVED` → canonical Intent → versioned Goal → explicitly accepted Commitment → Episode/Run binding → bounded Action.

`SYSTEM_DERIVED_PROPOSAL`, `EXTERNAL_REQUESTED_PROPOSAL`, and `HISTORICAL_IMPORTED` remain proposals or historical records until an explicit Owner-authorized transition. Repeated behavior, profile data, memory, chat, a successful run, a test, a receipt, a Pack result, or an executor report cannot silently cross that boundary.

## State and dependency separation

Intent and Goal lifecycle transitions preserve actor, authority, reason, evidence, and version lineage. A Goal can be `PROPOSED`, `ACTIVE`, `PAUSED`, `BLOCKED`, `SATISFIED`, `ABANDONED`, `SUPERSEDED`, or `FAILED_BOUNDED`; reopening a terminal Goal creates an explicit successor version. A child Run or Episode may report `PASS`, but only an independent Completion Contract evaluation can produce a Goal satisfaction decision.

Long-term Goal dependency edges are held in a `LONG_TERM_STEERING` graph. The existing Supervisor run DAG remains an execution coordination structure. Neither graph may impersonate the other or promote an execution result into Intent authority.

An `EpisodeGoalBinding` records the primary/secondary Goal references, objective digest, bound Run IDs, Episode status, Run outcomes, and handoff identities. Supervisor status changes, a `PASS` Run, or executor-instance handoff preserve the binding's Goal status and mark completion as `INDEPENDENT_CONTRACT_REQUIRED`; they never mutate the canonical Goal.

Before a handoff or next-work dispatch, `GoalDriftGuard` compares the objective digest, acceptance criteria, authority source, superseded references, memory conflict flags, and stable handoff identity. Objective/acceptance/handoff drift pauses for reconciliation; proposal-to-Owner escalation or a memory conflict requires human review. No drift report promotes a proposal or silently repairs a Goal.

## Priority and arbitration

Priority is an ordered tuple of explicit rules: eligibility/permission, active Owner override, Owner rank, commitment state, temporal state, dependency criticality, risk, and bounded fairness age. A telemetry score may be emitted for inspection, but it is not authoritative and cannot override permission, safety, blocked, stale, superseded, or executor-unavailable state.

Conflict arbitration records the conflict type, all candidate decisions, the selected candidate if one exists, the reasons for every skipped candidate, and whether reconciliation or human review is required. Permission failures are fail-closed. Safety conflicts without explicit Owner approval enter `HUMAN_REVIEW`. Stale/superseded intent and unavailable executor state enter `RECONCILIATION_REQUIRED` rather than being guessed through.

## Why-next surface

`DecisionTrace` is the durable explanation surface. It answers:

- why this Goal is next now;
- why each other candidate was skipped or blocked;
- what permission, budget, resource, deadline, commitment, and dependency inputs were used;
- which Owner override, Pack, and executor references were selected;
- which unknowns remain unresolved.

The trace is intentionally human-readable and machine-validatable. It does not contain private prompt material or hidden reasoning, and it does not claim that a selected bounded Run has satisfied its parent Goal.

## Claim ceiling

All R1 steering artifacts are repository-local deterministic state models and offline validation machinery. They do not establish Owner acceptance, production readiness, live external execution, real-world completion, `CURRENT_WITH_OPEN_OBLIGATIONS` closure, or `EPISTEMICALLY_ACCEPTED=1`.
