# Ignition Toolbox / 点火工具箱

> This page is generated from the canonical Current operation registry plus the pinned optional candidate-card source. It is a discovery surface, not a permission or truth authority.
>
> Current operation entries are registered capabilities; the registry does not prove that every entry is a standalone executable in this environment. Experimental tools are opt-in and default off.

Current operation registry: 20 entries · `blob 21fe1bfcdb0d9762edd60339aca14f1040393fc7`.
Optional experimental tools: 2 · `blob 593449134ec20d97139c9cb2663b113a5433c10a`.

Machine-readable cards: [toolbox-identity-cards-r0.json](data/operations/toolbox-identity-cards-r0.json).
Current operation authority: [ignition-operation-capability-registry-r1.json](data/operations/ignition-operation-capability-registry-r1.json).

## Registered operations

### `executor.reference_conformance` · Reference Executor 一致性边界 / Reference Executor conformance boundary

- State: `REFERENCE_ONLY` · callability `STATUS_ONLY` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Expose the frozen local executor only as a reference, conformance and minimal fallback boundary.
- Suitable for: inputs `executor compatibility status query`; declared outputs `reference/conformance boundary report`; class `EXECUTOR_ORCHESTRATION`.
- Use only if: Current status is REFERENCE_ONLY and callability is STATUS_ONLY.; ignition/data/architecture/current-system-identity.json; ignition/data/agent-federation/os-executor-ownership-r1.json
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: executor compatibility status query
- Outputs: reference/conformance boundary report
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/data/agent-federation/os-executor-ownership-r1.json, ignition/data/architecture/current-system-identity.json, ignition/docs/architecture/external-agent-federation-r1.md, ignition/tools/validate_federation_ownership.py; runtime `none declared`; version `UNKNOWN_NOT_DECLARED_BY_OPERATION_REGISTRY`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: Not a default or production executor.; Cannot grant Owner, truth, permission, network, channel, billing or epistemic authority.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tools/validate_federation_ownership.py`.
- Route default: `false` · claim ceiling: Reference and conformance compatibility only; no live execution, production safety, external completion or authority upgrade.

### `external.live_invocation` · 外部 Agent 实时调用 / Live external Agent invocation

- State: `OWNER_DEFERRED` · callability `STATUS_ONLY` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Represent the live external execution obligation and its current admission boundary without starting a process.
- Suitable for: inputs `explicit Owner external-action request, executor admission evidence`; declared outputs `deferred status, admission decision, bounded execution receipt if separately authorized and validated`; class `EXECUTOR_ORCHESTRATION`.
- Use only if: Current status is OWNER_DEFERRED and callability is STATUS_ONLY.; ignition/data/operations/open-obligation-registry-r1.json; ignition/data/architecture/current-facts.json; ignition/data/agent-federation/executor-inventory-r1.json
- Do not use when: The request requires a mode other than EXTERNAL_ACTION_RUN.; A required Current authority or declared source is unavailable.
- Inputs: explicit Owner external-action request, executor admission evidence
- Outputs: deferred status, admission decision, bounded execution receipt if separately authorized and validated
- Mode and permissions: `EXTERNAL_ACTION_RUN`; repository `FORBIDDEN`; external `EXPLICIT_OWNER_AUTHORIZATION_AND_CURRENT_ADMISSION`
- Side effects: repository `FORBIDDEN`; external `EXPLICIT_OWNER_AUTHORIZATION_AND_CURRENT_ADMISSION`.
- Dependencies: ignition/data/agent-federation/executor-inventory-r1.json, ignition/data/architecture/current-facts.json, ignition/data/operations/open-obligation-registry-r1.json, ignition/docs/architecture/external-agent-federation-r1.md, ignition/docs/architecture/os-control-plane-r2.md, ignition/tools/validate_federation_ownership.py, ignition/tools/validate_open_obligation_registry.py; runtime `none declared`; version `UNKNOWN_NOT_DECLARED_BY_OPERATION_REGISTRY`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: OPEN and OWNER_DEFERRED with zero validated completions.; No automatic resume; explicit Owner reopening and a prepared, installed and attested local environment are prerequisites.; Dispatch, process observation, inference observation, result return and validated completion remain separate facts.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tools/validate_open_obligation_registry.py, ignition/tools/validate_federation_ownership.py`.
- Route default: `false` · claim ceiling: Deferred capability status and admission boundary only; no live process, validated completion, external truth or production readiness.

### `foundation.resolve_current_asset` · 解析 Current canonical 资产 / Resolve a Current canonical asset

