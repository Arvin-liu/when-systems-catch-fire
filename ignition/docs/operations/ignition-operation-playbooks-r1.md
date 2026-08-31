# 点火 Operation-specific Playbooks R1

> Generated human view. Canonical authored playbook source: `ignition/data/operations/ignition-operation-playbooks-r1.json`; capability fields are projected from `ignition/data/operations/ignition-operation-capability-registry-r1.json`. The synchronized Task148 playbooks are Current on formal `main`; this repository-local lifecycle state does not assert external truth or production readiness.

## 选择规则

Only operations whose registry status is `CURRENT` or `CURRENT_BOUNDED` and whose AI callability is `PUBLIC` or `PUBLIC_BOUNDED` receive a callable playbook. Required inputs, outputs, status, mode, read set, authorities, validators and claim ceiling below are derived from the registry rather than copied as a second truth source.

## 类别覆盖审计

| Category | Coverage | Operation IDs | Boundary |
|---|---|---|---|
| `knowledge_navigation_retrieval` | `COVERED_BOUNDED` | `foundation.resolve_current_asset`, `knowledge.read_foundation` | Current identity resolution and Foundation reading are publicly callable but remain repository-local and claim-bounded. |
| `object_analysis_collision` | `COVERED_BOUNDED` | `knowledge.collide_object` | Task148 defines a read-only provenance-preserving collision operation with canonical function and non-function checks. |
| `source_evidence_research` | `PARTIAL_BOUNDED` | `knowledge.validate_evidence_link`, `research.coordinate_obligations` | Current operations validate evidence links and coordinate research obligations; no general direct-source retrieval or autonomous research operation is separately registered. |
| `function_claim_governance` | `COVERED_BOUNDED` | `foundation.resolve_current_asset`, `knowledge.validate_claim` | Identity resolution and claim-gate validation are Current bounded operations and preserve independent maturity and evidence axes. |
| `mechanism_model_mapping` | `PARTIAL_BOUNDED` | `knowledge.collide_object`, `knowledge.validate_claim` | Mechanisms and model mappings may be classified and governed inside collision and claim validation, but no dedicated general model-mapping operation exists. |
| `synthesis_open_question_generation` | `PARTIAL_BOUNDED` | `knowledge.collide_object`, `research.coordinate_obligations` | Collision can expose bounded gaps and questions and REOS LIGHT can coordinate them; no unconstrained synthesis or discovery operation is registered. |
| `writing_publication_transformation` | `COVERED_CURRENT` | `writing.apply_editorial_method`, `writing.validate_publication_surface` | The Current writing transformation and bounded publication-surface validator are both registered, while publication acceptance remains outside their authority. |
| `translation_language_thought` | `COVERED_BOUNDED` | `language_thought.project_bounded_meaning` | The Current language-thought plane supports bounded meaning projection with framing delta and unmapped residue. |
| `validation_audit` | `COVERED_BOUNDED` | `knowledge.validate_claim`, `knowledge.validate_evidence_link`, `maintenance.validate_checkpoint`, `research.validate_reos_light`, `writing.validate_publication_surface` | Five public bounded validators cover claim, evidence, repository checkpoint, REOS LIGHT and publication surfaces without substantive authority upgrades. |
| `repository_maintenance_self_iteration` | `COVERED_CURRENT` | `maintenance.inspect_repository`, `maintenance.validate_checkpoint`, `repository.apply_iteration_method` | Read-only maintenance is bounded and explicit Ignition self-change is Current only through the Iteration Method and its authorization gates. |
| `executor_orchestration` | `STATUS_ONLY_NOT_CALLABLE` | `executor.reference_conformance`, `external.live_invocation` | The Reference Executor is REFERENCE_ONLY and live external invocation is OWNER_DEFERRED, so neither receives a callable playbook. |

## 非可调用状态项

| Operation | Current status | Allowed output | Reason |
|---|---|---|---|
| `executor.reference_conformance` | `REFERENCE_ONLY` | `STATUS_AND_BOUNDARY_ONLY` | REFERENCE_ONLY is a conformance boundary, not a Current public executor. |
| `external.live_invocation` | `OWNER_DEFERRED` | `STATUS_AND_BOUNDARY_ONLY` | OWNER_DEFERRED with zero validated completions; explicit Owner reopening and Current admission remain absent. |
| `repository.apply_iteration_method_1_3` | `HISTORICAL` | `STATUS_AND_BOUNDARY_ONLY` | HISTORICAL and superseded by the Current Iteration Method 1.4.0. |
| `research.reos_full` | `UNSUPPORTED` | `STATUS_AND_BOUNDARY_ONLY` | UNSUPPORTED because no REOS FULL runtime exists. |

## 可调用 Playbooks

### `foundation.resolve_current_asset` — 解析 Current canonical 资产 / Resolve a Current canonical asset

- Registry status: `CURRENT_BOUNDED`
- Run mode: `READ_ONLY_RUN`
- Repository permission: `FORBIDDEN`
- External-action permission: `FORBIDDEN`

