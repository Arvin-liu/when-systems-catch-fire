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
| 07 | COMPLETED | pending closure | pending closure | Durable external dispatch/ack/progress/receipt journal with validation gate and conservative reconciliation. |
| 08 | COMPLETED | pending closure | pending closure | Concurrent operational memory with generation CAS, duplicate suppression, tombstones, stale capsules and deterministic compaction projection. |
| 09 | COMPLETED | pending closure | pending closure | Human-readable Driver Console projection with next-action ordering, open obligations and explicit epistemic boundaries. |
| 10 | COMPLETED | pending closure | pending closure | Five-child offline pilot covering real concurrency, conflicts, stale health, checkpoint/resume, cancel/deadline, forged completion and memory. |
| 11 | COMPLETED | pending closure | pending closure | Current State/map synchronization, deterministic Current Facts ordering guard, Phase-E CWD path repair and explicit historical propagation residual preservation. |

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

## Step 07 evidence

- Dispatch/reconciliation implementation: `agent_runtime/dispatch_reconciliation.py`
- Targeted unit tests: `tests/test_dispatch_reconciliation.py` (`3/3`)
- Adversarial validator: `tools/validate_dispatch_reconciliation.py` (`PASS`)
- Dispatch identity and idempotency keys are bound to a payload digest and
  effect class. Acknowledgements and public progress are identity-bound and
  strictly monotonic. A terminal external receipt is stored as
  `RECEIPT_RECORDED`; only an independent OS validation reference can move it
  to `COMPLETED_VALIDATED`. Lost acknowledgements permit retry only for an
  explicitly read-only effect. External and unknown side effects stop at
  `REQUIRES_RECONCILIATION`, with forged, duplicate and out-of-order records
  rejected.

## Step 08 evidence

- Concurrent memory implementation: `agent_runtime/concurrent_memory.py`
- Targeted unit tests: `tests/test_concurrent_memory.py` (`3/3`)
- Adversarial validator: `tools/validate_concurrent_memory.py` (`PASS`)
- Multi-writer append is serialized by a durable generation CAS; identical
  event/semantic content is idempotently suppressed while conflicting content
  fails closed. Supersession and redacting tombstones are atomic. Capsules
  carry the source generation and digest, so later writes make them
  explicitly stale. Compaction is a deterministic bounded projection and
  leaves append-only source history intact.

## Step 09 evidence

- Driver Console implementation: `agent_runtime/driver_console.py`
- Targeted unit tests: `tests/test_driver_console.py` (`2/2`)
- CLI projection tool: `tools/driver_console.py` (`--json` or human-readable)
- The console prioritizes reconciliation, stale/unsafe health, resource
  conflicts, queue pause, and explicit checkpoint resume before routine
  admission. It explains queue depth, route health, resource policy,
  dispatch states, memory generation/staleness and policy digest in one
  bounded view. The boundary text states that the projection cannot establish
  external completion, truth, Owner acceptance or epistemic acceptance.

## Step 10 evidence

- Pilot implementation: `agent_runtime/pilots/control_plane_r2.py`
- Durable pilot receipt: `data/agent-runtime/pilots/r2-control-plane/pilot-result.json`
- Targeted pilot test: `tests/test_control_plane_r2_pilot.py` (`1/1`)
- Validator: `tools/validate_control_plane_r2_pilot.py` (`PASS`)
- Five children are represented as `pilot-a` through `pilot-e`; actual worker
  overlap reached `2`. The adversarial matrix passed for shared-resource
  conflict, stale-executor routing rejection, crash/checkpoint plus explicit
  resume, pre-dispatch cancellation, deadline expiry, forged completion
  rejection, and stale operational-memory capsule. The result is an offline
  disposable fixture receipt and does not establish live executor behavior.

## Step 11 evidence

- Current identity: `identity_epoch=os-control-plane-r2`, boundary `124`, status
  `CURRENT_WITH_OPEN_OBLIGATIONS`, `EPISTEMICALLY_ACCEPTED=0`.
- Current State receipt: `data/operations/iterations/124/current-state-sync-receipt.json`;
  `validate_current_state_sync.py --check` passed all ten required surfaces.
- Derived projections: `current-facts` now rejects unsorted or duplicate source
  fingerprints; `SYSTEM_MAP_DERIVED_OK nodes=79 edges=84`; geometry quality is
  `PASS` with crossing proxy `187` and two mobile viewport fits.
- Architecture synchronization: the registry has `91` components and the map
  has current version `0.9.0`, historical version `0.8.0`, `79` visible nodes and
  `84` visible typed edges. The new OS Control Plane R2 document is the bounded
  human-readable component boundary.
- Residual audit: Phase-E validation passes without the inherited nested-CWD
  `git show` warnings after worktree-aware path resolution. The reconciliation
  validator still fails only on the historical 104–106 `NO_IMPACT_JUSTIFIED`
  records; those records remain append-only and are preserved as
  `PROPAGATION-104-106 / REQUIRES_REVIEW`, not rewritten into a false PASS.
