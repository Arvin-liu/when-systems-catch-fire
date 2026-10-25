# Ignition Toolbox / 点火工具箱

> This page is generated from the canonical Current operation registry plus the pinned optional candidate-card source. It is a discovery surface, not a permission or truth authority.
>
> Current operation entries are registered capabilities; the registry does not prove that every entry is a standalone executable in this environment. Experimental tools are opt-in and default off.

Current operation registry: 20 entries · `blob 21fe1bfcdb0d9762edd60339aca14f1040393fc7`.
Optional experimental tools: 9 · `blob bbb7bcb3e63c735bd90824961aa777fdafeeb51f`.

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

### `foundation.batch_resolve_current_asset_references` · Current 资产身份批量解析 / Batch Current asset identity resolver

- State: `EXPERIMENTAL_AVAILABLE` / `EXPERIMENTAL` · version `0.1.0` · license `BUSL-1.1` · maintainer `Ignition repository maintainers; this field does not grant Owner or scientific authority.` · source blob `983c0a43603bf7e6e786718266c51cd89a8c27ec`.
- Can do: Resolve an ordered batch of exact references against the checked-out Current canonical identity, alias, correction, claim, and legacy-mapping authorities; emit a source-hashed receipt to stdout.
- Good for: Resolving multiple exact IDs, canonical titles, registered aliases, and authority-backed identity corrections in one input-ordered batch.; Producing a reproducible receipt with SHA-256 references to the resolver and five Current authority snapshots.; Preserving ambiguous and unresolved references as explicit outcomes instead of dropping or guessing them.
- Not for: Fuzzy, semantic, natural-language, web, or cross-repository identity search.; Changing identities, repairing source data, or writing results into the repository.; Establishing scientific truth, proof, external validity, or evidence quality.
- Use only if: The caller supplies a nonempty JSON object containing exactly one key, references, whose value is a nonempty array of nonblank strings.; All five Current authority files and the existing exact resolver are available in the same repository snapshot.; The caller accepts repository-snapshot resolution semantics and an output receipt on stdout.
- Do not use when: The task requires fresh external sources, fuzzy matching, or resolution beyond the checked-out repository snapshot.; An ambiguous or unresolved result must be automatically selected or corrected.; The task asks for scientific adjudication, proof, or evidence validation.
- Inputs → outputs: JSON stdin object with an ordered nonempty array of exact reference strings → input-ordered canonical identity resolution rows, authority and resolver SHA-256 receipt
- Permissions: `READ_ONLY_RUN` / `READ_ONLY_REPOSITORY_SNAPSHOT` · explicit Owner authorization required `false` · reads `ignition/tools/foundation/resolve_current_canonical_asset.py, ignition/data/foundation/function-assets/identity-cards.jsonl, ignition/data/foundation/nonfunction-claims/claim-registry.jsonl, ignition/data/governance/knowledge-experience/alias-index.jsonl, ignition/data/foundation/function-assets/corrections.jsonl, ignition/data/foundation/mappings/legacy-mappings.jsonl` · writes `none` · network `false` hosts `none` · secrets `false` · billing `false` · external actions `false.
- Side effects: Writes the result only to stdout; malformed input and unavailable authority are reported to stderr with nonzero status; no repository files are created or changed..
- Dependencies: ignition/tools/foundation/resolve_current_canonical_asset.py, ignition/data/foundation/function-assets/identity-cards.jsonl, ignition/data/foundation/nonfunction-claims/claim-registry.jsonl, ignition/data/governance/knowledge-experience/alias-index.jsonl, ignition/data/foundation/function-assets/corrections.jsonl, ignition/data/foundation/mappings/legacy-mappings.jsonl; runtime dependencies: Python >=3.9 standard library.
- Cost: `UNKNOWN` · The resolver rebuilds exact lookup indexes for each reference; no comparable batch latency or memory benchmark has been established.
- Alternatives: `foundation.resolve_current_asset` (COMPLEMENTARY_SINGLE_REFERENCE_TOOL): The Current operation exposes the single-reference resolver contract; this experimental CLI adds ordered multi-reference input and a batch receipt while reusing that resolver algorithm..
- Invocation example: `python3 -B ignition/tools/toolbox_batch_resolve_current_assets.py --stdin (stdin JSON: {"references":[...]})`
- Fallback: For one reference, use the existing foundation.resolve_current_asset operation or ignition/tools/foundation/resolve_current_canonical_asset.py --reference; if this batch tool is unavailable, process references individually and preserve each unresolved or ambiguous status.
- Evidence: `REAL_TASK_OUTCOME` · source refs `ignition/tools/toolbox_batch_resolve_current_assets.py` (BATCH_TOOL_ENTRYPOINT), `ignition/tools/foundation/resolve_current_canonical_asset.py` (EXISTING_EXACT_RESOLVER_ALGORITHM), `ignition/data/foundation/function-assets/identity-cards.jsonl` (CURRENT_FUNCTION_IDENTITY_AUTHORITY), `ignition/data/foundation/nonfunction-claims/claim-registry.jsonl` (CURRENT_NONFUNCTION_CLAIM_AUTHORITY), `ignition/data/governance/knowledge-experience/alias-index.jsonl` (CURRENT_REGISTERED_ALIAS_AUTHORITY), `ignition/data/foundation/function-assets/corrections.jsonl` (CURRENT_IDENTITY_CORRECTION_AUTHORITY), `ignition/data/foundation/mappings/legacy-mappings.jsonl` (CURRENT_LEGACY_MIGRATION_AUTHORITY); focused checks [ignition/tests/test_batch_canonical_resolution_tool.py](tests/test_batch_canonical_resolution_tool.py), [ignition/tests/test_current_canonical_resolution.py](tests/test_current_canonical_resolution.py); negative controls: Unknown, historical-path, and near-match references remain explicitly unresolved in input order.; Malformed batches, path traversal, and symlinked authorities fail closed without partial stdout output.; Running the CLI creates or changes no repository files..
- Route default: `false` · conditions: Include only through an explicit experimental-tool allowlist for exact multi-reference repository identity resolution.; The route proposal does not execute the tool; the caller must separately authorize and supply the specific batch input.; Do not select when fuzzy matching, external freshness, scientific judgment, or automatic identity repair is required..
- Claim ceiling: Repository-snapshot canonical identity and migration resolution only; ambiguous and unresolved rows remain explicit; no fuzzy identity, truth, proof, evidence upgrade, or external validity is inferred.

### `foundation.read_current_asset_card` · Current Foundation 身份卡读取器 / Current Foundation record reader

- State: `EXPERIMENTAL_AVAILABLE` / `EXPERIMENTAL` · version `0.1.0` · license `BUSL-1.1` · maintainer `Ignition repository maintainers; this field does not grant Owner or scientific authority.` · source blob `80b1d6ebd20ec7107ff158d8f75d76f8cfb7dbd6`.
- Can do: Read one exact canonical ID from the checked-out Current function-identity or non-function-claim registry; return the complete stored record and verify its record SHA-256.
- Good for: Read the complete current record after the caller already has an exact canonical ID.; Inspect the record kind, authority fields, evidence references, use boundaries, and verified record digest in one deterministic JSON result.
- Not for: Discovering IDs, resolving aliases or historical references, fuzzy search, or selecting between ambiguous records.; Checking that linked source files still support the record, validating scientific claims, or establishing proof or external validity.; Changing registries or writing a dossier into the repository.
- Use only if: The caller supplies one exact canonical ID already listed in a Current registry.; The function identity and non-function claim registries are available in the same checked-out snapshot.; The caller accepts a full record payload on stdout and record-level SHA-256 verification only.
- Do not use when: The input is a title, alias, historical path, natural-language query, or uncertain identifier.; The task needs fresh external evidence, independent source-anchor checking, scientific adjudication, or an authority upgrade.; The caller needs only a compact yes/no identity resolution; use the existing resolver instead.
- Inputs → outputs: JSON stdin object containing exactly one exact canonical_id string → complete Current function-identity card or non-function claim record, verified record digest and hashes of both registry snapshots
- Permissions: `READ_ONLY_RUN` / `READ_ONLY_REPOSITORY_SNAPSHOT` · explicit Owner authorization required `false` · reads `ignition/data/foundation/function-assets/identity-cards.jsonl, ignition/data/foundation/nonfunction-claims/claim-registry.jsonl` · writes `none` · network `false` hosts `none` · secrets `false` · billing `false` · external actions `false.
- Side effects: Writes the record result only to stdout; invalid input or unavailable/corrupt authorities return a nonzero status and no partial stdout..
- Dependencies: ignition/data/foundation/function-assets/identity-cards.jsonl, ignition/data/foundation/nonfunction-claims/claim-registry.jsonl; runtime dependencies: Python >=3.9 standard library.
- Cost: `UNKNOWN` · Both checked-out JSONL registries are scanned per call; latency and memory have not been benchmarked.
- Alternatives: `foundation.batch_resolve_current_asset_references` (COMPLEMENTARY_NOT_EQUIVALENT): The batch resolver accepts aliases and historical references but returns bounded resolution rows; this reader accepts one canonical ID and returns its full current registry record..
- Invocation example: `python3 -B ignition/tools/toolbox_read_current_asset_card.py --stdin (stdin JSON: {"canonical_id":"<exact Current ID>"})`
- Fallback: Use foundation.batch_resolve_current_asset_references to confirm exact Current identity resolution; for full record content, read the authority row through a separately approved repository reader and verify its record_sha256.
- Evidence: `REAL_TASK_OUTCOME` · source refs `ignition/tools/toolbox_read_current_asset_card.py` (READ_ONLY_TOOL_ENTRYPOINT), `ignition/data/foundation/function-assets/identity-cards.jsonl` (CURRENT_FUNCTION_IDENTITY_AUTHORITY), `ignition/data/foundation/nonfunction-claims/claim-registry.jsonl` (CURRENT_NONFUNCTION_CLAIM_AUTHORITY); focused checks [ignition/tests/test_toolbox_read_current_asset_card.py](tests/test_toolbox_read_current_asset_card.py), [ignition/tests/test_current_canonical_resolution.py](tests/test_current_canonical_resolution.py); negative controls: Aliases, titles, paths, malformed IDs, and unknown IDs are rejected without partial stdout.; A duplicate canonical ID across function and claim registries, a corrupt record hash, or a symlinked authority fails closed.; The result marks only the stored record hash as verified and states that linked-source support and scientific validity are not established..
- Route default: `false` · conditions: Include only through an explicit experimental-tool allowlist when the task requires a full current record for an already-known canonical ID.; The route proposal does not execute the reader; the caller separately supplies the exact ID.; Do not select for discovery, alias resolution, source verification, scientific judgment, or truth/authority decisions..
- Claim ceiling: One exact checked-out Current registry record, with its stored record hash verified and both identity registries source-hashed; no truth, proof, external validity, or independent source-anchor verification is inferred.