用户常见意图：

- 这个旧编号现在对应什么？
- 请确认这个函数、断言或 alias 的 Current identity。

输入（registry-derived）：

- `canonical id`
- `legacy id`
- `alias`
- `natural-language asset query`

最小 Current read set：

- Core lifecycle reads: `ignition/OPERATING-METHOD.md`, `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/data/operations/ignition-operation-capability-registry-r1.json`, `ignition/data/operations/ignition-run-output-contract-r1.json`
- Operation-specific required reads: `ignition/data/foundation/function-assets/closure-summary.json`, `ignition/data/foundation/function-assets/identity-cards.jsonl`, `ignition/data/foundation/nonfunction-claims/claim-registry.jsonl`, `ignition/data/governance/knowledge-experience/manifest.json`, `ignition/docs/foundation/migration.md`
- Expand with declared authority/governance/validator paths: `ignition/data/foundation/function-assets/identity-cards.jsonl`, `ignition/data/foundation/nonfunction-claims/claim-registry.jsonl`, `ignition/docs/foundation/migration.md`, `ignition/KNOWLEDGE/EVOLUTION.md`, `ignition/data/governance/knowledge-experience/manifest.json`, `ignition/docs/foundation/claim-governance-and-function-identity.md`, `ignition/docs/foundation/future-claim-admission-protocol.md`, `ignition/tools/foundation/validate_function_asset_closure.py`, `ignition/tools/foundation/validate_nonfunction_claim_closure.py`, `ignition/tools/governance/validate_knowledge_experience.py`

执行步骤：

- Freeze the exact reference and Current ref.
- Run exact Current identity, alias, correction and migration resolution.
- Return the canonical identity with disposition, record hash and claim ceiling, or fail closed.

必须检查的 authority：

- `ignition/data/foundation/function-assets/identity-cards.jsonl`
- `ignition/data/foundation/nonfunction-claims/claim-registry.jsonl`
- `ignition/docs/foundation/migration.md`
- `ignition/KNOWLEDGE/EVOLUTION.md`
- `ignition/data/governance/knowledge-experience/manifest.json`
- `ignition/docs/foundation/claim-governance-and-function-identity.md`
- `ignition/docs/foundation/future-claim-admission-protocol.md`

允许的最大输出：

- `canonical identity match`
- `migration relation`
- `unresolved reference status`
- Claim ceiling: Repository-local identity and migration resolution only; no proof, evidence upgrade or external truth.

Stop conditions：

- Current identity authority is unavailable or inconsistent.
- The reference is ambiguous or has no validated Current mapping.

不得做什么：

- Do not use fuzzy similarity, historical files or model memory as identity authority.
- Do not turn canonical registration into truth, proof or external validity.

### `ignition.recover_current_state` — 恢复点火 Current 状态 / Recover Ignition Current state

- Registry status: `CURRENT`
- Run mode: `READ_ONLY_RUN`
- Repository permission: `FORBIDDEN`
- External-action permission: `FORBIDDEN`

用户常见意图：

- 先恢复点火最新 Current 状态。
- 这个仓库当前是什么身份、任务和开放义务？

输入（registry-derived）：

- `Ignition repository URL`
- `repository checkout`
- `Current state query`

最小 Current read set：

- Core lifecycle reads: `ignition/OPERATING-METHOD.md`, `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/data/operations/ignition-operation-capability-registry-r1.json`, `ignition/data/operations/ignition-run-output-contract-r1.json`
- Operation-specific required reads: `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/data/operations/open-obligation-registry-r1.json`
- Expand with declared authority/governance/validator paths: `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/docs/project-current-state.md`, `ignition/STATE-CHANGELOG.md`, `ignition/tools/validate_current_state_sync.py`, `ignition/tools/validate_state_changelog.py`

执行步骤：

- Freeze the observable repository ref or commit.
- Read the AI cold-start entry, Current Facts, Current Snapshot and open obligations.
- Return identity, lifecycle, method, map and a bounded next-read plan.

必须检查的 authority：

- `ignition/AI-START-HERE.md`
- `ignition/data/architecture/current-facts.json`
- `ignition/data/operations/current-snapshot-r1.json`
- `ignition/docs/project-current-state.md`
- `ignition/STATE-CHANGELOG.md`

允许的最大输出：

- `Current identity snapshot`
- `minimum authority read plan`
- `open-obligation boundary`
- Claim ceiling: Deterministic repository-local Current recovery only; no external truth, permission or epistemic upgrade.

Stop conditions：

- The repository or exact Current ref cannot be read.
- Current authorities conflict and cannot be reconciled.

不得做什么：

- Do not replace Current with memory or an old task record.
- Do not execute a domain operation or infer external truth from Current recovery.

### `knowledge.collide_object` — 运行受约束对象碰撞 / Run a bounded object collision

- Registry status: `CURRENT_BOUNDED`
- Run mode: `READ_ONLY_RUN`
- Repository permission: `FORBIDDEN`
- External-action permission: `FORBIDDEN`

