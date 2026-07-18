# 121Q32I typed change-propagation impact report

- Closure complete: `true`
- Closure hash: `a690d7e8bffecbab5540b7207f0bbb827630283ba3a2362f5cfb1add4560c642`
- Fixpoint iterations: `2`
- Seeds: `ai_guide, current_state, historical_reports, incremental_execution, iteration, iteration_manifest_contract, pages_pipeline, project_component_registry, propagation_calculator, propagation_topology, readme, summary, system_map_layout, system_map_projection, usage`
- Resolved components: `17`
- Registry-derived surfaces: `16`
- System-map decision: `CHANGE`

## Typed paths

- `propagation_calculator --projects / repository_dependency--> sync` — declared relation closure only
- `incremental_execution --publishes / repository_dependency--> pages_pipeline` — declared repository materialization relation only; no real-world causal identification
- `incremental_execution --generates / repository_dependency--> iteration` — declared repository materialization relation only; no real-world causal identification
- `incremental_execution --projects / repository_dependency--> system_map_projection` — declared repository materialization relation only; no real-world causal identification
- `incremental_execution --synchronization_requires / synchronization_obligation--> sync` — declared repository materialization relation only; no real-world causal identification
- `system_map_layout --generates / repository_dependency--> system_map_projection` — display derivation only
- `iteration_manifest_contract --version_tracks / repository_dependency--> iteration` — audit binding only
- `current_state --constraint / synchronization_obligation--> no_totality_proof` — interpretation boundary only
- `iteration --synchronization_requires / synchronization_obligation--> sync` — governance synchronization obligation
- `readme --documents / repository_dependency--> current_state` — declared navigation dependency only
- `readme --deployment_depends_on / repository_dependency--> pages_pipeline` — deployment dependency only
- `system_map_projection --deployment_depends_on / repository_dependency--> pages_pipeline` — deployment dependency only
- `project_component_registry --enabling_condition / repository_dependency--> propagation_calculator` — declared computation input
- `project_component_registry --generates / repository_dependency--> system_map_projection` — deterministic repository derivation
- `sync --synchronization_requires / synchronization_obligation--> readme` — governance obligation only
- `propagation_topology --enabling_condition / repository_dependency--> propagation_calculator` — declared computation input
- `propagation_topology --generates / repository_dependency--> system_map_projection` — deterministic repository derivation

## Residue

- None. This means declared closure is complete, not that substantive causality is proved.