- State: `CURRENT_BOUNDED` · callability `PUBLIC_BOUNDED` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Resolve function, claim and legacy references through Current identity, migration, evolution and alias authorities.
- Suitable for: inputs `canonical id, legacy id, alias, natural-language asset query`; declared outputs `canonical identity match, migration relation, unresolved reference status`; class `KNOWLEDGE`.
- Use only if: Current status is CURRENT_BOUNDED and callability is PUBLIC_BOUNDED.; ignition/data/foundation/function-assets/closure-summary.json; ignition/data/foundation/function-assets/identity-cards.jsonl; ignition/data/foundation/nonfunction-claims/claim-registry.jsonl; ignition/data/governance/knowledge-experience/manifest.json; ignition/docs/foundation/migration.md
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: canonical id, legacy id, alias, natural-language asset query
- Outputs: canonical identity match, migration relation, unresolved reference status
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/KNOWLEDGE/EVOLUTION.md, ignition/data/foundation/function-assets/closure-summary.json, ignition/data/foundation/function-assets/identity-cards.jsonl, ignition/data/foundation/nonfunction-claims/claim-registry.jsonl, ignition/data/governance/knowledge-experience/manifest.json, ignition/docs/foundation/claim-governance-and-function-identity.md, ignition/docs/foundation/future-claim-admission-protocol.md, ignition/docs/foundation/migration.md, ignition/tools/foundation/validate_function_asset_closure.py, ignition/tools/foundation/validate_nonfunction_claim_closure.py, ignition/tools/governance/validate_knowledge_experience.py; runtime `none declared`; version `UNKNOWN_NOT_DECLARED_BY_OPERATION_REGISTRY`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: Aliases and search hits are navigation aids, not canonical identity by themselves.; Unresolved legacy references must fail closed rather than be reconstructed from model memory.; Canonical registration does not prove truth or external validity.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tools/foundation/validate_function_asset_closure.py, ignition/tools/foundation/validate_nonfunction_claim_closure.py, ignition/tools/governance/validate_knowledge_experience.py`.
- Route default: `true` · claim ceiling: Repository-local identity and migration resolution only; no proof, evidence upgrade or external truth.

### `ignition.recover_current_state` · 恢复点火 Current 状态 / Recover Ignition Current state

- State: `CURRENT` · callability `PUBLIC` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Recover repository identity, formal task, lifecycle, open obligations, current method, current map and minimum read order before interpreting a user task.
- Suitable for: inputs `Ignition repository URL, repository checkout, Current state query`; declared outputs `Current identity snapshot, minimum authority read plan, open-obligation boundary`; class `CURRENT_RECOVERY`.
- Use only if: Current status is CURRENT and callability is PUBLIC.; ignition/AI-START-HERE.md; ignition/data/architecture/current-facts.json; ignition/data/operations/current-snapshot-r1.json; ignition/data/operations/open-obligation-registry-r1.json
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: Ignition repository URL, repository checkout, Current state query
- Outputs: Current identity snapshot, minimum authority read plan, open-obligation boundary
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/AI-START-HERE.md, ignition/STATE-CHANGELOG.md, ignition/data/architecture/current-facts.json, ignition/data/operations/current-snapshot-r1.json, ignition/data/operations/open-obligation-registry-r1.json, ignition/docs/project-current-state.md, ignition/tools/validate_current_state_sync.py, ignition/tools/validate_state_changelog.py; runtime `none declared`; version `UNKNOWN_NOT_DECLARED_BY_OPERATION_REGISTRY`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: Recovers what is Current and where authority lives; it does not itself choose or execute a user-facing domain operation.; Repository Current evidence is not external truth, production readiness or Owner acceptance.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tools/validate_current_state_sync.py, ignition/tools/validate_state_changelog.py`.
- Route default: `true` · claim ceiling: Deterministic repository-local Current recovery only; no external truth, permission or epistemic upgrade.

### `knowledge.collide_object` · 运行受约束对象碰撞 / Run a bounded object collision

- State: `CURRENT_BOUNDED` · callability `PUBLIC_BOUNDED` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Decompose a user-supplied note, article, case, argument or source object; preserve provenance; collide it with Current function and non-function canonical registries; and separate source-derived content from bounded post-collision increments.
- Suitable for: inputs `note, article, case, argument, source material, structured collision run`; declared outputs `provenance-preserving object decomposition, verified canonical collision matches, bounded relationship findings, unregistered candidate-new records`; class `KNOWLEDGE`.
- Use only if: Current status is CURRENT_BOUNDED and callability is PUBLIC_BOUNDED.; ignition/OPERATING-METHOD.md; ignition/data/foundation/function-assets/identity-cards.jsonl; ignition/data/foundation/nonfunction-claims/claim-registry.jsonl; ignition/docs/foundation/claim-governance-and-function-identity.md; ignition/docs/foundation/future-claim-admission-protocol.md
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: note, article, case, argument, source material, structured collision run
- Outputs: provenance-preserving object decomposition, verified canonical collision matches, bounded relationship findings, unregistered candidate-new records
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/OPERATING-METHOD.md, ignition/data/foundation/function-assets/identity-cards.jsonl, ignition/data/foundation/nonfunction-claims/claim-registry.jsonl, ignition/docs/foundation/claim-governance-and-function-identity.md, ignition/docs/foundation/future-claim-admission-protocol.md, ignition/schemas/operations/ignition-object-collision-run-r1.schema.json, ignition/tests/test_ignition_object_collision.py, ignition/tools/operations/evaluate_object_collision_run.py; runtime `none declared`; version `UNKNOWN_NOT_DECLARED_BY_OPERATION_REGISTRY`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: Canonical registry matches establish repository identity and relationship evidence, not truth, proof, external evidence or novelty.; Input-explicit viewpoints remain source-derived and cannot be counted as Ignition discoveries.; CANDIDATE_NEW requires actual nearest canonical matches and never writes a registry automatically.; Undefined percentages, similarity scores and isomorphism scores are prohibited.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tools/operations/evaluate_object_collision_run.py, ignition/tests/test_ignition_object_collision.py`.
- Route default: `true` · claim ceiling: Repository-local object decomposition and canonical collision relation only; no candidate registration, truth, evidence, proof, causality, novelty or epistemic acceptance.

### `knowledge.project_results` · 投影受约束知识结果 / Project bounded knowledge results

- State: `CURRENT_BOUNDED` · callability `PUBLIC_BOUNDED` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Route a declared result record into bounded Knowledge result projections without upgrading its epistemic state.
- Suitable for: inputs `result_record, epistemic_correction`; declared outputs `bounded result projection, projection validation report`; class `KNOWLEDGE`.
- Use only if: Current status is CURRENT_BOUNDED and callability is PUBLIC_BOUNDED.; ignition/packs/knowledge/manifest.json; ignition/data/governance/knowledge-experience/manifest.json
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: result_record, epistemic_correction
- Outputs: bounded result projection, projection validation report
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/data/architecture/current-facts.json, ignition/data/governance/knowledge-experience/manifest.json, ignition/docs/foundation/claim-governance-and-function-identity.md, ignition/docs/governance/knowledge-experience-layer.md, ignition/packs/knowledge/manifest.json, ignition/tools/governance/validate_knowledge_experience.py, ignition/tools/validate_pack_registry.py; runtime `none declared`; version `1.0.0`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: The Pack Bus routes a proposal and does not execute hooks.; Projection cannot increase claim, evidence, proof or acceptance status.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tools/validate_pack_registry.py, ignition/tools/governance/validate_knowledge_experience.py`.
- Route default: `true` · claim ceiling: Bounded repository result projection only; no truth, evidence or epistemic upgrade.

