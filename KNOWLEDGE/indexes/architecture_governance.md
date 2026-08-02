# 架构、治理与自我纠错：检索索引

引导问题：知识资产怎样被登记、裁决、修订、隔离并保持机器与人类表面一致？

索引按固定 500 条分片，避免单页过大而无法在 GitHub 渲染。分片连续覆盖本主题主归属资产，未按重要性删减。

- [第 001 片](./architecture_governance/part-001.md)：1—500；"""121-validator.py — Validate 121 fulltext artifacts by actually reading files. → "社会信任是由制度、文化、互动等多重因素共同塑造"（这是社会科学界的共识，点火框架只是重述）
- [第 002 片](./architecture_governance/part-002.md)：501—1000；"结构增益"容易被误读为"已解决" → Candidate signal ONLY — never an accepted relation."""
- [第 003 片](./architecture_governance/part-003.md)：1001—1500；candidates, historical_register, validation_report, prev_invalidated = CS.reconcile(candidates) → def build() -> dict\[Path, str\]:
- [第 004 片](./architecture_governance/part-004.md)：1501—2000；def build() -> None: → def main():
- [第 005 片](./architecture_governance/part-005.md)：2001—2500；def main(): → def test_current_surfaces_are_visible_paired_and_reachable(self):
- [第 006 片](./architecture_governance/part-006.md)：2501—3000；def test_current_tree_passes(self) -> None: → def test_runtime_error_div0(self):
- [第 007 片](./architecture_governance/part-007.md)：3001—3500；def test_schema_assets_are_valid_json_and_declared(self): → evidence_status = "EMPIRICAL_EVIDENCE_AVAILABLE" if any("evidence" in str(e).lower() or "验证" in str(e) for e in known_ev
- [第 008 片](./architecture_governance/part-008.md)：3501—4000；evidence_status = {item.get("case_id"): item for item in evidence_doc.get("cases", \[\])} → link: "统一案例总表/0728-C-0733-脱不花三十年只靠劳动所得.md"
- [第 009 片](./architecture_governance/part-009.md)：4001—4500；link: "统一案例总表/0729-C-0734-何刚一针见血.md" → require(binding\["closure_complete"\] and not binding\["unresolved_residue"\], f"{source}: unresolved propagation residue bl
- [第 010 片](./architecture_governance/part-010.md)：4501—5000；require(binding\["resolved_components"\] == recomputed\["resolved_components"\], f"{source}: resolved component closure mism → title: "四卡点统一根源"
- [第 011 片](./architecture_governance/part-011.md)：5001—5500；title: "四方向联合碰撞验证" → \| evidence_status \| EMPIRICAL_EVIDENCE_AVAILABLE, NO_EMPIRICAL_EVIDENCE, INTERNAL_REFERENCE_ONLY \|
- [第 012 片](./architecture_governance/part-012.md)：5501—6000；\| evidence_status \| 关键词命中 known_evidence 中的"验证" \| 否 \| → 何刚强调信息权和决策权对称，实质上是在强调真实退出权和认同验证的共同成立。
- [第 013 片](./architecture_governance/part-013.md)：6001—6500；你可以比较不同 AI 的回答，但多个 AI 给出一致答案，也不自动构成独立事实证据。 → 原文来源 / Source**：`/Users/zhiyuan/我的笔记/统一案例总表/0539-C-544-拓扑绝缘体 — 体态3D门控否决,表面=2D门控边界.md`
- [第 014 片](./architecture_governance/part-014.md)：6501—7000；原文来源 / Source**：`/Users/zhiyuan/我的笔记/统一案例总表/0540-C-545-安德森局域化 — 维度依赖=路径数vs最弱门否决.md` → 本层基础设施为文档/模板，不引入新数据文件结构；以下校验器仍须通过（见仓库 `tools/`）：
- [第 015 片](./architecture_governance/part-015.md)：7001—7500；本工具返回元数据和摘要，不返回全文 → 需要单独深挖的协议：V2、V3（仅事实度量验证，非重新审核）。**
- [第 016 片](./architecture_governance/part-016.md)：7501—7619；需要历史材料、制度分析、比较政治、数据支持。 → ：晋级门槛 + 初版验证器。machine_eligible=0/12，但验证器字段与 Schema 不一致。
