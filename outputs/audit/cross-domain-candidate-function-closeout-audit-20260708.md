# 跨域候选函数批次收口审计

时间：2026-07-08 16:38 (GMT+8)
仓库：when-systems-catch-fire（分支 main）
审计性质：轻量验收 + 批次收口（不新增函数、不新增案例、不修改 data/schema）

## 批次来源

- 跨域 smoke test：`outputs/collisions/20260708-cross-domain-smoke-test/`、`outputs/audit/cross-domain-smoke-test-audit-20260708.md`
- 候选函数复核：`outputs/audit/cross-domain-candidate-function-review-20260708.md`
- 小批量回填：`outputs/audit/cross-domain-candidate-function-small-batch-backfill-audit-20260708.md`

## NF-X1 收口

结论：**D597 扩展注释（不新增函数）**

验收确认：
- D597 文件含「## 扩展注释：指标排名隐性分层」；
- 含跨域 smoke test 来源（outputs/collisions/20260708-cross-domain-smoke-test/、候选复核报告）；
- 三领域复现证据已写入：社会学邻里积分制荣誉阶层 / 自然科学高通量 p 值续资助分层 / 历史学修志数字化积分职称层级；
- pending 更新为「教育材料 + 跨域 smoke test 三领域复现，仍需真实外部材料验证」，pending 降低但不取消，无过度泛化。

判定：NF-X1 已正确作为 D597 扩展注释处理，未误新增函数，未取消 pending 过度泛化。✅

## NF-X2 收口

结论：**新增 D599 刷分博弈（正式函数）**

验收确认：
- 文件存在：统一函数总表/0609-D599-刷分博弈.md；
- 标题：刷分博弈；机制表达式：G_score = B_metric × D_decomposable × R_reward × (1 - C_reality)；
- 核心结构齐全：评价绑定可量化指标 / 真实活动可拆分计分单元（D_decomposable 变量 + 正文明示）/ 奖励与指标强绑定 / 真实性约束不足 / 主体转向生产可计分碎片；
- 边界：与 D597（基底机制—策略响应机制）、与 D312（数学正反馈噪声放大 vs 社会行动者策略性拆分计分）均已写清；
- 三领域复现证据：社会学拍照打卡 / 自然科学重复变体 / 历史学拆分碑刻；
- pending：来自 smoke test 测试材料，三领域同构已现，仍需真实外部材料，不直接推出普遍社会规律。

判定：D599 已完成轻量验收，要素完整、边界清晰、可见性通过。✅

## NF-X3 收口

结论：**暂缓（不新增函数，继续 pending）**

验收确认：
- 未新增正式函数；
- 审计记录：NF-X3 指标驱动噪声累积，仅自然科学强出现，社会学/历史学证据不足，与 D312 不同构，跨域证据不足，继续 pending，待补更多领域后再判定。

判定：NF-X3 维持 pending，符合 G_δ 跨域不可收敛判定，未越界回填。✅

## 索引与可见性

确认：
- D599 在 INDEX 可见（INDEX.md 第 619 行）；
- D599 编号、标题、机制式可召回（grep 全局命中）；
- D597 扩展注释可召回（「指标排名隐性分层」「跨域 smoke test」均在 D597 文件命中）；
- 审计链条完整：smoke test → 候选复核 → 小批量回填 → 本收口审计，四份文件互相引用、NF-X1/X2/X3 在复核与回填审计中均可检索。

## 约束确认

- 未新增案例 ✅
- 未修改案例表 ✅
- 未修改 data ✅
- 未修改 schema ✅
- 未启动 UNESCO ✅
- 未启动得到笔记大规模任务 ✅
- 未处理其他候选 ✅（仅 NF-X1/X2/X3）
- 本轮未对 D597/D599/INDEX 做任何修正（上一轮回填产物验收通过，无需最小修正）。

## 下一步建议

跨域 smoke test 与跨域候选函数小批量回填已闭环。下一步不建议继续补函数或扩展基础设施，建议转入**得到笔记小批量真实材料测试**：

- 取 10 篇高价值笔记；
- 三步流程：Agent 初筛 → GPT 审核 → Agent 修改验收；
- 每周一次整体修正。

此举用真实外部材料验证 D597/D599 的跨行业普遍性 pending，避免停留在人工构造的 smoke test 小材料上。
