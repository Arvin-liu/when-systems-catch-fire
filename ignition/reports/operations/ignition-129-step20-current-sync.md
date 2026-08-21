# IGNITION-129 Step 20 — Current architecture/state synchronization

## Scope

Step 20 synchronizes the repository Current surface after the R1 steering implementation. The
change is classified `ARCHITECTURE_CHANGED` because Steering / Intent / Goal / Obligation R1 is
added to the existing Ignition OS / driver identity and to the single registry-derived system map.

## Canonical changes

- identity epoch: `os-control-plane-r4-steering-intent-r1`;
- current iteration boundary: `129`;
- current map: `0.12.0` Current; `0.11.0` Historical; `0.10.0` and earlier Historical;
- registry/topology/layout: `94` components, `128` typed relations, `82` visible nodes, `87` visible edges, `12` hidden represented components;
- current task-lineage source: Task 129 `COMPLETED_WITH_CLASSIFIED_RESIDUALS`, while `CURRENT_WITH_OPEN_OBLIGATIONS` and `EPISTEMICALLY_ACCEPTED=0` remain unchanged;
- machine and human projections: Current Facts, sole interactive map, SVG, human/AI front doors, Federation boundary and append-only State Changelog.

## Steering boundary

The synchronized surface records `OWNER_DECLARED` / `OWNER_APPROVED_DERIVED` authority separately
from system proposals. Intent, Goal, Commitment and Completion Contract records retain provenance,
version and evidence boundaries. A passing Run, executor report, telemetry, memory/profile signal or
Intent Capsule cannot infer Owner intent or Goal completion; independent Completion Contract
evaluation and OS reconciliation remain required.

## Validation contract

The machine receipt is [`current-state-sync-receipt.json`](../../data/operations/iterations/129/current-state-sync-receipt.json).
The projection sources are [`current-system-identity.json`](../../data/architecture/current-system-identity.json),
[`current-state-r1.json`](../../data/operations/steering/current-state-r1.json), the component registry,
typed topology and layout overlay. Exact Git commit and remote SHA evidence is intentionally kept in
the Step 20 progress record and final Step 21 machine receipt, not self-referentially in this report.

## Regression accounting

- `111` focused current/steering/map/profile tests: PASS.
- Steering validators, Current-State/task-lineage validators, deterministic map/Current Facts generators,
  geometry and fixtures, Agent Platform human-surface gate, component-profile gate, compileall and
  `git diff --check`: PASS.
- The repository-wide discovery was attempted twice. The first run was safely interrupted after more
  than six minutes while `tests/foundation/test_foundation.py` waited on the existing Foundation
  validator chain; the second non-Foundation run was safely interrupted after more than seven minutes
  at the existing Phase-E `git show` path. It is recorded as `CLASSIFIED_LONG_RUNNING_BASELINE_RESIDUALS`,
  not as a green full-suite claim.
- The human-front-door gate reproduces 11 pre-existing source-hash drift entries in the function and
  non-function human asset surfaces. They were not rewritten by this architecture task.

## Claim ceiling

This report is repository-local Current-State synchronization and deterministic navigation evidence
only. It does not establish real Owner intent, external truth, production readiness, live executor
completion, external validity, Owner acceptance or epistemic acceptance.
