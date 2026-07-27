# IGNITION-ITERATION-METHOD-1.4-RESPONSIBILITY-ACTOR-GATE-NARROW-REPAIR-R1-20260726 typed change-propagation impact report

- Closure complete: `true`
- Closure hash: `77da4171b1cc289f1d706e56263813431faceb8f410ee764bbb5a3034edba65f`
- Fixpoint iterations: `2`
- Seeds: `ai_guide, current_state, historical_reports, iteration, project_component_registry, propagation_calculator, readme, stage_snapshot_publication`
- Resolved components: `12`
- Registry-derived surfaces: `18`
- System-map decision: `CHANGE`

## Typed paths

- `propagation_calculator --projects / repository_dependency--> sync` — declared relation closure only
- `current_state --constraint / synchronization_obligation--> no_totality_proof` — interpretation boundary only
- `iteration --synchronization_requires / synchronization_obligation--> sync` — governance synchronization obligation
- `readme --documents / repository_dependency--> current_state` — declared navigation dependency only
- `readme --deployment_depends_on / repository_dependency--> pages_pipeline` — deployment dependency only
- `system_map_projection --deployment_depends_on / repository_dependency--> pages_pipeline` — deployment dependency only
- `project_component_registry --enabling_condition / repository_dependency--> propagation_calculator` — declared computation input
- `project_component_registry --generates / repository_dependency--> system_map_projection` — deterministic repository derivation
- `stage_snapshot_publication --publishes / repository_dependency--> pages_pipeline` — candidate Pages artifact only before merge; production deploy remains main-only
- `stage_snapshot_publication --projects / repository_dependency--> readme` — public stage-summary projection only; no capability lifecycle promotion
- `stage_snapshot_publication --synchronization_requires / synchronization_obligation--> sync` — repository synchronization obligation only
- `sync --synchronization_requires / synchronization_obligation--> readme` — governance obligation only

## Residue

- None. This means declared closure is complete, not that substantive causality is proved.
