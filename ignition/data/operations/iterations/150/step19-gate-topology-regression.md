# Task150 Step19 — Gate topology regression

Result: `TASK150_STEP19_GATE_TOPOLOGY_REGRESSION_PASS`

The old combined interpretation is retained as historical evidence, but it is
no longer the admission topology for the reopened scope. The new policy has
two independent gate families.

## Base operation gates

`visualization.render_derived_system_view` has a base gate family containing
canonical provenance, semantic fidelity, topology immutability, standalone
viewport containment, fail-closed provider failure, canonical-source
preservation, environment/no-auto-install, immutable compatibility,
artifact/provenance receipt, provider-local policy isolation, no default
renderer and no architecture-truth escalation.

`standalone_viewport_containment_zero_failure` is the base visual gate. The
Delta gate is not in this family, and Owner aesthetic endorsement is not in
this family. All base gates must pass before a base candidate can be admitted.

## Delta extension gates

`architecture_delta.before_delta_after` remains an independent
`EXPERIMENTAL_EXTENSION_DEFERRED`. Its gate is
`delta_viewport_containment_zero_failure`, whose current retained result is
`FAIL_DEFERRED` because the upstream compare wrapper still has three
`viewer/viewport-overflow` diagnostics. A future Delta fix still requires a
separate admission; it cannot be promoted by a base pass.

## Regression policy

The split evaluator passes these policy cases:

- standalone PASS + Delta FAIL → base may become a
  `CURRENT_BOUNDED` candidate, Delta remains `DEFER`;
- standalone FAIL + Delta PASS → base remains `DEFER`, and Delta remains
  `SEPARATE_ADMISSION_REQUIRED`;
- Delta repaired + base PASS → base may proceed, but Delta does not
  automatically promote;
- aesthetic endorsement absent → functional base admission is not blocked,
  and no aesthetic acceptance claim is emitted.

These are policy fixtures, not claims that the actual Step21 standalone run
has already passed. The Current Registry remains 19 operations and Step19
performs no write. Step14/15 files are retained and unchanged.

Exact next action: `TASK150_STEP20_FUNCTIONAL_VERSUS_AESTHETIC_BOUNDARY`.
