# IGNITION-20260815-120 typed change-propagation impact report

- Closure complete: `true`
- Closure hash: `92235c362eb55b43028bd3418e25d8120ec8bde477e5b9f274405e72f49d62dc`
- Fixpoint iterations: `2`
- Seeds: `agent_kernel_r0, agent_runtime_r0, current_state, foundation, historical_reports, human_knowledge_surfaces, incremental_execution, l6, project_component_registry, propagation_calculator, propagation_topology, system_map_projection`
- Resolved components: `29`
- Registry-derived surfaces: `20`
- System-map decision: `CHANGE`

## Typed paths

- `readme --publishes / repository_dependency--> human_knowledge_surfaces` — repository navigation, exploration and readability dependency only
- `incremental_execution --publishes / repository_dependency--> human_knowledge_surfaces` — declared repository materialization relation only; no real-world causal identification
- `incremental_execution --generates / repository_dependency--> iteration` — declared repository materialization relation only; no real-world causal identification
- `incremental_execution --projects / repository_dependency--> system_map_projection` — declared repository materialization relation only; no real-world causal identification
- `incremental_execution --synchronization_requires / synchronization_obligation--> sync` — declared repository materialization relation only; no real-world causal identification
- `current_state --constraint / synchronization_obligation--> no_totality_proof` — interpretation boundary only
- `epistemic_governance_kernel --constraint / synchronization_obligation--> l6` — public constraint only; publication cannot upgrade source
- `epistemic_governance_kernel --constraint / synchronization_obligation--> no_truth_upgrade` — negative permission only; FEDERATED_ARCHITECTURE_ONLY
- `foundation --projects / repository_dependency--> epistemic_governance_kernel` — referential projection only; Foundation status remains upstream
- `foundation --projects / repository_dependency--> l2` — registry authority projection
- `foundation --constraint / synchronization_obligation--> no_truth_upgrade` — interpretation boundary only
- `iteration --synchronization_requires / synchronization_obligation--> sync` — governance synchronization obligation
- `agent_kernel_r0 --enabling_condition / repository_dependency--> agent_runtime_r0` — runtime dependency only; no domain truth authority
- `agent_kernel_r0 --constraint / synchronization_obligation--> no_truth_upgrade` — negative permission and invariant only; no epistemic authority
- `knowledge_domain_pack --publishes / repository_dependency--> human_knowledge_surfaces` — human publication projection only; no acceptance upgrade
- `l2 --derives / repository_dependency--> l3` — declared workflow dependency
- `l3 --derives / repository_dependency--> l4` — declared workflow dependency
- `l4 --validates / repository_dependency--> l5` — validation dependency only
- `l5 --publishes / repository_dependency--> l6` — publication permission dependency; no truth upgrade
- `no_truth_upgrade --constraint / synchronization_obligation--> no_totality_proof` — claim boundary
- `domain_pack_contract --documents / repository_dependency--> knowledge_domain_pack` — bounded knowledge adapter; existing claim ceiling remains upstream
- `domain_pack_contract --documents / repository_dependency--> research_pack_reos_light` — bounded research coordination only; not Kernel definition
- `domain_pack_contract --documents / repository_dependency--> writing_pack` — bounded publication interface only; no independent evidence
- `readme --documents / repository_dependency--> current_state` — declared navigation dependency only
- `agent_runtime_r0 --projects / repository_dependency--> runtime_environment` — declared environment observation only
- `agent_runtime_r0 --generates / repository_dependency--> runtime_memory_loop` — run trace and resume material only; not knowledge truth
- `agent_runtime_r0 --validates / repository_dependency--> nonknowledge_pilot` — repository pilot evidence only; no general intelligence claim
- `agent_runtime_r0 --lifecycle_depends_on / repository_dependency--> domain_pack_contract` — loadable interface only; Pack cannot grant generic authority
- `system_map_projection --publishes / repository_dependency--> human_knowledge_surfaces` — repository navigation projection only
- `project_component_registry --generates / repository_dependency--> system_map_projection` — deterministic repository derivation
- `sync --synchronization_requires / synchronization_obligation--> readme` — governance obligation only
- `propagation_topology --generates / repository_dependency--> system_map_projection` — deterministic repository derivation

## Residue

- None. This means declared closure is complete, not that substantive causality is proved.
