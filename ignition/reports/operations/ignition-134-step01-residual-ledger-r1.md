# IGNITION-20260822-134 Step 01 — Residual Ledger R1

Status: `PASS`

Task134 now has one machine-readable Current Residual Ledger at `ignition/data/operations/residual-ledger-r1.json`, validated by `ignition/tools/validate_residual_ledger.py`. It contains five stable residual IDs:

- `CURRENT_PATH_MANIFEST_UNACCOUNTED`;
- `HUMAN_SURFACE_SOURCE_HASH_DRIFT`;
- `PROPAGATION_TASK104_106_MISMATCH`;
- `T16_SYMPY_COUNTEREXAMPLE`;
- `FULL_UNITTEST_DISCOVERY_TERMINAL_STATE`.

Every entry records its origin task, classification, status, baseline/current fingerprint, count, object/path set, failure dimensions, source command, validator, provenance paths, allowed persistence rule and release impact. Fingerprints are recomputed from the observed count, object set and failure dimensions; they are not trusted merely because a JSON field says they are valid.

The ledger deliberately points back to the path-classification validator, Human Surface validator, historical propagation source, executor inventory/SymPy probe and the long-window full-discovery record. It is a delta and provenance surface, not a parallel source of failure truth. Before any repair, all five baseline/current observations are unchanged and the ledger validator passes.

Claim ceiling: repository-local residual identity and provenance only; no external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.
