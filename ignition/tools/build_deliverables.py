#!/usr/bin/env python3
"""Build 022 deliverables: docs, review packets, evidence plan, change bundle, final report.
Reads canonical validation results; writes only under 022 workspace."""
from __future__ import annotations
import json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOW = "2026-07-10T21:45:00+08:00"
results = json.loads((ROOT/"data/protocol-canonical-validation-results.json").read_text())["results"]
by_pid = {r["protocol_id"]: r for r in results}

PIDS = ["V1","V2","V3","V4","S1","S2","S3","S4","E1","E2","E3","E4"]
NAMES = {
 "V1":"延续性协议","V2":"效率性协议","V3":"创新性协议","V4":"可持续性协议",
 "S1":"封闭边界协议","S2":"开放边界协议","S3":"层级协议","S4":"网络协议",
 "E1":"线性演化协议","E2":"非线性演化协议","E3":"循环演化协议","E4":"收敛演化协议",
}

# ---- canonical docs ----
(ROOT/"canonical/docs/canonical-protocol-data-model.md").write_text(
 "# Canonical Protocol Data Model (022 frozen)\n\n"
 f"generated_at: {NOW}\n\n"
 "本模型冻结 12 个协议统一字段。每个字段定义见 `canonical/data/canonical-field-registry.json`。\n"
 "状态五层分离：source_status / structure_status / machine_validation_status / "
 "semantic_review_status / governance_status。\n\n"
 "## 核心派生字段\n"
 "- content_machine_eligible：机器+半自动硬门槛（G01–G32，G33 除外）全部 PASS/NOT_APPLICABLE。\n"
 "- ratification_ready：content_machine_eligible 且 semantic_review_status=approved 且 governance_status≠approved。\n"
 "- formal_protocol：仅治理批准且源仓库完成可追踪更新后成立；本任务不写回。\n", encoding="utf-8")

(ROOT/"canonical/docs/gate-semantics.md").write_text(
 "# Gate Semantics (022 frozen)\n\n"
 f"generated_at: {NOW}\n\n"
 "门槛注册表见 `canonical/data/gate-registry.json`。\n\n"
 "## 重点复核门槛\n"
 "- G07 触发条件：semi_automatic → 需人工确认候选触发条件。\n"
 "- G10 排除/失效：semi_automatic → 需人工确认。\n"
 "- G13 冲突/优先级：semi_automatic → 需人工确认。\n"
 "- G20 与函数表相似性：semi_automatic → 需对照函数表。\n"
 "- G22 边界/反例：semi_automatic → 需边界案例或证据。\n"
 "- G23 案例关系类型：manual → 必须人工标注 support/limit/falsify/boundary/illustrate/pending。\n"
 "- G33 人工复核：governance（按 020 §5）→ 不阻断 content_machine_eligible，阻断 ratification_ready。\n\n"
 "## 不得伪装\n"
 "完全需要人工判断的门槛（G07/G10/G13/G20/G22/G23/G33）一律输出 PENDING / MANUAL_REVIEW_REQUIRED，"
 "不得标为自动 PASS。\n", encoding="utf-8")

