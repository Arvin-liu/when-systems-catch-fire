# P1 机器可读化抽取可行性审计

## 审计时间

2026-07-07

## 审计目标

复核 P1-0 规划的数据集是否能够从现有 Markdown 文档稳定抽取，并确定后续 P1-2 至 P1-6 的执行策略。

本次只做审计，不生成 CSV / JSON，不创建 schema，不创建校验器。

## 审计范围

| 数据集 | 来源文档 | 审计结论 |
|---|---|---|
| classic_problems_benchmark | `docs/classic_problem_ids.md` | 自动抽取 |
| storytelling_backlog | `docs/storytelling_backlog_ids.md` | 自动抽取（部分字段需后续补齐） |
| pending_claims | `docs/pending_claims_register.md` | 自动抽取 |
| publication_risk_rules | `docs/publication_risk_checklist.md` | 半自动抽取 |
| failure_typology | `docs/failure_typology.md` | 半自动抽取 |
| evidence_regimes | `docs/evidence_regime_library.md` | 半自动抽取 |
| function_dependency | `docs/function_dependency_map.md` | 半自动抽取 |

---

## 1. classic_problems_benchmark

### 检查结果

- 行数：34
- 编号连续：是（CP-001 至 CP-034）
- 来源文件存在：是（所有 source_file 路径均存在）
- 缺失标题：0
- 缺失来源文件路径：0
- 缺失来源行号：0
- 非法来源文件：无

### 可自动抽取字段

- id
- title
- source_file
- source_line

### 需后续补齐字段

- domain（领域，需从 benchmark 正文或人工补齐）
- benchmark_type（问题类型）
- claim_level_max（最高断言等级）
- pending_required（是否必须标注 pending）
- related_pend_ids（关联 PEND 编号）
- related_failure_types（关联失败类型）
- related_evidence_regime（关联证据制度）
- public_safe（是否可公开）

### 结论

**自动抽取**。34 行完整，编号连续，来源文件全部存在，可直接用脚本生成结构化数据的基础行。后续补齐字段建议在 P1-3 生成时通过半自动+人工方式填入。

---

## 2. storytelling_backlog

### 检查结果

- 行数：30
- 编号连续：是（SB-001 至 SB-030）
- 优先级合法：是（仅含"高"、"中"、"暂缓"）
- 缺失标题：0
- 缺失分数字段（score）：0（但所有 score 当前值为 `pending`，需后续填写）
- 优先级分布：高、中、暂缓

### 可自动抽取字段

- id
- priority
- title
- source
- domain（当前值为 `pending`，后续需填写）
- score（当前值为 `pending`，后续需填写）
- recommended_form（当前值为 `pending`，后续需填写）
- main_risk

### 需后续补齐字段

- domain（领域，当前全部为 `pending`，需人工或半自动填写）
- score（评分，当前全部为 `pending`，需规则化填写）
- recommended_form（推荐故事形式，当前全部为 `pending`，需人工补写）
- related_cp_ids（关联 CP 编号）
- related_pend_ids（关联 PEND 编号）
- publish_status（当前 `暂缓` 优先级条目建议默认 `hold`）
- notes

### 结论

**自动抽取（部分字段需后续补齐）**。30 行完整，编号连续，优先级合法。但 domain、score、recommended_form 当前全为 `pending`，在生成 JSON/CSV 前需人工或规则化填写。`暂缓` 优先级条目可在 P1-3 生成时自动映射 `publish_status = hold`。

---

## 3. pending_claims

### 检查结果

- 行数：34
- 编号连续：是（PEND-001 至 PEND-034）
- 核心字段完整：是
- 缺失 domain：0
- 缺失 claim：0
- 缺失 forbidden_wording：0
- 缺失 recommended_wording：0
- 含 HOLD 处理的条目：PEND-030、PEND-031、PEND-032

### 可自动抽取字段

- id
- domain
- claim
- allowed_level
- forbidden_wording
- recommended_wording
- handling

### 需后续补齐字段

- default_decision（可从 handling 字段和 HOLD 标记规则推断）
- related_cp_ids（关联 CP 编号）
- related_sb_ids（关联 SB 编号）
- notes

### 结论

**自动抽取**。34 行完整，编号连续，所有核心字段非空。`default_decision` 可在 P1-4 生成时通过规则从 `handling` 字段推断（如含"HOLD"或"保持 pending"则映射为 `pending`）。

---

## 4. publication_risk_rules

### 检查结果

- 是否包含 PASS / REVISE / HOLD：是
- 是否包含强制 HOLD 条件：是（第 10 节）
- 是否包含 CP / SB 编号检查：是（CP-001 至 CP-034，SB-001 至 SB-030）
- 文档结构：12 个一级节，34 个标题
- 覆盖领域：数学、物理学、历史学、社会科学与经济学、医学与心理健康、法律、AI 与计算机科学、文学艺术与审美

### 可半自动抽取字段

- rule_category（从二级标题推断，如"断言等级检查"、"pending 检查"等）
- decision（PASS / REVISE / HOLD，从各条规则文本提取）
- force_hold_conditions（从第 10 节强制 HOLD 条件列表提取）
- domain（从 5.x 高风险领域子节推断）

### 需人工结构化字段

- rule_id（需人工为每条规则分配唯一 ID）
- trigger_condition（每条规则的触发条件，需人工从列表语义提取）
- related_cp_ids、related_sb_ids（编号范围已在文档中，但需规则化绑定）
- applies_to（适用对象，如 benchmark、story、general）

