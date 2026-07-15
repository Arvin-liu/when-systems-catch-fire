# 版本说明

## 版本阶段

- v0.1：早期函数与案例积累期（历史）。
- v0.2：结构层升级与机器可读化期（历史，见 [v0.2 总结](./v0.2_summary.md)）。
- 2026-07-09 元协议生成层（历史）：12 元协议、64 组合和候选暂存阶段。
- 2026-07-12 数学与逻辑双地基七层架构版本（IGNITION-20260709-076，当前）：建立双地基、七层架构、新权威注册表、legacy 兼容视图、九状态轴与强术语门禁。

架构完成不等于内容证明完成。当前架构允许后续逐对象补源、补定义、补证明、补实验、发现反例或降级，而不再推倒整体架构。

## 什么算版本升级

版本升级必须改变项目本体或权威数据契约，并同步更新入口、架构、schema、工具、测试、CI、报告和兼容策略。普通候选增量不构成架构版本升级。

## 当前版本必须同步的表面

- README.md、SUMMARY.md、llms.txt
- ARCHITECTURE.md、FOUNDATION.md、docs/foundation/
- docs/PROJECT-ARCHITECTURE.md、USAGE.md、AGENT-GUIDE.md、VERSIONING.md
- data/foundation/、schemas/foundation/
- tools/foundation/、tests/foundation/、formal/、views/
- .github/workflows/、reports/foundation-architecture/
- CHANGELOG.md 与对应审计记录

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
