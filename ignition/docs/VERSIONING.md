# 版本说明

## 版本阶段

- v0.1：早期函数与案例积累期（历史）。
- v0.2：结构层升级与机器可读化期（历史，见 [v0.2 总结](./v0.2_summary.md)）。
- 2026-07-09 元协议生成层（历史）：12 元协议、64 组合和候选暂存阶段。
- 2026-07-12 数学与逻辑双地基七层架构版本（IGNITION-20260709-076，当前架构/Foundation 基线）：建立双地基、七层架构、新权威注册表、legacy 兼容视图、九状态轴与强术语门禁。

## 当前状态与候选状态

`docs/project-current-state.md` 是版本化当前项目状态的权威入口。当前仓库状态不等于停留在 2026-07-12：后续已经合并的 Q12-Q23/ARN 等能力可以成为当前 `main` 的一部分，但它们不改变 2026-07-12 架构/Foundation 基线的角色。

PR #56 / 121Q24 已在验收后合并：迭代操作法与同步验证契约是当前仓库操作能力。它约束状态改变任务怎样记录 gap、claim ceiling、同步矩阵、验证和回执，但不证明任何结论的真理、价值、因果、完整性或正确性。

PR #57 / Q25C 曾按当时合同完成独立验收、普通合并与外部表面核验并形成历史方法 1.1.0：它增加同步表面注册表、传播闭包，以及实现完成、仓库同步完成、外部同步与项目整体完成的分层。

Q25B 已因生命周期死锁降为 superseded non-ready 历史候选；Q25C 是 PR #57 中被接受的方法增量。它确立的逐表面 `blocks` 原则继续有效；任务 101 已把旧独立阅读站从当前表面注册表移除。

121Q28 的 `0.1.0` 因肉身硬门槛被拒绝；121Q28R `0.2.0` 修复入口但未完成 whole-project integration；121Q28S `0.3.0` 完成同源认知、全项目对应与双向反馈候选。121Q28T 将 accepted exact HEAD 以 merge commit 合入并完成 Current/Closed 收口。`之元写作法 / Zhiyuan Writing Method` `0.3.0` 现为当前 L6 公共表达与 provenance-gated feedback 能力。这不改变七层架构、Foundation 或迭代操作法版本。

121Q30T 已将 121Q30 接受的成果展示与来源链接口收口为 Current；它不升级之元写作法 `0.3.0`、七层架构或点火迭代操作法。作品状态、方法状态和历史 claim ceiling 分别记录；一项作品被接受不能自动提升方法版本或历史因果状态。

121Q31T 将之元写作法 `0.4.0` 与 spec 驱动的完整可点击系统图收口为 Current：素材来源分为外部输入与点火增量输出，后者可复用但不是独立外部证据。`0.3.0` 保留为历史已合并版本，Q29R 与第一条成果继续绑定真实生成版本 `0.3.0`。系统图版本独立为 `0.1.0` Current；它不改变七层架构、Foundation、迭代操作法 1.1.0 或历史成果的方法版本。

Q32I closed iteration method `1.3.0` and registry-derived system map `0.3.0` after third independent exact-head acceptance, ordinary merge of PR #62, final-main validation and the external checks required at that time. Method `1.3.0`, `1.2.0` and maps `0.3.0`, `0.2.0` are Historical; `1.1.0` and map `0.1.0` are earlier Historical. The contract separated authority and execution capability, added unified apply preflight and complete repository rollback verification without adding L7, a truth layer or causal identification.

Iteration method `1.4.0 — Continuous Stage Snapshot Publication` is Current. It adds a separate publication-status axis and a machine registry for public stage summaries; snapshot visibility never raises Accepted/Current/Activated. Task 101 adds machine/human dual outputs, repository-native result surfaces and self-correction CI, while retiring the former independent deployed reader from current and future completion gates.

当前方法 `1.4.0`、系统图 `0.6.0` 与之元写作法 `0.5.0` 均以各自权威资产为准；系统图 `0.5.0`、`0.4.0` 及更早版本只作为历史证据。面向 AI 的最近状态增量见 [`STATE-CHANGELOG.md`](../STATE-CHANGELOG.md)，它是恢复导航，不取代 `docs/project-current-state.md`、registry、claim/evidence 或 Results Book。

