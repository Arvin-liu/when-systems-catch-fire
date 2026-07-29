# 使用说明

## 1. 从哪里进入

先从[统一知识入口](../KNOWLEDGE/README.md)按最近变化、主题、搜索或阅读时长找到对象，再读 [README.md](../README.md)、[ARCHITECTURE.md](../ARCHITECTURE.md) 与 [FOUNDATION.md](../FOUNDATION.md)。当前机器状态见 [project-state.json](../data/foundation/project-state.json)。

不知道术语或编号时，使用[知识地图](../KNOWLEDGE/MAP.md)；知道旧称或自然语言词时，使用[搜索与交叉引用](../KNOWLEDGE/SEARCH.md)；要快速判断长文是否值得继续读，使用[分层阅读](../KNOWLEDGE/READING-LAYERS.md)。摘要和搜索只用于导航，最终判断仍回到完整来源与 canonical registry。

## 2. 按七层处理材料

1. L0：登记来源、版本、原始材料和冲突。
2. L1：写受控语义命题，声明主体、对象、条件、量词、范围和失败条件。
3. L2：分别选择 formal_object_type 与 claim_type；不能把所有材料都包装成 FUNCTION。
4. L3：写 Premises + Declared Rules -> Conclusion，并记录隐藏前提、反模型或 NOT_ASSESSED。
5. L4：建立数学模型、proof obligation 与 proof artifact；缺失内容保持 pending。
6. L5：分别验证 formal、logic、proof、evidence、scope 和 provenance。
7. L6：写解释、故事、文章或前端，并回链 L0-L5；不得制造新的数学真实性。

无法无损形式化时，使用 NATURAL_LANGUAGE_CANDIDATE 或 ARGUMENT_SCHEMA，并写明原因。

### L6 当前公共表达与反馈接口：之元写作法

之元写作法 [`0.4.0`](./publication/zhiyuan-writing-method.md) 是当前 L6 接口，[后台规格](../templates/publication/zhiyuan-writing-spec.md)使用双来源素材池；`0.3.0` 保留为历史已合并版本。先把材料标为 `external_input` 或 `ignition_increment`：外部输入保存作者、时间、渠道、版权与核验状态；点火增量保存 canonical 路径／ID、生成任务、版本、claim ceiling、gap／residue 及其原始来源回链。点火分析、Q12—Q14、MCF／PSD／ARN 投影和 provenance-gated 返回项都可继续写作，但不能被重算为独立外部证据。

需要查看当前已接受应用时，进入[之元写作法成果索引](./publication/zhiyuan-writing-showcase.md)。每项成果必须同时回链正式作品、起始案例来源记录、点火分析和方法版本；原始材料受版权或隐私限制时，只公开来源记录，不复制全文。README 只展示 registry 中最近三项，完整索引才是人类成果入口。

需要从整体结构定位入口时，打开[完整可点击系统图](./architecture/interactive-system-map.md)。图只用于导航；视觉邻近、连线和 cluster 不自动表示因果、同构、真值或新增架构层。

## 3. 宪章体系怎样进入使用过程

价值宪章与 Charter System R1 约束“什么值得做”，但不冒充事实证据或数学证明，也不在首页展示阶段快照。其边界须作为前门同步义务进入使用过程：

- 阅读 [生命共同体价值宪章](./governance/life-community-value-charter.md) 与 [Charter System R1 治理系统](./governance/charter-system-r1.md)，理解 activated=false / UNPUBLISHED 边界：治理系统已就位并 Current，尚未激活任何能力、运行时或执行器，也未发布快照。
- 任何使用、写作或协作不得把宪章条款当作已证明事实，也不得在首页或阶段快照之外反推能力已经生效。
- 宪章门控的变更先经 charter → charter_system_r1 → iteration 同步链评估；独立同步任务核验并合并前，提案仍只是请求。

## 4. 变更怎样传播、执行与记录阶段

点火把一次变更拆成可审计的传播、执行与阶段记录三步，不提升生命周期、不制造新的真值层：

