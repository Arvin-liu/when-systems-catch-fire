# R5-A 架构决策记录（Adaptive Relational Runtime R5-A ADRs）

> 候选。记录 R5-A 在宪章层级、非重复、非影响方面的关键决策。控制提交 `d653c07e…`。

## ADR-R5A-1：生命完整性附则位于生命共同体价值宪章之下

- **背景**：用户授权把“性命一体、身心互成”转写为普遍生命完整性原则，但南宗修法、象征语言与宗教宇宙论只能作为历史候选协议与解释来源。
- **决策**：规范栈为 `Life Community Value Charter (最高) -> Life Integrity Annex Candidate -> Life Integrity Gate Candidate -> future domain/practice protocols`。R5-A 不新建竞争的最高宪章、L7、平行真值层或替代执行器。
- **后果**：既有的价值宪章权威与文本不被改动；R5-A 的任何制品都不得插入高于宪章的节点。

## ADR-R5A-2：复用 ARR 原语，不建立平行真值层

- **背景**：ARR 已有 Source / Observation / Object / State / Event / Assertion / Relation / Mechanism 等通用原语。
- **决策**：`EmbodiedAgent` 七视图复用 ARR 通用原语，作为同一主体的投影，而不是新事实层。
- **后果**：不增加第二执行器；不修改 ARR 运行时语义。

## ADR-R5A-3：七视图为封闭集，单一主体身份

- **决策**：`EMBODIED_VIEW_IDS` 恰好七类，且所有视图共享同一 `subject_identity` 与 provenance boundary。
- **后果**：任一视图不得声明 `WHOLE_PERSON_COMPLETE`；缺失视图保持 `UNKNOWN`，不得从另一视图推断。

## ADR-R5A-4：传统 claim-class 为封闭集且失败关闭

- **决策**：`TRADITION_CLAIM_CLASS_IDS` 恰好 8 类；5 个无声升级被显式禁止（`TRADITION_FORBIDDEN_TRANSITIONS`）。
- **后果**：体验≠机制、形而上学≠科学、后期解释≠作者意图、实践≠疗效、历史久远≠有效，均失败关闭。

## ADR-R5A-5：概念映射生命周期为封闭状态机

- **决策**：`CONCEPT_MAPPING_STATE_IDS` 恰好 8 态；`UNMAPPED`/`SYMBOLIC_DESCRIPTION` 不得直接跳到 `PARTIALLY_SUPPORTED`；`CONTRADICTED` 与 `UNKNOWN` 保留为一级结果。
- **后果**：无证据的中间跃迁被拒绝；矛盾与未知不被沉默。

## ADR-R5A-6：非影响优先于功能

- **决策**：R5-A 的所有新增仅为候选治理/架构叠加层；不激活、不干预、不医疗、不领域包、不联邦。
- **后果**：发布阶段核对实际 diff 与 `non_impact.build_non_impact_proof()` 清单一致。

## ADR-R5A-7：确定性公开制品可重生成

- **决策**：由 `tools/generate_life_integrity_r5a.py` 生成 JSON 制品，CI 校验 `git diff --exit-code`（字节级确定性）。
- **后果**：任何提交若使公开制品非确定性或不最新，CI 失败关闭。
