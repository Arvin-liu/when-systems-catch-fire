# F15-D1-I1 typed change-propagation impact report

- Closure complete: `true`
- Closure hash: `68df8016bc8dcfb42ea410ef6cfc10e0d22f0d294ea1e410de8301cb7582fc53`
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
