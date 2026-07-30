# 活系统图治理核验（任务 104 · §7）

本文件记录任务 104 对「活系统图」一项的核验结论：仓库现有的系统图是**确定性派生投影**，已有 **CI 门禁**，支持**变更传播**与 **NO_MAP_IMPACT** 分类；任务 104 自身的编辑产出被界定为 NO_MAP_IMPACT，不改动首页系统图。

## 1. 确定性派生投影（已满足）

首页系统图由 `tools/generate_interactive_system_map.py` 从三个受治理源**派生**，不手工编写任何节点身份或关系：

- `data/operations/project-components.json`（构件 registry：节点身份、canonical target、生命周期）
- `data/operations/change-propagation-topology.json`（边的 relation class / domain）
- `data/architecture/interactive-system-map-layout.json`（分组、几何、颜色、顺序）

`build_projection()` 仅做投影：节点来自 registry 中 `map_projection.visible` 的成员，按 layout 的 `node_order` 确定性排序；边来自 topology 中 `map_visible` 的关系。无 set 迭代随机性、无网络依赖。`render_svg()` 在生成前调用 `validate_spec()` 校验 schema / 投影状态 / 权威文件 / 无本地路径泄漏 / L0–L6 层约束 / 边类型化 domain。

## 2. CI 门禁（已满足且已接线）

`generate_interactive_system_map.py --check` 即为门禁：

- 要求 materialized spec 存在且等于重新派生的序列化结果（捕获**陈旧 / 手工编辑**的 spec）；
- 要求 SVG 存在且等于重新渲染的字节（捕获**陈旧 / 手工编辑**的 SVG）；
- 任一不一致即非零退出。

该门禁已接入 `.github/workflows/foundation-validation.yml`：

- 步骤「Validate registry-derived system map」直接执行 `python3 tools/generate_interactive_system_map.py --check`（约第 215–216 行）；
- 工作流 `paths:` 触发器包含 `tools/generate_interactive_system_map.py`、`data/operations/**`、`data/architecture/**`（约第 27、85 行）——凡改动三个受治理源或生成器，必跑此门。

本地核验（本任务分支）：`--check` 通过，输出 `SYSTEM_MAP_DERIVED_OK nodes=49 edges=44`，证明当前提交的系统图为干净派生、非陈旧、非手工编辑。

## 3. 变更传播（已有机制）

`tools/operations/compute_change_propagation.py` 按 `data/operations/change-propagation-topology.json` 计算传播闭包，并产出 `--map-delta`（系统图增量）与 `--residue`（不可容纳残余）。CI 中以 `--check` 对多个治理产物的 era-ref 闭包做复算（foundation-validation.yml 第 174–212 行）。隐藏构件在 `build_projection()` 中必须声明 `represented_by`（可见代表）与 `no_change_reason`（NO_CHANGE 理由），这正是 NO_MAP_IMPACT 的具象化。

## 4. NO_MAP_IMPACT：任务 104 产出的分类

任务 104 在本仓库新增/修改的均为**编辑与语料关系层**产物：

- `docs/editorial/*`（六篇文章、`MANIFEST.md`、`README.md`、`QUALITY-REPORT.md`、`system-map-governance.md`）
- `analysis/corpus-relation/*`（§4 语料关系图、簇候选、源资产简报）
- `tools/extract_cluster_source_brief.py`、`tools/check_editorial_quality.py`

**以上均未修改** `project-components.json`、`change-propagation-topology.json`、`interactive-system-map-layout.json` 三个系统图受治理源，也未修改生成器。因此首页系统图对其**无影响（NO_MAP_IMPACT）**：104 的编辑产出不会触发系统图重生成，也不改变首页地图的节点/边。

同理，104 不向首页系统图**新增编辑/叙事节点**——那样需改动 layout overlay（触发地图重生成）并可能冲击首页两路 SVG（`README` 的 `<object data="./generated/...">` Pages 嵌入路径与 GitHub `<img>` 路径）与 `validate_human_front_door.py` 的校验，且属 §12 明确不授权的「手动编辑系统图输出」。叙事层的导航由 `analysis/corpus-relation/corpus_relation_graph.json`（§4 确定性产物，351 节点 / 259 边 / 15 簇）与本目录的 `README.md`（§6 三分离入口）承担，而非首页架构图。

## 5. 叙事层「活系统图」的确定性

§4 语料关系图 `analysis/corpus-relation/corpus_relation_graph.json` 与 `article_cluster_candidates.json` 由 `tools/build_corpus_relation_graph.py` 确定性生成（stdlib-only、无网络、`sort_keys=True`、节点/边按 key 排序）。本地复算后 `git status` 干净，证明字节级可复现；其变更由 §4 工具自身保证与受治理卡语料一致。它即为叙事/语料层的「活系统图」，与首页架构图各司其职、互不耦合。
