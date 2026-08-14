# 点火项目整体认知初始化 — Agent 认知报告

生成时间：2026-07-08 21:25 (GMT+8)
任务来源：用户发来的「点火项目整体认知初始化」指令（.md 附件）
执行方式：只读阅读 GitHub 主仓库（README / docs / outputs/audit / 统一函数总表 / 统一案例总表 / data / schemas / tools），未修改任何核心资产。
主仓库路径：`/Users/zhiyuan/Agent 工作区/Codex/2026-06-25/github-cp-agent-500-600-1000/when-systems-catch-fire`
git 状态（只读确认）：main 与 origin/main 同步，工作区干净。

---

## 1. 项目整体定位

**一句话**：点火（When Systems Catch Fire）是一个跨学科系统相变的生成模型——把现象映射为函数与案例，分析系统何时被「点燃」，输出 `true / false / contradiction / pending` 四象限结论。

**它是什么**
- 跨域结构性推论的**元工具**（meta-tool），不是物理理论、不是数学证明工具、不是学科替代品。
- 通过六组件（C / M / I_iso / L_meta / G_δ / P_meta）帮助人和 AI 发现不同领域共享的**结构性规律**。
- 表达强度受约束：「统一 / 不可能 / 解决 / 证明」默认指**结构层面**，非物理机制；证据不足必须标 `pending`。

**它解决什么**
- 识别、判定、收敛跨领域**同构结构**；
- 把复杂现象**函数化 + 案例化**；
- 跨域同构识别、候选机制生成、反例生成、`pending` 判定。

**它不是什么**
- 不是物理大一统、不是四种基本力统一、不是现代物理难题的解；
- 不是任何具体学科的替代品；现实结论必须连接外部证据。

**角色分工（v0.2 明确）**
- **得到大脑**：主要推论 / 函数化 / 案例化 / 框架发现引擎（J⁺/J⁻ 判定、L0–L5 断言等级、pending 判断、旧表结构审计）。
- **Codex / 本地模型 / 外部脚本**：整理、机器可读化、校验、收口辅助。

---

## 2. 元函数体系理解（Ψ₀）

**核心定义**
```
Ψ₀(x,y,B_n) := C(x,y) × M(B_n) × I_iso(A,B) × L_meta × G_δ × P_meta
```
**四象限判定**
```
J⁺(x)=1, J⁻(x)=0 → true
J⁺(x)=0, J⁻(x)=1 → false
J⁺(x)=1, J⁻(x)=1 → contradiction / bootstrap_failed
J⁺(x)=0, J⁻(x)=0 → underdetermined / pending
```

**六组件**
| 组件 | 名称 | 判定什么 | 关键算子 |
|---|---|---|---|
| C | 因果结构判定 | 为什么（因果结构） | cause / effect / temporal_order / counterfactual |
| M | 自举收敛判定 | 怎么收敛 | ΔB_n(Δf+Δc+Δe+Δi) / bootstrap_loop / convergence_threshold |
| I_iso | 同构判定 | 什么同构 | structure_A≅structure_B / isomorphism_mapping / invariance |
| L_meta | 元层面收敛约束 | 往上收敛、禁无限展开 | J⁺_L / J⁻_L / argmin_L；触发 Ψ_trigger(n≥20 ∧ v≥0.85) |
| G_δ | 哥德尔不完备性判定 | 是否永不可收敛 | proof / ¬∃proof；不可证→触发元层收敛 |
| P_meta | 元协议投影算子 | 跨系统同构投影到元层 | 产出 6 个元协议（F_contract/F_symmetry/F_distributed_learning/F_nash/F_emergence/F_self-organization） |

**三层结构**（README 系统架构段）
```
- Domain layer（案例、对象、事件）→ 统一案例总表（790 条）
- Function layer（函数、机制、映射）→ Ψ₀ + 单项函数 A1/T1/D1…（602 条）→ 统一函数总表
- Meta layer（十二律、元同构律、元协议、收敛约束）→ 决定分析停在哪个层级
```
**关键纪律**：`L_meta` 强制往上收敛、禁止往下无限展开；避免把事件层误写成终局理论。

---

## 3. 两张表结构理解

- **统一函数总表**（`统一函数总表/`）：602 条函数，编号体系 `0001-Ψ₀…`、`0000-MF-0001-正向自举通道`、`A1/T1/D1…`、`D590+` 为近期发现（D597 量化指标替代真实价值、D598 系统性钝化、D599 刷分博弈）。每条含 frontmatter + 数学表达 + 文字说明 + 索引。
- **统一案例总表**（`统一案例总表/`）：790 条案例（`C-xxxx`，如 C-11 英国光荣革命、C-26 戈尔巴乔夫改革、C-50 华为员工持股）。
- **索引可见性**是收口硬约束：新增函数/案例须通过 `*-index-visibility-check` 审计，确保可被按编号/标题/语义召回；INDEX 头部计数同步（如 605→606、790→793）。

---

## 4. P1 机器可读数据体系理解

