# 22 本书验证候选案例 · 正式案例表入表 crosswalk

> 任务：IGNITION-20260709-007（基于 `Arvin-liu/1111/agent-commands/IGNITION-20260709-007-book-cases-case-table-review.md`）。
> 分支：`case/book-validation-22-20260709`（从 main `bb8144c76c956082eea183fb49d31b2a41e8a254` 切出）。
> 结论：**0 条正式入表；22 条全部维持 candidate_only；未分配任何 C 编号。** 详见 `formalization-audit-20260709.md`。

## 为什么 0 条入表（摘要，详情见审计）

1. **缺少形式化函数引用**：`docs/two-tables-entry-writing-standard-20260709.md` 强制要求正式案例条目必须有「对应函数（至少 1 条函数编号）」，且「没有对应函数的案例只能作为候选案例或 pending 案例，不得直接入正式案例表」。22 个候选的 `related_existing_functions` 均为 Ψ₀ / 框架记号（M1、L3、P_meta、G_δ、σ_opt、1/ln、Φ、ε_eff、I_iso、P_exit、H），**不是统一函数表的正式 ID**（正式 ID 形如 D353 / MF-0001 / A4 / T20 / Y1）。统一函数表中不存在以这些记号为 ID 的形式化函数。
2. **单一材料证据**：每条候选均只有 1 篇「最终收敛报告」来源，且 `author: pending_human_review`。标准禁止「从单一材料推出普遍结论」，并要求缺失项显式 pending。
3. **查重结果**：22 本书名与现有 804 条案例（C-1…C-809）无任何重复；但「unique」不足以触发入表，因为上述 1、2 两条硬门槛未过。

## 每条候选裁定

| BC ID | 书名 | 相关元协议 | 候选相关函数（记号） | 建议映射（proposed，非形式化） | 裁定 | 原因 |
|---|---|---|---|---|---|---|
| BC-20260709-001 | 《系统之美》 | pending | M1 | 增强回路机制（暂无对应 D 编号，待定位） | candidate_only | 无形式化函数 ID；单材料 |
| BC-20260709-002 | 《第五项修炼》 | S3 | L3/ε_eff | ε_eff 认同强度（暂无对应 D 编号，待定位） | candidate_only | 无形式化函数 ID；单材料 |
| BC-20260709-003 | 《枪炮、病菌与钢铁》 | V1 | P_meta | Y1（Ψ₀）/ P_meta 待形式化 D 编号 | candidate_only | 无形式化函数 ID；单材料 |
| BC-20260709-004 | 《国家为什么会失败》 | pending | P_exit | A4 R_perceived 应约者感知退出权（0005-A4） | candidate_only | 有候选 ID（A4）但仍缺形式化映射确认 + 单材料 |
| BC-20260709-005 | 《创新者的窘境》 | V3 | 1/ln | 门控函数（暂无对应 D 编号，待定位） | candidate_only | 无形式化函数 ID；单材料 |
| BC-20260709-006 | 《黑天鹅》 | pending | G_δ | Y1（Ψ₀）/ G_δ 待形式化 D 编号 | candidate_only | 无形式化函数 ID；单材料 |
| BC-20260709-007 | 《反脆弱》 | pending | M1 | 增强回路机制（暂无对应 D 编号，待定位） | candidate_only | 无形式化函数 ID；单材料 |
| BC-20260709-008 | 《思考，快与慢》 | pending | 1/ln/exp[-ln²] | 门控函数（暂无对应 D 编号，待定位） | candidate_only | 无形式化函数 ID；单材料 |
| BC-20260709-009 | 《影响力》 | pending | P_meta | Y1（Ψ₀）/ P_meta 待形式化 D 编号 | candidate_only | 无形式化函数 ID；单材料 |
| BC-20260709-010 | 《人类简史》 | pending | -（无） | 待定位 | candidate_only | 完全无函数引用；单材料 |
| BC-20260709-011 | 《未来简史》 | pending | Φ | Y1（Φ元统一律） | candidate_only | 有候选 ID（Y1）但仍缺形式化映射确认 + 单材料 |
| BC-20260709-012 | 《文明的冲突》 | S1 | -（无） | 待定位 | candidate_only | 完全无函数引用；单材料 |
| BC-20260709-013 | 《乌合之众》 | pending | H/ε_eff | H 遮蔽函数族（待定位具体 D 编号） | candidate_only | 无精确形式化函数 ID；单材料 |
| BC-20260709-014 | 《娱乐至死》 | pending | ε_eff | ε_eff 认同强度（暂无对应 D 编号，待定位） | candidate_only | 无形式化函数 ID；单材料 |
| BC-20260709-015 | 《技术与文明》 | pending | -（无） | 待定位 | candidate_only | 完全无函数引用；单材料 |
| BC-20260709-016 | 《复杂》 | pending | I_iso | D177 深层同构函数（0214-D177） | candidate_only | 有候选 ID（D177）但仍缺形式化映射确认 + 单材料 |
| BC-20260709-017 | 《有限与无限的游戏》 | V1/V3 | -（无） | 待定位 | candidate_only | 完全无函数引用；单材料 |
| BC-20260709-018 | 《贫穷的本质》 | pending | M1 | 增强回路机制（暂无对应 D 编号，待定位） | candidate_only | 无形式化函数 ID；单材料 |
| BC-20260709-019 | 《规模》 | E4 | σ_opt | T20 σ_opt=√e 解析解（0030-T20） | candidate_only | 有候选 ID（T20）但仍缺形式化映射确认 + 单材料 |
| BC-20260709-020 | 《大图景》 | pending | G_δ | Y1（Ψ₀）/ G_δ 待形式化 D 编号 | candidate_only | 无形式化函数 ID；单材料 |
| BC-20260709-021 | 《原则》 | pending | P_meta | Y1（Ψ₀）/ P_meta 待形式化 D 编号 | candidate_only | 无形式化函数 ID；单材料 |
| BC-20260709-022 | 《混沌》 | E1/E2 | -（无） | 待定位（非线性演化协议，暂无对应 D 编号） | candidate_only | 完全无函数引用；单材料 |

## 统计

- 候选总数：22
- 入表数量：0
- 暂缓数量：22（全部 candidate_only）
- duplicate 数量：0
- reject 数量：0
- 起始 C 编号：无（未分配）
- 结束 C 编号：无（未分配）
- 建议映射中已出现可定位的正式 ID 候选：A4（BC-004）、Y1（BC-003/006/009/011/020/021）、D177（BC-016）、T20（BC-019）

## 进入下一轮（12 元协议 / 函数表映射）后的预期动作

1. 在统一函数表中为 M1 增强回路、P_meta 元协议投影、G_δ 哥德尔判定、σ_opt、ε_eff、I_iso、门控函数族 等建立/定位正式 D/MF/T 编号；
2. 将每条候选的「建议映射」转化为正式函数引用；
3. 补齐作者、多材料证据或显式 pending；
4. 再按 `unified-case-entry-template.md` 逐条生成 C-0810 起编号的正式案例条目；
5. 更新 `统一案例总表/INDEX.md` 与计数。
