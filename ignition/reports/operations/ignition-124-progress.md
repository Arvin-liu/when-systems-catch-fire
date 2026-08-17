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
