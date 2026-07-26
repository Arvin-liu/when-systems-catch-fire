# Charter System R1 — Architecture Candidate (Draft / 非 Main / 非 Current)

Status: DRAFT CANDIDATE. Not merged to `main`; not Current. Submitted as a formal-repo Draft PR; does not modify any existing charter or governance document.

> Provenance: promoted from 1111 Draft PR #53 (relay head `8f802a45285905ce3b350955dd95b3367b650e59`). This formal-repo Draft PR places the same candidate into the formal repository file tree as a Draft (non-Main, non-Current). It has not been merged to `main` and is not the Current charter system. Final acceptance / promotion remains the account owner's independent action.

## 执行决定

**CHARTER_SYSTEM_R1_CANDIDATE** — 建立"宪章系统 R1"：作为**元治理层**，规定单个宪章（含《生命共同体价值宪章》）如何被提议、版本化、批准、与决策绑定、并跨 Fork 继承责任。本文件即该候选本身，状态为 **Draft / 非 Main / 非 Current**，未授予任何权威。

> 边界说明：本候选以 Draft PR 形式存在于正式仓库文件树中，但**未合并入 `main`**、**非 Current**。它不修改任何既有宪章或治理文档；其若被所有者接受并经受控同步提升为 Current，那是为所有者保留的独立后续动作。本文件严格保持 Draft、非 Main、非 Current。

## 0. 范围与非目标

- **在范围内**：治理"宪章"这一对象的**系统**（生命周期、版本、修订、绑定、继承）。
- **不在范围内**：任何具体宪章的**内容**（如价值宪章的原则正文）。系统可治理价值宪章的*生命周期*，但**不改写其正文**。
- R1 是 Draft Candidate。在经独立 exact-head acceptance 并由所有者提升为 Current 之前，它不运作、不约束、不自称有效。
- **执行者边界**：WorkBuddy 仅以 `execution_agent` 起草本候选；它不持有任何宪章权威，不以 `responsible_actor` / `publisher_actor` 自居（沿用 stage-snapshot 与迭代操作法的同一边界）。

---

## 1. 总则（General Principles）

宪章系统管理的是"规范性前提"这一特殊对象。它必须始终区分四类问题（沿用价值宪章 §价值判断、事实证据与治理批准）：

1. **价值/规范**：什么值得追求、什么不能以生命共同体成员为代价实现 —— 宪章的本职。
2. **事实证据**：某个事实主张是否成立 —— 证据制度回答。
3. **语义审核**：定义与边界是否合理 —— 人工审读回答。
4. **治理批准**：是否正式生效或晋级 —— governance 回答。

据此，宪章系统的总则：

- **G1 宪章不证明事实。** 宪章是规范性边界，不构成经验证据，不替代数学证明、实验验证、案例核验、外部学科审查或治理批准。符合宪章 ≠ 事实层已验证；违反宪章 = 规范性否决理由。
- **G2 系统不越权改写宪章内容。** 宪章系统只治理宪章的*生命周期、版本、绑定与继承*，不修改任何宪章的规范正文。价值宪章的**底线（保留底线）**高于本系统。
- **G3 底线不可修订（red-line）。** 任何修订不得借"修订"之名允许：无证据事实结论、无偿商业抽取、赞助俘获、或对生命共同体成员的不可逆非自愿重大伤害。此红色边界不在修订协议的可谈判范围内。
- **G4 分歧必须留存。** 修订与批准必须保留主要反对意见，不得用合并结果抹去分歧。
- **G5 执行者无宪章权威。** 任何 AI / Agent / 自动化工作流只能以 `execution_agent` 起草、核验、记录；宪章的批准（Accepted/Current）只能由账号所有者（人类 `responsible_actor`）独立执行。
- **G6 候选不自称有效。** 处于 Draft/Candidate 的宪章系统或其管辖下的宪章，不得被当作当前已生效的治理约束使用；公开 Draft 工作停留在 Candidate / Ready，不是当前能力。
- **G7 可见性 ≠ 有效性。** 宪章出现在主页/README/索引中（HOMEPAGE_VISIBLE）不推断其已被接受或当前生效（≠ CAPABILITY_AVAILABLE / CURRENT）。

---

## 2. 生命周期（Lifecycle）

宪章文档沿用迭代操作法的**能力生命周期轴**（`ITERATION.md` §13），但作用于"规范性文档"而非"能力"：

