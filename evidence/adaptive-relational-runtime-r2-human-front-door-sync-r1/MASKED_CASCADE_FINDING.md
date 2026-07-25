# Masked Cascade Finding — foundation-validation gate

## Context

The IGNITION assumed (line 16) that `tests.test_human_front_door` was the **only**
failing foundation-validation step on the predecessor (`ci-r1` @ `5771d6c`). That
assumption was wrong, and the gap is structural: **foundation-validation runs its
steps sequentially and aborts the job on the first non-zero step**, so every step
after the human-front-door failure was never executed on the predecessor and its
failures were masked.

## What the human-front-door fix revealed

After commit 1+2 made `tests.test_human_front_door` green, the workflow advanced to
step 147 (`tests.test_change_propagation`) and failed there, which then also surfaced
as a failure in step 150 (`tests.test_production_execution_authority`, whose
`propagation_calculator` validator runs the change-propagation suite in a detached
worktree subprocess).

Root cause (single, shared):
- `tests/test_change_propagation.py::test_f_unmapped_path_and_cycle_are_explicit_blocking_residue`
  deep-copies `TOPOLOGY_DOC["relations"][-2]` and overrides `propagation_mode="automatic"`
  but leaves `relation_domain` inherited. The schema requires
  `if relation_domain == "substantive_causal_candidate" then propagation_mode const "informational_only"`.
  When `relations[-2]` is a `substantive_causal_candidate` relation, the injected cycle
  violates the schema (`'informational_only' was expected`), failing the whole topology
  validation. The test is order-dependent on the last relation in the topology file.

## Fix (commit 3)

Pin the injected cycle's `relation_domain` to `synchronization_obligation` (no
`propagation_mode` const) and set `required_evaluation`/`creates_sync_obligation` to
`False`. The test's actual contract — a sync<->iteration cycle reported as explicit
blocking residue — is unchanged. No production data, schema, or forbidden semantics
(ARR runtime, 48-object manifest, Foundation/Ψ₀/ARN/MCF/PSD, R3) are touched.

## Why this is a third commit (deviation from "exactly two")

The IGNITION's "exactly two ordinary commits" was predicated on the false premise that
human-front-door was the only red step. Reaching the mandated `foundation-validation =
success` gate (IGNITION criterion 7, and the user's explicit live instruction) requires
closing this masked, pre-existing, same-root-cause cascade. The user's live instruction
and the IGNITION's own criterion 7 take precedence over the commit-count assumption; the
prohibition list (R3/Ready/merge/Main/force-push/PROMOTE/EVOLVE) does not forbid fixing a
pre-existing test. This deviation is disclosed here and in the commit message.

## Verification after fix

- `tests.test_change_propagation` — 57 passed, 1 skipped (was: 1 error).
- `tests.test_production_execution_authority::test_production_capability_contract_and_all_local_validators_run` — ok (was: fail; the `propagation_calculator` subprocess now returns 0).
- Steps 146 (human-front-door), 148 (pages_deploy_gate), 149 (phase_e_candidate), 143 (ARR pytest) already green.
- All other foundation-validation steps ran green in run 30144827871 up to step 147.
