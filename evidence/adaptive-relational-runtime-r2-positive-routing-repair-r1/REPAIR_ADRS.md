# Repair ADRs — R2 Positive Routing Repair R1

Authorized by external review verdict `POSITIVE_ROUTING_REPAIR_R1=AUTHORIZED`
(predecessor `R2_POSITIVE_REAL_OBJECT_PROCESSING=REJECT`,
`R2_FAIL_CLOSED_BOUNDARY_PILOT=ACCEPT`, `R3_SCALE_RUN_AUTHORIZED=NO`).

## ADR-R2-REPAIR-1 — Adapter dispatch protocol (defect 4.1)
Replace the unconditional `adapter(ref, declared_capabilities=...)` call with a
registry-driven dispatcher (`adapter_protocol.ADAPTER_DISPATCH` + `dispatch()`).
Each object class declares the exact context keys its adapter may receive; only
the mechanism/state adapter forwards the Function OS `declared_capabilities`
contract. Unknown class or undeclared context key fails closed. The registry is
the single source of truth; the repair test suite proves mutation changes behavior.

## ADR-R2-REPAIR-2 — Schema-valid Source / Observation (defect 4.2)
`_build_source_observation()` now constructs records that validate against the
exact current ARR `source.schema.json` / `observation.schema.json`: typed locator,
rights/privacy boundary (`private_corpus` / `hash_only`), 64-hex content digest,
source tier, claim ceiling, time statuses, provenance, and deterministic
`<kind>_<32hex>` ids. The private source stays a typed reference only.

## ADR-R2-REPAIR-3 — Locked-manifest immutability (defect 4.3)
`run_pilot()` deep-copies every object (and `run_object()` deep-copies
`adapter_ref`) so the locked manifest is byte-identical before and after the run
and can be run repeatedly. No adapter `setdefault` mutates caller-owned objects.

## ADR-R2-REPAIR-4 — Real projection routing (defect 4.4)
`_project_for_obj()` builds a schema-valid `Relation` from the object's declared
expected routing and calls the ACTUAL ARR projection router (`eng._project`),
recording `rule_id` / `target` / `reject_code`. It never defaults to `None`.

## ADR-R2-REPAIR-5 — Receipt + outcome semantics (defect 4.5)
Every receipt states `adapter_success`, `runtime_success`, `projection_executed`,
`expected_route`, `actual_route`, `expectation_matched`, `outcome_status`
(SUCCESS / EXPECTED_REJECT / FAILURE / QUARANTINED), `input_immutable`,
`replay_stable`, `privacy_boundary_ok`, `real_world_actions`, and failure
attribution. A receipt existing is not proof of success.

## ADR-R2-REPAIR-6 — Aggregation semantics (defect 4.6)
`CAPABILITY_COVERAGE_MATRIX` measures successful positive processing and expected
rejection, not mere receipt presence. `ROUTING_RESIDUE` explicitly counts
quarantined / missing-projection / mismatched objects. `FALSE_CONSENSUS_CASES`
consumes manifest digests / source-cluster identifiers (no fabricated zero).
`ENGINEERING_SIGNALS` claims `pilot_coverage_complete` only when coverage is
actually complete.
