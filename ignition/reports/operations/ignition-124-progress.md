# IGNITION-20260817-124 — OS Control Plane R2 progress

This is the task-branch progress surface for the independently pushed Step
00–12 ledger. It records repository evidence and bounded claims only. The
formal `main` tip does not move during the task branch run.

## Step ledger

| Step | Status | Commit | Remote | Summary |
| --- | --- | --- | --- | --- |
| 00 | COMPLETED | pending closure | pending closure | Fresh baseline, Control Plane gap audit and two-ready-child concurrency experiment. |
| 01 | COMPLETED | pending closure | pending closure | Canonical typed event ledger with CAS, hash chain, deterministic replay and snapshot-tail recovery. |
| 02 | COMPLETED | pending closure | pending closure | Monotonic Effective Policy compiler with digest binding, narrowing proof trace and escalation rejection. |
| 03 | COMPLETED | pending closure | pending closure | Typed resource intents, hierarchical overlap, atomic multi-resource leases and deterministic conflict arbitration. |
| 04 | COMPLETED | pending closure | pending closure | Bounded concurrent DAG scheduler with budgets, cancellation, deadlines, checkpoint/resume and terminal rollup. |
| 05 | COMPLETED | pending closure | pending closure | Digest-bound executor capability/health leases with expiry, cooldown, stale rejection and deterministic routing candidates. |
| 06 | COMPLETED | pending closure | pending closure | Durable bounded queue with quota/backpressure, priority/aging, deadline, pause and cancel boundaries. |

## Boundary

`OS != executor`; `Reasoner != Executor`; `Pack != truth authority`; Memory is
operational recall, not Knowledge truth; `CURRENT_WITH_OPEN_OBLIGATIONS` and
`EPISTEMICALLY_ACCEPTED=0` remain unchanged. No live provider, daemon,
network/browser/message action, vector memory or remote Git mutation is part of
this task.

## Step 00 evidence

- Baseline fixture: `data/operations/iterations/124/fixtures/baseline-concurrency-r1.json`
- Gap audit: `reports/architecture/os-control-plane-r2-gap-audit.md`
- Inherited core regression: 143 focused tests passed.
- Reference/federation and state gates passed; historical reconciliation residuals remain explicitly classified.

## Step 01 evidence

- Event chain implementation: `agent_runtime/event_ledger.py`
- Targeted unit tests: `tests/test_event_ledger.py` (`3/3`)
- Adversarial validator: `tools/validate_event_ledger.py` (`PASS`)
- The ledger rejects stale aggregate writers, duplicate event identities,
  corrupted chain/payload records and forbidden prompt/secret material. A
  snapshot may be older than the ledger and is recovered by deterministic tail
  replay; a snapshot that is not a ledger prefix is rejected.

## Step 02 evidence

- Policy compiler: `agent_runtime/policy_compiler.py`
- Targeted unit tests: `tests/test_policy_compiler.py` (`3/3`)
- Adversarial validator: `tools/validate_policy_compiler.py` (`PASS`)
- Capability/path/resource-intent dimensions use intersection and requested
  subsets; booleans and budgets use minimum; expiry uses the earliest bound;
  prohibitions use a stronger-restriction union. Pack and executor ceilings
  cannot widen parent scope, and approval is valid only for a predeclared,
  task-bound action.

## Step 03 evidence

- Resource arbiter: `agent_runtime/resource_arbitration.py`
- Targeted unit tests: `tests/test_resource_arbitration.py` (`3/3`)
- Adversarial validator: `tools/validate_resource_arbitration.py` (`PASS`)
- Shared reads may coexist; writes and metadata/external/unknown side effects
  conflict on exact or hierarchical overlap. Multi-resource acquisition is
  all-or-nothing and must be in canonical order. Lease expiry is recoverable;
  unknown side effects remain serialized and are never treated as safe for
  automatic failover.

## Step 04 evidence

- Scheduler implementation: `agent_runtime/scheduler.py`
- Targeted unit tests: `tests/test_scheduler.py` (`4/4`)
- Adversarial validator: `tools/validate_scheduler.py` (`PASS`)
- The scheduler validates a dependency DAG, dispatches only ready units,
  caps both global and per-executor concurrency, orders equal-priority work
  deterministically, acquires resource leases atomically, and persists state
  before waiting on worker futures. Time, action and output budgets, deadline
  expiry, cooperative cancellation, fail-fast/independent policy, and
  checkpoint-with-explicit-resume are terminally visible. The 39-test
  event/policy/resource/scheduler/core regression is `PASS`.

## Step 05 evidence

- Executor lease implementation: `agent_runtime/executor_health.py`
- Targeted unit tests: `tests/test_executor_health.py` (`3/3`)
- Adversarial validator: `tools/validate_executor_health.py` (`PASS`)
- A lease binds observed adapter/version, capability tokens, permission and
  workspace ceilings, support flags, concurrency ceiling, probe class and
  public evidence references to a digest. Expiry becomes `STALE`; a failed
  probe enters cooldown and repeated failures become `UNSAFE_TO_PROBE` until
  a fresh observation replaces the lease. Tampered persisted leases are
  rejected before routing.

## Step 06 evidence

- Queue control implementation: `agent_runtime/queue_control.py`
- Targeted unit tests: `tests/test_queue_control.py` (`3/3`)
- Adversarial validator: `tools/validate_queue_control.py` (`PASS`)
- Admission is bounded by depth and profile/project quotas; rejected items
  remain as durable `REJECTED_BACKPRESSURE` or `REJECTED_QUOTA` records. Ready
  items use priority, deterministic FIFO and aging. `not_before` and deadline
  are checked before admission, pause blocks admission, pre-dispatch cancel
  becomes `CANCELLED_BEFORE_DISPATCH`, and post-dispatch cancel is explicitly
  `CANCEL_REQUESTED_REQUIRES_RECONCILIATION`.
