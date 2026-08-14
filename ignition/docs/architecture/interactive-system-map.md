# 点火仓库原生系统图

状态：`0.5.0 Current registry-derived navigation projection`；`0.4.0` 与更早版本为 Historical。

## 打开与生成

- [仓库内完整 SVG](../generated/ignition-system-map.svg)
- [机器可读投影](../../data/architecture/interactive-system-map.json)
- [构件 registry](../../data/operations/project-components.json)
- [类型化传播 topology](../../data/operations/change-propagation-topology.json)
- [布局 overlay](../../data/architecture/interactive-system-map-layout.json)

生成链：

`project component registry + typed propagation topology + layout overlay → deterministic generator → materialized spec + repository SVG → .github/README.md / ordinary Markdown navigation`

不要手改 materialized spec 或 SVG：

```bash
python3 tools/generate_interactive_system_map.py
python3 tools/generate_interactive_system_map.py --check
```

SVG 现在位于 `docs/generated/ignition-system-map.svg`，通过 README 和普通 Markdown 直接访问，不依赖独立部署站点。SVG 节点链接指向 GitHub 仓库 canonical 文件；若客户端不支持 SVG 内部热点，可使用本页的文本入口。

## 权威与边界

- 节点身份、canonical target 与生命周期来自 component registry。
- 边的 relation class/domain 来自 propagation topology。
- 分组、几何、颜色和顺序来自 layout overlay。
- cluster 只表达导航分组，不增加架构层。
- `language_thought` 是横穿 L0—L6 的控制平面 overlay；`layers` 组仍严格只有 L0—L6。它与各层的连线表示框架审计和同步义务，不表示语言决定现实因果。
- `repository_dependency`、`synchronization_obligation` 和 `substantive_causal_candidate` 权限不同。
- 图的边、可达性、视觉邻近或 map delta 不证明经验因果、严格同构或理论完整性。
- “完整”只指当前声明构件的投影覆盖；未来发现缺口时必须更新 registry，而不是把图当永久总图。

本轮退役了独立阅读站及其专用工作流。旧部署工件和验证记录继续保留在 Git 历史与历史报告中，仅作历史证据。