### `function_os.run_bounded_symbolic_spec` · 有界符号函数规格执行器 / Bounded symbolic FunctionSpec runner

- State: `EXPERIMENTAL_AVAILABLE` / `EXPERIMENTAL` · version `toolbox-wrapper-0.1.0; Function OS 0.2.1rc0 candidate` · license `BUSL-1.1` · maintainer `Ignition repository maintainers; this field does not grant Owner or scientific authority.` · source blob `bcb1537700d14acff651aabb5ddbe7f311561c27`.
- Can do: Run one explicitly supplied, single-output pure symbolic FunctionSpec through Function OS N1-N7 with bounded expression size, arithmetic intermediates, and numeric input magnitude.
- Good for: Run one declared deterministic symbolic function with one output and 1 to 16 explicitly supplied numeric or boolean inputs.; Inspect the N1-N7 execution status, in-memory artifact integrity report, trace, and N7 internal consistency checks for a bounded specification.
- Not for: Executing untrusted or malicious code, acting as an isolated security sandbox, or processing arbitrary Python expressions.; Scientific adjudication, proof, empirical validation, external truth claims, or recognition that a function models reality.; Stateful or I/O effects, multiple outputs, exponentiation, calls, attributes, N8 routing, N9 registry writes, or persisted artifacts.
- Use only if: Python 3.10 or newer is available and the checked-out Function OS v0.2 source and wrapper are intact.; The caller supplies a single symbolic FunctionSpec with exactly one output, exactly pure effects, 1 to 16 declared inputs, and one output equality postcondition.; The UTF-8 JSON request is at most 16 KiB; expressions are at most 512 characters, 64 AST nodes, and depth 16; numeric inputs/constants are at most 10^12 in magnitude and arithmetic intermediates/results at most 10^100.
- Do not use when: Inputs or expressions are adversarial and require operating-system isolation or a security boundary.; The specification needs exponentiation, calls, attributes, strings, collections, multiple outputs, non-pure effects, or values beyond the declared bounds.; The task requires persistence, registry admission, source-backed evidence, scientific truth, proof, or external validation.
- Inputs → outputs: UTF-8 JSON stdin object containing exactly one bounded FunctionSpec object and one exact input-value object → N1-N7 execution status and single declared output when successful, in-memory artifact integrity report, execution trace, and N7 internal consistency result, source-tree and wrapper source digests
- Permissions: `READ_ONLY_RUN` / `READ_ONLY_REPOSITORY_SOURCE_AND_STDIN` · explicit Owner authorization required `false` · reads `ignition/tools/toolbox_function_os_evaluator.py, ignition/function-os-candidate/v0.2/function_os/, ignition/function-os-candidate/v0.2/v0.2-scope-contract.json, ignition/function-os-candidate/v0.2/pyproject.toml` · writes `none` · network `false` hosts `none` · secrets `false` · billing `false` · external actions `false.
- Side effects: Writes the bounded JSON result to stdout; execution artifacts and traces remain in process memory and N9 is not invoked., The wrapper disables Python bytecode writes before loading Function OS modules..
- Dependencies: ignition/function-os-candidate/v0.2/function_os/, ignition/function-os-candidate/v0.2/v0.2-scope-contract.json, ignition/function-os-candidate/v0.2/pyproject.toml; runtime dependencies: Python >=3.10 standard library; no third-party runtime packages.
- Cost: `UNKNOWN` · Execution is local and bounded by request and AST limits, but no latency or memory benchmark has been established.
- Alternatives: none mapped.
- Invocation example: `python3.11 -B ignition/tools/toolbox_function_os_evaluator.py --stdin (stdin JSON: {"function_spec":{...},"inputs":{...}})`
- Fallback: Use the checked-in Function OS N1-N7 tests on Python 3.10 or newer and inspect the exact specification and expected outputs manually; do not substitute eval, a general Python runner, or a scientific-validity claim.
- Evidence: `REAL_TOOL_TEST` · source refs `ignition/tools/toolbox_function_os_evaluator.py` (BOUNDED_READ_ONLY_TOOL_ENTRYPOINT), `ignition/function-os-candidate/v0.2/function_os/` (FUNCTION_OS_N1_TO_N7_IMPLEMENTATION), `ignition/function-os-candidate/v0.2/v0.2-scope-contract.json` (UPSTREAM_SCOPE_AND_NON_GOAL_CONTRACT), `ignition/function-os-candidate/v0.2/pyproject.toml` (UPSTREAM_VERSION_LICENSE_AND_RUNTIME_METADATA); focused checks [ignition/tests/test_toolbox_function_os_evaluator.py](tests/test_toolbox_function_os_evaluator.py); negative controls: Calls, attributes, exponentiation, multiple outputs, non-pure effects, oversized inputs, and oversized intermediate arithmetic are rejected.; Duplicate JSON keys and requests over 16 KiB return nonzero with no partial stdout; division by zero is rejected by the bounded arithmetic preflight.; Precondition failure is preserved; N9 registry writes are never invoked; a passing N7 status is explicitly limited to internal consistency..
- Route default: `false` · conditions: Include only through an explicit experimental-tool allowlist when the task supplies a bounded pure symbolic FunctionSpec and asks for its local N1-N7 execution report.; A route proposal never runs the function; the caller separately supplies the complete FunctionSpec and inputs to the CLI.; Never select for arbitrary code, scientific proof, truth, registry admission, or effectful execution..
- Claim ceiling: A bounded local execution report for one pure symbolic FunctionSpec through Function OS N1-N7, with internal artifact/trace consistency checks only; it does not establish specification truth, empirical or scientific correctness, proof, external validation, security isolation, registry admission, or publication status.

### `ignition.adaptive_toolbox_route_planner` · 点火工具组合路由预览 / Ignition toolbox route preview

- State: `EXPERIMENTAL_AVAILABLE` / `EXPERIMENTAL` · version `0.1.0` · license `BUSL-1.1` · maintainer `Ignition repository maintainers; this field does not grant Owner or scientific authority.` · source blob `d7881daae28a3d82612ceadb78d77bcd879bfe83`.
- Can do: Select a sufficient set of registered operations for exact input and output requirements, optionally considering explicitly allowlisted experimental cards and exact caller-supplied network hosts.
- Good for: Planning routes from explicit input types and required output types.; Showing when a task needs one operation, complementary operations, or remains uncovered.; Keeping experimental tools opt-in and returning an explicit incomplete result when no declared route covers a requirement.; Keeping fixed-host network candidates excluded unless the typed profile explicitly lists every exact required DNS host.
- Not for: Inferring the task contract from unstructured natural language.; Calling, dispatching, or executing selected operations.; Granting permissions, Owner approval, or scientific authority.; Claiming measured cost optimality or a globally minimal set.; Authenticating the caller authority behind an allowed_network_hosts value or authorizing a network request.
- Use only if: The caller supplies exact input types, required outputs, allowed modes, and a nonblank Current reference string; the planner echoes that string without resolving it.; The operation registry and pinned experimental candidate-card source are present.; Optional allowed_network_hosts entries are caller-supplied route context only and never grant authority; actual invocation and permissions are checked separately.
- Do not use when: Task requirements cannot be expressed with the declared input/output types.; The caller needs actual tool execution or a scientific conclusion rather than a route proposal.; The current operation registry no longer matches the candidate-card source pin.
- Inputs → outputs: typed toolbox route profile on stdin, optional allowed_network_hosts exact DNS-name list; omitted means no network hosts allowed → typed route proposal, covered and unmet output list, candidate rejection reasons, caller-supplied network-host context and its unverified binding status
- Permissions: `READ_ONLY_RUN` / `READ_ONLY_REPOSITORY_SNAPSHOT` · explicit Owner authorization required `false` · reads `ignition/data/operations/ignition-operation-capability-registry-r1.json, ignition/data/operations/toolbox-candidate-cards-r0.json` · writes `none` · network `false` hosts `none` · secrets `false` · billing `false` · external actions `false.
- Side effects: stdout only.
- Dependencies: ignition/data/operations/ignition-operation-capability-registry-r1.json, ignition/data/operations/toolbox-candidate-cards-r0.json, ignition/tools/operations/classify_ignition_run_mode.py; runtime dependencies: Python >=3.9 standard library.
- Cost: `UNKNOWN` · The selection run is local, but no calibrated latency, memory, or compute-cost comparison exists.
- Alternatives: `repository.apply_iteration_method` (NOT_EQUIVALENT): The existing single-operation lifecycle planner resolves one declared operation; this preview selects a typed set and still does not execute it..
- Invocation example: `python3 -B ignition/tools/operations/plan_ignition_operation_run.py --route-request`
- Fallback: If exact typed coverage is unavailable, return INCOMPLETE and use the existing single-operation planner or report the missing capability; never guess an operation from natural-language similarity.
- Evidence: `REAL_TOOL_TEST` · source refs `ignition/data/operations/ignition-operation-capability-registry-r1.json` (CURRENT_OPERATION_AUTHORITY), `ignition/data/operations/toolbox-candidate-cards-r0.json` (OPT_IN_CANDIDATE_CARDS), `ignition/tools/operations/classify_ignition_run_mode.py` (EXECUTION_MODE_CLASSIFIER_DEPENDENCY); focused checks [ignition/tests/test_ignition_operation_lifecycle.py](tests/test_ignition_operation_lifecycle.py), [ignition/tests/test_toolbox_routing.py](tests/test_toolbox_routing.py); negative controls: Owner-deferred, historical, unsupported, and external-action operations are not selected.; Experimental tools remain excluded unless their IDs are explicitly allowlisted.; Unknown required outputs yield INCOMPLETE and do not cause dispatch..
- Route default: `false` · conditions: Invoke only when a task explicitly needs an auditable operation-set proposal.; A route proposal never authorizes invocation; each selected tool is separately checked at call time..
- Claim ceiling: A deterministic proposal based on declared contracts and caller-supplied exact host strings only; host authorization, measured cost optimality, tool invocation, permission, Owner approval, and scientific validity remain unverified.