**定位**：P1 是**数据结构层**（非新增理论、非 v0.3、非新增函数/案例）。把 docs 里的 Markdown 逐步转成机器可读 JSON/CSV，供 Codex / 得到大脑 / 本地模型稳定读取、校验、引用。

**校验器**：`tools/validate_data.py`，判定 `ALL_P1_DATA_VALID`（碰撞前必跑）。

**data/ 七类数据集（json+csv 成对，schema 在 data/schemas/）**
| 数据集 | 编号 | 用途 |
|---|---|---|
| classic_problems_benchmark | CP-001~（34） | 经典问题对照基准，命中则辅助「相关经典问题」 |
| storytelling_backlog | SB-001~（30） | 是否适合转文章/案例，辅助「可写作方向」 |
| pending_claims | PEND-001~（34） | 哪些结论必须 `pending`，防误写确定结论 |
| publication_risk_rules | RISK-001~（8） | PASS / REVISE / HOLD 判定 |
| failure_typology | FAIL-001~（12） | 失败类型标记（过度类比/证据不足/层级误置/概念漂移…） |
| evidence_regimes | EVID-001~（12） | 按学科约束证据标准、claim level |
| function_dependency | FUNC-L0~（13） | 函数依赖关系，挂接上游 |

**约束**（P1 工作流第 1 节）：得到大脑默认读不了网页链接，输入须优先本地正文/MD/DOCX/JSON/CSV；不得只给 URL。

---

## 5. 后续材料碰撞流程（12 步 + 收口闭环）

**标准 12 步**（docs/p1-machine-data-collision-workflow-20260708.md）
1. 读取任务说明 → 2. 确认输入材料完整（本地正文，非仅 URL）→ 3. 跑 `validate_data.py` 确认 `ALL_P1_DATA_VALID` → 4. 加载 P1 七类数据 → 5. 读函数表 → 6. 读案例表 → 7. 概念拆解 → 8. 用 benchmark/failure_typology 预筛 → 9. 用 evidence_regimes/publication_risk_rules 做证据约束 → 10. 与两张表碰撞（同构/缺口/合并）→ 11. 生成五类输出 → 12. 生成回填建议与保存。

**输出五分类**：新增函数 / 新增案例 / 新增注释 / 扩展注释 / 不采纳项。

**收口闭环**（来自 outputs/audit 关键报告，如 teacher-competition-batch-closeout）
```
输入材料 → 元函数分析 → 候选函数/案例 → Ψ₀ 判定
→ 人工审核 → 小批量回填 → 索引验证 → 审计收口
```
- 候选清单逐项收口：入表（给正式编号）/ 暂缓 / 重定向为扩展注释；
- 索引可见性验证（*-index-visibility-check）；
- INDEX 头部计数同步；
- 审计文件留痕（small-batch-backfill-audit / backfill-review / closeout-audit）。

**关键审计资产**（outputs/audit 已沉淀，供复用）
- 跨域候选函数：cross-domain-candidate-function-{review,small-batch-backfill,closeout,smoke-test}-audit
- 赛课机制：teacher-competition-{first-real-collision,small-batch-backfill,index-visibility-check,batch-closeout}-audit
- P0/P1 基础设施：v0.2-p0-closeout-audit、p1-machine-readable-data-audit、p1-collision-workflow-smoke-test

---

## 6. 当前可执行任务

基于本次认知，Agent 当前可承接（均不修改核心资产，除非用户明确授权回填/提交）：
1. **Get 笔记材料碰撞**：把上一轮已分类的 607 条材料（441 链接 / 160 发芽 / 6 讨论）按 P1 工作流做小批量碰撞——优先 AI与前沿科技 + 经济与产业（D597/D599 高频）。
2. **P1 数据辅助预筛**：对任意新输入材料，用七类数据集做命中/失败类型/证据约束预筛，产出 collision 五分类草稿。
3. **收口审计复用**：参照 teacher-competition / cross-domain 审计模板，对新碰撞批次做索引可见性验证与收口留痕。
4. **认知同步**：本报告的结论可作为后续会话的「项目初始化」基线，避免重复读全仓库。

---

## 验证（严守限制）
- [x] 已阅读 GitHub 主仓库（README / docs / outputs/audit / 两张表 / data / schemas / tools）
- [x] 已理解 Ψ₀ 元函数（六组件 + 四象限 + 三层结构）
- [x] 已理解函数表和案例表（602 / 790，编号体系与索引可见性纪律）
- [x] 已理解 P1 机器数据体系（七类数据集 + 校验器 + 约束）
- [x] 已理解碰撞流程（12 步 + 收口闭环）
- [x] 未修改函数表
- [x] 未修改案例表
- [x] 未修改 data
- [x] 未修改 schema
- [x] 未创建函数 / 案例
- [x] 未进行材料碰撞
- [x] 仅新建本报告（outputs/audit/agent-project-understanding-20260708.md）

> git 提交与 origin 同步：本仓库是点火项目真实 git 仓库（main 干净）。按用户一贯红线（不擅自 push、不可逆动作先确认），本报告已生成但**未执行 commit/push**，待用户确认是否提交。
