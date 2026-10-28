# IGNITION-20260822-132 Step 07 — Publication Witness Task-ID Binding

Status: PASS

Step 07 binds the observation-time publication witness to the formal result, canonical Current source, lifecycle, and release candidate. The latest architecture-changing task remains `IGNITION-20260821-129`; it is deliberately not promoted to the current formal task.

The witness schema now requires a `task_binding` object. Its exact-match fields are:

- publication witness task: `IGNITION-20260822-132`
- formal result task: `IGNITION-20260822-132`
- canonical Current formal task: `IGNITION-20260822-132`
- lifecycle task: `IGNITION-20260822-132`
- release candidate task: `IGNITION-20260822-132`
- latest architecture-changing task: `IGNITION-20260821-129`

The builder reads the execution contract, canonical lineage, and lifecycle before emitting a witness. When a formal result already exists, its explicit `Task ID:` line must also match. The formal repository still does not contain a publication witness; the eventual witness remains a separate `Arvin-liu/1111` receipt.

The negative matrix includes a case where candidate SHA, observed remote SHA, local HEAD, and fresh-clone HEAD all match while task identity is stale. That case fails closed with `TASK_ID_BINDING_MISMATCH`.

Validation: `PYTHONPATH=ignition python3 -m unittest ignition.tests.test_publication_witness ignition.tests.test_post_publication_current` — 16 tests passed.

Claim ceiling: repository-local task identity binding and observation-time remote-ref evidence only; no external truth, production readiness, Owner acceptance, or epistemic acceptance is inferred.