### `knowledge.cluster_source_brief` · 文章簇来源简报 / Article-cluster source brief

- State: `EXPERIMENTAL_AVAILABLE` / `EXPERIMENTAL` · version `0.1.0` · license `BUSL-1.1` · maintainer `Ignition repository maintainers; this field does not grant Owner or scientific authority.` · source blob `493513e3966d02214692918b847f4c4e92d81884`.
- Can do: Render a deterministic source brief for declared article-cluster IDs from the repository's existing asset-card corpus.
- Good for: Preparing a source-linked inventory of the members and declared status of a known article cluster.; Finding source and evidence fields already recorded in the repository's governed asset cards.
- Not for: Determining whether a cluster's claims are true.; Producing a finished or publication-approved article.; Looking up clusters or sources outside the checked-out repository snapshot.
- Use only if: The requested cluster ID exists in ignition/analysis/corpus-relation/article_cluster_candidates.json.; The governed Knowledge card corpus and source parser are available in the same checkout.
- Do not use when: The task requires live or freshly updated external sources.; The task asks for scientific adjudication, proof, or external evidence validation.; The cluster snapshot is stale for the user's requested time period.
- Inputs → outputs: article cluster ID → source-backed cluster member brief, source and output digest receipt
- Permissions: `READ_ONLY_RUN` / `READ_ONLY_REPOSITORY_SNAPSHOT` · explicit Owner authorization required `false` · reads `ignition/KNOWLEDGE/cards/, ignition/analysis/corpus-relation/article_cluster_candidates.json, ignition/tools/build_corpus_relation_graph.py` · writes `none` · network `false` hosts `none` · secrets `false` · billing `false` · external actions `false.
- Side effects: Writes only the JSON receipt to stdout; does not create or overwrite repository files..
- Dependencies: ignition/analysis/corpus-relation/article_cluster_candidates.json, ignition/KNOWLEDGE/cards/, ignition/tools/build_corpus_relation_graph.py, ignition/tools/extract_cluster_source_brief.py; runtime dependencies: Python >=3.9 standard library.
- Cost: `UNKNOWN` · No comparable timing, token, memory, or compute-cost profile has been established.
- Alternatives: `knowledge.read_foundation` (COMPLEMENTARY_NOT_EQUIVALENT): The registered operation provides source-bounded knowledge summaries but does not render this cluster-member brief contract..
- Invocation example: `python3 -B ignition/tools/toolbox_cluster_source_brief.py C000`
- Fallback: If the cluster ID or source data is unavailable, stop and report the missing reference; read the canonical asset cards manually without substituting an inferred cluster.
- Evidence: `REAL_TOOL_TEST` · source refs `ignition/tools/toolbox_cluster_source_brief.py` (READ_ONLY_TOOL_ENTRYPOINT), `ignition/tools/extract_cluster_source_brief.py` (BRIEF_RENDERER_AND_RECEIPT_BUILDER), `ignition/analysis/corpus-relation/article_cluster_candidates.json` (CLUSTER_SNAPSHOT), `ignition/tools/build_corpus_relation_graph.py` (CARD_PARSER), `ignition/KNOWLEDGE/cards/` (GOVERNED_ASSET_CARD_CORPUS); focused checks [ignition/tests/test_cluster_source_brief_tool.py](tests/test_cluster_source_brief_tool.py); negative controls: Unknown cluster ID returns nonzero and emits no partial brief.; --stdout creates or overwrites no repository file..
- Route default: `false` · conditions: Only include through an explicit experimental-tool allowlist for source-brief tasks.; Do not invoke after selection without the task's own user authorization and input..
- Claim ceiling: A formatted projection of repository-local cluster metadata and asset-card fields only; no truth, proof, external evidence, article quality, acceptance, or publication status is inferred.

### `research.validate_evidence_program_snapshot` · 科研证据计划快照校验器 / Evidence Program snapshot validator

- State: `EXPERIMENTAL_AVAILABLE` / `EXPERIMENTAL` · version `toolbox-wrapper-0.1.0; upstream Task103 Evidence Program validator` · license `BUSL-1.1` · maintainer `Ignition repository maintainers; this field does not grant Owner or scientific authority.` · source blob `b1abb127207333b53472b48be3fdc7d81b732f1c`.
- Can do: Run the existing standard-library Evidence Program validator against the fixed checked-out evidence-program tree and return a compact summary plus a source-tree digest.
- Good for: Check the fixed repository Evidence Program schemas, recorded preregistration-order metadata, source provenance fields, post-hoc threshold equality, and metric leakage constraints.; Get a compact check/failure count and SHA-256 digest for the entire fixed Evidence Program input tree.
- Not for: Running Crossref, OpenAlex, model, browser, search, or other network queries; the source-acquisition runner is a separate tool with different permissions.; Authenticating source origins, proving every file was committed as claimed, verifying scientific content, deciding truth, or recording independent/human acceptance.; Editing manifests, registrations, run records, thresholds, or the evidence-program tree.
- Use only if: The caller wants to validate the fixed `ignition/evidence-program/` snapshot in the currently checked-out Formal repository.; Python >=3.9 and the local Git CLI are available; Git is used only for repository-root discovery and preregistration ancestor checks.; The caller understands that the result validates recorded structure and consistency only, and that checkout-level Git metadata is read-only input.
- Do not use when: The task asks to fetch or refresh any evidence source; use a separately authorized acquisition workflow with network and output-path controls.; The task requires scientific adjudication, primary-source support review, authorship/authenticity proof, or epistemic acceptance.; The tool router must authorize an exact Git metadata read path; the current route planner cannot represent the containing checkout's `.git` metadata and will fail closed.
- Inputs → outputs: fixed checked-out ignition/evidence-program snapshot plus containing checkout Git metadata for read-only ancestry checks → compact validator status, check count, failure count, and bounded failure details, SHA-256 digest and file count for the complete checked-out Evidence Program tree, validator source SHA-256 and local Git root identity
- Permissions: `READ_ONLY_RUN` / `READ_ONLY_FIXED_TREE_AND_LOCAL_GIT_METADATA` · explicit Owner authorization required `false` · reads `ignition/evidence-program/, containing checkout Git metadata (read-only; `git rev-parse` and `git merge-base --is-ancestor` only)` · writes `none` · network `false` hosts `none` · secrets `false` · billing `false` · external actions `false.
- Side effects: Writes one compact JSON summary to stdout; no repository files are created or changed., Runs the validator and fixed-argument local Git read commands as child processes; never invokes a shell or a remote Git operation..
- Dependencies: ignition/evidence-program/tools/validate_evidence_program.py, ignition/evidence-program/; runtime dependencies: Python >=3.9 standard library and local Git CLI; no third-party runtime packages.
- Cost: `UNKNOWN` · The fixed tree has 31 files and 499 observed checks in the current run, but no calibrated latency or memory profile has been established.
- Alternatives: `ignition.evidence_program.validate_evidence_program.py` (EQUIVALENT_VALIDATION_DIFFERENT_INTERFACE): The upstream validator exposes a configurable root and a verbose per-check log; this wrapper fixes the repository root and summarizes the same validator run..
- Invocation example: `python3 -B ignition/tools/toolbox_validate_evidence_program.py --check`
- Fallback: Run the upstream validator directly with `--root ignition/evidence-program` when full per-check output is needed; if local Git ancestry cannot be read, report validation unavailable rather than inferring an ordering pass.
- Evidence: `REAL_TOOL_TEST` · source refs `ignition/tools/toolbox_validate_evidence_program.py` (FIXED_ROOT_READ_ONLY_SUMMARY_WRAPPER), `ignition/evidence-program/tools/validate_evidence_program.py` (EXISTING_SCHEMA_AND_CROSS_FILE_VALIDATOR), `ignition/evidence-program/` (FIXED_VALIDATION_INPUT_TREE); focused checks [ignition/tests/test_toolbox_validate_evidence_program.py](tests/test_toolbox_validate_evidence_program.py), [ignition/evidence-program/tests/test_evidence_program.py](evidence-program/tests/test_evidence_program.py); negative controls: A modified schema, missing provenance field, changed threshold, leaked metric, or failed recorded preregistration ordering remains a validator failure and returns a nonzero status.; The wrapper has no caller-controlled root, output path, network option, or mutation operation; invalid checkout identity fails closed.; The adaptive route planner must reject the candidate because the declared local Git metadata read is outside its ignition/ path authority..
- Route default: `false` · conditions: Direct CLI invocation only after an explicit task request; the current typed route planner is expected to reject the Git metadata path as unavailable or unsafe.; Do not remove the Git metadata dependency to make routing pass; preregistration ancestry is one of the validator's declared checks.; Never use the result as evidence of scientific truth, source authenticity, acceptance, or publication readiness..
- Claim ceiling: The fixed checked-out Evidence Program tree passed or failed this repository validator's schema and recorded-consistency checks, with local Git metadata read-only; no source authenticity, committed-file binding, scientific truth, independent review, acceptance, or publication is established.

