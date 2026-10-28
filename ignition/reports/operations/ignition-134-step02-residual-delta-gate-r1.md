# IGNITION-20260822-134 Step 02 — Residual delta gate

Status: `PASS`

The residual comparator now recomputes baseline and current fingerprints from the count, object set and failure-dimension set. It fails closed when an inherited residual grows, replaces an object at the same count, changes failure dimensions, changes its source command without an explicit migration, or presents a forged fingerprint. A new residual is release-blocking even when its status is explicitly `NEW_REGRESSION`; it cannot be made green by registering a new label.

The negative fixture matrix has eight cases. The only allowed positive transitions are an unchanged inherited residual and a residual whose current object/dimension set is explicitly empty with status `RESOLVED_CURRENT`. The tests also verify that comparison is pure and does not mutate the ledger entry.

Claim ceiling: repository-local residual delta-gate evidence only; no external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.
