# 088 阶段5 补丁候选蓝图（基于 087 重算覆盖 + 088 架构指令）

> 本文件为蓝图，待阶段4真实文献落地并经你授权后，方可注入 088 正式补丁库。
> 红线：禁止凭空补函数/编号；补丁须来自外部真实文献；保持 Ψ₀ 最小必要结构。

| 缺口 | 标题 | 类型 | 重算覆盖(missing/partial) | 定位 | 证据门槛 |
|---|---|---|---|---|---|
| GAP-001 | 干预与控制 | NEW_OBJECT_TYPE | 250/0 | 引擎新增对象类型 intervention_control（含 interven… | ≥2 来源：1 CURRENT_REVIEW(因果推断)+1 METHOD(实验设计/工具变量)。 |
| GAP-002 | 层级尺度 | NEW_OBJECT_TYPE | 206/44 | 新增 level_scale 对象类型（micro/meso/macro 三层 … | ≥2：1 CURRENT_REVIEW(多尺度/涌现)+1 METHOD(重整化/粗粒化)。 |
| GAP-003 | 时间动态 | NEW_OBJECT_TYPE | 222/28 | 新增 temporal_dynamics 对象类型（state_trajecto… | ≥2：1 CURRENT_REVIEW(动力系统/临界转变)+1 METHOD(状态空间/早期预警)。 |
| GAP-004 | 随机不确定性 | NEW_OBJECT_TYPE | 209/41 | 新增 stochastic_uncertainty 对象类型（noise_mod… | ≥2：1 CURRENT_REVIEW(贝叶斯/稳健统计)+1 METHOD(不确定性量化)。 |
| GAP-005 | 优化权衡 | NEW_OBJECT_TYPE | 242/8 | 新增 optimization_tradeoff 对象类型（objectives… | ≥2：1 CURRENT_REVIEW(多目标优化)+1 METHOD(机制设计/鲁棒优化)。 |
| GAP-006 | 路径依赖与历史 | NEW_OBJECT_TYPE | 234/16 | 新增 path_dependence 对象类型（history、lock_in、… | ≥2：1 CURRENT_REVIEW(历史制度主义/演化经济)+1 METHOD(技术锁定/临界路径)。 |
| GAP-007 | 表示语言 | NEW_OBJECT_TYPE | 168/82 | 新增 representation_language 对象类型（formal_l… | ≥2：1 CURRENT_REVIEW(知识表示/类型论)+1 METHOD(范畴论/语义映射)。 |
| GAP-008 | 计算复杂度 | NEW_OBJECT_TYPE | 212/38 | 新增 computational_complexity 对象类型（complex… | ≥2：1 CURRENT_REVIEW(复杂度/近似算法)+1 FOUNDATIONAL(可计算性经典)。 |
| GAP-009 | 不完备性与不可判定 | ENHANCE_KEEP | 104/146 | 保持现有 G_δ 组件，新增‘开放系统边界的形式化限制’接口字段 open_sy… | ≥1 CURRENT_REVIEW(开放系统/形式化限制)。 |
| GAP-010 | 测量与可观测性 | ENHANCE_KEEP | 116/134 | 保持现有 evidence obligation interface，补 con… | ≥1 METHOD(心理测量/统计测量理论)。 |
| GAP-011 | 本体论 | ENHANCE_KEEP | 0/250 | 保持现有 ontology（partial），补领域本体工程接口 domain_… | ≥1 CURRENT_REVIEW(科学本体论/过程本体论)。 |
| GAP-012 | 因果识别 | ENHANCE_KEEP | 0/250 | 保持现有 causal_identification（partial），补 tr… | ≥1 METHOD(潜在结果/工具变量/自然实验)。 |
| GAP-013 | 证据制度 | ENHANCE_KEEP | 0/250 | 保持现有 evidence_regime（partial），补 reproduc… | ≥1 CURRENT_REVIEW(元研究/可重复性)。 |
| GAP-014 | 反例与失败 | ENHANCE_KEEP | 0/250 | 保持现有 counterexample_failure（partial），补 n… | ≥1 FAILURE_OR_LIMIT(失败模式/安全工程)。 |

## 分层策略

- **NEW_OBJECT_TYPE（8个 HIGH）**：GAP-001~008，对应 087 重算 missing 占多数（164~250），需开新对象类型承载外部理论来源族。
- **ENHANCE_KEEP（6个 MEDIUM）**：GAP-009~014，引擎内部已 partial 支持（087 partial 高），只增强接口字段，不动 Ψ₀ 最小必要结构。

## 与 088 红线的一致性

1. 不新增 Ψ₀ 函数编号；仅扩展对象类型/接口字段。
2. 每个 NEW_OBJECT_TYPE 的注入前须有 ≥2 条 stage4 验真来源支撑。
3. ENHANCE_KEEP 不修改现有判定结构，仅补字段。
4. 所有补丁 min_content 为最小语法，避免膨胀。