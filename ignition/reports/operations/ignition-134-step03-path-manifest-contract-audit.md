# IGNITION-20260822-134 Step 03 — Current path manifest contract audit

Status: `PASS`

The contract audit selects方案 A: `classification-manifest.jsonl` remains the sole Current generated snapshot of the live path-classification engine. This is supported by the validator's source contract and by its `--check` behavior, which compares the live tracked set to the committed manifest and reports missing/stale paths.

The old manifest is therefore not reinterpreted as an immutable historical snapshot. Historical observations remain intact in Git commits and Task127–133 receipts. The Current release gate instead requires tracked-set equality, unresolved/stale/duplicate/category-drift zero, and zero anti-backflow violations. An explicit machine contract now records this choice, and the path validator fails closed if that contract is missing or points to a different Current source.

No authoritative allowlist is expanded in this step. Path coverage and anti-backflow are audited separately in Step 04; regeneration occurs only in Step 05.

Claim ceiling: repository-local Current path-manifest contract evidence only; no external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.
