# OS Control Plane R2 gap audit — IGNITION-20260817-124

## Baseline identity

- Formal repository: `Arvin-liu/when-systems-catch-fire`
- Execution baseline: `origin/main=266426d7110af9ee921a020a46c3a0347aa364e9`
- Control source: `Arvin-liu/1111`, `origin/relay/current=c06c556cf6e98e8d4f0b004a8c15cd19a64b3cae`
- Task branch: `codex/ignition-124-os-control-plane-r2-20260817`
- Current architecture identity: `agent-platform-federation-r1`; map `0.8.0`; status `CURRENT_WITH_OPEN_OBLIGATIONS`; `EPISTEMICALLY_ACCEPTED=0`
- Reference executor: `REFERENCE_EXECUTOR / CONFORMANCE_EXECUTOR / FALLBACK_MINIMAL`; no live external invocation was made.

## Baseline experiment

The existing Supervisor R0 was run with two dependency-ready children, `ready-a`
and `ready-b`, whose write targets do not overlap. Both were accepted and the
episode reached `EPISODE_COMPLETED_VALIDATED`, but the trace was strictly
`ready-a → ready-b` and the maximum observed concurrency was `1`. The current
implementation selects `ready[0]` and executes it to return before selecting
another ready child. The machine receipt is
`data/operations/iterations/124/fixtures/baseline-concurrency-r1.json`.

## Gap classification

| Class | Confirmed gap | Required R2 boundary |
| --- | --- | --- |
| `CRITICAL_CONTROL_PLANE` | No canonical append-only event ledger, aggregate CAS, hash-chain replay, policy digest or durable dispatch/reconcile fabric. | Add typed event, policy, dispatch and reconciliation contracts that fail closed and are deterministic. |
| `CONCURRENCY_SAFETY` | Supervisor is sequential; no ready-set bound, resource intent leases, conflict matrix, deadlock/starvation policy or executor-slot ceiling. | Add bounded scheduler and atomic resource arbitration without adding an Agent shell. |
| `STATE_CONSISTENCY` | Supervisor trace is an in-memory projection persisted as a whole JSON state; Memory R1 has file locking but no versioned concurrent event absorption or stale-snapshot guard. | Add CAS/versioned operational state and deterministic snapshots/tails. |
| `EXECUTOR_FEDERATION` | Inventory records observed capabilities but health is not leased/expiring, and routing cannot consume a typed R2 capability/health lease. | Add capability/health leases, staleness, cooldown and bounded handoff. |
| `OPERATOR_USABILITY` | Existing status/trace surfaces are machine-oriented and do not explain queue, route, policy, conflict, health expiry or next action in natural language. | Add a bounded Driver Console with human-first status and optional JSON detail. |
| `PREEXISTING_RESIDUAL` | `CURRENT-FACTS-ORDER-DRIFT` remains order-sensitive in the inherited full discovery; `PROPAGATION-104-106` remains historical `NO_IMPACT_JUSTIFIED` incompatible with current derived paths; `PHASE-E-CWD-WARNINGS` remains a legacy path warning. | Audit after architecture changes. Close only with a semantics-preserving repair; otherwise retain exact disposition. |
| `DEFER` | Live providers, daemons, browser/network/message actions, vector memory, remote Git mutation, generic subagents and external account mutation remain out of scope. | Keep the Reference Executor freeze and provider-neutral offline fixtures. |

## Inherited targeted gates

The task-121/122/123 core regression and bounded gates passed at baseline:
143 focused unit tests, Current State Sync, executor inventory, federation
ownership/routing, Supervisor, Operational Memory and compact system-map checks.
The reconciliation validator continues to report the historical 104–106
records as invalid under the current derived path set; this is recorded as a
pre-existing residual, not silently converted to PASS.

## Claim ceiling

This audit establishes only repository structure, validator output and a
disposable offline scheduling observation. It does not establish production
autonomy, external executor success, universal safety, causality, Owner
acceptance, general intelligence or epistemic acceptance.