### `knowledge.read_foundation` · 读取 Foundation / Read Foundation

- State: `CURRENT_BOUNDED` · callability `PUBLIC_BOUNDED` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Read declared Foundation objects and Current knowledge entrances under Pack and claim-governance boundaries.
- Suitable for: inputs `foundation_object, function_asset, nonfunction_assertion, natural-language knowledge query`; declared outputs `source-bounded knowledge summary, canonical source references`; class `KNOWLEDGE`.
- Use only if: Current status is CURRENT_BOUNDED and callability is PUBLIC_BOUNDED.; ignition/FOUNDATION.md; ignition/KNOWLEDGE/README.md; ignition/packs/knowledge/manifest.json
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: foundation_object, function_asset, nonfunction_assertion, natural-language knowledge query
- Outputs: source-bounded knowledge summary, canonical source references
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/FOUNDATION.md, ignition/KNOWLEDGE/README.md, ignition/data/architecture/current-facts.json, ignition/docs/foundation/claim-governance-and-function-identity.md, ignition/docs/foundation/future-claim-admission-protocol.md, ignition/packs/knowledge/manifest.json, ignition/tools/foundation/validate_foundation.py, ignition/tools/validate_pack_registry.py; runtime `none declared`; version `1.0.0`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: Navigation, registry closure and summaries do not prove substantive claims.; The Pack Bus is declarative and performs no hook execution.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tools/validate_pack_registry.py, ignition/tools/foundation/validate_foundation.py`.
- Route default: `true` · claim ceiling: Repository-local Foundation reading only; no independent truth, proof or evidence upgrade.

### `knowledge.validate_claim` · 校验断言边界 / Validate claim boundaries

- State: `CURRENT_BOUNDED` · callability `PUBLIC_BOUNDED` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Apply declared function and non-function claim governance checks without inferring human-review passes.
- Suitable for: inputs `claim, function_asset, nonfunction_assertion, proof_obligation`; declared outputs `claim-governance findings, required human review, bounded adjudication status`; class `VALIDATION_AUDIT`.
- Use only if: Current status is CURRENT_BOUNDED and callability is PUBLIC_BOUNDED.; ignition/docs/foundation/claim-governance-and-function-identity.md; ignition/docs/foundation/future-claim-admission-protocol.md; ignition/packs/knowledge/manifest.json
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: claim, function_asset, nonfunction_assertion, proof_obligation
- Outputs: claim-governance findings, required human review, bounded adjudication status
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/docs/foundation/claim-governance-and-function-identity.md, ignition/docs/foundation/future-claim-admission-protocol.md, ignition/packs/knowledge/manifest.json, ignition/tools/foundation/validate_claim_governance.py, ignition/tools/foundation/validate_nonfunction_claim_closure.py; runtime `none declared`; version `1.0.0`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: Formal maturity and external evidence remain independent.; Unautomatable gates return human review rather than inferred PASS.; Quarantine or closure does not establish truth.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tools/foundation/validate_claim_governance.py, ignition/tools/foundation/validate_nonfunction_claim_closure.py`.
- Route default: `true` · claim ceiling: Repository-local governance validation only; no truth, proof, evidence, causal or Owner-status upgrade.

### `knowledge.validate_evidence_link` · 校验证据链接 / Validate an evidence link