### `research.verify_crossref_metadata` · Crossref 元数据核验器 / Crossref metadata verifier

- State: `EXPERIMENTAL_AVAILABLE` / `EXPERIMENTAL` · version `0.1.0` · license `Wrapper BUSL-1.1; Crossref bibliographic metadata reuse basis documented at https://www.crossref.org/documentation/retrieve-metadata/.` · maintainer `Ignition repository maintainers; Task 103 Crossref pilot supplies reused normalization helpers, not Owner or scientific authority.` · source blob `803e4666c00df462207d52db4495f9ca31cad0ac`.
- Can do: Compare up to ten caller-supplied DOI title/year expectations against live Crossref bibliographic metadata using bounded fixed-host HTTPS GET requests.
- Good for: Comparing caller-supplied expected DOI title and year with the live Crossref metadata record.; Retaining per-record HTTP outcome, response SHA-256, observed fields, and explicit mismatch or network-failure status.; Checking public bibliographic metadata for a bounded batch without retrieving article content.
- Not for: Retrieving article full text, abstracts, publisher pages, or arbitrary URLs.; Establishing that a paper is authentic, scientifically correct, or supports a claim.; Treating missing or stale Crossref fields as proof that a source does not exist.; Adding or correcting records in a repository registry.
- Use only if: The caller has explicitly approved transmission of the DOI identifiers in this invocation and passes --allow-public-network.; A route proposal may include this candidate only when allowed_network_hosts explicitly contains api.crossref.org; the proposal is not a permission grant.; The request contains one to ten unique bare DOI identifiers with caller-supplied expected title and year.; The public Crossref REST API is reachable from the declared environment.
- Do not use when: The DOI or associated task context is confidential or must not be sent to a public service.; Network access is unavailable, disallowed, or not explicitly approved for this invocation.; The task requires article-content review, source authenticity, current retraction adjudication, or scientific assessment.
- Inputs → outputs: UTF-8 JSON stdin object with one to ten unique DOI, expected-title, expected-year records → input-ordered Crossref metadata comparison rows, per-response SHA-256 and explicit HTTP or network outcome summary
- Permissions: `READ_ONLY_RUN` / `READ_ONLY_FIXED_HOST_NETWORK_QUERY` · explicit Owner authorization required `false` · reads `ignition/tools/toolbox_crossref_metadata_verifier.py, ignition/evidence-program/tools/run_crossref_verification.py` · writes `none` · network `true` hosts `api.crossref.org` · secrets `false` · billing `false` · external actions `false.
- Side effects: When explicitly invoked with --allow-public-network, sends at most ten HTTPS GET requests to api.crossref.org with DOI identifiers only; no user title, source_id, credential, or arbitrary URL is transmitted., Writes the JSON result to stdout and validation errors to stderr; does not create or modify repository files., Follows no redirects; uses a 5-second socket inactivity timeout, checks a 7-second response-body budget between and after 8 KiB reads, and caps responses at 256 KiB; records timeout, size, HTTP, and malformed-response failures explicitly..
- Dependencies: ignition/evidence-program/tools/run_crossref_verification.py; runtime dependencies: Python >=3.9 standard library, Task103 Crossref helper source in the same checkout.
- Cost: `UNKNOWN` · Crossref documents public REST access without signup. The wrapper permits at most ten serial requests, applies a 5-second socket timeout and a 7-second body-read budget with bounded chunks; no comparable latency, bandwidth, service-availability, or compute-cost profile has been measured.
- Alternatives: `research.validate_evidence_program_snapshot` (COMPLEMENTARY_NOT_EQUIVALENT): The local validator checks the Evidence Program structure and recorded provenance but does not retrieve current Crossref metadata..
- Invocation example: `python3 -B ignition/tools/toolbox_crossref_metadata_verifier.py --stdin --allow-public-network`
- Fallback: If live network use is not approved or fails, retain the explicit NOT_RUN or acquisition failure and use a pinned historical Crossref source manifest only as historical evidence; never label it a live re-check.
- Evidence: `REAL_TOOL_TEST` · source refs `ignition/tools/toolbox_crossref_metadata_verifier.py` (BOUNDED_FIXED_HOST_CLI), `ignition/evidence-program/tools/run_crossref_verification.py` (TASK103_METADATA_NORMALIZATION_HELPERS), `ignition/evidence-program/preregistration/IGNITION-EVIDENCE-PILOT-R1-CROSSREF-DOI-VERIFICATION.prereg.json` (FROZEN_METADATA_COMPARISON_PROTOCOL), `ignition/tests/test_toolbox_crossref_metadata_verifier.py` (FOCUSED_MOCKED_NETWORK_AND_NEGATIVE_CONTROLS); focused checks [ignition/tests/test_toolbox_crossref_metadata_verifier.py](tests/test_toolbox_crossref_metadata_verifier.py); negative controls: Missing --allow-public-network makes no request and emits no result.; Reject URLs, malformed or duplicate DOI rows, duplicate JSON keys, and batches above ten before network access.; Only api.crossref.org is contacted; redirects, non-JSON, oversized responses, 404, timeout, and malformed JSON are explicit outcomes.; No repository files are written and network failures are not silently dropped..
- Route default: `false` · conditions: Remain excluded unless the candidate ID is explicitly allowlisted and the typed route profile explicitly lists api.crossref.org in allowed_network_hosts.; A route proposal has execution_authorized=false and does not validate the caller authority behind that host list.; Every actual CLI invocation separately requires --allow-public-network and a task-specific decision to transmit the supplied DOI identifiers..
- Claim ceiling: Live Crossref bibliographic metadata retrieval and normalized title/year comparison only; response hashes bind received bytes, not source authenticity, article contents, scientific truth, or a complete retraction check.

### `runtime.inspect_declared_pack_catalog` · 声明式 Pack 能力目录检查器 / Declared Pack catalog inspector

- State: `EXPERIMENTAL_AVAILABLE` / `EXPERIMENTAL` · version `0.1.0` · license `BUSL-1.1` · maintainer `Ignition repository maintainers; this field does not grant Owner or scientific authority.` · source blob `20a8685606421cc537284c2526eb18c35e759818`.
- Can do: List or show versioned Pack manifest metadata and declared capability routes from the local checkout, with source hashes; it does not load Packs or execute hooks.
- Good for: Discovering which Pack IDs and versions are declared in the checked-out repository.; Inspecting the object types, declared permissions, lifecycle policy, and capability routes of one Pack.; Checking manifest source hashes before planning a Pack-aware task.
- Not for: Proving that a declared capability is executable or that its runtime dependencies are installed in another environment.; Loading or unloading a Pack, routing a domain action, or executing any action or planning hook.; Granting permission, Owner authority, truth, proof, or scientific acceptance.
- Use only if: The task needs local Pack metadata discovery or one manifest's declared capability routes.; The checked-out ignition/packs directory contains non-symlink manifest files and the local Agent Runtime source is available.; The caller accepts declaration-only output and does not treat route metadata as runtime execution evidence.
- Do not use when: The task requires executing a Pack hook, validating task data, or proving operational availability.; The task needs current information outside the local repository snapshot.; The requested Pack ID is missing or its manifest source is ambiguous.
- Inputs → outputs: Pack metadata list request, local Pack ID → declared Pack metadata, declared capability route list, manifest and source-tree SHA-256 references
- Permissions: `READ_ONLY_RUN` / `READ_ONLY_REPOSITORY_SNAPSHOT` · explicit Owner authorization required `false` · reads `ignition/packs/, ignition/agent_runtime/, ignition/agent_kernel/` · writes `none` · network `false` hosts `none` · secrets `false` · billing `false` · external actions `false.
- Side effects: Writes JSON only to stdout or error text to stderr; does not load, activate, or execute any Pack hook and creates no repository files..
- Dependencies: ignition/agent_runtime/, ignition/agent_kernel/, ignition/packs/; runtime dependencies: Python >=3.9 standard library.
- Cost: `UNKNOWN` · The command imports the local Agent Runtime package and hashes its source trees; no latency or memory benchmark has been established.
- Alternatives: `ignition.adaptive_toolbox_route_planner` (COMPLEMENTARY_NOT_EQUIVALENT): The route planner maps typed task requirements to registered operations; this tool inspects Pack manifest declarations and does not propose or execute a task route..
- Invocation example: `python3 -B ignition/tools/toolbox_pack_registry_inspector.py list | show <pack_id>`
- Fallback: Read ignition/TOOLBOX.md and the generated identity cards for the repository's static operation/candidate directory; if this inspector fails, report that local Pack metadata could not be read and do not infer that hooks ran.
- Evidence: `REAL_TASK_OUTCOME` · source refs `ignition/tools/toolbox_pack_registry_inspector.py` (FIXED_READ_ONLY_CATALOG_ENTRYPOINT), `ignition/agent_runtime/` (PACK_REGISTRY_AND_PACKAGE_RUNTIME_SOURCE_TREE), `ignition/agent_kernel/` (PACK_REGISTRY_KERNEL_CONTRACT_DEPENDENCY_TREE), `ignition/packs/` (FOUR_LOCAL_PACK_MANIFESTS); focused checks [ignition/tests/test_toolbox_pack_registry_inspector.py](tests/test_toolbox_pack_registry_inspector.py), [ignition/tests/test_pack_registry.py](tests/test_pack_registry.py); negative controls: List and show do not call PackLoader.load/unload or execute action/planning hooks.; Unknown Pack IDs return nonzero without a partial JSON result.; Symlinked Pack directories or manifests and path traversal are rejected..
- Route default: `false` · conditions: Include only through an explicit experimental-tool allowlist when local Pack capability discovery is a required task output.; The route proposal does not invoke this tool; the caller must separately authorize and provide the requested action and Pack ID.; Never select it to execute hooks or infer that declared routes are callable..
- Claim ceiling: Local Pack manifest declarations and versioned capability-route metadata only; no Pack module is loaded, no hook is executed, and no declared capability is proved callable in another environment.

