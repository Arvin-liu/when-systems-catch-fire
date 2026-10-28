# 121Q37 typed change-propagation impact report

- Closure complete: `true`
- Closure hash: `cb6e1b8554f81d1e61f47ba787990abc676a3f4d9037ac051d25ebd09d8a5ecf`
- Fixpoint iterations: `2`
- Seeds: `analogy_audit_contract, analogy_audit_gate_validator, analogy_audit_pilot, historical_reports, incremental_execution, iteration_manifest_contract, pages_pipeline, project_component_registry, propagation_calculator, system_map_layout, system_map_projection`
- Resolved components: `14`
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