用户常见意图：

- 用点火跑一遍这篇笔记。
- 把这个案例或论证与点火 Current 资产碰撞。

输入（registry-derived）：

- `note`
- `article`
- `case`
- `argument`
- `source material`
- `structured collision run`

最小 Current read set：

- Core lifecycle reads: `ignition/OPERATING-METHOD.md`, `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/data/operations/ignition-operation-capability-registry-r1.json`, `ignition/data/operations/ignition-run-output-contract-r1.json`
- Operation-specific required reads: `ignition/OPERATING-METHOD.md`, `ignition/data/foundation/function-assets/identity-cards.jsonl`, `ignition/data/foundation/nonfunction-claims/claim-registry.jsonl`, `ignition/docs/foundation/claim-governance-and-function-identity.md`, `ignition/docs/foundation/future-claim-admission-protocol.md`
- Expand with declared authority/governance/validator paths: `ignition/OPERATING-METHOD.md`, `ignition/schemas/operations/ignition-object-collision-run-r1.schema.json`, `ignition/docs/foundation/claim-governance-and-function-identity.md`, `ignition/docs/foundation/future-claim-admission-protocol.md`, `ignition/tools/operations/evaluate_object_collision_run.py`, `ignition/tests/test_ignition_object_collision.py`

执行步骤：

- Freeze object provenance and split source facts, claims, interpretations, mechanisms and questions.
- Search and verify both Current function and non-function canonical registries.
- Classify actual relationships and separate source-derived content from post-collision increments.
- Apply the candidate-new, source-overlap and pseudo-quantification gates before rendering.

必须检查的 authority：

- `ignition/OPERATING-METHOD.md`
- `ignition/schemas/operations/ignition-object-collision-run-r1.schema.json`
- `ignition/docs/foundation/claim-governance-and-function-identity.md`
- `ignition/docs/foundation/future-claim-admission-protocol.md`

允许的最大输出：

- `provenance-preserving object decomposition`
- `verified canonical collision matches`
- `bounded relationship findings`
- `unregistered candidate-new records`
- Claim ceiling: Repository-local object decomposition and canonical collision relation only; no candidate registration, truth, evidence, proof, causality, novelty or epistemic acceptance.

Stop conditions：

- Object provenance or request-object boundary is unresolved.
- Required canonical registries are unavailable.
- A candidate lacks actual nearest-match evidence or source-overlap review.

不得做什么：

- Do not relabel an input-explicit viewpoint as an Ignition discovery.
- Do not invent undefined scores, auto-register candidates, mutate repositories or perform external actions.

### `knowledge.project_results` — 投影受约束知识结果 / Project bounded knowledge results

- Registry status: `CURRENT_BOUNDED`
- Run mode: `READ_ONLY_RUN`
- Repository permission: `FORBIDDEN`
- External-action permission: `FORBIDDEN`

用户常见意图：

- 把这个受约束结果投影到 Knowledge 视图。
- 检查这份 epistemic correction 能否形成知识结果投影。

输入（registry-derived）：

- `result_record`
- `epistemic_correction`

最小 Current read set：

- Core lifecycle reads: `ignition/OPERATING-METHOD.md`, `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/data/operations/ignition-operation-capability-registry-r1.json`, `ignition/data/operations/ignition-run-output-contract-r1.json`
- Operation-specific required reads: `ignition/packs/knowledge/manifest.json`, `ignition/data/governance/knowledge-experience/manifest.json`
- Expand with declared authority/governance/validator paths: `ignition/packs/knowledge/manifest.json`, `ignition/data/architecture/current-facts.json`, `ignition/docs/governance/knowledge-experience-layer.md`, `ignition/docs/foundation/claim-governance-and-function-identity.md`, `ignition/tools/validate_pack_registry.py`, `ignition/tools/governance/validate_knowledge_experience.py`

执行步骤：

- Verify the result record, provenance and existing epistemic status.
- Read the Knowledge Pack and Current Knowledge Experience manifest.
- Render only the bounded projection and its validation findings.

必须检查的 authority：

- `ignition/packs/knowledge/manifest.json`
- `ignition/data/architecture/current-facts.json`
- `ignition/docs/governance/knowledge-experience-layer.md`
- `ignition/docs/foundation/claim-governance-and-function-identity.md`

允许的最大输出：

- `bounded result projection`
- `projection validation report`
- Claim ceiling: Bounded repository result projection only; no truth, evidence or epistemic upgrade.

Stop conditions：

- The result has no source-bound status or provenance.
- Projection would increase claim, evidence, proof or acceptance status.

不得做什么：

- Do not treat Pack Bus routing as hook execution.
- Do not persist a repository change in READ_ONLY_RUN or upgrade epistemic state.

### `knowledge.read_foundation` — 读取 Foundation / Read Foundation

