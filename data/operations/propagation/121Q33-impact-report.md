# 121Q33 typed change-propagation impact report

- Closure complete: `false`
- Closure hash: `6339f3427c13fcd3d03092e653d710cc722f93b26b7094e490fb102d407a055a`
- Fixpoint iterations: `2`
- Seeds: `copyright_governance_history_remediation, copyright_governance_jurisdiction_registry, copyright_governance_material_classification, copyright_governance_non_republication_principle, copyright_governance_publication_gate_validator, copyright_governance_source_rights, copyright_governance_tests`
- Resolved components: `9`
- Registry-derived surfaces: `16`
- System-map decision: `CHANGE`

## Typed paths

- `copyright_governance_publication_gate_validator --validates / repository_dependency--> pages_pipeline` — Publication gate is a repository-level fail-closed check; does not prove external legality
- `copyright_governance_jurisdiction_registry --projects / repository_dependency--> system_map_projection` — Repository-level governance surface; not global legality or real-world causality
- `system_map_projection --deployment_depends_on / repository_dependency--> pages_pipeline` — deployment dependency only

## Residue

- `unmapped_path`: Changed path has no canonical component mapping.
- `unmapped_path`: Changed path has no canonical component mapping.
- `unmapped_path`: Changed path has no canonical component mapping.
- `unmapped_path`: Changed path has no canonical component mapping.
- `unmapped_path`: Changed path has no canonical component mapping.