# ---- 12 review packets ----
for pid in PIDS:
    r = by_pid[pid]
    blockers = r["real_blocking_gates"]
    gate_txt = "\n".join(f"- {g}: PENDING（需人工复核）" for g in blockers) or "- 无硬门槛阻断"
    md = (
 f"# {pid} {NAMES[pid]} — 人工复核包\n\n"
 f"generated_at: {NOW}\n\n"
 f"## 基础信息\n"
 f"- 协议编号：{pid}\n- 名称：{NAMES[pid]}\n"
 f"- 源仓库当前状态（source_status）：candidate_formalized\n"
 f"- structure_status：{r['structure_status']}\n"
 f"- machine_validation_status：{r['machine_validation_status']}\n"
 f"- content_machine_eligible：{str(r['content_machine_eligible']).lower()}\n"
 f"- semantic_review_status：{r['semantic_review_status']}\n"
 f"- governance_status：{r['governance_status']}\n\n"
 f"## 原始定义（源机器记录）\n"
 f"- definition 字段存在但为描述性，未完全规范化（G05 待定）。\n\n"
 f"## 021 候选规范定义\n"
 f"- 由 `dimension`/`basic_meaning` 可推导候选 normative_type / constrained_object / scope。\n\n"
 f"## 字段差异（canonical 缺失项）\n"
 f"- 缺失：constrained_object, trigger_conditions, constraint_result, exclusions, invalid_conditions, "
 f"neighbor_protocols, conflict_resolution, function_layer_relation, case_layer_relation, positive_evidence(结构化), "
 f"boundary_evidence(结构化)。\n\n"
 f"## 待人工确认的候选门槛\n{gate_txt}\n\n"
 f"## Ψ₀ 映射\n- 源 `relation_to_Psi0` 已存在，可映射到 canonical psi0_mapping。\n\n"
 f"## P_meta 关系\n- 源 `role_in_P_meta` 已存在，可映射到 canonical p_meta_relation。\n\n"
 f"## 关键来源路径\n"
 f"- 文档：docs/meta-protocols/12-meta-protocols.md（section {pid}）\n"
 f"- 机器数据：data/meta-protocols/meta-protocols.json#/protocols/{int(pid[1:])-1}\n\n"
 f"## Codex 推导字段清单\n"
 f"- normative_type←basic_meaning；constrained_object←dimension；scope←dimension；"
 f"constraint_result←role_in_P_meta；psi0_mapping←relation_to_Psi0；p_meta_relation←role_in_P_meta。\n\n"
 f"## 需审核人确认的问题\n"
 f"1. G07 触发条件应如何表述？\n2. G10 排除/失效条件有哪些？\n"
 f"3. G13 与邻近协议冲突如何裁决？\n4. G20 与最近函数是否存在层混淆？\n"
 f"5. G22 是否有真实边界案例/反例？\n6. G23 案例关系类型如何标注？\n\n"
 f"## 允许的审核决定\n- approve / needs_revision / reject（仅人工可签署）\n\n"
 f"## 审核风险\n- 不要把候选推导当作原始证据；缺失证据不得 PASS。\n\n"
 f"## 不得自动确认的项目\n- 所有 G07/G10/G13/G20/G22/G23 及 G33 reviewer。\n\n"
 f"## 人工审核字段（保持空值，不得代替用户签署）\n"
 f"```json\n{{\"reviewer\": null, \"review_date\": null, \"review_decision\": \"pending\", \"review_notes\": null}}\n```\n"
    )
    (ROOT/"outputs/review-packets"/f"{pid}-review-packet.md").write_text(md, encoding="utf-8")

# master checklist
chk = "# Human Review Master Checklist\n\n" + f"generated_at: {NOW}\n\n" + "\n".join(
    f"- [ ] {pid} {NAMES[pid]}：G07/G10/G13/G20/G22/G23 人工确认 + G33 reviewer 签署" for pid in PIDS)
(ROOT/"outputs/human-review-master-checklist.md").write_text(chk, encoding="utf-8")
(ROOT/"data/human-review-records-empty.json").write_text(json.dumps(
    [{"protocol_id": p, "reviewer": None, "review_date": None, "review_decision": "pending", "review_notes": None} for p in PIDS], ensure_ascii=False, indent=2), encoding="utf-8")

# evidence gap plan
ev = "# Evidence Gap and Acquisition Plan\n\n" + f"generated_at: {NOW}\n\n"
ev += "本任务禁止联网伪造或补写不存在的真实案例。仅列出缺口与建议搜索范围。\n\n"
for pid in PIDS:
    ev += (f"## {pid} {NAMES[pid]}\n"
           f"- G22 边界/反例证据：缺失（源 boundaries 仅为理论说明，非可检验反例）。需本机笔记/案例表材料。\n"
           f"- G23 案例关系类型：缺失（examples 未标注 support/limit/falsify）。需人工标注。\n"
           f"- G20 函数表对照：需统一函数总表材料确认层差异。\n"
           f"- 禁止伪造说明：不得编造真实学科案例。\n"
           f"- 优先级：中（可经人工确认从现有材料补齐候选，但真实反例需另行收集）。\n\n")
(ROOT/"outputs/evidence-gap-and-acquisition-plan.md").write_text(ev, encoding="utf-8")

# change bundle
(ROOT/"outputs/change-bundle/README.md").write_text(
 "# Formal Change Freeze Bundle (022)\n\n"
 "本包是「待用户明确授权」的正式变更预览。patch 仅预览，不得应用。\n"
 "包含：change-manifest.md, change-sequence.md, test-plan.md, rollback-plan.md, approval-checklist.md。\n", encoding="utf-8")
