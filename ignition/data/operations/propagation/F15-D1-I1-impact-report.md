# F15-D1-I1 typed change-propagation impact report

- Closure complete: `true`
- Closure hash: `84d658f88fb4f66b87a96ca46e67a27b4f13caea93e9c68f44a34fe8fdbd00e2`
- Fixpoint iterations: `2`
- Seeds: `current_state, historical_reports, incremental_execution, iteration_manifest_contract, latent_system_identifiability_contract, latent_system_identifiability_gate_validator, latent_system_identifiability_pilot, pages_pipeline, project_component_registry, propagation_calculator, system_map_layout, system_map_projection`
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