- State: `CURRENT_BOUNDED` · callability `PUBLIC_BOUNDED` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Check declared evidence-link structure, provenance and source relationship without treating a link as substantive confirmation.
- Suitable for: inputs `evidence_link, source record, claim-to-source relation`; declared outputs `provenance validation report, missing-evidence finding, scope mismatch`; class `VALIDATION_AUDIT`.
- Use only if: Current status is CURRENT_BOUNDED and callability is PUBLIC_BOUNDED.; ignition/packs/knowledge/manifest.json; ignition/docs/foundation/claim-governance-and-function-identity.md
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: evidence_link, source record, claim-to-source relation
- Outputs: provenance validation report, missing-evidence finding, scope mismatch
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/docs/foundation/claim-governance-and-function-identity.md, ignition/docs/foundation/future-claim-admission-protocol.md, ignition/packs/knowledge/manifest.json, ignition/tools/validate_epistemic_governance_relationships.py, ignition/tools/validate_pack_registry.py; runtime `none declared`; version `1.0.0`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: A valid link establishes traceability, not truth or replication.; Source presence cannot substitute for claim-specific support.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tools/validate_pack_registry.py, ignition/tools/validate_epistemic_governance_relationships.py`.
- Route default: `true` · claim ceiling: Evidence-link structure and provenance validation only; no substantive confirmation or epistemic acceptance.

### `language_thought.project_bounded_meaning` · 语言—思维受约束投影 / Bounded Language-Thought projection

- State: `CURRENT_BOUNDED` · callability `PUBLIC_BOUNDED` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Normalize and project meaning across source and target language profiles while preserving framing delta and unmapped residue.
- Suitable for: inputs `source text, proposition, translation request, target-language publication material`; declared outputs `normalized meaning candidate, target form candidate, framing delta, unmapped residue`; class `LANGUAGE_THOUGHT`.
- Use only if: Current status is CURRENT_BOUNDED and callability is PUBLIC_BOUNDED.; ignition/docs/architecture/language-thought-logic-plane.md; ignition/data/language-thought/manifest.json; ignition/docs/language-thought/README.md
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: source text, proposition, translation request, target-language publication material
- Outputs: normalized meaning candidate, target form candidate, framing delta, unmapped residue
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/data/language-thought/manifest.json, ignition/docs/architecture/language-thought-logic-plane.md, ignition/docs/foundation/claim-governance-and-function-identity.md, ignition/docs/language-thought/README.md, ignition/docs/publication/zhiyuan-writing-method.md, ignition/tests/test_language_thought_plane.py, ignition/tools/language_thought/validate_language_thought.py; runtime `none declared`; version `UNKNOWN_NOT_DECLARED_BY_OPERATION_REGISTRY`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: Meaning candidates are not language-independent truth.; Human review remains required for naturalness, literary quality and context-sensitive loss.; Language profiles do not establish strong linguistic determinism or different truth logics.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tools/language_thought/validate_language_thought.py, ignition/tests/test_language_thought_plane.py`.
- Route default: `true` · claim ceiling: Bounded cross-language representation and audit only; no universal meaning, literary-quality or truth guarantee.

### `maintenance.inspect_repository` · 检查仓库 / Inspect a repository

- State: `CURRENT_BOUNDED` · callability `PUBLIC_BOUNDED` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Perform declared offline, read-only repository inspection through the Repository Maintenance Pack boundary.
- Suitable for: inputs `repository_snapshot, declared repository path, offline maintenance query`; declared outputs `read-only inspection report, offline maintenance proposal`; class `REPOSITORY_MAINTENANCE`.
- Use only if: Current status is CURRENT_BOUNDED and callability is PUBLIC_BOUNDED.; ignition/packs/maintenance/manifest.json; ignition/agent_runtime/README.md
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: repository_snapshot, declared repository path, offline maintenance query
- Outputs: read-only inspection report, offline maintenance proposal
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/ITERATION.md, ignition/agent_runtime/README.md, ignition/docs/architecture/os-control-plane-r2.md, ignition/packs/maintenance/manifest.json, ignition/tools/validate_agent_runtime_boundary.py, ignition/tools/validate_r2_offline_repository_maintenance.py; runtime `none declared`; version `1.0.0`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: Network and remote Git mutation are prohibited.; Pack Bus routing produces a proposal and does not execute hooks.; Inspection does not authorize repository change.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tools/validate_r2_offline_repository_maintenance.py, ignition/tools/validate_agent_runtime_boundary.py`.
- Route default: `true` · claim ceiling: Offline read-only repository inspection only; no mutation, remote publication or production claim.

### `maintenance.validate_checkpoint` · 校验仓库 checkpoint / Validate a repository checkpoint

- State: `CURRENT_BOUNDED` · callability `PUBLIC_BOUNDED` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Validate bounded repository checkpoint and runtime-boundary evidence without publishing or mutating remote state.
- Suitable for: inputs `checkpoint_receipt, repository_snapshot, offline validation request`; declared outputs `checkpoint validation report, bounded failure finding`; class `VALIDATION_AUDIT`.
- Use only if: Current status is CURRENT_BOUNDED and callability is PUBLIC_BOUNDED.; ignition/packs/maintenance/manifest.json; ignition/agent_runtime/README.md
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: checkpoint_receipt, repository_snapshot, offline validation request
- Outputs: checkpoint validation report, bounded failure finding
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/ITERATION.md, ignition/agent_runtime/README.md, ignition/docs/architecture/os-control-plane-r2.md, ignition/packs/maintenance/manifest.json, ignition/tools/validate_agent_runtime_boundary.py, ignition/tools/validate_state_changelog.py; runtime `none declared`; version `1.0.0`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: A passing checkpoint does not imply accepted, merged, Current, deployed or externally valid state.; Remote Git mutation remains prohibited.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tools/validate_agent_runtime_boundary.py, ignition/tools/validate_state_changelog.py`.
- Route default: `true` · claim ceiling: Repository-local checkpoint validation only; no publication, deployment, external completion or acceptance.

### `repository.apply_iteration_method` · 按点火迭代操作法修改点火 / Change Ignition through the Iteration Method