- Registry status: `CURRENT_BOUNDED`
- Run mode: `READ_ONLY_RUN`
- Repository permission: `FORBIDDEN`
- External-action permission: `FORBIDDEN`

用户常见意图：

- 点火 Foundation 里怎样定义这个对象？
- 请从 Current Foundation 找相关资产和来源。

输入（registry-derived）：

- `foundation_object`
- `function_asset`
- `nonfunction_assertion`
- `natural-language knowledge query`

最小 Current read set：

- Core lifecycle reads: `ignition/OPERATING-METHOD.md`, `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/data/operations/ignition-operation-capability-registry-r1.json`, `ignition/data/operations/ignition-run-output-contract-r1.json`
- Operation-specific required reads: `ignition/FOUNDATION.md`, `ignition/KNOWLEDGE/README.md`, `ignition/packs/knowledge/manifest.json`
- Expand with declared authority/governance/validator paths: `ignition/packs/knowledge/manifest.json`, `ignition/data/architecture/current-facts.json`, `ignition/docs/foundation/claim-governance-and-function-identity.md`, `ignition/docs/foundation/future-claim-admission-protocol.md`, `ignition/tools/validate_pack_registry.py`, `ignition/tools/foundation/validate_foundation.py`

执行步骤：

- Resolve the query to Current Foundation and Knowledge entrances.
- Read only the required canonical sources and preserve source paths.
- Return a source-bounded summary with unresolved or quarantined boundaries.

必须检查的 authority：

- `ignition/packs/knowledge/manifest.json`
- `ignition/data/architecture/current-facts.json`
- `ignition/docs/foundation/claim-governance-and-function-identity.md`
- `ignition/docs/foundation/future-claim-admission-protocol.md`

允许的最大输出：

- `source-bounded knowledge summary`
- `canonical source references`
- Claim ceiling: Repository-local Foundation reading only; no independent truth, proof or evidence upgrade.

Stop conditions：

- No Current canonical source can be identified.
- The query would require inventing an unregistered object or authority.

不得做什么：

- Do not treat navigation, summaries or registry closure as proof.
- Do not execute Pack hooks or silently promote quarantined assets.

### `knowledge.validate_claim` — 校验断言边界 / Validate claim boundaries

- Registry status: `CURRENT_BOUNDED`
- Run mode: `READ_ONLY_RUN`
- Repository permission: `FORBIDDEN`
- External-action permission: `FORBIDDEN`

用户常见意图：

- 核查这个断言最多能说到哪里。
- 检查这个函数或命题的定义、证据和 claim ceiling。

输入（registry-derived）：

- `claim`
- `function_asset`
- `nonfunction_assertion`
- `proof_obligation`

最小 Current read set：

- Core lifecycle reads: `ignition/OPERATING-METHOD.md`, `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/data/operations/ignition-operation-capability-registry-r1.json`, `ignition/data/operations/ignition-run-output-contract-r1.json`
- Operation-specific required reads: `ignition/docs/foundation/claim-governance-and-function-identity.md`, `ignition/docs/foundation/future-claim-admission-protocol.md`, `ignition/packs/knowledge/manifest.json`
- Expand with declared authority/governance/validator paths: `ignition/packs/knowledge/manifest.json`, `ignition/docs/foundation/claim-governance-and-function-identity.md`, `ignition/docs/foundation/future-claim-admission-protocol.md`, `ignition/tools/foundation/validate_claim_governance.py`, `ignition/tools/foundation/validate_nonfunction_claim_closure.py`

执行步骤：

- Freeze the minimal atomic claim and classify its claim layer.
- Resolve linked function and non-function identities and run applicable governance gates.
- Return PASS, FAIL, REQUIRES_HUMAN_REVIEW or NOT_APPLICABLE per gate and preserve the lowest ceiling.

必须检查的 authority：

- `ignition/packs/knowledge/manifest.json`
- `ignition/docs/foundation/claim-governance-and-function-identity.md`
- `ignition/docs/foundation/future-claim-admission-protocol.md`

允许的最大输出：

- `claim-governance findings`
- `required human review`
- `bounded adjudication status`
- Claim ceiling: Repository-local governance validation only; no truth, proof, evidence, causal or Owner-status upgrade.

Stop conditions：

- The claim cannot be isolated from the source object.
- Required definitions, identity or authority are unavailable; report the missing obligation instead.

不得做什么：

- Do not infer an unautomatable PASS.
- Do not merge mathematical maturity with external evidence or turn validation into truth.

### `knowledge.validate_evidence_link` — 校验证据链接 / Validate an evidence link

- Registry status: `CURRENT_BOUNDED`
- Run mode: `READ_ONLY_RUN`
- Repository permission: `FORBIDDEN`
- External-action permission: `FORBIDDEN`

用户常见意图：

- 这条来源真的支持这个具体断言吗？
- 检查 claim-to-source 的 provenance 和范围。

输入（registry-derived）：

- `evidence_link`
- `source record`
- `claim-to-source relation`

最小 Current read set：

