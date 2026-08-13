# STEP09 MCF / PSD / ARN / Function OS execution result

Status: CALIBRATION_COMPLETE_WITH_EXPLICIT_RESIDUALS

This execution compares each candidate component with the frozen simplest baseline from STEP08. The outcome is bounded repository capability evidence only. It is not a claim of scientific truth, production readiness, safety, or external validity.

## Execution receipt

Frozen base and candidate branch:

- formal main base: e5c6d1d0b75dae41b414474bc22747816cd00c78
- calibration preregistration commit: 593dda901d7a1073680eb4c185b4fe5dd1d728bb

The default system pytest command was unavailable, and the first component attempt exposed a missing jsonschema dependency. The declared suites were rerun in an isolated temporary uv environment with pytest and jsonschema; this is recorded as an environment limitation, not hidden as a component failure.

## Results

| Component | Simplest baseline | Baseline result | Current-main declared validation | Status | What the component added in this replay |
|---|---|---:|---:|---|---|
| MCF | nodes plus source-target edges | simple graph representation PASS; typed relation, residue, and claim ceiling absent | 4 passed | OBSERVED_INCREMENTAL_VALUE_WITHIN_REPLAY | typed relation classes, causal-fabric diff, explicit claim ceiling and unmapped residue, deterministic projection |
| PSD | normalized transition matrix and path multiplication | normalization and a small trajectory probability PASS; probability semantics and observation/intervention split absent | 6 passed | OBSERVED_INCREMENTAL_VALUE_WITHIN_REPLAY | probability semantics, system boundary, transition/intervention records, calibration and model-diff boundaries |
| ARN | static directed adjacency dictionary | simple static path PASS; temporal activation, higher-order relation, and claim ceiling absent | 37 passed | OBSERVED_INCREMENTAL_VALUE_WITHIN_REPLAY | temporal path continuity, direction policy, multilayer/higher-order preservation, deterministic diff and residue |
| Function OS | direct bounded function with precondition | success and precondition rejection PASS; artifact, trace, validator, revision, rollback absent | 166 passed | OBSERVED_INCREMENTAL_VALUE_WITHIN_REPLAY | specification-to-artifact chain, execution trace, validator feedback, registry revision and rollback |

## Interpretation

The four components all showed a bounded incremental capability against their frozen baselines. The incremental result is architectural and repository-operational: the richer components retain distinctions and produce auditable records that the minimal baselines cannot produce. The result does not show that any component discovers hidden reality, proves a causal relation, validates a scientific model, or is ready for arbitrary untrusted production use.

Function OS remains a candidate reference implementation and not a complete sandbox or general-purpose operating system. MCF, PSD, and ARN remain derived representations and not truth layers. A passing test suite means the declared examples and contracts passed; it does not establish universal coverage.

## Residuals

- The baselines were intentionally narrow and do not represent every simpler implementation a user might choose.
- The comparison did not measure time, memory, maintenance burden, or human review cost; the capability status is therefore not a product ROI claim.
- The component tests are repository examples and contract tests, not independent external deployments.
- The full current-main validation still contains separate Foundation, closure, path-accounting, and front-door defects recorded at STEP00; those are not silently cleared by this component subset.
- No component is EPISTEMICALLY_ACCEPTED, production-ready, or externally validated by this calibration.