- State: `CURRENT` · callability `PUBLIC_BOUNDED` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Govern explicitly authorized changes to Ignition through remote truth, gap, claim ceiling, propagation, validation, review, merge and receipt boundaries.
- Suitable for: inputs `explicit Ignition repository change request, declared change manifest`; declared outputs `candidate repository change, validation evidence, Draft lifecycle record, merge/current receipt when separately authorized`; class `REPOSITORY_SELF_ITERATION`.
- Use only if: Current status is CURRENT and callability is PUBLIC_BOUNDED.; ignition/ITERATION.md; ignition/AI-START-HERE.md; ignition/data/operations/project-components.json; ignition/data/operations/change-propagation-topology.json
- Do not use when: The request requires a mode other than REPOSITORY_CHANGE_RUN.; A required Current authority or declared source is unavailable.
- Inputs: explicit Ignition repository change request, declared change manifest
- Outputs: candidate repository change, validation evidence, Draft lifecycle record, merge/current receipt when separately authorized
- Mode and permissions: `REPOSITORY_CHANGE_RUN`; repository `EXPLICIT_USER_OR_OWNER_AUTHORIZATION_AND_ITERATION_METHOD`; external `FORBIDDEN`
- Side effects: repository `EXPLICIT_USER_OR_OWNER_AUTHORIZATION_AND_ITERATION_METHOD`; external `FORBIDDEN`.
- Dependencies: ignition/AI-START-HERE.md, ignition/ITERATION.md, ignition/data/architecture/current-system-identity.json, ignition/data/operations/change-propagation-topology.json, ignition/data/operations/project-components.json, ignition/docs/foundation/claim-governance-and-function-identity.md, ignition/docs/governance/life-community-value-charter.md, ignition/tests/test_change_propagation.py, ignition/tools/validate_current_state_sync.py; runtime `none declared`; version `UNKNOWN_NOT_DECLARED_BY_OPERATION_REGISTRY`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: Governs how Ignition changes itself; it is not the general protocol for using Ignition on an external object.; An open Draft PR is not Current and tests do not self-establish acceptance or merge.; Repository propagation is not reality causality.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tests/test_change_propagation.py, ignition/tools/validate_current_state_sync.py`.
- Route default: `true` · claim ceiling: Repository-state change discipline only; no truth, evidence, causal, Owner-acceptance or publication inference.

### `repository.apply_iteration_method_1_3` · 点火迭代操作法 1.3.0 / Ignition Iteration Method 1.3.0

- State: `HISTORICAL` · callability `STATUS_ONLY` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Preserve the superseded incremental-execution method as historical provenance only.
- Suitable for: inputs `historical method query`; declared outputs `historical status, supersession relation`; class `REPOSITORY_SELF_ITERATION`.
- Use only if: Current status is HISTORICAL and callability is STATUS_ONLY.; ignition/ITERATION.md; ignition/data/architecture/current-system-identity.json
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: historical method query
- Outputs: historical status, supersession relation
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/ITERATION.md, ignition/data/architecture/current-system-identity.json, ignition/docs/VERSIONING.md; runtime `none declared`; version `UNKNOWN_NOT_DECLARED_BY_OPERATION_REGISTRY`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: Cannot be selected as the Current method.; Historical execution evidence cannot override Current 1.4.0.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/ITERATION.md`.
- Route default: `false` · claim ceiling: Historical provenance and supersession status only; no Current execution authority.

### `research.coordinate_obligations` · 协调受约束研究义务 / Coordinate bounded research obligations

- State: `CURRENT_BOUNDED` · callability `PUBLIC_BOUNDED` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Coordinate bounded research obligations, dependencies, negative results and typed handoff through REOS LIGHT.
- Suitable for: inputs `research_obligation, evidence_request, negative_result`; declared outputs `bounded obligation DAG, case status, typed handoff bundle`; class `RESEARCH`.
- Use only if: Current status is CURRENT_BOUNDED and callability is PUBLIC_BOUNDED.; ignition/docs/architecture/reos-vnext-light.md; ignition/packs/research/manifest.json
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: research_obligation, evidence_request, negative_result
- Outputs: bounded obligation DAG, case status, typed handoff bundle
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/docs/architecture/reos-vnext-light.md, ignition/docs/foundation/claim-governance-and-function-identity.md, ignition/docs/foundation/future-claim-admission-protocol.md, ignition/packs/research/manifest.json, ignition/tests/test_reos_vnext_minimal_kernel.py, ignition/tools/validate_pack_registry.py; runtime `none declared`; version `1.0.0`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: REOS LIGHT adds process control, not epistemic authority.; Direct research remains preferable when obligation control is unnecessary.; The Pack Bus does not execute declared hooks.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tools/validate_pack_registry.py, ignition/tests/test_reos_vnext_minimal_kernel.py`.
- Route default: `true` · claim ceiling: Bounded research-process coordination only; no truth, publication, acceptance or external-validation inference.

### `research.reos_full` · REOS FULL / REOS FULL

- State: `UNSUPPORTED` · callability `STATUS_ONLY` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Record that no REOS FULL runtime is available and prevent an Agent from inventing one.
- Suitable for: inputs `REOS FULL capability request`; declared outputs `UNSUPPORTED status, bounded alternative reference`; class `RESEARCH`.
- Use only if: Current status is UNSUPPORTED and callability is STATUS_ONLY.; ignition/docs/architecture/reos-vnext-light.md
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: REOS FULL capability request
- Outputs: UNSUPPORTED status, bounded alternative reference
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/docs/architecture/reos-vnext-light.md, ignition/docs/foundation/claim-governance-and-function-identity.md; runtime `none declared`; version `UNKNOWN_NOT_DECLARED_BY_OPERATION_REGISTRY`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: There is no available REOS FULL runtime.; No recovery layer or expanded authority may be inferred.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/docs/architecture/reos-vnext-light.md`.
- Route default: `false` · claim ceiling: Unsupported-status declaration only; no runtime, recovery, execution or epistemic capability.

### `research.validate_reos_light` · 校验 REOS LIGHT / Validate REOS LIGHT