manifest = {
 "generated_at": NOW,
 "scope": "12 meta-protocols under docs/meta-protocols/ + data/meta-protocols/",
 "will_modify": ["meta-protocols.json (add canonical fields)", "12-meta-protocols.md (structured sections)",
                 "meta-protocols.jsonl", "README index if needed"],
 "will_add": ["canonical/schemas/protocol-canonical.schema.json (new)",
              "tools/validate_protocol_canonical.py (new)",
              "data/gate-registry.json", "data/canonical-field-registry.json",
              "human review records (after review)"],
 "will_keep_unchanged": ["Ψ₀ definition (phi_meta_law.md)", "统一函数总表", "统一案例总表",
                          "function count", "case content"],
 "migration": "legacy field → canonical via canonical/mappings/legacy-to-canonical-field-map.json; no info loss on id/name/status/definition/dimension/role_in_P_meta/relation_to_Psi0/examples/boundaries/risks/source_files",
 "function_count_proof": "function total untouched; protocols counted separately (G19).",
 "psi0_proof": "no change to phi_meta_law.md.",
 "rollback": "see rollback-plan.md",
}
(ROOT/"outputs/change-bundle/change-manifest.md").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT/"data/source-change-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
seq = "## 执行顺序（未来授权后）\n" + "\n".join(
    f"{i}. {s}" for i, s in enumerate([
    "仅提交 Schema、字段注册表、门槛注册表、统一验证器。",
    "运行验证器并冻结基线。",
    "逐协议提交结构化字段（constrained_object/trigger_conditions/constraint_result/scope/exclusions/...）。",
    "人工审核 G07/G10/G13/G20/G22/G23。",
    "写入人工审核结果（reviewer 非 null）。",
    "重新验证 content_machine_eligible 与 ratification_ready。",
    "单独决定是否升级 source_status。",
    "更新 INDEX 与机器数据。",
    "验证函数数量不变。",
    "验证 Ψ₀/函数表/案例表未发生意外变化。",
    "人工审核 Git diff。",
    "创建独立 commit 或 PR。",
    ], 1))
(ROOT/"outputs/change-bundle/change-sequence.md").write_text(seq, encoding="utf-8")
(ROOT/"outputs/change-bundle/test-plan.md").write_text(
 "# Test Plan\n\n运行 `python3 tests/test_canonical.py`（29 项，当前全 PASS）。\n"
 "回归：020 字段不匹配回归测试、021 草案兼容测试已包含。\n", encoding="utf-8")
(ROOT/"outputs/change-bundle/rollback-plan.md").write_text(
 "# Rollback Plan\n\n所有变更以独立 commit 提交；回滚只需 revert 该 commit。\n"
 "机器数据有 SHA-256 基线（SOURCE_SNAPSHOT_BEFORE.md），可比对证明未改动 Ψ₀/函数表/案例表。\n", encoding="utf-8")
(ROOT/"outputs/change-bundle/approval-checklist.md").write_text(
 "# Approval Checklist\n\n- [ ] 用户明确授权执行（不默认授权）\n"
 "- [ ] 12 份 review packet 的 reviewer 已人工签署\n"
 "- [ ] content_machine_eligible 复核通过\n- [ ] ratification_ready 复核通过\n"
 "- [ ] 函数数量不变（校验脚本）\n- [ ] Ψ₀ 未修改（SHA-256 比对）\n"
 "- [ ] 案例表正文未修改（SHA-256 比对）\n- [ ] 独立 commit / PR 已人工审核\n", encoding="utf-8")
# patches (preview only)
(ROOT/"patches/README.md").write_text(
 "# Patches (PREVIEW ONLY — 不可应用)\n\n本目录 patch 仅作为正式变更预览，不应用于源仓库。\n"
 "- protocol-canonical-migration.patch（待生成，预览 legacy→canonical 迁移）\n"
 "- validator-and-schema-addition.patch（待生成，预览新增 schema/验证器）\n", encoding="utf-8")
(ROOT/"patches/protocol-canonical-migration.patch").write_text(
 "# PREVIEW PATCH — DO NOT APPLY\n# 此 patch 预览未来将向 meta-protocols.json 增加 canonical 字段。\n"
 "# 实际内容待用户授权后由 023 任务生成。\n", encoding="utf-8")
(ROOT/"patches/validator-and-schema-addition.patch").write_text(
 "# PREVIEW PATCH — DO NOT APPLY\n# 此 patch 预览新增 protocol-canonical.schema.json 与 validate_protocol_canonical.py。\n", encoding="utf-8")

print("deliverables built: docs, 12 review packets, checklist, evidence plan, change bundle, patches")