| 状态 | 含义 | 进入门槛 |
| --- | --- | --- |
| `DRAFT` | 在分支 / Draft PR 中起草，未提议 | 仅本地 / 分支编辑 |
| `CANDIDATE` | 已作为正式提案公开，待独立验收 | 公开提案 + 理由 + 影响 + 异议记录 + 试行边界 + 回滚条件 |
| `ACCEPTED` | 独立验收了该确切 HEAD | 独立重取 PR/HEAD/review/CI 后接受；满足所有 `accepted` blocker |
| `MERGED` | 被接受的 HEAD 进入 `main`，ancestry 核验 | 普通合并；Merged 不自动 Current |
| `CURRENT` | 合并态在 `main` 上验证、front-door/current-state 表面同步 | 真理式 post-merge 收口、无未决 residue、逐表面 attestation |
| `CLOSED` | 收口完成 | 同 Current 收口 |
| `HISTORICAL` | 被新版本取代 | 新版本进入 CURRENT 后旧版本转 HISTORICAL |

- **宪章系统 R1 当前状态**：`DRAFT` / `CANDIDATE`（本文件即候选）。它**不是** `CURRENT`，**不在** `main`。
- **发布 / 可见性轴**（如需将宪章摘要公开而不提升其生命周期）：`UNPUBLISHED → PR_VISIBLE → PUBLISHED_SNAPSHOT → SUPERSEDED/WITHDRAWN/HISTORICAL_SNAPSHOT`。该轴与生命周期轴**正交**；`PUBLISHED_SNAPSHOT != ACCEPTED/CURRENT/ACTIVATED`，与迭代操作法 1.4.0 的快照契约同构。
- `CURRENT` 的宪章可被子宪章 / 决策引用；`HISTORICAL` 宪章仅用于历史溯源，不作为当前约束。

---

## 3. 权威层级（Authority Hierarchy）

沿用价值宪章的规范栈，并将"宪章系统"作为**元层**插入：

1. **价值宪章（最高规范层）**：决定什么值得做、什么不能以生命共同体成员为代价实现。其**底线**不可被任何下层（含本系统）推翻。
2. **宪章系统（元治理层，本 R1）**：治理"宪章"这一对象的生命周期、版本、修订、绑定与 Fork 继承。它从属于价值宪章底线，高于任何单个具体宪章。
3. **治理与权利边界**：决定谁可以参与、反对、审查、暂停、要求回滚。
4. **Ψ₀ 与元协议**：决定怎样合理判断结构、收敛、冲突与条件适用性。
5. **Function OS**：决定怎样把函数 / 工具 / 执行器组织为可运行系统。
6. **验证层**：决定事实 / 证明 / 实验 / 语义审读 / 外部证据是否足够。
7. **现实反馈**：发现错误、暴露缺口、记录伤害、修正函数、更新价值冲突。

约束：

- 宪章系统 R1 在未被接受前**不占据**第 2 层权威；它只是候选提案。
- 执行者（WorkBuddy 等）不出现在规范栈的任何权威位置；它们只执行、不批准。
- 第 2 层不得用于自我提升：宪章系统不能借自身条款把自己声明为 Current；它成为 Current 只能经独立 exact-head acceptance + 合并 + 收口（与它所治理的对象经历同一流程）。

---

## 4. 修订协议（Revision Protocol）

任何宪章（含价值宪章、含本系统自身）的修订，必须包含以下记录字段（继承并形式化价值宪章 §宪章修订与冲突程序）：

- **R1 公开提案**：说明要新增 / 删除 / 改写 / 降级的条款与精确文本。
- **R2 理由**：当前条款造成的不足、冲突或现实代价。
- **R3 利益相关者影响**：受益者、风险承担者、沉默主体、维护者成本。
- **R4 异议记录**：保留主要反对意见，不合并抹去。
- **R5 试行边界**：适用范围、期限、监测指标、停止条件。
- **R6 回滚条件**：哪些事实 / 伤害 / 失败 / 治理异议触发撤回。
- **R7 保留底线**：不得修订允许无证据事实结论、无偿商业抽取、赞助俘获或不可逆非自愿重大伤害（= G3 red-line）。
- **R8 版本号与谱系**：每次修订产生新版本号，并记录 parent 版本与修订 HEAD；修订不得静默改动另一宪章。

修订门禁：

- 修订提案须以 Draft PR 公开，HEAD 可独立重取核验。
- 修订不得与价值宪章底线冲突；冲突即构成规范性否决。
- 修订记录进入**宪章修订谱系**（与 §6 Fork 谱系同构为可审计树）。

---

## 5. 决策—宪章版本绑定（Decision-Charter Version Binding）

核心规则：**每个被合并的能力、被接受的方法、被批准的治理决定，必须记录其作出时所依宪章版本（`charter_version_at_decision`）**。

