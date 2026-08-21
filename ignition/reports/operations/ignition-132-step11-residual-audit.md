# IGNITION-20260822-132 Step 11 — Residual and Regression Audit

Status: PASS WITH CLASSIFIED RESIDUALS

The Current semantic surfaces are clean: task lineage, release lifecycle, Current Facts, Current Snapshot, compiler output, typed semantic checks and Current State sync all pass. No new Task132 Current semantic regression was observed.

The audit keeps residual classes separate:

- The Human Surface validator reproduces the same 11 pre-existing source-hash drifts (`d127`, `d182`, `d190`, `d260`, `t2`, `y1`, and five `nfc-*` entries) recorded by Tasks 129–131.
- The projection-hygiene gate fails on a clean `e04752d20d071bac8f0c4a1e5cff20fb3004dae1` baseline with `missing=164`; the Task131 receipt had recorded the earlier historical baseline as `missing=96`. The Step11 candidate reports `missing=194`. The delta is 30 newly added Task132 formal paths by the end of this step, recorded separately as a new operational-hygiene residual rather than hidden inside the historical baseline.
- The T16 SymPy-unavailable residual and the historical 104–106 propagation mismatch (9 dimensions) remain preserved.
- The existing bounded validator/generator interruptions and Foundation/Phase-E long-running boundaries remain environmental baseline classifications. They are not converted to PASS by timeout or by changing validator semantics.

The Task132 new residual is limited to projection-manifest accounting for its 30 newly added formal paths. No residual-owned Human Surface entries, durability pilot code, or architecture/map source was modified in this task.

Evidence is recorded in `ignition/data/operations/iterations/132/step11-residual-audit.json`. Claim ceiling: repository-local residual classification and semantic regression evidence only; no external truth, production readiness, Owner acceptance, or epistemic acceptance is inferred.
