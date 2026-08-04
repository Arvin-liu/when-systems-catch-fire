# 架构、治理与自我纠错：检索索引

引导问题：知识资产怎样被登记、裁决、修订、隔离并保持机器与人类表面一致？

索引按固定 500 条分片，避免单页过大而无法在 GitHub 渲染。分片连续覆盖本主题主归属资产，未按重要性删减。

- [第 001 片](./architecture_governance/part-001.md)：1—500；"""121-validator.py — Validate 121 fulltext artifacts by actually reading files. → "validation_authority": {"authority": "external", "required_evidence": \["receipt"\], "evidence_boundary": "fixture"},
- [第 002 片](./architecture_governance/part-002.md)：501—1000；"validation_authority": {"authority": "human", "required_evidence": \["review"\], "evidence_boundary": "fixture"}, → benchmark 为后续 UNESCO 学科深跑提供了基准。后续学科深跑时，可以参考 benchmark 的四类结果（结构增益 + 重述 + 失败 + pending），评估点火框架在该学科的解释力、边界、失败类型和 pending 条件
- [第 003 片](./architecture_governance/part-003.md)：1001—1500；benchmark 通过"证据制度"字段，调用任务 E 的证据制度库。每个经典问题都会明确说明本问题在该领域中如何判断成立，以及需要什么证据才能升级到 L4/L5。 → def _tamper_and_validate(self, tamper_fn) -> None:
- [第 004 片](./architecture_governance/part-004.md)：1501—2000；def _test_count(path: Path) -> int: → def load_evidence_map(path: Path) -> dict\[str, dict\[str, Any\]\]:
- [第 005 片](./architecture_governance/part-005.md)：2001—2500；def load_evidence_map(path: Path) -> dict\[str, dict\[str, Any\]\]: → def sha256_json(obj) -> str:
- [第 006 片](./architecture_governance/part-006.md)：2501—3000；def sha256_of(path: Path) -> str: → def test_missing_provenance_reason_rule_version_rejected(self):
- [第 007 片](./architecture_governance/part-007.md)：3001—3500；def test_missing_q25_seal_is_rejected(self): → die(f"{code} FUNCTION_PARTIAL without explicit matched evidence")
- [第 008 片](./architecture_governance/part-008.md)：3501—4000；die(f"{code} NARRATIVE_READY without matched_story_artifacts") → if card.get("evidence_tier") == "FULLTEXT_REVIEWED":
- [第 009 片](./architecture_governance/part-009.md)：4001—4500；if claim_class == "PREDICTION_OR_FORECAST": → P1 数据索引图（2026-07-08）
- [第 010 片](./architecture_governance/part-010.md)：4501—5000；P1 数据说明（本文件第 2 节摘要） → self.assertIn("iteration", closure\["resolved_components"\])
- [第 011 片](./architecture_governance/part-011.md)：5001—5500；self.assertIn("pages_artifacts", str(ctx.exception)) → Versioned, resumable episode state with explicit, validated transitions. Minimum
- [第 012 片](./architecture_governance/part-012.md)：5501—6000；Versions, lineages, bundle IDs, Pareto states, retirement and epitaphs are strong registry primitives, but no actual imm → \|OQ-103-3：OpenAlex 跨源一致性（首轮已执行，仍有歧义）\|117 条 DOI 的 OpenAlex 首轮已完成；116 条主分母中 7 条为 null/inconclusive，4 条多重精确命中、3 条无精确命中。\|若要重
- [第 013 片](./architecture_governance/part-013.md)：6001—6500；\|OQ-103-4：案例表历史锚点\|案例表引用的历史人名/事件是否对应真实 Wikipedia 条目。\|Wikipedia 验证（备用试点 2）。\|无法解析的锚点降级为“待核”而非断言。\| → 原文来源 / Source**：`/Users/zhiyuan/我的笔记/统一案例总表/0062-C-62-宋朝.md`
- [第 014 片](./architecture_governance/part-014.md)：6501—7000；原文来源 / Source**：`/Users/zhiyuan/我的笔记/统一案例总表/0063-C-63-明朝覆灭.md` → 四种基本力统一；
- [第 015 片](./architecture_governance/part-015.md)：7001—7500；四阶段严格串行验证 — 不能跳过Stage2直接到Stage3-rcross=0时D84三条路径失效 → 用户 087 纠正消息：只能接受为'学科投影初稿完成'
- [第 016 片](./architecture_governance/part-016.md)：7501—7959；用途：解决 web_fetch 受限；扩补 6 MEDIUM 缺口外部文献；任何「找线索→验真」文献任务 → ：晋级门槛 + 初版验证器。machine_eligible=0/12，但验证器字段与 Schema 不一致。