- **B1 绑定记录**：合并 / 接受 / 批准时，在对应注册表 / 请求 / 回执中写入 `bound_charter_versions: [<charter_id>@<version>]`。例：某方法在价值宪章 v2 + 宪章系统 R1 生效期间被接受，则绑定 `[life-community-value-charter@v2, charter-system@R1]`。
- **B2 有效性范围**：决策的有效性**限定于**其绑定宪章版本所处的规范语境。宪章后来修订，不自动使先前决策失效；先前决策继续绑定其原始宪章版本，除非被显式重新批准（re-ratification）。
- **B3 重新批准**：若新宪章版本改变了某决策的规范性前提，且该决策仍持续生效，则须显式 re-ratify 并绑定新版本；否则决策应降级 / 回滚至其原始版本语境或停止。
- **B4 不可追溯改写**：不得通过后补宪章版本 retroactively 声明某历史决策"一直符合"新规范；历史决策只在其当时绑定版本下被评价。
- **B5 可审计性**：绑定是 provenance 链的一环，与 exact-head acceptance、来源链（provenance-gated）同源；任何审计必须能回溯 决策 → 绑定宪章版本 → 该版本 HEAD → 该版本修订谱系。

此规则把"决策"与"当时有效的宪章"钉死，避免宪章修订后的规范性漂移，也避免把新规范 retroactively 强加于历史成果（呼应 `VERSIONING.md`：一项作品被接受不能自动提升方法版本或历史因果状态）。

---

## 6. Fork 责任谱系（Fork Responsibility Lineage）

当本仓库（及其宪章体系）被 Fork 时，责任随代码与规范一并继承，且必须可审计：

- **F1 义务继承**：Fork 继承价值宪章与本宪章系统的全部规范性义务，包括保留底线（G3）、非无偿商业抽取、反赞助俘获、未知主体谨慎义务、维护者可持续性。Fork 不得以"独立项目"为由剥离这些义务。
- **F2 许可约束**：价值宪章与一般治理原则为 CC-BY-SA-4.0；治理报告 / 清单为 CC-BY-NC-SA-4.0；核心软件 BUSL-1.1（Change Date 后转 AGPL-3.0-or-later）；互操作 schema 为 Apache-2.0。Fork 必须保留上述共享署名（share-alike）义务，不得将价值宪章以排除 share-alike 的方式再许可。
- **F3 外部输入不重发**：源自外部研究 / 外部输入的内容不随 Fork 被重新发布或主张权利（沿用 `external-input-non-republication-principle.md`）。Fork 必须继续排除这些不清权利内容。
- **F4 谱系记录**：每个 Fork 必须记录 `lineage`：`derived_from_repo`、`derived_from_head`（fork 时的精确 HEAD）、`fork_date`、`fork_owner`、`parent_fork`（若自身也是 Fork）。谱系形成树，每个节点记录其父。
- **F5 谱系可审计与 preservable**：谱系信息必须随 Fork 仓库持久保存（如本系统注册表中的 `fork_lineage` 记录），下游 Fork 不得删除上游谱系。审计可沿树回溯任意 Fork 到 canonical 源。
- **F6 责任不随 Fork 转移给受害者**：Fork 不能把本应由 Fork 所有者承担的义务、成本或伤害转嫁给上游、沉默主体或维护者。Fork 所有者对其 Fork 的部署、商业化与规范背离承担首要责任。
- **F7 宪章修订在 Fork 中的传播**：上游宪章修订不自动覆盖 Fork 中的宪章；Fork 可选择同步上游修订（并记录同步 HEAD），但须显式 re-ratify；Fork 不得假称"与上游宪章一致"而未实际同步。
- **F8 回滚与停止的跨 Fork 责任**：若上游因伤害 / 失败触发宪章回滚或停止条件，Fork 若仍包含被回滚内容，须在其自身范围内执行相应回滚 / 停止，并保留记录。

---

## 7. 与既有制品的关系

- **价值宪章**（`docs/governance/life-community-value-charter.md`）：本系统治理其生命周期，不改写其正文；其底线（§宪章修订与冲突程序"保留底线"）为本系统红色边界。
- **迭代操作法**（`ITERATION.md`、方法 1.4.0 Current）：宪章生命周期轴沿用其能力生命周期与 exact-head acceptance 门禁；宪章的 `PUBLISHED_SNAPSHOT` 可见性轴与 1.4.0 快照契约同构。
- **版本说明**（`VERSIONING.md`）：宪章版本升级须同步相应表面（如 `docs/governance/README.md`、本系统注册表、CI / 报告），并遵循其审计要求。
- **许可边界**（`docs/governance/README.md`、`LICENSES/`）：Fork 责任谱系以此为准。
- **执行者边界**（`stage-snapshot-publication.md` 等）：WorkBuddy 等仅 `execution_agent`。

## 8. 本 R1 候选自身的验收门禁

宪章系统 R1 须经历与它所治理对象相同的生命周期：Draft → Candidate →（独立 exact-head acceptance）→ Merged → Current/Closed。在所有者完成该流程前，本文件仅为候选提案，**不运作、不约束、不自称有效**。WorkBuddy 起草完成后停止，等待独立人工验收。

---

## 附：机器可读记录（见 charter-system-r1.schema.json）

`charter-system-r1.schema.json` 提供宪章记录 / 修订记录 / Fork 谱系记录的 schema 草图与不变式，供未来受控同步升入 formal `docs/governance/` 时直接使用。