- Core lifecycle reads: `ignition/OPERATING-METHOD.md`, `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/data/operations/ignition-operation-capability-registry-r1.json`, `ignition/data/operations/ignition-run-output-contract-r1.json`
- Operation-specific required reads: `ignition/packs/knowledge/manifest.json`, `ignition/docs/foundation/claim-governance-and-function-identity.md`
- Expand with declared authority/governance/validator paths: `ignition/packs/knowledge/manifest.json`, `ignition/docs/foundation/claim-governance-and-function-identity.md`, `ignition/docs/foundation/future-claim-admission-protocol.md`, `ignition/tools/validate_pack_registry.py`, `ignition/tools/validate_epistemic_governance_relationships.py`

执行步骤：

- Freeze the exact claim, source record and locator.
- Check provenance, exact support relation, scope and evidence class.
- Return a valid link, missing evidence or scope mismatch without substantive confirmation.

必须检查的 authority：

- `ignition/packs/knowledge/manifest.json`
- `ignition/docs/foundation/claim-governance-and-function-identity.md`
- `ignition/docs/foundation/future-claim-admission-protocol.md`

允许的最大输出：

- `provenance validation report`
- `missing-evidence finding`
- `scope mismatch`
- Claim ceiling: Evidence-link structure and provenance validation only; no substantive confirmation or epistemic acceptance.

Stop conditions：

- The source body or claim-specific locator is unavailable.
- The relation cannot distinguish source presence from exact support.

不得做什么：

- Do not treat a URL or citation as evidence for every nearby claim.
- Do not infer truth, replication or acceptance from link validity.

### `language_thought.project_bounded_meaning` — 语言—思维受约束投影 / Bounded Language-Thought projection

- Registry status: `CURRENT_BOUNDED`
- Run mode: `READ_ONLY_RUN`
- Repository permission: `FORBIDDEN`
- External-action permission: `FORBIDDEN`

用户常见意图：

- 把这段内容翻译并保留概念边界。
- 比较源语言与目标语言的 framing delta。

输入（registry-derived）：

- `source text`
- `proposition`
- `translation request`
- `target-language publication material`

最小 Current read set：

- Core lifecycle reads: `ignition/OPERATING-METHOD.md`, `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/data/operations/ignition-operation-capability-registry-r1.json`, `ignition/data/operations/ignition-run-output-contract-r1.json`
- Operation-specific required reads: `ignition/docs/architecture/language-thought-logic-plane.md`, `ignition/data/language-thought/manifest.json`, `ignition/docs/language-thought/README.md`
- Expand with declared authority/governance/validator paths: `ignition/docs/architecture/language-thought-logic-plane.md`, `ignition/data/language-thought/manifest.json`, `ignition/docs/foundation/claim-governance-and-function-identity.md`, `ignition/docs/publication/zhiyuan-writing-method.md`, `ignition/tools/language_thought/validate_language_thought.py`, `ignition/tests/test_language_thought_plane.py`

执行步骤：

- Freeze source text, source profile, target language and intended use.
- Normalize a bounded meaning candidate and project the target form.
- Return framing delta, unmapped residue and human-review needs.

必须检查的 authority：

- `ignition/docs/architecture/language-thought-logic-plane.md`
- `ignition/data/language-thought/manifest.json`
- `ignition/docs/foundation/claim-governance-and-function-identity.md`
- `ignition/docs/publication/zhiyuan-writing-method.md`

允许的最大输出：

- `normalized meaning candidate`
- `target form candidate`
- `framing delta`
- `unmapped residue`
- Claim ceiling: Bounded cross-language representation and audit only; no universal meaning, literary-quality or truth guarantee.

Stop conditions：

- Source or target language profiles are unavailable.
- Loss, ambiguity or context cannot be represented without human review.

不得做什么：

- Do not claim language-independent universal meaning or guaranteed literary quality.
- Do not erase unmapped residue or let translation raise truth status.

### `maintenance.inspect_repository` — 检查仓库 / Inspect a repository

- Registry status: `CURRENT_BOUNDED`
- Run mode: `READ_ONLY_RUN`
- Repository permission: `FORBIDDEN`
- External-action permission: `FORBIDDEN`

用户常见意图：

- 只读检查这个仓库的结构或状态。
- 给出离线 maintenance proposal，不要修改。

输入（registry-derived）：

- `repository_snapshot`
- `declared repository path`
- `offline maintenance query`

最小 Current read set：

- Core lifecycle reads: `ignition/OPERATING-METHOD.md`, `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/data/operations/ignition-operation-capability-registry-r1.json`, `ignition/data/operations/ignition-run-output-contract-r1.json`
- Operation-specific required reads: `ignition/packs/maintenance/manifest.json`, `ignition/agent_runtime/README.md`
- Expand with declared authority/governance/validator paths: `ignition/packs/maintenance/manifest.json`, `ignition/agent_runtime/README.md`, `ignition/ITERATION.md`, `ignition/docs/architecture/os-control-plane-r2.md`, `ignition/tools/validate_r2_offline_repository_maintenance.py`, `ignition/tools/validate_agent_runtime_boundary.py`

