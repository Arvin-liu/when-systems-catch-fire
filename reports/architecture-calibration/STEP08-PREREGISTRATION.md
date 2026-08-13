# STEP08 MCF / PSD / ARN / Function OS baseline-relative calibration

Status: FROZEN_CALIBRATION_PREREGISTRATION

This is a capability calibration of four current-main candidate components. It is not a truth test and does not promote any component to production, scientific validity, or external acceptance.

## Frozen base

- repository: when-systems-catch-fire
- formal main base: e5c6d1d0b75dae41b414474bc22747816cd00c78
- branch: research/architecture-capability-calibration-r1-20260813

## Comparison requirement

Each component is compared with the simplest plausible baseline that can perform the narrow task. The baseline is not expected to reproduce the component's full type system. The question is whether the component adds an observable, declared capability within the replay, and what cost or boundary accompanies it.

### Baselines

- MCF baseline: a list of nodes and source-target edges. It can represent a simple graph but has no typed relation class, temporal or spatial semantics, residue, or claim ceiling.
- PSD baseline: a normalized transition matrix and trajectory multiplication. It can calculate a small path probability but has no probability semantics, system boundary, intervention distribution, calibration record, or observation-versus-intervention distinction.
- ARN baseline: a directed adjacency dictionary. It can answer a simple static path query but has no multilayer or higher-order relation, temporal activation, direction policy, residue, or projection claim ceiling.
- Function OS baseline: a direct bounded Python function with an input check and return value. It can compute and reject a precondition failure but has no FunctionSpec, representation hash, artifact package, execution trace, validator, revision, rollback, or registry record.

## Current-main validation

The current component test suites will be run at the same frozen tip:

- MCF: tests/test_multiscale_causal_fabric.py
- PSD: tests/test_probabilistic_system_dynamics.py
- ARN: tests/test_adaptive_relational_network.py, tests/test_adaptive_relational_network_operational.py, tests/test_adaptive_relational_network_validation_contract.py
- Function OS: function-os-candidate/v0.2/tests

The validation receipt must record the exact command, environment limitation if any, pass/fail count, and warnings. A missing optional test dependency is an environment limitation until rerun with the declared dependency; it is not silently converted to a component defect.

## Outcome vocabulary

Every component receives one status from:

- OBSERVED_INCREMENTAL_VALUE_WITHIN_REPLAY
- NO_INCREMENTAL_VALUE_OBSERVED
- MIXED_VALUE_WITH_COST
- NOT_APPLICABLE
- BLOCKED_WITH_EVIDENCE
- REGRESSION_OR_DEFECT_FOUND
- UNDERDETERMINED

The status describes this bounded comparison only. A PASS in a unit test is not a scientific proof; a simpler baseline passing the narrow task is not evidence that the richer component has no operational value.

## Predeclared scoring dimensions

For each component record:

1. narrow task outcome for the simple baseline;
2. current-main validation outcome;
3. extra observable capability;
4. extra assumptions or complexity;
5. whether the extra capability is only repository-process value;
6. whether real-world validity remains untested;
7. residual defect or environment limitation.

No result may be changed to improve a component's status, and no science conclusion may be edited to make a test pass.