- State: `CURRENT_BOUNDED` · callability `PUBLIC_BOUNDED` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Validate bounded REOS LIGHT case state, references, obligation graph, review and typed handoff.
- Suitable for: inputs `reos_light_run, research case state, typed handoff bundle`; declared outputs `REOS LIGHT validation report, bounded failure state`; class `VALIDATION_AUDIT`.
- Use only if: Current status is CURRENT_BOUNDED and callability is PUBLIC_BOUNDED.; ignition/docs/architecture/reos-vnext-light.md; ignition/packs/research/manifest.json
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: reos_light_run, research case state, typed handoff bundle
- Outputs: REOS LIGHT validation report, bounded failure state
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/docs/architecture/reos-vnext-light.md, ignition/docs/foundation/claim-governance-and-function-identity.md, ignition/docs/foundation/future-claim-admission-protocol.md, ignition/packs/research/manifest.json, ignition/tests/test_reos_vnext_minimal_kernel.py, ignition/tools/validate_pack_registry.py; runtime `none declared`; version `1.0.0`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: Validation checks process structure, not proposition truth.; Generic SUCCESS and authority upgrades fail closed.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tests/test_reos_vnext_minimal_kernel.py, ignition/tools/validate_pack_registry.py`.
- Route default: `true` · claim ceiling: REOS LIGHT structural validation only; no truth, external validity or publication status.

### `visualization.render_derived_system_view` · 生成受约束派生系统视图 / Render a bounded derived system view

- State: `CURRENT_BOUNDED` · callability `PUBLIC_BOUNDED` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Generate a provider-neutral, source-bound derived system view for declared technical readability while preserving canonical topology, provenance and failure boundaries.
- Suitable for: inputs `canonical architecture source, derived system view request, bounded visualization run`; declared outputs `standalone derived system view artifact, provenance receipt, provider unavailable status`; class `VALIDATION_AUDIT`.
- Use only if: Current status is CURRENT_BOUNDED and callability is PUBLIC_BOUNDED.; ignition/data/architecture/overall-architecture.json; ignition/data/architecture/interactive-system-map.json; ignition/schemas/operations/task150-step18-scope-split-admission-objects-r1.schema.json; ignition/schemas/operations/task150-step21-fresh-standalone-evidence-r1.schema.json; ignition/schemas/operations/task150-step22-immutable-compatibility-envelope-r1.schema.json
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: canonical architecture source, derived system view request, bounded visualization run
- Outputs: standalone derived system view artifact, provenance receipt, provider unavailable status
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/ITERATION.md, ignition/data/architecture/interactive-system-map.json, ignition/data/architecture/overall-architecture.json, ignition/data/operations/iterations/150/step22-immutable-compatibility-envelope.json, ignition/docs/foundation/claim-governance-and-function-identity.md, ignition/docs/foundation/future-claim-admission-protocol.md, ignition/schemas/operations/task150-step18-scope-split-admission-objects-r1.schema.json, ignition/schemas/operations/task150-step21-fresh-standalone-evidence-r1.schema.json, ignition/schemas/operations/task150-step22-immutable-compatibility-envelope-r1.schema.json, ignition/tests/test_task150_step21_fresh_standalone_evidence.py, ignition/tests/test_task150_step22_immutable_compatibility_envelope.py, ignition/tools/run_task150_bounded_visualization_adapter.py, ignition/tools/validate_task150_step21_fresh_standalone_evidence.py, ignition/tools/validate_task150_step22_immutable_compatibility_envelope.py; runtime `none declared`; version `UNKNOWN_NOT_DECLARED_BY_OPERATION_REGISTRY`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: The operation produces a bounded derived artifact for declared technical use; it does not replace or write back to the canonical architecture source.; The provider is an optional tested implementation selected by Ignition; provider validation cannot add, delete or semantically mutate topology.; An unavailable provider returns PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT and cannot trigger installation, substitution or repository mutation.; A request for architecture analysis alone does not auto-render a derived view.; Delta, default-renderer selection, architecture truth, external truth, production readiness and aesthetic endorsement remain outside this operation.; The tested compatibility envelope is pinned to Archify exact commit 06dd052602dd9a369e4d034e24faef0917b5a60c; future provider versions require a new compatibility check.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tools/run_task150_bounded_visualization_adapter.py, ignition/tools/validate_task150_step21_fresh_standalone_evidence.py, ignition/tools/validate_task150_step22_immutable_compatibility_envelope.py, ignition/tests/test_task150_step21_fresh_standalone_evidence.py, ignition/tests/test_task150_step22_immutable_compatibility_envelope.py`.
- Route default: `true` · claim ceiling: Current bounded provider-neutral derived system view for declared technical use only; no canonical architecture truth, topology authority, default renderer, Delta promotion, aesthetic endorsement, external truth or production readiness.

### `writing.apply_editorial_method` · 应用之元写作法 / Apply the Zhiyuan Writing Method