执行步骤：

- Bind the declared repository snapshot and inspection scope.
- Run only offline read-only checks allowed by the Maintenance Pack.
- Return findings and a non-executing maintenance proposal.

必须检查的 authority：

- `ignition/packs/maintenance/manifest.json`
- `ignition/agent_runtime/README.md`
- `ignition/ITERATION.md`
- `ignition/docs/architecture/os-control-plane-r2.md`

允许的最大输出：

- `read-only inspection report`
- `offline maintenance proposal`
- Claim ceiling: Offline read-only repository inspection only; no mutation, remote publication or production claim.

Stop conditions：

- The path is outside the declared scope or snapshot.
- The requested check requires network access, mutation or an unavailable authority.

不得做什么：

- Do not mutate local or remote repository state.
- Do not treat a proposal or Pack route as executed maintenance.

### `maintenance.validate_checkpoint` — 校验仓库 checkpoint / Validate a repository checkpoint

- Registry status: `CURRENT_BOUNDED`
- Run mode: `READ_ONLY_RUN`
- Repository permission: `FORBIDDEN`
- External-action permission: `FORBIDDEN`

用户常见意图：

- 校验这个 repository checkpoint。
- 确认这份离线回执是否与当前快照一致。

输入（registry-derived）：

- `checkpoint_receipt`
- `repository_snapshot`
- `offline validation request`

最小 Current read set：

- Core lifecycle reads: `ignition/OPERATING-METHOD.md`, `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/data/operations/ignition-operation-capability-registry-r1.json`, `ignition/data/operations/ignition-run-output-contract-r1.json`
- Operation-specific required reads: `ignition/packs/maintenance/manifest.json`, `ignition/agent_runtime/README.md`
- Expand with declared authority/governance/validator paths: `ignition/packs/maintenance/manifest.json`, `ignition/agent_runtime/README.md`, `ignition/ITERATION.md`, `ignition/docs/architecture/os-control-plane-r2.md`, `ignition/tools/validate_agent_runtime_boundary.py`, `ignition/tools/validate_state_changelog.py`

执行步骤：

- Bind checkpoint identity, repository snapshot and claimed evidence.
- Run declared boundary and state checks without publication.
- Return exact mismatches, bounded PASS evidence or fail-closed status.

必须检查的 authority：

- `ignition/packs/maintenance/manifest.json`
- `ignition/agent_runtime/README.md`
- `ignition/ITERATION.md`
- `ignition/docs/architecture/os-control-plane-r2.md`

允许的最大输出：

- `checkpoint validation report`
- `bounded failure finding`
- Claim ceiling: Repository-local checkpoint validation only; no publication, deployment, external completion or acceptance.

Stop conditions：

- Checkpoint identity or source snapshot cannot be bound.
- Validation requires remote mutation or missing evidence.

不得做什么：

- Do not publish, push or mutate remote Git.
- Do not equate checkpoint PASS with merged, Current, deployed, accepted or externally valid.

### `repository.apply_iteration_method` — 按点火迭代操作法修改点火 / Change Ignition through the Iteration Method

- Registry status: `CURRENT`
- Run mode: `REPOSITORY_CHANGE_RUN`
- Repository permission: `EXPLICIT_USER_OR_OWNER_AUTHORIZATION_AND_ITERATION_METHOD`
- External-action permission: `FORBIDDEN`

用户常见意图：

- 请修改点火并建立 Draft PR。
- 给点火增加、删除或调整一个正式能力。

输入（registry-derived）：

- `explicit Ignition repository change request`
- `declared change manifest`

最小 Current read set：

- Core lifecycle reads: `ignition/OPERATING-METHOD.md`, `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/data/operations/ignition-operation-capability-registry-r1.json`, `ignition/data/operations/ignition-run-output-contract-r1.json`
- Operation-specific required reads: `ignition/ITERATION.md`, `ignition/AI-START-HERE.md`, `ignition/data/operations/project-components.json`, `ignition/data/operations/change-propagation-topology.json`
- Expand with declared authority/governance/validator paths: `ignition/ITERATION.md`, `ignition/data/architecture/current-system-identity.json`, `ignition/docs/foundation/claim-governance-and-function-identity.md`, `ignition/docs/governance/life-community-value-charter.md`, `ignition/tests/test_change_propagation.py`, `ignition/tools/validate_current_state_sync.py`

执行步骤：

- Confirm explicit repository-mutation authorization and route into ITERATION.md.
- Recover remote truth, define the gap and claim ceiling, and compute propagation scope.
- Implement bounded candidate changes, validate, review and preserve Draft lifecycle receipts.

必须检查的 authority：

- `ignition/ITERATION.md`
- `ignition/data/architecture/current-system-identity.json`
- `ignition/docs/foundation/claim-governance-and-function-identity.md`
- `ignition/docs/governance/life-community-value-charter.md`

