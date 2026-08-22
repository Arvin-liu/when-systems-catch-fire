# IGNITION-20260822-134 Step 08 — Residual sealing and baseline preservation

Status: `PASS`

The residual builder was corrected so a current repair does not erase the debt it repaired. It now reads only the prior ledger's baseline tuple—objects, failure dimensions and baseline command—while recomputing the current tuple from live validators. The current observation is never reused as the new baseline.

The resulting ledger has five named residuals. The path-manifest observation decreased from baseline 245 to current 0, and the 11 Human Surface source-hash observations decreased from baseline 11 to current 0; both are `RESOLVED_CURRENT`. The Task104–106 propagation mismatch remains exactly 27 objects and is `SEALED_HISTORICAL`; the SymPy counterexample remains exactly one environmental observation; and the previous short-window full discovery remains one inherited terminal-state observation pending the required long run. No object or failure dimension was added.

`validate_residual_ledger.py --check` returned `RESIDUAL_LEDGER_OK entries=5 inherited_unchanged=3 resolved=2`. The ledger therefore distinguishes paid-down current debt from historical/environmental debt without treating either category as a green-light bypass.

Claim ceiling: repository-local residual sealing and non-growth evidence only; no external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.
