# 两张表条目模板固化审计

## 输入

引用审计报告：
- `outputs/audit/two-tables-entry-format-audit-20260709.md`（提交 66f67d1d，2026-07-09）

该报告已完成单条条目结构对比（旧函数 9 条 + D595-D599 + Ψ₀；旧案例 4 条 + C-0807-C-0809），提出统一函数 14 字段草案、统一案例 13 字段草案、得到大脑/ Agent-Codex 分工与迁移建议。

本审计记录将该草案**固化为正式规范与模板文件**的过程。

---

## 新增文件

1. `docs/two-tables-entry-writing-standard-20260709.md`
   - 两张表条目写作标准（正式规范）：目的、适用对象、基本原则（8 条）、函数条目 15 字段标准（含重点约束）、案例条目 14 字段标准（含重点约束）、得到大脑输出要求、Agent/Codex 整理要求（9 步 + 禁止事项）、迁移策略。

2. `templates/two-tables/unified-function-entry-template.md`
   - 函数条目模板（占位符版）：含 frontmatter(kind/seq/id/title/source/link) + 编号/一句话定义/机制表达/变量解释/因果链/适用条件/边界条件/反例/与已有函数关系/对应案例/来源回指/pending/扩展注释/版本记录。

3. `templates/two-tables/unified-case-entry-template.md`
   - 案例条目模板（占位符版）：含 frontmatter(kind=case/seq/id/title/source/link) + 编号/一句话概括/现实场景/核心冲突/因果链/对应函数/证据来源/边界条件/为什么不是已有案例/反例/pending/扩展注释/版本记录。

4. `templates/two-tables/getbrain-candidate-output-template.md`
   - 得到大脑候选输出模板：函数候选 13 字段 + 案例候选 12 字段；明确不负责编号/入表/Git，缺字段标"缺失"/"pending"。

---

## 决策

- **模板正式固化**：自本审计提交起，两份模板（`unified-function-entry-template.md` / `unified-case-entry-template.md`）与写作标准（`two-tables-entry-writing-standard-20260709.md`）作为两张表写入的强制依据。
- **生效时间**：从 2026-07-09 起，新条目（函数/案例/扩展注释/pending）必须使用模板，先经模板整理再入正式两张表。
- **旧条目暂不迁移**：旧条目（约 600+ 函数、800- 案例）结构已收敛、信息完整，不做一次性全表格式迁移；仅在每周维护或被再次引用时逐步补齐缺失字段（边界条件/适用条件/反例/对应案例/版本记录）。
- **D595-D599 与 C-0807-C-0809 后续处理**：这 5 个函数、3 个案例暂不立即迁移到新模板结构；后续如需格式修订，单独开任务处理，不在此次范围内。
- **得到大脑职责边界**：只输出候选（按模板），不负责编号、不负责最终入表判定、不负责 Git。
- **Agent/Codex 职责边界**：入表前必须查重、跑 Ψ₀ 六维判定、做边界比较、套模板、补齐来源、标 pending、更新 INDEX、生成审计、提交 Git；不得直接塞候选原文、不得编造证据、不得在边界不清时强行新增。

---

## 红线确认

- [x] 未修改统一函数总表任何条目
- [x] 未修改统一案例总表任何条目
- [x] 未修改 README
- [x] 未修改 INDEX
- [x] 未修改 data
- [x] 未修改 schema
- [x] 未新增函数（仅新增规范/模板文件）
- [x] 未新增案例（仅新增规范/模板文件）
- [x] 未回填
- [x] 未做格式迁移

---

## 验证（第六部分）

```
python3 tools/validate_data.py
→ OK function_dependency: json=13 csv=13
→ OK cross-references and dataset-specific checks
→ ALL_P1_DATA_VALID

git diff --stat
→ （仅新增文件，无已跟踪文件改动）

git status --short
→ ?? docs/two-tables-entry-writing-standard-20260709.md
→ ?? templates/two-tables/unified-function-entry-template.md
→ ?? templates/two-tables/unified-case-entry-template.md
→ ?? templates/two-tables/getbrain-candidate-output-template.md
→ ?? outputs/audit/two-tables-entry-template-finalization-audit-20260709.md
```

确认仅新增以下 5 个文件，未修改任何表/README/INDEX/data/schema：
- docs/two-tables-entry-writing-standard-20260709.md
- templates/two-tables/unified-function-entry-template.md
- templates/two-tables/unified-case-entry-template.md
- templates/two-tables/getbrain-candidate-output-template.md
- outputs/audit/two-tables-entry-template-finalization-audit-20260709.md

---

## 完成确认

- [x] 已读取两张表条目结构审计报告（66f67d1d）
- [x] 已创建两张表写作标准
- [x] 已创建函数条目模板
- [x] 已创建案例条目模板
- [x] 已创建得到大脑候选输出模板
- [x] 已创建模板固化审计
- [x] 未修改函数表
- [x] 未修改案例表
- [x] 未修改 README
- [x] 未修改 INDEX
- [x] 未修改 data
- [x] 未修改 schema
- [x] 未新增函数
- [x] 未新增案例
- [x] P1 校验器通过（ALL_P1_DATA_VALID）
- [x] git status 干净（仅新增 5 文件）

两张表条目写作标准与模板固化完成，待 GPT 给下一步指令。