- State: `CURRENT` · callability `PUBLIC` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Transform source-bounded material into L6 writing while preserving source class, provenance, language-thought deltas and claim ceiling.
- Suitable for: inputs `editorial_source, external_input, ignition_increment, publication draft request`; declared outputs `source-bounded publication draft, editorial provenance record, language-thought residue`; class `WRITING`.
- Use only if: Current status is CURRENT and callability is PUBLIC.; ignition/docs/publication/zhiyuan-writing-method.md; ignition/templates/publication/zhiyuan-writing-spec.md; ignition/docs/architecture/language-thought-logic-plane.md
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: editorial_source, external_input, ignition_increment, publication draft request
- Outputs: source-bounded publication draft, editorial provenance record, language-thought residue
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/docs/architecture/language-thought-logic-plane.md, ignition/docs/foundation/claim-governance-and-function-identity.md, ignition/docs/governance/life-community-value-charter.md, ignition/docs/publication/zhiyuan-writing-method.md, ignition/packs/writing/manifest.json, ignition/templates/publication/zhiyuan-writing-spec.md, ignition/tools/governance/validate_human_surface_contract.py, ignition/tools/publication/validate_fire_seeds.py; runtime `none declared`; version `1.0.0`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: Writing quality cannot raise fact, cause, proof, value or evidence status.; Ignition-derived material is not a new independent source.; The Pack Bus routes a proposal and does not execute publishing hooks.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tools/publication/validate_fire_seeds.py, ignition/tools/governance/validate_human_surface_contract.py`.
- Route default: `true` · claim ceiling: Current L6 writing transformation only; no factual, causal, proof, value, publication-acceptance or literary-quality guarantee.

### `writing.validate_publication_surface` · 校验出版表面 / Validate a publication surface

- State: `CURRENT_BOUNDED` · callability `PUBLIC_BOUNDED` · availability `REGISTERED_OPERATION_NOT_INFERRED_EXECUTABLE`
- Can do: Validate declared publication and human-surface structure, provenance and navigation without establishing substantive acceptance.
- Suitable for: inputs `publication_draft, publication_review, human_surface_entry`; declared outputs `publication-surface validation report, provenance or navigation finding`; class `VALIDATION_AUDIT`.
- Use only if: Current status is CURRENT_BOUNDED and callability is PUBLIC_BOUNDED.; ignition/packs/writing/manifest.json; ignition/docs/publication/zhiyuan-writing-method.md
- Do not use when: The request requires a mode other than READ_ONLY_RUN.; A required Current authority or declared source is unavailable.
- Inputs: publication_draft, publication_review, human_surface_entry
- Outputs: publication-surface validation report, provenance or navigation finding
- Mode and permissions: `READ_ONLY_RUN`; repository `FORBIDDEN`; external `FORBIDDEN`
- Side effects: repository `FORBIDDEN`; external `FORBIDDEN`.
- Dependencies: ignition/docs/foundation/claim-governance-and-function-identity.md, ignition/docs/governance/life-community-value-charter.md, ignition/docs/publication/zhiyuan-writing-method.md, ignition/packs/writing/manifest.json, ignition/tools/governance/validate_human_surface_contract.py, ignition/tools/publication/validate_fire_seeds.py; runtime `none declared`; version `1.0.0`.
- Cost: `UNKNOWN` · No comparable per-operation cost evidence is declared.
- Alternatives: `NOT_MAPPED_IN_CURRENT_REGISTRY` · none mapped.
- Fallback: Follow the operation-specific stop conditions and report the unmet input, authority, or output contract.
- Limits: Surface validity does not imply content truth, literary quality, acceptance, deployment or Current status.; Public visibility is distinct from capability availability.
- Evidence: `DECLARATION_ONLY` · registry blob `21fe1bfcdb0d9762edd60339aca14f1040393fc7` · validation `ignition/tools/governance/validate_human_surface_contract.py, ignition/tools/publication/validate_fire_seeds.py`.
- Route default: `true` · claim ceiling: Publication-surface structure and provenance validation only; no substantive acceptance, truth or deployment inference.

## Optional experimental tools

### `ignition.adaptive_toolbox_route_planner` · 点火工具组合路由预览 / Ignition toolbox route preview

- State: `EXPERIMENTAL_AVAILABLE` / `EXPERIMENTAL` · version `0.1.0` · license `BUSL-1.1` · maintainer `Ignition repository maintainers; this field does not grant Owner or scientific authority.` · source blob `a329c8e438429bffad0daa33dbe7525e54831f67`.
- Can do: Select a sufficient set of registered operations for exact input and output requirements, optionally considering explicitly allowlisted experimental cards.
- Good for: Planning routes from explicit input types and required output types.; Showing when a task needs one operation, complementary operations, or remains uncovered.; Keeping experimental tools opt-in and returning an explicit incomplete result when no declared route covers a requirement.
- Not for: Inferring the task contract from unstructured natural language.; Calling, dispatching, or executing selected operations.; Granting permissions, Owner approval, or scientific authority.; Claiming measured cost optimality or a globally minimal set.
- Use only if: The caller supplies exact input types, required outputs, allowed modes, and a nonblank Current reference string; the planner echoes that string without resolving it.; The operation registry and pinned experimental candidate-card source are present.
- Do not use when: Task requirements cannot be expressed with the declared input/output types.; The caller needs actual tool execution or a scientific conclusion rather than a route proposal.; The current operation registry no longer matches the candidate-card source pin.
- Inputs → outputs: typed toolbox route profile on stdin → typed route proposal, covered and unmet output list, candidate rejection reasons
- Permissions: `READ_ONLY_RUN` / `READ_ONLY_REPOSITORY_SNAPSHOT` · explicit Owner authorization required `false` · reads `ignition/data/operations/ignition-operation-capability-registry-r1.json, ignition/data/operations/toolbox-candidate-cards-r0.json` · writes `none` · network `false` · secrets `false` · billing `false` · external actions `false.
- Side effects: stdout only.
- Dependencies: ignition/data/operations/ignition-operation-capability-registry-r1.json, ignition/data/operations/toolbox-candidate-cards-r0.json, ignition/tools/operations/classify_ignition_run_mode.py; runtime dependencies: Python >=3.9 standard library.
- Cost: `UNKNOWN` · The selection run is local, but no calibrated latency, memory, or compute-cost comparison exists.
- Alternatives: `repository.apply_iteration_method` (NOT_EQUIVALENT): The existing single-operation lifecycle planner resolves one declared operation; this preview selects a typed set and still does not execute it..
- Invocation example: `python3 -B ignition/tools/operations/plan_ignition_operation_run.py --route-request`
- Fallback: If exact typed coverage is unavailable, return INCOMPLETE and use the existing single-operation planner or report the missing capability; never guess an operation from natural-language similarity.
- Evidence: `REAL_TOOL_TEST` · source refs `ignition/data/operations/ignition-operation-capability-registry-r1.json` (CURRENT_OPERATION_AUTHORITY), `ignition/data/operations/toolbox-candidate-cards-r0.json` (OPT_IN_CANDIDATE_CARDS), `ignition/tools/operations/classify_ignition_run_mode.py` (EXECUTION_MODE_CLASSIFIER_DEPENDENCY); focused checks [ignition/tests/test_ignition_operation_lifecycle.py](tests/test_ignition_operation_lifecycle.py), [ignition/tests/test_toolbox_routing.py](tests/test_toolbox_routing.py); negative controls: Owner-deferred, historical, unsupported, and external-action operations are not selected.; Experimental tools remain excluded unless their IDs are explicitly allowlisted.; Unknown required outputs yield INCOMPLETE and do not cause dispatch..
- Route default: `false` · conditions: Invoke only when a task explicitly needs an auditable operation-set proposal.; A route proposal never authorizes invocation; each selected tool is separately checked at call time..
- Claim ceiling: A deterministic proposal based on declared contracts only; completion quality, measured cost, invocation, permission, Owner approval, and scientific validity remain unverified.

