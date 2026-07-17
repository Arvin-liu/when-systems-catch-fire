# 121Q32 typed change-propagation impact report

- Closure complete: `true`
- Closure hash: `279c32833db13f9e31c8c2157b9c94d00673106347b5581abcb5ad2eae629350`
- Fixpoint iterations: `2`
- Seeds: `ai_guide, current_state, historical_reports, iteration, iteration_manifest_contract, mcf, no_l7, pages_pipeline, project_component_registry, propagation_calculator, propagation_topology, readme, summary, sync, system_map_layout, system_map_projection, usage`
- Resolved components: `19`
- Registry-derived surfaces: `16`
- System-map decision: `CHANGE`

## Typed paths

- `propagation_calculator --projects / repository_dependency--> sync` — declared relation closure only
- `system_map_layout --generates / repository_dependency--> system_map_projection` — display derivation only
- `iteration_manifest_contract --version_tracks / repository_dependency--> iteration` — audit binding only
- `current_state --constraint / synchronization_obligation--> no_totality_proof` — interpretation boundary only
- `iteration --synchronization_requires / synchronization_obligation--> sync` — governance synchronization obligation
- `no_l7 --constraint / synchronization_obligation--> no_truth_upgrade` — architecture boundary
- `no_truth_upgrade --constraint / synchronization_obligation--> no_totality_proof` — claim boundary
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
