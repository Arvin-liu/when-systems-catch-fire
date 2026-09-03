# 活系统图治理核验（任务 104 · §7）

本文件记录任务 104 对「活系统图」一项的核验结论：仓库的机器可读系统图是**确定性派生投影**，已有 **CI 门禁**，支持**变更传播**与 **NO_MAP_IMPACT** 分类；Task151 只把 Task150 已验证的 standalone derived visualization 投影到稳定首页路径，并没有改动 canonical architecture、机器投影、Agent Reach 或 live external invocation。

## 1. 确定性派生投影（已满足）

机器可读系统图由 `tools/generate_interactive_system_map.py` 从三个受治理源**派生**，不手工编写任何节点身份或关系：

- `data/operations/project-components.json`（构件 registry：节点身份、canonical target、生命周期）
- `data/operations/change-propagation-topology.json`（边的 relation class / domain）
- `data/architecture/interactive-system-map-layout.json`（分组、几何、颜色、顺序）

`build_projection()` 仅做投影：节点来自 registry 中 `map_projection.visible` 的成员，按 layout 的 `node_order` 确定性排序；边来自 topology 中 `map_visible` 的关系。无 set 迭代随机性、无网络依赖。`render_svg()` 在生成前调用 `validate_spec()` 校验 schema / 投影状态 / 权威文件 / 无本地路径泄漏 / L0—L6 层约束 / 边类型化 domain。

首页稳定 SVG/HTML 则复用 Task150 已验证的 standalone 派生证据，并由 `tools/validate_homepage_architecture_projection.py` 将 canonical authored source 的摘要、Task150 Step21/29 证据摘要和稳定输出字节绑定在一起。该门禁只允许 exact verified bytes 通过；source digest 漂移时必须重新生成或 fail closed。

## 2. CI 门禁（已满足且已接线）

机器投影的 `generate_interactive_system_map.py --check` 与首页投影的 `validate_homepage_architecture_projection.py --check` 共同构成门禁：

- 要求 materialized spec 存在且等于重新派生的序列化结果（捕获**陈旧 / 手工编辑**的 spec）；
- 对 registry-derived SVG，要求输出等于重新渲染的字节（捕获**陈旧 / 手工编辑**的机器投影）；
- 对首页 SVG/HTML，要求 canonical-source digest、Task150 verified artifact digest、跨格式嵌入内容和 README 稳定路径全部一致；
- 任一不一致即非零退出。

该门禁已接入 `.github/workflows/foundation-validation.yml`：

- 步骤「Validate registry-derived system map」直接执行 `python3 tools/generate_interactive_system_map.py --check`，随后执行首页 provenance 门禁 `python3 tools/validate_homepage_architecture_projection.py --check`；
- 工作流 `paths:` 触发器包含 `tools/generate_interactive_system_map.py`、`data/operations/**`、`data/architecture/**`（约第 27、85 行）——凡改动三个受治理源或生成器，必跑此门。

本地核验需同时通过两项：机器投影输出 `SYSTEM_MAP_DERIVED_OK`（节点/边数由当前 registry projection 报告），首页投影输出 `HOMEPAGE_ARCHITECTURE_PROJECTION_OK`，后者还必须报告 `homepage_display_verified=true`，证明 README 实际引用的是新版稳定 SVG，而不是仅证明某个文件存在。

## 3. 变更传播（已有机制）

`tools/operations/compute_change_propagation.py` 按 `data/operations/change-propagation-topology.json` 计算传播闭包，并产出 `--map-delta`（系统图增量）与 `--residue`（不可容纳残余）。CI 中以 `--check` 对多个治理产物的 era-ref 闭包做复算（foundation-validation.yml 第 174–212 行）。隐藏构件在 `build_projection()` 中必须声明 `represented_by`（可见代表）与 `no_change_reason`（NO_CHANGE 理由），这正是 NO_MAP_IMPACT 的具象化。

## 4. NO_MAP_IMPACT：任务 104 产出的分类

任务 104 在本仓库新增/修改的均为**编辑与语料关系层**产物：

- `docs/editorial/*`（六篇文章、`MANIFEST.md`、`README.md`、`QUALITY-REPORT.md`、`system-map-governance.md`）
- `analysis/corpus-relation/*`（§4 语料关系图、簇候选、源资产简报）
- `tools/extract_cluster_source_brief.py`、`tools/check_editorial_quality.py`

**以上均未修改** `project-components.json`、`change-propagation-topology.json`、`interactive-system-map-layout.json` 三个系统图受治理源，也未修改生成器。因此首页系统图对其**无影响（NO_MAP_IMPACT）**：104 的编辑产出不会触发系统图重生成，也不改变首页地图的节点/边。

同理，104 不向首页系统图**新增编辑/叙事节点**——那样需改动 layout overlay（触发机器投影重生成）并可能冲击首页稳定 SVG/HTML 与 `validate_human_front_door.py` 的校验，且属 §12 明确不授权的「手动编辑系统图输出」。叙事层的导航由 `analysis/corpus-relation/corpus_relation_graph.json`（§4 确定性产物，351 节点 / 259 边 / 15 簇）与本目录的 `README.md`（§6 三分离入口）承担，而非首页架构图。

## 5. 叙事层「活系统图」的确定性

§4 语料关系图 `analysis/corpus-relation/corpus_relation_graph.json` 与 `article_cluster_candidates.json` 由 `tools/build_corpus_relation_graph.py` 确定性生成（stdlib-only、无网络、`sort_keys=True`、节点/边按 key 排序）。本地复算后 `git status` 干净，证明字节级可复现；其变更由 §4 工具自身保证与受治理卡语料一致。它即为叙事/语料层的「活系统图」，与首页架构图各司其职、互不耦合。

## 6. 任务 105 的系统图影响分类（NO_MAP_IMPACT）

任务 105 在本仓库新增/修改的均为**基准证据层与编辑叙事层**产物，以及一个 Function OS 内部实现缺陷的有界修复：

- `function-os-candidate/v0.2/benchmark/*`（预注册、语料、oracle、RESULTS、PREREGISTRATION）——基准证据层；
- `docs/editorial/articles/007-*`、`docs/editorial/MANIFEST.md`、`docs/editorial/README.md`——编辑叙事层（类比 104 的 NO_MAP_IMPACT 产出，不向首页系统图新增编辑/叙事节点）；
- `function-os-candidate/v0.2/function_os/n2_representation.py`（N2 嵌套相等提取缺陷的有界修复，`split('==')` → `split('==',1)`）与回归测试——Function OS 现有 N2 构件的**内部实现变更**，未新增/移除节点身份，未改动 `project-components.json` 的 `canonical target` 或 `map_projection`，未改动 `change-propagation-topology.json` / `interactive-system-map-layout.json`，也未改动生成器。

以上均未触碰系统图三个受治理源与生成器，因此首页系统图对其**无影响（NO_MAP_IMPACT）**：105 不触发系统图重生成，也不改变首页地图的节点/边。

**渲染复核证据**：在当前任务分支 HEAD 运行 `python3 tools/generate_interactive_system_map.py --check`，输出 `SYSTEM_MAP_DERIVED_OK`，退出码 0——证明当前提交的系统图为干净派生、非陈旧、非手工编辑，与 104 结论一致。
