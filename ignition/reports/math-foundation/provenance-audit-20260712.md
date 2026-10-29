# Provenance Audit

> 076 correction notice: the 075 labels below are raw-row heuristics, not verified provenance facts. DIRECT_SOURCE_FOUND meant that an absolute-path string appeared, without existence or hash verification; MULTIPLE_CONFLICTING_SOURCES could be triggered by the conceptual word “冲突”; PEND representations were duplicated across Markdown and JSON. The counts remain only as audit history. See reports/foundation-architecture/075-truth-audit-20260712.md.

## Summary

- DIRECT_SOURCE_FOUND: 596
- GENERATED_WITHOUT_TRACEABLE_SOURCE: 2
- INDIRECT_SOURCE_ONLY: 9
- MULTIPLE_CONFLICTING_SOURCES: 14
- SOURCE_NOT_FOUND: 93

## Interpretation

- `DIRECT_SOURCE_FOUND`: 当前文本中能定位到原始笔记路径或明确原文来源。
- `INDIRECT_SOURCE_ONLY`: 仅能定位到治理文档、报告或来源描述，未恢复直接原始材料。
- `MULTIPLE_CONFLICTING_SOURCES`: 同一对象出现多来源冲突信号，需要人工比对。
- `SOURCE_NOT_FOUND`: 当前仓库与可见本地目录中未恢复到来源痕迹。
- `GENERATED_WITHOUT_TRACEABLE_SOURCE`: 看起来是生成/救援重写结果，但没有可追溯原始来源。

## Selected Gaps

- `BC-20260709-001` 《系统之美》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-002` 《第五项修炼》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-003` 《枪炮、病菌与钢铁》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-004` 《国家为什么会失败》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-005` 《创新者的窘境》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-006` 《黑天鹅》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-007` 《反脆弱》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-008` 《思考，快与慢》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-009` 《影响力》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-010` 《人类简史》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-011` 《未来简史》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-012` 《文明的冲突》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-013` 《乌合之众》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-014` 《娱乐至死》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-015` 《技术与文明》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-016` 《复杂》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-017` 《有限与无限的游戏》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-018` 《贫穷的本质》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-019` 《规模》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-020` 《大图景》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-021` 《原则》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `BC-20260709-022` 《混沌》: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `D126` 认知-收益滞后函数: MULTIPLE_CONFLICTING_SOURCES; missing=direct local note path or raw source artifact missing
- `D128` 退相干-退化统一函数: MULTIPLE_CONFLICTING_SOURCES; missing=direct local note path or raw source artifact missing
- `D129` 退相干-退化等价函数: MULTIPLE_CONFLICTING_SOURCES; missing=direct local note path or raw source artifact missing
- `D225` 引力B型必要性定理: MULTIPLE_CONFLICTING_SOURCES; missing=direct local note path or raw source artifact missing
- `D228` T33修正: MULTIPLE_CONFLICTING_SOURCES; missing=direct local note path or raw source artifact missing
- `D583` 认知肌肉锻炼: INDIRECT_SOURCE_ONLY; missing=direct local note path or raw source artifact missing
- `D595` 0605-D595-绩效绑定裹挟: INDIRECT_SOURCE_ONLY; missing=direct local note path or raw source artifact missing
- `D596` 0606-D596-避风港: INDIRECT_SOURCE_ONLY; missing=direct local note path or raw source artifact missing
- `D597` 0607-D597-量化指标替代真实价值: INDIRECT_SOURCE_ONLY; missing=direct local note path or raw source artifact missing
- `D598` 0608-D598-系统性钝化: INDIRECT_SOURCE_ONLY; missing=direct local note path or raw source artifact missing
- `D599` 0609-D599-刷分博弈: INDIRECT_SOURCE_ONLY; missing=direct local note path or raw source artifact missing
- `D600` 资源托举退化为路径控制: INDIRECT_SOURCE_ONLY; missing=direct local note path or raw source artifact missing
- `D601` 角色覆盖主体身份: MULTIPLE_CONFLICTING_SOURCES; missing=direct local note path or raw source artifact missing
- `D602` 价值创造权与决策权错配与回收: INDIRECT_SOURCE_ONLY; missing=direct local note path or raw source artifact missing
- `D603` 计划过期识别与主动刹车: INDIRECT_SOURCE_ONLY; missing=direct local note path or raw source artifact missing
- `D604` 模糊需求显性化与协作排序: MULTIPLE_CONFLICTING_SOURCES; missing=direct local note path or raw source artifact missing
- `MF-0001` 正向自举通道: SOURCE_NOT_FOUND; missing=direct local note path or raw source artifact missing
- `MF-0002` 反向自举通道: SOURCE_NOT_FOUND; missing=direct local note path or raw source artifact missing
- `MF-0003` 正反互斥判定器: MULTIPLE_CONFLICTING_SOURCES; missing=direct local note path or raw source artifact missing
- `MF-0004` 自举嵌套判定器: SOURCE_NOT_FOUND; missing=direct local note path or raw source artifact missing
- `MF-0005` 自举收敛判定器: MULTIPLE_CONFLICTING_SOURCES; missing=direct local note path or raw source artifact missing
- `T10` 缓存倒U型 / cache inverted-U curve: MULTIPLE_CONFLICTING_SOURCES; missing=direct local note path or raw source artifact missing
- `T13` 三效率冲突三角约束 / three-efficiency conflict triangle constraint: MULTIPLE_CONFLICTING_SOURCES; missing=direct local note path or raw source artifact missing
- `T33` A-B型门控面冲突函数 / A-B type gate-surface conflict function: MULTIPLE_CONFLICTING_SOURCES; missing=direct local note path or raw source artifact missing
- `T44` 元层面收敛与子系统展开冲突函数: MULTIPLE_CONFLICTING_SOURCES; missing=direct local note path or raw source artifact missing
- `0001-Ψ₀元函数完整数学定义` Φ元统一律内部构件完整构成版 2026年07月06日12时32分: GENERATED_WITHOUT_TRACEABLE_SOURCE; missing=direct local note path or raw source artifact missing
- `0001-Ψ₀元统一律完整定义` 2026年7月4日23:41 Ψ₀元函数完整数学定义（2026.07.04·修订版）: GENERATED_WITHOUT_TRACEABLE_SOURCE; missing=direct local note path or raw source artifact missing
- `INDEX` INDEX: MULTIPLE_CONFLICTING_SOURCES; missing=direct local note path or raw source artifact missing
- `PEND-001` 数学: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `PEND-002` 数学: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `PEND-003` 数学: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `PEND-004` 物理学: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `PEND-005` 物理学: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `PEND-006` 物理学: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `PEND-007` 物理学: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `PEND-008` 历史学: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `PEND-009` 历史学: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
- `PEND-010` 历史学: SOURCE_NOT_FOUND; missing=direct source artifact unresolved