允许的最大输出：

- `candidate repository change`
- `validation evidence`
- `Draft lifecycle record`
- `merge/current receipt when separately authorized`
- Claim ceiling: Repository-state change discipline only; no truth, evidence, causal, Owner-acceptance or publication inference.

Stop conditions：

- The current request does not explicitly authorize changing Ignition.
- Remote truth, clean isolated workspace, propagation authority or required validation is unavailable.
- Ready, merge or close would require Owner authority not present in the request.

不得做什么：

- Do not infer mutation authority from a repository URL or input object.
- Do not modify protected main directly, force-push, auto-merge, mark Ready or claim Draft as Current.
- Do not infer external action or epistemic acceptance from repository change.

### `research.coordinate_obligations` — 协调受约束研究义务 / Coordinate bounded research obligations

- Registry status: `CURRENT_BOUNDED`
- Run mode: `READ_ONLY_RUN`
- Repository permission: `FORBIDDEN`
- External-action permission: `FORBIDDEN`

用户常见意图：

- 把这项研究拆成有依赖的证据义务。
- 用 REOS LIGHT 协调负结果、review 和 handoff。

输入（registry-derived）：

- `research_obligation`
- `evidence_request`
- `negative_result`

最小 Current read set：

- Core lifecycle reads: `ignition/OPERATING-METHOD.md`, `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/data/operations/ignition-operation-capability-registry-r1.json`, `ignition/data/operations/ignition-run-output-contract-r1.json`
- Operation-specific required reads: `ignition/docs/architecture/reos-vnext-light.md`, `ignition/packs/research/manifest.json`
- Expand with declared authority/governance/validator paths: `ignition/packs/research/manifest.json`, `ignition/docs/architecture/reos-vnext-light.md`, `ignition/docs/foundation/claim-governance-and-function-identity.md`, `ignition/docs/foundation/future-claim-admission-protocol.md`, `ignition/tools/validate_pack_registry.py`, `ignition/tests/test_reos_vnext_minimal_kernel.py`

执行步骤：

- Confirm that obligation coordination is needed beyond direct research.
- Build a bounded obligation DAG with references, statuses and stop conditions.
- Return case status and a typed handoff bundle while preserving negative results.

必须检查的 authority：

- `ignition/packs/research/manifest.json`
- `ignition/docs/architecture/reos-vnext-light.md`
- `ignition/docs/foundation/claim-governance-and-function-identity.md`
- `ignition/docs/foundation/future-claim-admission-protocol.md`

允许的最大输出：

- `bounded obligation DAG`
- `case status`
- `typed handoff bundle`
- Claim ceiling: Bounded research-process coordination only; no truth, publication, acceptance or external-validation inference.

Stop conditions：

- A direct bounded answer is sufficient and REOS control would add no value.
- Required obligation identity, references or handoff fields are missing.

不得做什么：

- Do not invent REOS FULL or a recovery layer.
- Do not treat process completion, Agent agreement or Pack routing as truth or publication acceptance.

### `research.validate_reos_light` — 校验 REOS LIGHT / Validate REOS LIGHT

- Registry status: `CURRENT_BOUNDED`
- Run mode: `READ_ONLY_RUN`
- Repository permission: `FORBIDDEN`
- External-action permission: `FORBIDDEN`

用户常见意图：

- 校验这次 REOS LIGHT run 的结构。
- 检查 research case state 和 typed handoff 是否闭合。

输入（registry-derived）：

- `reos_light_run`
- `research case state`
- `typed handoff bundle`

最小 Current read set：

- Core lifecycle reads: `ignition/OPERATING-METHOD.md`, `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/data/operations/ignition-operation-capability-registry-r1.json`, `ignition/data/operations/ignition-run-output-contract-r1.json`
- Operation-specific required reads: `ignition/docs/architecture/reos-vnext-light.md`, `ignition/packs/research/manifest.json`
- Expand with declared authority/governance/validator paths: `ignition/packs/research/manifest.json`, `ignition/docs/architecture/reos-vnext-light.md`, `ignition/docs/foundation/claim-governance-and-function-identity.md`, `ignition/docs/foundation/future-claim-admission-protocol.md`, `ignition/tests/test_reos_vnext_minimal_kernel.py`, `ignition/tools/validate_pack_registry.py`

执行步骤：

- Bind the REOS LIGHT run, case state and referenced obligations.
- Validate graph, states, review and typed handoff fields.
- Return structural PASS or a bounded failure state.

必须检查的 authority：

- `ignition/packs/research/manifest.json`
- `ignition/docs/architecture/reos-vnext-light.md`
- `ignition/docs/foundation/claim-governance-and-function-identity.md`
- `ignition/docs/foundation/future-claim-admission-protocol.md`

允许的最大输出：

- `REOS LIGHT validation report`
- `bounded failure state`
- Claim ceiling: REOS LIGHT structural validation only; no truth, external validity or publication status.

Stop conditions：

- The run or case identity is missing.
- References, obligation graph or handoff bundle cannot be resolved.

