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
| 4 真实文献试投影 | 088-external-source-atlas-v1.jsonl（**65 条全部 Crossref 验真**） | ✅ |
| 5 补丁候选蓝图 | 088-patch-blueprint.{md,jsonl}（14 补丁：8 新建+6 保持） | ✅ 蓝图，待授权注入 |
| 6 089–103 编排 | 088-orchestration-089-103.jsonl | ✅ 蓝图 |

## 阶段4 来源统计（Crossref 双向核验，零伪造）
- 总条数：65（GAP-001/002/003/004/005/006/008 各 8 条 + GAP-007 9 条）
- 角色：FOUNDATIONAL 23 / METHOD 14 / BENCHMARK 7 / CURRENT_REVIEW 16 / FAILURE 5
- 关键纠偏：Rubin 1974 真实 DOI=10.1037/h0037350（非记忆中的错误 DOI）；Angrist-Imbens-Rubin 1996 真实 DOI=10.2307/2291634；均经 Crossref 验证。

## 续跑入口（Resumable）
- 阶段4 若需补某 gap：重跑 /tmp/088work/crossref_search_all.py <GAP-XXX>
- 阶段5 注入 088 补丁库：需你授权（>2 验真源/补丁）后，按 088-patch-blueprint 注入，不得新增 Ψ₀ 编号。
- 阶段6 089–103：按 088-orchestration-089-103.jsonl 拓扑序推进。

## 已知限制
- 阶段4 部分条目为书评/综述的"review of"或近期预印本，peer_review_status 已标注；作为原始方法证据时强度较弱，注入补丁时应降权。
- 阶段5/6 为蓝图，尚未执行注入/对齐/基准/可视化等下游动作。
