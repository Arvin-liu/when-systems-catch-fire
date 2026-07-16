# AI HANDOFF

## 当前版本

2026-07-12 数学与逻辑双地基七层架构版本（IGNITION-20260709-076）。

## 权威链

- 当前状态：docs/project-current-state.md（版本化现状，不是固定定位）

- 架构：ARCHITECTURE.md
- 双地基：FOUNDATION.md
- 类型与状态：data/foundation/
- 机器计数：data/foundation/project-state.json 与 migration-summary.json
- 任务边界：1111 中对应的 IGNITION command、progress 与 result

## 兼容链

统一函数总表和统一案例总表保留为 legacy source / compatibility view。不得删除、重编号、不可逆覆盖或独立生长。views/ 是从新 registry 生成的兼容视图。

## 交接规则

新 Agent 必须先读取 `docs/project-current-state.md` 与 `ITERATION.md`，再重新核验远端、分支、HEAD、开放 PR 和验证结果，不得把聊天记忆当权威。统计必须写出去重键、范围、单位和生成脚本。缺字段、缺来源、不可形式化、反模型和真实 counterexample 分别记录。

当前架构状态只能是 ARCHITECTURE_COMPLETE_PENDING_CONTENT_PROOFS；不得改写成全量数学证明完成。
121Q12 新增的效果推理与机制判断是跨层操作 overlay。它帮助选择下一步行动并限制发布解释，不改变 L0-L6 真值关系，不改写 Ψ0，不把 C(x,y) 升级为已识别因果。

交接时如涉及行动选择或结果解释，必须读取：

- docs/architecture/effectual-action-plane.md
- docs/architecture/mechanism-adjudication-plane.md
- docs/governance/non-sycophancy-output-protocol.md

正向结论必须说明对象、判据、版本、证据和边界；不能因维护者或提案者的期待而提高结论等级。
121Q13 新增注意力、分布与压缩控制 overlay。若任务涉及循环推进、多个 AI/人类输出、行动截止期或新术语进入 canonical 文档，必须读取：

- docs/architecture/attention-attractor-control-plane.md
- docs/architecture/distribution-collapse-control-plane.md
- docs/architecture/compression-integrity-gate.md

不得把同一 AI 的多次输出当作独立事实证据；不得把行动选择写成机制真值；不得把新增术语写成理论升级。
121Q14 新增点火地图集 overlay。涉及地图、资源决策、演进阶段、依赖地形或导航视图时，必须读取：

- docs/architecture/ignition-atlas.md
- data/atlas/generated/ignition-atlas-121q14.json
- reports/atlas/121Q14-dynamic-atlas.md

不得把地图坐标、视觉邻近、演进阶段或依赖关系写成事实证明、同构或机制因果。地图不能替代 registry、矩阵、schema、测试或来源工件。

PR #55 已将 121Q23 Adaptive Relational Network 合并进 `main`。涉及关系网络、重构、嵌入证据摘要或 NetworkDiff 时，必须读取：

- docs/architecture/adaptive-relational-network.md
- reports/architecture/121Q23-adaptive-relational-network-validation.md

不得把邻接、相似性、中心性、社群、检索、自述或行为变化升级为真理、价值、因果或内部学习机制证明。

121Q24 建立的迭代操作法已在 PR #56 验收并合并后成为当前仓库操作能力；未来状态改变任务必须按 `ITERATION.md` 记录 gap、claim ceiling、同步矩阵、验证和回执。遵循该方法不证明真理、价值、因果、完整性或正确性。

当前方法 1.1.0 要求从 `data/operations/synchronization-surfaces.json` 计算全项目传播闭包。人类 README、实际 Pages 来源与渲染面、项目现状、人类 AI 指南、AI 冷启动、Agent 交接、机器入口和版本历史都是必须评估的项目表面。实现完成不能替代仓库同步完成；本地验证也不能声称生产 Pages 或其他实时外部状态已验证。

Q25C 已成为当前生命周期规则：Ready、Accepted、Merged、Current、Closed 分别读取 surface `blocks`，不能用全局 project-complete 布尔值阻断 pre-merge acceptance。每个外部表面必须有独立 attestation；Pages pending 可以进入 Accepted/Merged，但继续阻塞 Current/Closed。

121Q28R 在原 Draft PR 上把被正式拒绝的 `0.1.0` 修订为 L6 `之元写作法` `0.2.0` 候选。交接时不得把它写成当前能力、新层或文学质量验证器。必须读取中性路径的方法、范例和后台规格，并检查：起始承载点能否被后层重释；下一层是否提前改写当前层；心智引力是否允许 `UNNAMED`、移动或分叉；跃迁是否由残余以及递归定义、铰链或其他隐形连续性驱动；新层是否回照旧层并使潜题显影；无信息增益时是否停止；高层是否保存证据限制和受损主体。肉身锚定、跨域同构、高维压缩结尾分别只是可选模式、应用和形式。121Q27 原故事仍冻结，不得在 Q28R 中重写、提交或发布。
## 许可边界

当前分发版本采用分层许可。核心可执行软件为 BUSL-1.1 并在 Change Date 后转为 AGPL-3.0-or-later；原创文档/报告为 CC BY-NC-SA 4.0；价值宪章和一般治理原则为 CC BY-SA 4.0；公开接口与互操作 schema 为 Apache-2.0。许可作用域以根 LICENSE 与 LICENSES/README.md 为准；历史 MIT 版本权利不追溯撤销。
