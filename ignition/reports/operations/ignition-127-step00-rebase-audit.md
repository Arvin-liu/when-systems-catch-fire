# IGNITION-127 Step 00 — Fresh baseline and 125→127 rebase audit

Status: `COMPLETED` (repository-local audit only)

## Boundary

Execution started from formal `origin/main@c5cec3a212dbf42564985b71c0fcec3b1fb1e564` in the isolated task branch `codex/ignition-127-os-durability-lifecycle-r3-rebased-20260820`. The control source was freshly fetched from `origin/relay/current@cfd50804`. The relay checkout and the old 125 command remained read-only. IGNITION-125 was not executed; its requirements were re-audited and are recorded as `DEFERRED_REBASED_INTO_127`.

## What 126 changes in the rebase

The final 126 baseline already contains the R2 Event Ledger/CAS/replay spine, concurrent scheduler and queue controls, durable dispatch/reconciliation, operational memory, Pack registry/bus, executor federation and health leases, Driver Console, and the advisory Structural Governance Surface/ESI contract. Therefore 127 adds durable lifecycle semantics around those existing boundaries rather than creating a second control plane or an Agent shell.

The 126 soft-governance state is intentionally treated as advisory context. Persistence, migration and recovery must preserve `CANDIDATE_ESI_SIGNAL`, `ADVISORY_ONLY`, the existing claim ceiling, and the absence of permission/truth/M/E/Owner/safety authority.

## Rebase decisions

The complete machine matrix is in `data/operations/iterations/127/step00-rebase-matrix.json`. Snapshot/restore, schema migration, namespace isolation, Pack transactions, crash recovery, DR, continuity, adversarial coverage and current-surface synchronization remain required. Executor admission/revocation, budget accounting, Driver recovery and current-state synchronization are `MODIFIED_BY_126`: existing R2/126 contracts are the baseline, and 127 must make their lifecycle state durable without widening authority.

## Historical residuals retained

The 126 closure remains the authority for historical/environment residuals. 127 preserves function census drift, nonfunction projection drift, the recorded `T16_SYMPY_COUNTEREXAMPLE`/SymPy environment residual, and propagation reconciliation 104–106 as sealed or classified residuals. No generated snapshot, recovery bundle, or new runtime code may enter authoritative discovery or rewrite those records.

## Read-only baseline findings

- Event Ledger is append-only and hash chained, with aggregate CAS and a basic prefix snapshot/replay helper; it does not yet carry the 127 taxonomy, namespace scope, schema migration, Pack pins, reconciliation pointers, or advisory version pointers.
- Scheduler, queue, resource arbitration and dispatch reconciliation are durable but their budgets, leases and recovery are not yet one replayable lifecycle state.
- Operational memory is integrity checked and supports supersede/tombstone/compaction, but namespace/schema/recovery semantics are not yet explicit.
- Pack manifests are declarative and validated; activation is not transactional, version-pinned, or rollback/quarantine aware.
- Federation and executor health leases already separate OS from replaceable executors; durable admission epoch and future-dispatch revocation semantics remain to be added.
- Current facts and the 0.10.0 map are generated from canonical registries and are not authoritative inputs; 127 must preserve that direction and synchronize the one Current map only after architecture changes are complete.

Claim ceiling: this audit establishes only a source-bounded repository baseline and requirement rebase. It does not establish production readiness, external side-effect exactly-once, external truth, Owner acceptance, or epistemic acceptance.
