# D2-I1 typed change-propagation impact report

- Closure complete: `true`
- Closure hash: `060fd2a6642edd03152808a42b9f05f23114577ae7d924fbea43389681d631d1`
- Fixpoint iterations: `2`
- Seeds: `current_state, historical_reports, incremental_execution, iteration_manifest_contract, multi_history_world_projection_contract, multi_history_world_projection_gate_validator, multi_history_world_projection_pilot, pages_pipeline, project_component_registry, propagation_calculator, system_map_layout, system_map_projection`
- Resolved components: `15`
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
