# 点火完整可点击系统图

Status: `0.2.0 Current registry-derived navigation interface`; `0.3.0` is the Q32I Draft candidate projection.

本页说明点火完整系统图的权威来源、生成方式、双表面行为和解释边界。它是当前仓库的导航接口，不是第二份项目真相表、永久唯一总地图、因果图、严格同构证明或理论完备性证明。

## 打开交互版

- [Pages 完整交互版](https://arvin-liu.github.io/when-systems-catch-fire/system-map.html)
- [生成的 SVG](../../pages/generated/ignition-system-map.svg)
- [机器可读 spec](../../data/architecture/interactive-system-map.json)

## Current 与候选权威生成链

Current 0.2.0 established this authority chain; the 0.3.0 Draft candidate preserves it while projecting incremental-execution lifecycle metadata:

`project component registry + typed propagation topology + layout overlay → deterministic generator → materialized spec + SVG → README / Pages`

`data/architecture/interactive-system-map.json` therefore becomes a generated inspection artifact, not a second manual truth. Node identity, canonical target and lifecycle status derive from `data/operations/project-components.json`; relation class/domain derive from `data/operations/change-propagation-topology.json`; only grouping, geometry, color and order remain in `data/architecture/interactive-system-map-layout.json`.

Do not manually edit the materialized spec or SVG. Regenerate and check both:

```bash
python3 tools/generate_interactive_system_map.py
python3 tools/generate_interactive_system_map.py --check
```

验证要求 additionally include projection freshness against all three authorities and coverage of the current propagation closure's map impact. The Q32I projection remains 9 groups, 41 nodes, 37 visible edges and L0–L6. `incremental_execution` is deliberately hidden and represented by the existing iteration node with a machine-checkable reason, rather than adding a decorative architecture node.

## GitHub README 与 Pages

- Pages 首页使用 `<object>` 嵌入 SVG，因此节点自身可点击；独立 `system-map.html` 是完整交互版 canonical surface。
- GitHub README 可能过滤或限制嵌入对象。README 因此保留同一完整 SVG 预览，并提供明确的“打开交互版完整图”入口；不声称 GitHub 图片预览中的节点热点一定可用。
- 两个表面使用同一个生成 SVG，不维护第二张人工图。

## 解释边界

- cluster 只表达导航分组，不增加架构层。
- 边表示导航、来源、操作或受约束的信息流；除非目标文档另有证据，不表示经验因果。
- 图中的 L0—L6、Foundation、Function OS、MCF、PSD、ARN、Q12—Q14、迭代、Charter、之元写作法与反馈环仍服从各自 canonical 文档。
- “完整”只指本轮 spec 覆盖当前要求的系统构件，不表示点火理论已完整、所有现实机制已识别或未来无需修订。
- The map's `repository_dependency`, `synchronization_obligation` and `substantive_causal_candidate` domains have different authority. A typed edge or computed map delta is not real-world causal proof.
