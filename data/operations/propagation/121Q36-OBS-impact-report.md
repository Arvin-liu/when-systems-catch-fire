# 121Q36-OBS typed change-propagation impact report

- Closure complete: `true`
- Closure hash: `e2af20ba4de25cf28514e98193f0370f0ccee097b9708c68b1f2bb12eaa15f1c`
- Fixpoint iterations: `2`
- Seeds: `historical_reports, incremental_execution, iteration_manifest_contract, observation_prediction_contract, observation_prediction_gate_validator, observation_prediction_pilot_q34, project_component_registry, propagation_calculator`
- Resolved components: `13`
- Registry-derived surfaces: `14`
- System-map decision: `CHANGE`

## Typed paths

- `incremental_execution --publishes / repository_dependency--> pages_pipeline` — declared repository materialization relation only; no real-world causal identification
- `incremental_execution --generates / repository_dependency--> iteration` — declared repository materialization relation only; no real-world causal identification
- `incremental_execution --projects / repository_dependency--> system_map_projection` — declared repository materialization relation only; no real-world causal identification
- `incremental_execution --synchronization_requires / synchronization_obligation--> sync` — declared repository materialization relation only; no real-world causal identification
- `project_component_registry --generates / repository_dependency--> system_map_projection` — deterministic repository derivation
- `sync --synchronization_requires / synchronization_obligation--> readme` — governance obligation only

## Residue

- None. This means declared closure is complete, not that substantive causality is proved.
