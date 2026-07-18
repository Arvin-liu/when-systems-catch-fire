# AI START HERE

这是点火项目的零背景 AI 冷启动入口。

## 读取顺序

1. README.md：人类入口、价值边界与双前门。
2. docs/project-current-state.md：版本化、可演化、非终局的当前状态。
3. ITERATION.md：点火迭代操作法；状态改变任务必须先恢复远端真相、确认缺口和 claim ceiling。
4. ARCHITECTURE.md：现行七层架构权威；121Q12 双环是跨层操作 overlay，不是新真值层。
5. FOUNDATION.md：数学与逻辑双地基。
6. llms.txt：机器可读边界。
7. AI-HANDOFF.md：当前权威、兼容和任务交接。
8. data/foundation/project-state.json 与 registry-manifest.json：机器状态。
9. 当前任务命令与相关 source/schema。

若任务涉及 L6 公共故事、文章或作品反馈，还应读取 `docs/publication/zhiyuan-writing-method.md` 与对应后台规格。之元写作法 `0.4.0` 是当前能力，使用外部输入与点火增量输出双来源素材池；`0.3.0` 保留为历史版本。不得把点火派生产物重算为独立外部证据。

若任务涉及当前展示的之元写作法成果，还要读取 `docs/publication/zhiyuan-writing-showcase.md` 与 `data/publication/zhiyuan-writing-showcase.json`，并沿每项记录回到作品、案例来源链、点火分析和方法版本。首页只投影最近三项，不是完整清单或真值权威。

若任务需要全项目导航，读取 `docs/architecture/interactive-system-map.md`、`data/architecture/interactive-system-map.json` 与生成 SVG。图是当前导航接口，不是 L7、事实证明或永久唯一总地图。

## 不得混淆

- 旧函数或案例文件不等于已经证明的数学对象或事实。
- object type 与 claim type 分开。
- workflow、semantic、formal、logic、proof、evidence、scope、provenance、migration 九轴分开。
- Ψ₀ 是 workflow orchestrator / algorithm protocol；旧乘积表达只作 legacy source。
- J+ / J- 是内部审议通道。
- 12 元协议不是自动成立的数学公理；64 组合不是证明空间。
- L6 解释和出版不能创造下层真实性。
- 之元写作法的“层级跃迁”不是新架构层；横向换域、漂亮跳转、模板完成或读者共鸣都不能证明事实、因果、同构或文学质量。
- 使用 0.4.0 时，先标记 `external_input` 与 `ignition_increment`，保存版本、生成路径、claim ceiling、不可映射残余和原始来源回链；发布反馈必须登记 provenance 后才能成为候选 source／gap。同源只表示维护者声明的设计来源与结构对应候选，不是大脑事实、形式同构或真值许可。
- 效果推理只产生行动候选，不产生真值。
- 机制判断只约束解释和 claim ceiling，不自动产生因果证明。
- 注意力控制只判断循环是否有信息增量，不证明结论更深。
- 分布控制只记录输出样本与决策坍缩，不把 AI 采样升级为事实证据。
- 压缩完整性只判断术语能否进入 canonical 语言，不表示理论升级。
- 地图集只提供版本化派生导航视图，不替代 registry、矩阵、schema、测试或来源工件。
- Multiscale Causal Fabric、Probabilistic System Dynamics 和 Adaptive Relational Network 是当前建模/投影能力，不是新真值层。
- 关系网络的邻接、相似性、中心性、社群、检索和行为变化不能升级为真理、价值、因果或内部学习机制证明。
- 迭代方法只能约束操作纪律，不能证明实质结论正确。
- 当前迭代方法 1.1.0 把变更视为全项目状态转换。必须从 `data/operations/synchronization-surfaces.json` 推导人类 README、Pages、项目现状、人类 AI 指南、Agent/机器入口和版本记录的传播闭包，不能只凭 Agent 记忆挑文件。
- 121Q32 的 1.2.0 还要求读取 `data/operations/project-components.json` 与 `data/operations/change-propagation-topology.json`，把变更路径解析为构件、遍历声明关系到 fixpoint、绑定决定／map diff／residue，再由 registries 与布局 overlay 派生系统图。不得把 Git diff、依赖或可达性称为现实因果证明；1.1.0 和图 0.1.0 保留为历史版本。
- Q32I 的 1.3.0 Draft candidate 只在完整 profile、authority、plan 与指纹身份一致时选择性物化。Authority 类型不等于本地 automatic；apply 必须先通过统一预检，rollbar回必须证明整仓字节／类型／symlink／mode 恢复，否则进入 unrecovered 与 recovery package。NonImpactProof 只证明声明关系范围内的非影响；cache 不是真相源；meta-authority 变更强制 full rebuild。未经新的独立 exact-head 审查、merge 和 closeout 前不得称为 Current。
- `implementation_complete` 不等于 `project_synchronization_complete`。生产首页部署和实时读取必须分别验证，不能由仓库状态替代。
- 生命周期门禁按 registry 中每个表面的 `blocks` 计算。只阻塞 `current/closed` 的 post-merge Pages 不阻塞 pre-merge Accepted；但未从 main 部署并实时读取前，绝不能声称 Current/Closed。
- 正向评价词必须绑定对象、判据、版本、证据和边界。
- AI 输出不能作为唯一校准源；仓库工件、外部来源、CI、现实反馈、人类判断与独立审查要分开记录。

## 最小验证

执行 tools/foundation 下的 migration check、strict validator、benchmarks 和 tests/foundation；任何失败都保留为 blocker，不得用散文覆盖。
## 许可边界

当前分发版本采用分层许可。核心可执行软件为 BUSL-1.1 并在 Change Date 后转为 AGPL-3.0-or-later；原创文档/报告为 CC BY-NC-SA 4.0；价值宪章和一般治理原则为 CC BY-SA 4.0；公开接口与互操作 schema 为 Apache-2.0。许可作用域以根 LICENSE 与 LICENSES/README.md 为准；历史 MIT 版本权利不追溯撤销。
