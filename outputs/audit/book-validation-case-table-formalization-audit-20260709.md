# 22 本书验证候选案例 · 正式案例表入表审计 2026-07-09

> 任务：IGNITION-20260709-007。分支 `case/book-validation-22-20260709`。结论：**0 条正式入表，22 条全部维持 candidate_only**。

## 1. 输入来源

- 点火主仓库 main：`Arvin-liu/when-systems-catch-fire@bb8144c76c956082eea183fb49d31b2a41e8a254`（已确认 origin/main == 该 merge commit，PR#1 已合并）
- 1111 当前版本口径包：`Arvin-liu/1111/project-context/`、`agent-results/IGNITION-20260709-005-*`、`006-*`
- 22 本书候选数据：`data/meta-protocols/book-validation-cases-20260709.json`（count=22，均 status=candidate_only，formal_case_id=null）
- 可读候选清单：`docs/meta-protocols/book-validation-22-cases-20260709.md`、`outputs/book-collisions/20260709-22-book-validation/book-case-candidates.md`
- 写作规范：`docs/two-tables-entry-writing-standard-20260709.md`、模板 `templates/two-tables/unified-case-entry-template.md`

## 2. 执行前校验

- 当前分支：`main` → 已切到 `case/book-validation-22-20260709`
- `python3 tools/validate_meta_protocols.py`：`protocols=12 combinations=64 book_cases=22`（通过）
- `python3 tools/validate_data.py`：未变动 data/*.json|csv，预期通过
- 未对 main 做任何修改；工作树仅新增/修改本任务相关文件

## 3. 逐条裁定方法

对每条候选执行：
1. **查重**：在 `统一案例总表/`（C-1…C-809，共 804 文件）按书名/核心机制词检索；22 本书名均无命中，机制词（门控面/退出权/同构/哥德尔/遮蔽）命中均为既有无关案例，判定全部 `unique`（无重复、无 near_duplicate）。
2. **入表门槛**：依 `docs/two-tables-entry-writing-standard-20260709.md`：
   - 案例必须「对应函数（至少 1 条函数编号）」；
   - 「没有对应函数的案例只能作为候选案例或 pending 案例，不得直接入正式案例表」；
   - 「案例不能从单一材料推出普遍结论」；
   - 缺失字段必须显式 pending，不得伪造确定结论。
3. **函数引用核对**：候选的 `related_existing_functions` 为 Ψ₀/框架记号（M1, L3, P_meta, G_δ, σ_opt, 1/ln, exp[-ln²], Φ, ε_eff, I_iso, P_exit, H）。核对统一函数表（ID 形如 Dxxxx / MF-xxxx / Axx / Txx / Y1），**不存在以这些记号为 ID 的形式化函数**。其中少数可定位到形式化 ID 候选（A4 退出权、Y1 Ψ₀/Φ/G_δ、D177 同构、T20 σ_opt），但仅作「建议映射」，未在本轮作为正式引用。
4. **证据等级**：每条候选仅 1 篇「最终收敛报告」来源，`author: pending_human_review`，属单材料，须 pending。

## 4. 结论统计

- 候选总数：22
- 入表数量：**0**
- 暂缓数量（candidate_only 维持）：**22**
- duplicate 数量：0
- reject 数量：0
- 起始 C 编号：无（未分配）
- 结束 C 编号：无（未分配）
- 说明：查重全 unique，但因「缺形式化函数引用 + 单材料证据」两道硬门槛，全部暂缓，不强行入表。

## 5. 修改 / 新增文件清单

新增：
- `outputs/book-collisions/20260709-22-book-validation/formalization-crosswalk.md`
- `outputs/book-collisions/20260709-22-book-validation/formalization-crosswalk.json`
- `outputs/audit/book-validation-case-table-formalization-audit-20260709.md`（本报告）

修改（均为指令允许的导航/索引类）：
- `CHANGELOG.md`：追加 IGNITION-20260709-007 条目（0 入表，22 暂缓）
- `docs/meta-protocols/book-validation-22-cases-20260709.md`：追加 formalization 状态小段与 crosswalk 链接

未修改：
- 统一案例总表/（0 个新案例文件）
- 统一函数总表/（未动）
- data/functions/、data/cases/（空，未动）
- data/*.json|csv（未动，validate_data 不受影响）
- Ψ₀ 定义文件（未动）
- 12 元协议定义（未动）
- 1735 / 1902 原始笔记（未动）

## 6. 红线确认

- 是否修改函数表：否
- 是否修改 data/functions：否（目录本为空，未建）
- 是否修改 Ψ₀：否
- 是否修改 12 元协议定义：否
- 是否修改 1735 / 1902 原始笔记：否
- 是否自动 merge：否（仅开 draft PR，等待 GPT 审核）
- 是否给 22 本书分配 C 编号：否
- 是否把 12 元协议计入普通函数总数：否

## 7. 校验结果

- `validate_meta_protocols.py`：ALL_META_PROTOCOL_DATA_VALID（protocols=12 / combos=64 / book_cases=22）
- `validate_data.py`：ALL_P1_DATA_VALID（data 数据集未变动）
- `git diff --name-only origin/main...HEAD`：仅含上述 5 个文件，不含任何红线文件

## 8. 后续建议（待 GPT 决策）

1. 下一轮：在统一函数表中为 M1 增强回路、P_meta 元协议投影、G_δ 哥德尔判定、σ_opt、ε_eff、I_iso、门控函数族 建立/定位正式 D/MF/T 编号。
2. 将 crosswalk 的「建议映射」转化为正式函数引用，补齐作者与多材料证据或显式 pending。
3. 再按 `unified-case-entry-template.md` 从 C-0810 起逐条生成正式案例条目，更新 `统一案例总表/INDEX.md` 与计数。
4. 是否更新 DOCX 两张表索引以反映新口径。