不得做什么：

- Do not convert generic SUCCESS into a valid research outcome.
- Do not infer proposition truth, external validity or publication status from structural validation.

### `writing.apply_editorial_method` — 应用之元写作法 / Apply the Zhiyuan Writing Method

- Registry status: `CURRENT`
- Run mode: `READ_ONLY_RUN`
- Repository permission: `FORBIDDEN`
- External-action permission: `FORBIDDEN`

用户常见意图：

- 把这些来源材料写成一篇受约束文章。
- 按之元写作法改写，但保留来源和点火增量边界。

输入（registry-derived）：

- `editorial_source`
- `external_input`
- `ignition_increment`
- `publication draft request`

最小 Current read set：

- Core lifecycle reads: `ignition/OPERATING-METHOD.md`, `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/data/operations/ignition-operation-capability-registry-r1.json`, `ignition/data/operations/ignition-run-output-contract-r1.json`
- Operation-specific required reads: `ignition/docs/publication/zhiyuan-writing-method.md`, `ignition/templates/publication/zhiyuan-writing-spec.md`, `ignition/docs/architecture/language-thought-logic-plane.md`
- Expand with declared authority/governance/validator paths: `ignition/packs/writing/manifest.json`, `ignition/docs/publication/zhiyuan-writing-method.md`, `ignition/docs/foundation/claim-governance-and-function-identity.md`, `ignition/docs/governance/life-community-value-charter.md`, `ignition/tools/publication/validate_fire_seeds.py`, `ignition/tools/governance/validate_human_surface_contract.py`

执行步骤：

- Separate editorial source, external input and Ignition increment with provenance.
- Apply the Current writing specification and language-thought boundary.
- Return a source-bounded draft, editorial provenance and unmapped residue.

必须检查的 authority：

- `ignition/packs/writing/manifest.json`
- `ignition/docs/publication/zhiyuan-writing-method.md`
- `ignition/docs/foundation/claim-governance-and-function-identity.md`
- `ignition/docs/governance/life-community-value-charter.md`

允许的最大输出：

- `source-bounded publication draft`
- `editorial provenance record`
- `language-thought residue`
- Claim ceiling: Current L6 writing transformation only; no factual, causal, proof, value, publication-acceptance or literary-quality guarantee.

Stop conditions：

- Source classes or provenance cannot be separated.
- Requested wording would exceed the lowest input claim ceiling or require external publication action.

不得做什么：

- Do not let writing quality raise fact, cause, proof, value or evidence status.
- Do not treat Ignition-derived text as an independent source or execute publication hooks.

### `writing.validate_publication_surface` — 校验出版表面 / Validate a publication surface

- Registry status: `CURRENT_BOUNDED`
- Run mode: `READ_ONLY_RUN`
- Repository permission: `FORBIDDEN`
- External-action permission: `FORBIDDEN`

用户常见意图：

- 检查这篇 draft 的 publication surface。
- 核查人类入口、provenance 和导航是否合规。

输入（registry-derived）：

- `publication_draft`
- `publication_review`
- `human_surface_entry`

最小 Current read set：

- Core lifecycle reads: `ignition/OPERATING-METHOD.md`, `ignition/AI-START-HERE.md`, `ignition/data/architecture/current-facts.json`, `ignition/data/operations/current-snapshot-r1.json`, `ignition/data/operations/ignition-operation-capability-registry-r1.json`, `ignition/data/operations/ignition-run-output-contract-r1.json`
- Operation-specific required reads: `ignition/packs/writing/manifest.json`, `ignition/docs/publication/zhiyuan-writing-method.md`
- Expand with declared authority/governance/validator paths: `ignition/packs/writing/manifest.json`, `ignition/docs/publication/zhiyuan-writing-method.md`, `ignition/docs/foundation/claim-governance-and-function-identity.md`, `ignition/docs/governance/life-community-value-charter.md`, `ignition/tools/governance/validate_human_surface_contract.py`, `ignition/tools/publication/validate_fire_seeds.py`

执行步骤：

- Bind the publication draft or human-surface entry and its provenance.
- Validate declared structure, navigation and surface-level claim boundaries.
- Return exact surface findings without substantive acceptance.

必须检查的 authority：

- `ignition/packs/writing/manifest.json`
- `ignition/docs/publication/zhiyuan-writing-method.md`
- `ignition/docs/foundation/claim-governance-and-function-identity.md`
- `ignition/docs/governance/life-community-value-charter.md`

允许的最大输出：

- `publication-surface validation report`
- `provenance or navigation finding`
- Claim ceiling: Publication-surface structure and provenance validation only; no substantive acceptance, truth or deployment inference.

Stop conditions：

- The draft, provenance or target surface cannot be identified.
- The request asks the validator to decide truth, quality, acceptance or deployment.

不得做什么：

- Do not infer content truth, literary quality or publication acceptance from surface validity.
- Do not publish, deploy or claim public visibility as capability availability.
