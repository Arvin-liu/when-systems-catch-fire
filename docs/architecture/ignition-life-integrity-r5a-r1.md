# 点火生命完整性架构 R5-A R1（Ignition Life Integrity R5-A R1）

> 候选叠加层，位于生命共同体价值宪章之下。`CANDIDATE_ONLY` / 未激活 / 未经外部接受。

## 1. 定位

R5-A 不是运行时、不是第二执行器、不是 L7。它是把“性命一体、身心互成”这一用户授权规范来源转写为**可机器测试的治理与架构合同**的候选叠加层。它复用 ARR 通用原语（Source / Observation / Object / State / Event / Assertion / Relation / Mechanism），不建立平行真值层。

## 2. 包结构（候选源码）

`life_integrity_r5a/`（仓库根级包，确定性、无运行时激活）：

- `registries.py` — 封闭集与失败关闭谓词（七视图、八 claim class、八概念状态、十类型标签、禁止升级、概念转移图）。
- `manifest.py` — 候选旗标清单（`CANDIDATE_ONLY` 等）。
- `embodied_view.py` — `EmbodiedAgent` 与七视图投影合同。
- `tradition_translation.py` — 传统/宗教材料翻译合同与 claim-class 注册表。
- `concept_mapping.py` — 概念映射生命周期状态机。
- `safety_envelope.py` — 实践/干预安全包络合同。
- `life_integrity.py` — 生命完整性门与局部优化披露合同。
- `non_impact.py` — 强制非影响证明（task §13）。
- `validators.py` — 聚合验证入口 `validate_all()`。

## 3. 具身主体模型（七视图）

```text
EmbodiedAgent (同一主体身份 + 同一 provenance boundary)
├── PhysiologicalView
├── PhenomenologicalView
├── CognitiveAffectiveView
├── BehavioralView
├── RelationalView
├── EnvironmentalView
└── MeaningView
```

强制属性：所有视图共享同一主体身份；每个视图有 observations / confidence / time_scope / UNKNOWN；跨视图关系类型化且不暗示因果；矛盾视图可共存且必须呈现；主体有不可归约为视图分数的自主/同意字段；表示从不声称穷尽此人。

## 4. 顶层不变量

1. 整体人非总体化（whole-person non-totalization）。
2. 局部优化门（local-optimization gate）。
3. 体验/机制/疗效分离（experience / mechanism / efficacy separation）。
4. 历史解释边界（historical interpretation boundary）。
5. 安全、同意与专业边界（safety, consent, professional boundary）。
6. 测试不是人体证据（tests are not human evidence）。

## 5. 确定性公开制品

由 `tools/generate_life_integrity_r5a.py` 生成到 `docs/architecture/ignition-r5a-life-integrity-r1/`，CI 校验字节级确定性（`git diff --exit-code`）。

## 6. 验证

`tests/adaptive_relational_runtime/test_life_integrity_r5a.py` 含 ≥120 个确定性接受/攻击检查，覆盖 task §12 全部要求。