### `knowledge.cluster_source_brief` · 文章簇来源简报 / Article-cluster source brief

- State: `EXPERIMENTAL_AVAILABLE` / `EXPERIMENTAL` · version `0.1.0` · license `BUSL-1.1` · maintainer `Ignition repository maintainers; this field does not grant Owner or scientific authority.` · source blob `493513e3966d02214692918b847f4c4e92d81884`.
- Can do: Render a deterministic source brief for declared article-cluster IDs from the repository's existing asset-card corpus.
- Good for: Preparing a source-linked inventory of the members and declared status of a known article cluster.; Finding source and evidence fields already recorded in the repository's governed asset cards.
- Not for: Determining whether a cluster's claims are true.; Producing a finished or publication-approved article.; Looking up clusters or sources outside the checked-out repository snapshot.
- Use only if: The requested cluster ID exists in ignition/analysis/corpus-relation/article_cluster_candidates.json.; The governed Knowledge card corpus and source parser are available in the same checkout.
- Do not use when: The task requires live or freshly updated external sources.; The task asks for scientific adjudication, proof, or external evidence validation.; The cluster snapshot is stale for the user's requested time period.
- Inputs → outputs: article cluster ID → source-backed cluster member brief, source and output digest receipt
- Permissions: `READ_ONLY_RUN` / `READ_ONLY_REPOSITORY_SNAPSHOT` · explicit Owner authorization required `false` · reads `ignition/KNOWLEDGE/cards/, ignition/analysis/corpus-relation/article_cluster_candidates.json, ignition/tools/build_corpus_relation_graph.py` · writes `none` · network `false` · secrets `false` · billing `false` · external actions `false.
- Side effects: Writes only the JSON receipt to stdout; does not create or overwrite repository files..
- Dependencies: ignition/analysis/corpus-relation/article_cluster_candidates.json, ignition/KNOWLEDGE/cards/, ignition/tools/build_corpus_relation_graph.py, ignition/tools/extract_cluster_source_brief.py; runtime dependencies: Python >=3.9 standard library.
- Cost: `UNKNOWN` · No comparable timing, token, memory, or compute-cost profile has been established.
- Alternatives: `knowledge.read_foundation` (COMPLEMENTARY_NOT_EQUIVALENT): The registered operation provides source-bounded knowledge summaries but does not render this cluster-member brief contract..
- Invocation example: `python3 -B ignition/tools/toolbox_cluster_source_brief.py C000`
- Fallback: If the cluster ID or source data is unavailable, stop and report the missing reference; read the canonical asset cards manually without substituting an inferred cluster.
- Evidence: `REAL_TOOL_TEST` · source refs `ignition/tools/toolbox_cluster_source_brief.py` (READ_ONLY_TOOL_ENTRYPOINT), `ignition/tools/extract_cluster_source_brief.py` (BRIEF_RENDERER_AND_RECEIPT_BUILDER), `ignition/analysis/corpus-relation/article_cluster_candidates.json` (CLUSTER_SNAPSHOT), `ignition/tools/build_corpus_relation_graph.py` (CARD_PARSER), `ignition/KNOWLEDGE/cards/` (GOVERNED_ASSET_CARD_CORPUS); focused checks [ignition/tests/test_cluster_source_brief_tool.py](tests/test_cluster_source_brief_tool.py); negative controls: Unknown cluster ID returns nonzero and emits no partial brief.; --stdout creates or overwrites no repository file..
- Route default: `false` · conditions: Only include through an explicit experimental-tool allowlist for source-brief tasks.; Do not invoke after selection without the task's own user authorization and input..
- Claim ceiling: A formatted projection of repository-local cluster metadata and asset-card fields only; no truth, proof, external evidence, article quality, acceptance, or publication status is inferred.