- **传播：** 从 `data/operations/propagation/<task>-request.json` 登记 changed paths、seed components、dimensions 与 classifications，再运行 `tools/operations/compute_change_propagation.py` 生成 closure、impact report、map delta 与 residue。只有 closure 达到 fixpoint、每个 required component/surface 有决定、map 投影匹配且 residue 为空，才能进入候选 Ready。
- **执行：** 当前能力从真实 change request 运行 `plan_incremental_execution.py`，再由 `run_incremental_execution.py` 在统一 authority preflight 通过后，只执行显式标记 automatic 的 profile 结构化 argv。Execution 与 validation capability 分开登记；失败只有整仓字节、类型、symlink 与适用 mode 完全一致才报 `restored`。
- **阶段记录：** 阶段快照来自 `data/operations/stage-snapshots.json` 的确定性投影，沿 lifecycle 与 publication 两条轴记录 Accepted、Current、Activated、正式能力影响与应用许可五个显式布尔量；完整制度见 `docs/operations/stage-snapshot-publication.md`。该模块仅在注册表与历史中保留，不在首页展示。

`NO_CHANGE_WITH_REASON` 允许纯历史修字不触发无关全仓更新；新增正式构件则必须进入系统图，或提供 validator 可检查的 hidden representation 与理由。这里计算的是声明关系下的仓库／治理传播，不是现实因果。

向外表达时保存来源、不可映射残余与受损主体；发布或试读后，记录误解、反例、遗漏主体、失败跃迁与伪压缩的 provenance。只有经登记和范围审查的反馈才能成为候选 source／gap，再交回适用的 Q12、Q13、MCF、PSD、ARN、Atlas 或迭代流程。点赞、赞美、传播与多 AI 共识只能是体验／传播数据。

横向增加领域不等于纵向升层。下一层若只换词、重复同级案例或制造宏大感，应停止。任何写作感染力、模板完成或机器检查都不能提高 L0-L5 的事实、因果、同构、证明或价值状态。

## 5. 使用 12 元协议与 64 组合

12 元协议可作规范、启发与治理坐标；64 组合可作设计与生成空间。它们不是数学公理、证明空间或现实全枚举。

- [12 个元协议](./meta-protocols/12-meta-protocols.md)
- [64 组合矩阵](./meta-protocols/meta-protocol-64-combination-matrix.md)

## 6. 查阅权威与 legacy 兼容视图

先查 data/foundation 注册表和 project-state。统一函数总表、统一案例总表及 views 仅用于历史追溯和兼容展示，不代表内容已经证明或外部验证。

## 7. 提交候选

候选首先分成对象、命题、论证、来源与证据。book candidate 保留 BC 临时 ID，不分配 C ID。pending claim 保留 PEND ID；多种文件表示按同一 ID 合并，不重复计数。

非函数型定理、规律、机制、因果、不可能性、跨域对应、预测、经验与本体断言必须先按[未来断言准入协议](./foundation/future-claim-admission-protocol.md)进入 task-100 registry，提交原子命题、来源、十三门、证据谱系、依赖、M/E、复现状态、处置与公共上限。自动发现、登记闭合或 quarantine 均不表示内容已证明或已获得外部验证。

## 8. 理解状态与旧断言等级

workflow、semantic、formal、logic、proof、evidence、scope、provenance、migration 九轴独立，任何一轴不推出另一轴。

docs/claim_levels.md 中的历史 L0-L5 是 legacy claim_level / assertion_grade，不是新 architecture_layer L0-L6。引用时必须写明字段，禁止裸用 L0-L5 造成混淆。

## 9. 避免误用

- 点火不是万能证明器；只有有可检查工件的具体命题才可获得相应 proof 状态。
- 单案例不能证明普遍定理。
- 数值采样、符号化简和有限模型都有后端范围。
- 缺字段、缺来源、不可形式化和真实反例是不同状态。
- 解释与出版内容必须回指下层证据和验证。
- 抽象升层不得删除肉身成本、具体受损主体、不可映射差异或 Charter Gate 边界。
## 许可边界

当前分发版本采用分层许可。核心可执行软件为 BUSL-1.1 并在 Change Date 后转为 AGPL-3.0-or-later；原创文档/报告为 CC BY-NC-SA 4.0；价值宪章和一般治理原则为 CC BY-SA 4.0；公开接口与互操作 schema 为 Apache-2.0。许可作用域以根 LICENSE 与 LICENSES/README.md 为准；历史 MIT 版本权利不追溯撤销。
