# 版本说明

## 版本阶段

- v0.1：早期函数与案例积累期（历史）。
- v0.2：结构层升级与机器可读化期（历史，见 [v0.2 总结](./v0.2_summary.md)）。
- 2026-07-09 元协议生成层（历史）：12 元协议、64 组合和候选暂存阶段。
- 2026-07-12 数学与逻辑双地基七层架构版本（IGNITION-20260709-076，当前架构/Foundation 基线）：建立双地基、七层架构、新权威注册表、legacy 兼容视图、九状态轴与强术语门禁。

## 当前状态与候选状态

`docs/project-current-state.md` 是版本化当前项目状态的权威入口。当前仓库状态不等于停留在 2026-07-12：后续已经合并的 Q12-Q23/ARN 等能力可以成为当前 `main` 的一部分，但它们不改变 2026-07-12 架构/Foundation 基线的角色。

PR #56 / 121Q24 已在验收后合并：迭代操作法与同步验证契约是当前仓库操作能力。它约束状态改变任务怎样记录 gap、claim ceiling、同步矩阵、验证和回执，但不证明任何结论的真理、价值、因果、完整性或正确性。

PR #57 / Q25C 已在独立验收、普通合并、生产 Pages 部署与实时读取后成为当前方法 1.1.0：它增加同步表面注册表、传播闭包，以及实现完成、仓库同步完成、外部同步与项目整体完成的分层。

Q25B 已因生命周期死锁降为 superseded non-ready 历史候选；Q25C 是 PR #57 中被接受并进入当前状态的方法增量。Q25C 允许 post-merge-only Pages pending 时进行 pre-merge Accepted/Merged，同时仍要求逐表面 attestation 才能进入 Current/Closed。

121Q28 的 `0.1.0` 因肉身硬门槛被拒绝；121Q28R `0.2.0` 修复入口但未完成 whole-project integration；121Q28S `0.3.0` 完成同源认知、全项目对应与双向反馈候选。121Q28T 将 accepted exact HEAD 以 merge commit 合入并完成 Current/Closed 收口。`之元写作法 / Zhiyuan Writing Method` `0.3.0` 现为当前 L6 公共表达与 provenance-gated feedback 能力。这不改变七层架构、Foundation 或迭代操作法版本。

121Q30T 已将 121Q30 接受的成果展示与来源链接口收口为 Current；它不升级之元写作法 `0.3.0`、七层架构或点火迭代操作法。作品状态、方法状态和历史 claim ceiling 分别记录；一项作品被接受不能自动提升方法版本或历史因果状态。

121Q31T 将之元写作法 `0.4.0` 与 spec 驱动的完整可点击系统图收口为 Current：素材来源分为外部输入与点火增量输出，后者可复用但不是独立外部证据。`0.3.0` 保留为历史已合并版本，Q29R 与第一条成果继续绑定真实生成版本 `0.3.0`。系统图版本独立为 `0.1.0` Current；它不改变七层架构、Foundation、迭代操作法 1.1.0 或历史成果的方法版本。

架构完成不等于内容证明完成。当前架构允许后续逐对象补源、补定义、补证明、补实验、发现反例或降级，而不再推倒整体架构。

## 什么算版本升级

版本升级必须改变项目本体或权威数据契约，并同步更新入口、架构、schema、工具、测试、CI、报告和兼容策略。普通候选增量不构成架构版本升级。

## 当前版本必须同步的表面

- README.md、SUMMARY.md、llms.txt
- ITERATION.md、AI-HANDOFF.md、AI-START-HERE.md、docs/project-current-state.md
- ARCHITECTURE.md、FOUNDATION.md、docs/foundation/
- docs/PROJECT-ARCHITECTURE.md、USAGE.md、AGENT-GUIDE.md、VERSIONING.md
- data/foundation/、schemas/foundation/
- tools/foundation/、tests/foundation/、formal/、views/
- .github/workflows/、reports/foundation-architecture/
- CHANGELOG.md 与对应审计记录

任何影响项目身份、能力、使用方式、当前状态或 Agent 交接的迭代，必须按 `ITERATION.md` 和 `tools/validate_iteration_sync.py` 同步这些表面；纯修复若不更新，必须记录可验证的 `NO_CHANGE_WITH_REASON`。

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