### 结论

**半自动抽取**。文档结构较复杂，规则分散在标题、列表和表格中，不适合完全自动化解析。P1-4 生成时建议使用"规则手工结构化 + 脚本校验"方式，优先抽取强制 HOLD 条件和 PASS/REVISE/HOLD 三类决策规则。

---

## 5. failure_typology

### 检查结果

- 是否覆盖 12 种失败类型：是（全部 12 种均在文档中）
- 标题结构是否稳定：否（12 种类型以编号列表形式列在"当前覆盖的失败类型"节中，不是以独立二级标题展示）
- 文档标题数：9 个
- 12 种失败类型：材料错误、边界选错、尺度错配、函数过度泛化、同构误判、证据等级不足、AI 过度解释、L2 推论误写成 L5 结论、学科证据制度误配、观察者位置错误、把局部机制误写成全局规律、把历史叙事误写成因果定律

### 可半自动抽取字段

- id（如 FAIL-001 至 FAIL-012，需分配后才可抽取）
- name（12 种类型名称可自动提取）
- category（高风险 / 普通，从"高风险失败类型"节推断）

### 需后续补齐字段

- description（每种类型的文字说明，需从正文段落中提取）
- affected_functions（与函数系统的关系，需从"与函数系统的关系"节半自动提取）
- correction_method（修正方式，需从正文中提取）
- related_evidence_regimes（关联证据制度）
- related_cp_ids、related_sb_ids、related_pend_ids

### 结论

**半自动抽取**。12 种类型全部存在，但标题格式不稳定（以列表而非独立二级标题组织）。P1-4 生成时建议先建立 FAIL-001 至 FAIL-012 的结构化映射表，再逐条填充字段。

---

## 6. evidence_regimes

### 检查结果

- 是否覆盖主要证据制度领域：是（13 个领域：数学、物理、历史、社会科学、经济、工程、医学、法律、文学、艺术、教育、AI、计算机）
- 是否可识别领域标题：可（领域名称嵌在"当前覆盖领域"节的列表中）
- 文档标题数：14 个
- 文档结构：以概述性文本为主，领域条目在列表中，核心字段在"核心字段"节中定义，无独立领域表格

### 可半自动抽取字段

- domain（13 个领域名称可直接提取）
- 核心字段名（从"核心字段"节列表中提取：L_level_recommended、evidence_required_min、evidence_required_strong、pending_conditions、forbidden_claims）

### 需后续补齐字段

- domain_id（需分配，如 ER-数学、ER-物理等）
- L_level_recommended（每个领域的推荐等级，需从学科卡片正文中填充）
- evidence_required_min（最低证据要求）
- evidence_required_strong（强证据要求）
- pending_conditions（pending 触发条件）
- forbidden_claims（禁止断言）

### 结论

**半自动抽取**。13 个领域均可识别，核心字段已在文档中定义。但各领域的具体字段值（推荐等级、证据要求等）主要存在于学科卡片（`outputs/getbrain/` 中的各学科文档）中，需在 P1-5 时逐领域从学科卡片填充。建议 P1-2 先建立 schema，P1-5 逐领域填充。

---

## 7. function_dependency

### 检查结果

- 是否识别 L0-L6：是（L0 至 L6 全部在文档中）
- 是否可识别函数组：是（8 个函数族：退出权函数族、门控函数族、自举函数族、乘法函数族、认知函数族、财富域函数、学科域函数、生物学域函数）
- 是否可自动识别依赖边：否（依赖关系以自然语言描述，未结构化）
- 文档标题数：12 个
- 已识别关键词：依赖、层级、函数（均存在）；depends、active、pending、review（不在文档中）

### 可半自动抽取字段

- layer（L0-L6，可自动识别）
- function_group（8 个函数族名称，可从列表提取）
- status（层级状态，需从正文推断）

### 需后续补齐字段

- function_id（需分配唯一 ID）
- function_name（每个函数的具体名称，需从函数族列表和正文中提取）
- depends_on（依赖关系，需人工从自然语言描述中结构化提取）
- used_by（被引用函数，需人工补充）
- layer（每个函数的层级归属，需人工映射）
- active_status（active / pending / review，需人工或规则判断）

### 结论

**半自动抽取**。L0-L6 层级可稳定识别，8 个函数族可提取，但具体函数列表和依赖边主要以自然语言描述，无结构化表格。P1-5 生成时建议分两步：先抽取层级和函数组，再由人工逐步补充依赖边。

---

## 总体结论

**可以进入 P1-2：建立 JSON Schema。**

3 个数据集（classic_problems_benchmark、pending_claims、storytelling_backlog）可自动抽取，基础行完整；4 个数据集（publication_risk_rules、failure_typology、evidence_regimes、function_dependency）需半自动抽取，结构可识别但字段值需人工补充或规则化处理。整体阻塞项为零，不存在无法进入下一步的致命问题。

---

## 推荐后续顺序

1. P1-2：建立 JSON Schema；
2. P1-3：生成 CP / SB 数据（自动抽取，可直接执行）；
3. P1-4：生成 pending / risk / failure 数据（pending_claims 可自动，risk 和 failure 需半自动）；
4. P1-5：生成 evidence / function dependency 数据（均需半自动，从学科卡片逐领域填充）；
5. P1-6：建立数据校验器；
6. P1-7：P1 数据完整性审计。

---

## 边界说明

本次审计没有生成 CSV / JSON，没有创建 schema，没有创建校验器，没有修改 getbrain 原始输出、函数表、案例表或编号表。
