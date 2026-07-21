# SCIENTIFIC-METACOGNITION-I1 typed change-propagation impact report

- Closure complete: `true`
- Closure hash: `6c0ce665a996530f4c3843b5f0c369b4dfa30e6a35a16be4ded5c5e795d1bd8f`
- Fixpoint iterations: `2`
- Seeds: `current_state, epistemic_state_control_plane_contract, epistemic_state_control_plane_gate_validator, epistemic_state_control_plane_pilot, historical_reports, incremental_execution, iteration_manifest_contract, pages_pipeline, project_component_registry, propagation_calculator, system_map_layout, system_map_projection`
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
