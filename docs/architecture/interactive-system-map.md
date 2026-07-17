# 点火完整可点击系统图

Status: `121Q31_DRAFT_CANDIDATE_INTERFACE`

本页说明点火完整系统图的权威来源、生成方式、双表面行为和解释边界。它是当前仓库的导航接口，不是第二份项目真相表、永久唯一总地图、因果图、严格同构证明或理论完备性证明。

## 打开交互版

- [Pages 完整交互版](https://arvin-liu.github.io/when-systems-catch-fire/system-map.html)（Draft 阶段由精确 HEAD Pages artifact 验证；合并后才进入生产地址）
- [生成的 SVG](../../pages/generated/ignition-system-map.svg)
- [机器可读 spec](../../data/architecture/interactive-system-map.json)

## 单一权威生成链

`data/architecture/interactive-system-map.json → tools/generate_interactive_system_map.py → pages/generated/ignition-system-map.svg`

JSON spec 是节点、分组、目标与关系的机器权威。每个节点至少保存 `id / label / group / target / description`；生成器从分组位置和节点顺序计算布局，并把 canonical 仓库目标写入 SVG 超链接。不得手工修改生成 SVG；修改 spec 后重新运行：

```bash
python3 tools/generate_interactive_system_map.py
python3 tools/generate_interactive_system_map.py --check
```

验证要求：节点 ID 与分组唯一；target 存在；链接闭合；生成文件无漂移；L0—L6 恰为七层且不存在 L7；README 中图位于价值宪章之后、使用指南之前；Pages artifact 必须包含独立页面和 SVG；公开资产不得含本机路径。

## GitHub README 与 Pages

- Pages 首页使用 `<object>` 嵌入 SVG，因此节点自身可点击；独立 `system-map.html` 是完整交互版 canonical surface。
- GitHub README 可能过滤或限制嵌入对象。README 因此保留同一完整 SVG 预览，并提供明确的“打开交互版完整图”入口；不声称 GitHub 图片预览中的节点热点一定可用。
- 两个表面使用同一个生成 SVG，不维护第二张人工图。

## 解释边界

- cluster 只表达导航分组，不增加架构层。
- 边表示导航、来源、操作或受约束的信息流；除非目标文档另有证据，不表示经验因果。
- 图中的 L0—L6、Foundation、Function OS、MCF、PSD、ARN、Q12—Q14、迭代、Charter、之元写作法与反馈环仍服从各自 canonical 文档。
- “完整”只指本轮 spec 覆盖当前要求的系统构件，不表示点火理论已完整、所有现实机制已识别或未来无需修订。
