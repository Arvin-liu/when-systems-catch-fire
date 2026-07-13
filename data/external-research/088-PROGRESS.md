# 088 点火框架外部文献缺口与来源图谱 — 阶段进度

执行器：QClaw / qclaw/pool-glm-5.2 / max（GLM-5.2 池，非 Codex）
红线：禁伪造 DOI；每条来源须经 Crossref 双向核验；不得新增 Ψ₀ 函数编号；补丁须来自外部真实文献。

## 完成状态
| 阶段 | 产物 | 状态 |
|---|---|---|
| 0 计数审计 | 087 reconciliation / overlay 分母 143 纠错 | ✅ |
| 1 087 纠偏 | 集合一致 250/250，24 大类总和 250，14 缺口齐全 | ✅ |
| 2 250 学科路由 | 088-discipline-source-routing.jsonl | ✅ |
| 3 14 缺口图谱 | 088-gap-source-atlas.jsonl | ✅ |
| 4 真实文献试投影 | **088-external-source-atlas-v2.jsonl（74 条全部 Crossref 验真）** | ✅ |
| 5 补丁候选蓝图 | 088-patch-blueprint.{md,jsonl}（14 补丁：8 新建+6 保持） | ✅ 蓝图，待授权注入 |
| 6 089–103 编排 | 088-orchestration-089-103.jsonl | ✅ 蓝图 |

## 阶段4 来源统计（v2，Crossref 双向核验，零伪造）
- 总条数：74
  - GAP-001: 8（子代理验真）| GAP-002: 8（Crossref）| GAP-003: 12（子代理验真）
  - GAP-004: 8（Crossref）| GAP-005: 8（Crossref）| GAP-006: 13（子代理验真）
  - GAP-007: 9（子代理验真）| GAP-008: 8（Crossref）
- 角色：CURRENT_REVIEW 19 / FOUNDATIONAL 20 / METHOD 18 / FAILURE 7 / BENCHMARK 10
- 关键纠偏：Rubin 1974 真实 DOI=10.1037/h0037350；Angrist-Imbens-Rubin 1996=10.2307/2291634；Pearl 2009 Causality=10.1017/cbo9780511803161；均经 Crossref 二次核验。
- 子代理产出经主线程独立二次核验（非轻信声称），全部真实通过。

## 续跑入口（Resumable）
- 阶段4 补某 gap：子代理已验真者直接采用；否则重跑 /tmp/088work/crossref_search_all.py <GAP-XXX>
- 阶段5 注入 088 补丁库：需你授权（>2 验真源/补丁）后，按 088-patch-blueprint 注入，不得新增 Ψ₀ 编号。
- 阶段6 089–103：按 088-orchestration-089-103.jsonl 拓扑序推进。

## 已知限制
- 阶段5/6 为蓝图，尚未执行注入/对齐/基准/可视化等下游动作。
- 注入补丁须保持 Ψ₀ 最小必要结构，不新增函数编号（点火红线）。
