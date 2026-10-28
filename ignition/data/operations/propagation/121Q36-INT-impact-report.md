# 121Q36-INT typed change-propagation impact report

- Closure complete: `true`
- Closure hash: `5e19971dc6d71f890be9b1c4c2b8ebb3a70904e6cdff0c1dab838ca11b28b722`
- Fixpoint iterations: `2`
- Seeds: `historical_reports, incremental_execution, intervention_failure_contract, intervention_failure_gate_validator, intervention_failure_pilot, iteration_manifest_contract, project_component_registry, propagation_calculator`
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
