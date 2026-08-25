# 点火仓库原生系统图

状态：`0.14.0 Current registry-derived navigation projection`；`0.13.0`、`0.12.0`、`0.11.0`、`0.10.0`、`0.9.0`、`0.8.0`、`0.7.0`、`0.6.0`、`0.5.0`、`0.4.0` 与更早版本为 Historical。

## 打开与生成

- [仓库内唯一完整可点击 SVG](../generated/ignition-system-architecture.svg)
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

SVG 现在位于 `docs/generated/ignition-system-architecture.svg`，通过 README 和普通 Markdown 直接访问，不依赖独立部署站点。SVG 节点链接指向 GitHub 仓库 canonical 文件；若客户端不支持 SVG 内部热点，可使用本页的文本入口。它是当前唯一完整总架构图，不再并列维护另一张图。

## 权威与边界

- 节点身份、canonical target 与生命周期来自 component registry。
- 边的 relation class/domain 来自 propagation topology。
- 分组、几何、颜色和顺序来自 layout overlay。
- 当前语义主干是一个有界阅读路径：`Owner / Value Charter → Ignition OS control / governance spine → Pack / Federation routing → External replaceable executors → Actions / observations / receipts → Validation / provenance / state update / feedback → OS`。中央 OS control spine 现在包含 Event Ledger、Steering / Intent / Goal / Obligation R1、monotonic policy、resource arbitration、bounded scheduler、health lease、queue/backpressure、durable dispatch/reconciliation、concurrent operational memory、Durability / Lifecycle R3 和 Driver Console。Steering 记录来源权威、Goal lifecycle、独立 completion contract、obligation、priority、arbitration、why-next 与 drift；它不推断 Owner intent 或 completion。Durability / Lifecycle 负责 snapshot、migration、namespace、Pack lifecycle、revocation、accounting、recovery 与 DR continuity，uncertain external dispatch 只到 reconciliation；它不是第二张图或第二真相源。这里的 external executors 是 replaceable executors，不是 OS authority；Reference / Conformance / Fallback 是本地冻结边界；它是导航阅读顺序，不新增因果边，也不证明完整性。
- `os_spine` 位于图的中央列；`federation` 明确标为外部、可替换手脚；`domain_packs` 单列表示 Domain/Skill Pack，不把 Knowledge 重新画成系统本体。
- cluster 只表达导航分组，不增加架构层。
- Task 136 将 Live External Executor Bridge R1 单列为 Federation 下的 OS-owned 节点：它负责 bounded envelope、capability lease、transport、receipt、timeout/cancel、reconciliation 与独立验证，不拥有 provider、channel、browser、remote Git、配置、billing 或 completion authority。
- Task 140 将 Live Observation / Reconciliation Plane 注册为当前 OS 架构节点：它把 probe、transport、live process、durable capture、structured result、validator 和 append-only reconciliation event overlay 保持为可区分的 typed outcomes；事件闭合仍不等于成功，未知 external effect 仍不得升级为 validated completion。
- `language_thought` 是横穿 L0—L6 的控制平面 overlay；`structural_governance_surface` 是 governance 组中的 advisory cross-cutting overlay；`layers` 组仍严格只有 L0—L6。两者的连线表示框架审计、同步义务或候选阅读关系，不表示语言或结构决定现实因果。
- `repository_dependency`、`synchronization_obligation` 和 `substantive_causal_candidate` 权限不同。
- `os_spine`、`federation` 与 `domain_packs` 三个 overlay 分别表达 Owner/Human、Generic Kernel/Runtime/Memory，External Agent Federation/adapter，以及可加载 Domain/Skill Pack 的边界；`Structural Governance Surface` 只表达 advisory reading/experiment context，不增加 L7。`Kernel ≠ Knowledge`，`Runtime ≠ Research`，`OS ≠ executor`，soft context ≠ permission。
- 图的边、可达性、视觉邻近或 map delta 不证明经验因果、严格同构或理论完整性。
- “完整”只指当前声明构件的投影覆盖；未来发现缺口时必须更新 registry，而不是把图当永久总图。

## Agent Platform R2 在图中的位置

R2 把 Generic Kernel、Agent Runtime、Profile、Reasoner Gateway、Supervisor、
OS Control Plane 与 Operational Memory 放入中央 `os_spine`；External Agent Federation 与 adapter
位于 `federation`；四个 Domain Pack 位于 `domain_packs`。这三个当前 overlay
共同表达 OS/driver、外部可替换 executors 与可加载 Pack 的边界，不新增 L7，也不
替代 L0—L6、Foundation、claim/evidence registry 或 Human Surface。Knowledge、
REOS LIGHT Research、之元 Writing 和 Maintenance 仍由各自 manifest 声明能力、
对象类型、validator 与禁止的 authority upgrade。

当前机器投影的 registry、可见节点、typed edges 和隐藏 components 计数以
`current-facts.json` 为准；当前地图为 `0.13.0`，上一版 `0.12.0`、更早版 `0.11.0` 仅作 Historical。
Structural Governance Surface 的可见关系仍是 advisory repository projection。
R2 的 source-domain 与
blast-radius 规则见
[`agent-platform-r2-propagation-contract.json`](../../data/operations/propagation/agent-platform-r2-propagation-contract.json)。
联邦 source domain 单独落在 `agent_platform.federation`，不直接生成 Knowledge、
Writing、Human front-door 或 Pack registry。上述数字是仓库导航与生成器覆盖计数，
不是现实系统规模、因果图或能力证明。

本轮退役了独立阅读站及其专用工作流。旧部署工件和验证记录继续保留在 Git 历史与历史报告中，仅作历史证据。

## Steering / Intent / Goal / Obligation R1

`steering_intent_obligation_r1` 是 `os_spine` 中的一个可点击节点，指向
[`os-steering-intent-r1.md`](./os-steering-intent-r1.md)。它与 Driver Console R3、
Durability / Lifecycle、Event Ledger 和 Federation Intent Capsule 形成仓库依赖与同步义务
投影；连线不表示现实因果。`PASS` Run 不能推断 Goal completion，系统 proposal 不能成为
Owner authority，当前地图仍不增加 L7。