Charter System R1（`docs/governance/charter-system-r1.md`，元治理层）经独立 exact-head acceptance（PR #137 head `669c9f8c` → merge commit `0e7c032`）收口为 Current（non-Activated），并经 front-door / 系统注册表 / VERSIONING 三表面同步（PR #139 → `09bf6400`，方法 `IGNITION-CHARTER-SYSTEM-R1-CURRENT-FRONT-DOOR-REGISTRY-AND-VERSIONING-SYNCHRONIZATION-R1-20260726`）完成 Current 收口的逐表面 attestation。它保持 `activated=false`、`publication_status=UNPUBLISHED`：Current 不等于 Activated，亦不构成任何已发布快照（满足 `PUBLISHED_SNAPSHOT != ACCEPTED/CURRENT/ACTIVATED`）。本同步不改变价值宪章、七层架构、Foundation 或迭代操作法版本。

IGNITION-HOMEPAGE-USAGE-CHARTER-SYNC-EXACT-HEAD-ACCEPTANCE-AND-PAGES-CLOSEOUT-R1-20260727 将 PR #143（head `77fc5f95777a3b7d2c5fd2f269541f35d45c4f34`）独立验收并以普通 merge 合入 `main`：首页／使用说明／系统图／宪章体系统一同步收口，系统图 `0.4.0` 由候选提升为 Current，`0.3.0` 与 `0.2.0` 为 Historical，`0.1.0` 为更早 Historical；Charter System R1 维持 `activated=false` / `publication_status=UNPUBLISHED`（Current 不等于 Activated，未发布快照）。本收口只改变系统图版本生命周期与前门表面 attestation，不激活任何能力／运行时／执行器，不改变七层架构、Foundation、迭代操作法 1.4.0、价值宪章或阶段快照历史。

架构完成不等于内容证明完成。当前架构允许后续逐对象补源、补定义、补证明、补实验、发现反例或降级，而不再推倒整体架构。

## 什么算版本升级

版本升级必须改变项目本体或权威数据契约，并同步更新入口、架构、schema、工具、测试、CI、报告和兼容策略。普通候选增量不构成架构版本升级。

## 当前版本必须同步的表面

- .github/README.md、SUMMARY.md、llms.txt
- ITERATION.md、AI-HANDOFF.md、AI-START-HERE.md、docs/project-current-state.md
- ARCHITECTURE.md、FOUNDATION.md、docs/foundation/
- docs/PROJECT-ARCHITECTURE.md、USAGE.md、AGENT-GUIDE.md、VERSIONING.md
- data/foundation/、schemas/foundation/
- tools/foundation/、tests/foundation/、formal/、views/
- .github/workflows/、reports/foundation-architecture/
- CHANGELOG.md 与对应审计记录
- STATE-CHANGELOG.md（每次正式 `main` 合并的一条 AI 状态 delta）

任何影响项目身份、能力、使用方式、当前状态或 Agent 交接的迭代，必须按 `ITERATION.md` 和 `tools/validate_iteration_sync.py` 同步这些表面；纯修复若不更新，必须记录可验证的 `NO_CHANGE_WITH_REASON`。每次正式迭代合并 `main` 都必须在同一轮向 `STATE-CHANGELOG.md` append 一条简短 delta，并由结构/链接 validator 检查；普通软件 `CHANGELOG.md` 继续记录面向人类的发布历史，二者不互相替代。

## 审计要求

每次架构版本升级必须核对：

1. 输入分支、HEAD 与开放 PR 真值；
2. 文件、索引、对象、案例、候选、pending、问题命中和反例的去重口径；
3. 全量迁移覆盖及 silent omission；
4. legacy 资产零丢失、零重编号、零不可逆覆盖；
5. THEOREM、AXIOM、ISOMORPHISM、CAUSAL、PROVED 门禁；
6. 九状态轴不非法联动；
7. 数学与逻辑后端真实状态；
8. schema、validator、test、CI 与兼容视图；
9. blocker、未解决证明义务、commit 和 Draft PR。

## 兼容策略

新注册表合并后承担对象、命题、论证、来源、证据、证明和验证状态权威。旧两张表继续作为 legacy source / compatibility view，保留原 ID 和正文，不独立生长。计数不得手写，必须来自可复算的 project-state 和 migration-summary。
## 许可边界

当前分发版本采用分层许可。核心可执行软件为 BUSL-1.1 并在 Change Date 后转为 AGPL-3.0-or-later；原创文档/报告为 CC BY-NC-SA 4.0；价值宪章和一般治理原则为 CC BY-SA 4.0；公开接口与互操作 schema 为 Apache-2.0。许可作用域以根 LICENSE 与 LICENSES/README.md 为准；历史 MIT 版本权利不追溯撤销。