### `visualization.build_archify_derived_ir` · 派生架构 IR 导出器 / Derived architecture IR exporter

- State: `EXPERIMENTAL_AVAILABLE` / `EXPERIMENTAL` · version `toolbox-wrapper-0.1.0; upstream adapter IGNITION-20260831-149 Step05` · license `BUSL-1.1` · maintainer `Ignition repository maintainers; this field does not grant Owner or scientific authority.` · source blob `9036e4ee41c91da8a3c6da074c5b850352ed608d`.
- Can do: Build the existing Task149 provider-neutral typed visualization IR from the checked-out canonical architecture source and include the current system-map snapshot digest as context; emit JSON without writing files or invoking a renderer.
- Good for: Produce the repository's deterministic typed component/connection/boundary IR as stdout JSON for a separately selected downstream consumer.; Inspect canonical architecture node and edge coverage together with the exact source-file digests and caller-supplied revision string.
- Not for: Rendering an image, invoking Archify, validating provider delivery, or claiming visual usefulness or visual review.; Changing canonical architecture files, repairing the separately deferred Task150 geometry delta, or publishing a derived artifact.; Establishing architecture truth, Current integration, provider admission, or resolution of the caller-supplied revision to the checked-out Git HEAD.
- Use only if: The canonical architecture, current system map, and Task149 adapter source are present in the checked-out Ignition repository and pass fixed-path safety checks.; The caller supplies an exact lowercase 40-character SHA string; the tool records that string but does not resolve or verify it against Git.; The request is at most 4 KiB and both fixed canonical JSON sources are at most 1 MiB.
- Do not use when: The user needs a rendered or visually reviewed system map, fresh provider evidence, or a Current provider integration.; The requested input requires arbitrary source paths or the caller needs the formal revision independently resolved.; The task requires the Task150 geometry repair or any aesthetic, architecture-truth, Owner, or scientific claim.
- Inputs → outputs: UTF-8 JSON stdin object containing exactly one formal_revision lowercase commit-SHA string → typed Archify-shaped derived visualization IR with component, connection, and boundary counts, SHA-256 refs for the wrapper, reused builder, canonical architecture source, and system-map context, provider-invoked false and caller-supplied revision-binding status
- Permissions: `READ_ONLY_RUN` / `READ_ONLY_FIXED_REPOSITORY_SOURCES` · explicit Owner authorization required `false` · reads `ignition/tools/toolbox_build_archify_derived_ir.py, ignition/tools/run_task149_archify_adapter.py, ignition/data/architecture/overall-architecture.json, ignition/data/architecture/interactive-system-map.json` · writes `none` · network `false` hosts `none` · secrets `false` · billing `false` · external actions `false.
- Side effects: Writes only the IR result to stdout; does not create or overwrite repository artifacts., The renderer/provider is not imported, contacted, or invoked..
- Dependencies: ignition/tools/run_task149_archify_adapter.py, ignition/data/architecture/overall-architecture.json, ignition/data/architecture/interactive-system-map.json; runtime dependencies: Python >=3.9 standard library; no third-party runtime packages.
- Cost: `UNKNOWN` · The projection is local and bounded by fixed source sizes, but no latency or memory benchmark has been established.
- Alternatives: `visualization.render_derived_system_view` (COMPLEMENTARY_NOT_EQUIVALENT): The registered bounded operation describes a derived view/provider status; this candidate emits typed IR only and never renders or invokes a provider..
- Invocation example: `python3 -B ignition/tools/toolbox_build_archify_derived_ir.py --stdin (stdin JSON: {"formal_revision":"<40 lowercase hex SHA>"})`
- Fallback: Use the existing Task149 writer only when an intentional repository artifact write is needed; for a rendered image, separately select and validate an admitted renderer. Do not treat the IR as a visual or canonical architecture result.
- Evidence: `REAL_TOOL_TEST` · source refs `ignition/tools/toolbox_build_archify_derived_ir.py` (READ_ONLY_STDOUT_TOOL_ENTRYPOINT), `ignition/tools/run_task149_archify_adapter.py` (REUSED_PROVIDER_NEUTRAL_IR_BUILDER), `ignition/data/architecture/overall-architecture.json` (CANONICAL_ARCHITECTURE_INPUT), `ignition/data/architecture/interactive-system-map.json` (CURRENT_SYSTEM_MAP_CONTEXT_DIGEST); focused checks [ignition/tests/test_toolbox_build_archify_derived_ir.py](tests/test_toolbox_build_archify_derived_ir.py), [ignition/tests/test_task150_step28_owner_adjudication_scope_split.py](tests/test_task150_step28_owner_adjudication_scope_split.py); negative controls: Moving refs, malformed SHAs, duplicate JSON keys, and requests over 4 KiB fail with no partial stdout.; The route never invokes Archify or selects the separately deferred Task150 geometry delta; output states provider_invoked=false.; The output binds four local source digests and explicitly marks formal_revision as caller-supplied and unresolved..
- Route default: `false` · conditions: Include only through an explicit experimental-tool allowlist when the task requires typed IR from the fixed canonical architecture source.; The route proposal never builds or renders the IR; a caller separately invokes the CLI and supplies the revision string.; Do not select for rendering, provider validation, Task150 geometry repair, architecture truth, or source revision resolution..
- Claim ceiling: A deterministic provider-neutral typed IR projection from the checked-out canonical architecture, with a source-hashed system-map context and an unresolved caller-supplied revision string; no external Archify validation/delivery, visual quality, architecture truth, Current integration, provider admission, or publication is inferred.
