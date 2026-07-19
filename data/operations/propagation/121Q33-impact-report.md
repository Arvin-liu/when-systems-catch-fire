# 121Q33 typed change-propagation impact report

- Closure complete: `true`
- Closure hash: `d0a7ee051574cabc919a9718fd86f85e3bedaf0e3c15109d3bac72ffd188d6e9`
- Fixpoint iterations: `3`
- Seeds: `copyright_governance_history_remediation, copyright_governance_jurisdiction_registry, copyright_governance_material_classification, copyright_governance_non_republication_principle, copyright_governance_publication_gate_validator, copyright_governance_source_rights, copyright_governance_tests`
- Resolved components: `27`
- Registry-derived surfaces: `16`
- System-map decision: `CHANGE`

## Typed paths

- `copyright_governance_publication_gate_validator --validates / repository_dependency--> pages_pipeline` — Publication gate is a repository-level fail-closed check; does not prove external legality
- `copyright_governance_jurisdiction_registry --projects / repository_dependency--> system_map_projection` — Repository-level governance surface; not global legality or real-world causality
- `charter --governance_constrains / synchronization_obligation--> q12` — normative constraint only
- `external_input --derives / repository_dependency--> source_pool` — writing input relation only
- `foundation --projects / repository_dependency--> l2` — registry authority projection
- `foundation --constraint / synchronization_obligation--> no_truth_upgrade` — interpretation boundary only
- `copyright_governance_jurisdiction_registry --governance_constrains / synchronization_obligation--> charter` — normative constraint only
- `copyright_governance_material_classification --validates / repository_dependency--> source_pool` — classification only
- `copyright_governance_non_republication_principle --constraint / synchronization_obligation--> accepted_work` — interpretation boundary only
- `copyright_governance_publication_gate_validator --validates / repository_dependency--> current_state` — validation gate only
- `copyright_governance_source_rights --governance_constrains / synchronization_obligation--> external_input` — normative constraint only
- `copyright_governance_tests --validates / repository_dependency--> foundation` — test validation only
- `l2 --derives / repository_dependency--> l3` — declared workflow dependency
- `l3 --derives / repository_dependency--> l4` — declared workflow dependency
- `l4 --validates / repository_dependency--> l5` — validation dependency only
- `l5 --publishes / repository_dependency--> l6` — publication permission dependency; no truth upgrade
- `zhiyuan_method --generates / repository_dependency--> accepted_work` — historical generation provenance; no retroactive rewrite
- `source_pool --enabling_condition / repository_dependency--> zhiyuan_method` — writing generation dependency
- `q12 --derives / repository_dependency--> q13` — declared operation dependency
- `q13 --projects / repository_dependency--> q14` — declared navigation projection
- `accepted_work --documents / repository_dependency--> showcase_registry` — provenance registration only
- `accepted_work --publishes / repository_dependency--> showcase` — presentation relation only
- `system_map_projection --deployment_depends_on / repository_dependency--> pages_pipeline` — deployment dependency only

## Residue

- None. This means declared closure is complete, not that substantive causality is proved.
