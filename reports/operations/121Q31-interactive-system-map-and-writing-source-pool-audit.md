# 121Q31｜完整可点击系统图与双来源写作素材池审计

Status: `READY_FOR_GPT_VERIFICATION_CANDIDATE_ONLY`

Claim ceiling: `candidate_zhiyuan_writing_method_0_4_0_and_interactive_system_map_implemented / repository_synchronization_complete_pending_independent_review`。

## 缺口与最小实质动作

之元写作法 0.3.0 已建立 L6 公共表达与 provenance-gated feedback，但“素材来源”仍容易被读成只有外部原始材料。与此同时，README 虽有架构与成果入口，却没有一张仓库原生、节点可点击、由机器 spec 生成并受测试约束的完整当前系统图。

121Q31 的最小实质动作是：把 0.4.0 候选素材池显式分为 `external_input` 与 `ignition_increment`，并建立 `JSON spec → deterministic generator → linked SVG → README/Pages` 单一生成链。它不改 Foundation、Function OS、MCF、PSD、ARN、Q12—Q14 或迭代运行时。

## 双来源边界

点火增量输出包括 claim、argument、formal object、mechanism、map、gap、residue、Q12—Q14 输出、MCF／PSD／ARN／Atlas 投影、分析报告与完成 provenance capture 的返回项。它们可以成为新的起始承载点、概念压力、竞争解释、不可容纳残余或回照对象，但必须保存 canonical 路径／ID、版本或 commit、生成任务、claim ceiling、原始来源回链和未决边界。

这不是独立复证规则。相同外部证据经点火分析后的派生产物不能重新计数为第二份外部证据；扩大的是 L6 生成材料范围，不是 L0—L5 证据权限。受限原文、未经登记的读者反应、点赞和多 AI 一致都不会因进入素材讨论而自动公开或升级真值。

## 系统图实现

- 权威 spec：`data/architecture/interactive-system-map.json`；
- 确定性生成器：`tools/generate_interactive_system_map.py`；
- 生成 SVG：`pages/generated/ignition-system-map.svg`；
- canonical 交互页：`pages/system-map.html`；
- 维护说明：`docs/architecture/interactive-system-map.md`。

当前 spec 包含 9 个 group、41 个 node 与有标签关系边。每个节点保存 `id / label / group / target / description`，target 文件与 Markdown anchor 均验证存在；SVG 中每个节点是带 canonical HTTPS 目标、tooltip、ARIA 与 data-target 的 `<a>`。层级组严格只有 L0—L6；边界组明确“不增加 L7、不自动升级真值、不证明理论完整”。

Pages 首页通过 `<object>` 直接嵌入 SVG，节点可点击；独立 `system-map.html` 承载完整交互版。GitHub README 可能过滤 `<object>`，因此保留同一 SVG 的完整预览并把整图链接到 Pages 交互版，不声称图片预览的内部热点一定可用。两个表面不维护第二张人工图。

## 同步与生命周期

README 中图位于生命共同体价值宪章之后、使用指南之前。方法、后台规格、架构、项目现状、SUMMARY、USAGE、AI 参考、AI START、Agent handoff、llms、Changelog 与 Versioning 已同步 Draft 候选状态。0.3.0 在独立接受和合并前仍为 Current；成果 registry 中 Q29R 的 `method_version=0.3.0` 保持不变。

Draft Pages 只构建和检查 artifact，不部署生产。精确 candidate HEAD、Foundation、Function OS、Pages artifact 中 `system-map.html`／SVG 以及 1111 回执由 PR #60 与外部回执承载。进入 Current 仍需独立审查、精确 HEAD 合并、final-main CI、生产部署和 live 点击实况。

## 冻结与未执行

Q29R 正文 SHA-256 继续为 `c135acd35a2232f0a6b3f933db482932a9fe5d5add51f870af97901faac90d4b`，未修改一个字节。没有公开第三方课程原文，没有合并 main，没有增加真值层或 L7，也没有把“完整图”写成点火理论完整证明。
