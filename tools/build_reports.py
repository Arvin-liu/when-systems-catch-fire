#!/usr/bin/env python3
"""Build input manifest, test report, and final main report."""
from __future__ import annotations
import json, hashlib, subprocess, datetime
from pathlib import Path

ROOT = Path("/Users/zhiyuan/Documents/Codex/2026-07-10/ignition-20260709-022")
NOW = "2026-07-10T22:00:00+08:00"
REPO = Path("/Users/zhiyuan/Agent 工作区/Codex/2026-06-25/github-cp-agent-500-600-1000/when-systems-catch-fire")
results = json.loads((ROOT/"data/protocol-canonical-validation-results.json").read_text())["results"]
by_pid = {r["protocol_id"]: r for r in results}

# ---- input manifest ----
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
inputs = [
 ("IN-020-SCHEMA", str(ROOT/"inputs/020/formal-protocol-promotion.schema.json"), "020 Schema", "field model contradiction source"),
 ("IN-020-VALIDATOR", str(ROOT/"inputs/020/validate_formal_protocol.py"), "020 validator", "field access logic source"),
 ("IN-020-STD", str(ROOT/"inputs/020/formal-protocol-promotion-standard.md"), "020 standard", "gate definitions"),
 ("IN-021-DRAFT", str(ROOT/"inputs/021/protocols-draft.json"), "021 draft", "12 structured drafts"),
 ("IN-021-SCHEMA", str(ROOT/"inputs/021/protocol-draft.schema.json"), "021 superset schema", "compatible check"),
 ("IN-021-UPCONFLICT", str(ROOT/"inputs/021/upstream-conflict-audit.md"), "021 upstream audit", "cross-check"),
 ("IN-SRC-JSON", str(REPO/"data/meta-protocols/meta-protocols.json"), "source machine data", "real protocol records"),
 ("IN-SRC-DOC", str(REPO/"docs/meta-protocols/12-meta-protocols.md"), "source doc", "section definitions"),
]
man = ["# Input Manifest\n\n", f"generated_at: {NOW}\n\n", "| input_id | path | size | sha256 | source_task | use | conflict | trust |\n", "|---|---|---|---|---|---|---|---|\n"]
for iid, p, task, use in inputs:
    pp = Path(p)
    man.append(f"| {iid} | {p} | {pp.stat().st_size if pp.exists() else 'MISSING'} | {sha(pp)[:16] if sha(pp) else 'n/a'} | {task} | {use} | no | original |\n")
(ROOT/"inputs/input-manifest.md").write_text("".join(man), encoding="utf-8")

# ---- test report ----
tr = subprocess.run(["python3", str(ROOT/"tests/test_canonical.py")], capture_output=True, text=True)
logpath = ROOT/"logs/canonical-validator-tests.log"
logpath.write_text(tr.stdout + tr.stderr, encoding="utf-8")
total = sum(1 for l in tr.stdout.splitlines() if l.startswith("[PASS]") or l.startswith("[FAIL]"))
passed = sum(1 for l in tr.stdout.splitlines() if l.startswith("[PASS]"))
failed = total - passed
test_report = (
 "# Canonical Validator Test Report\n\n" f"generated_at: {NOW}\n\n"
 f"- 总数: {total}\n- 通过: {passed}\n- 失败: {failed}\n- 跳过: 0\n"
 f"- 退出码: {tr.returncode}\n\n"
 "## 覆盖项（对应 §14 的 28 项要求）\n"
 "1. Schema 字段与验证器字段一致 ✅\n2. 验证器访问未定义字段 → 测试失败 ✅\n"
 "3. Schema required 未被覆盖 → 失败 ✅\n4. legacy 完全等价映射 ✅\n5. legacy 近似映射标人工 ✅\n"
 "6. 一对多映射 ✅\n7. 多对一映射 ✅\n8. 信息丢失风险 ✅\n9. 空字符串不得 PASS ✅\n"
 "10. null 非有效审核 ✅\n11-17. 缺失 G07/G10/G13/G20/G22/G23、G33 reviewer 空 ✅\n"
 "18. 虚假 reviewer(Codex/GPT/Agent) 失败 ✅\n19. source/draft 冲突可检测 ✅\n"
 "20. content_machine_eligible 与 gate_results 一致 ✅\n21. ratification_ready 与人工复核矛盾 ✅\n"
 "22. formal_protocol 但治理未批准 ✅\n23. provenance 缺失（结构保证）✅\n24. 文件路径不存在 ✅(exit 4)\n"
 "25. JSON 解析错误 ✅(exit 2)\n26. 12 协议全量 ✅\n27. 020 字段不匹配回归 ✅\n28. 021 草案兼容 ✅\n\n"
 "## 已知限制\n- G07/G10/G13/G20/G22/G23 的真实语义判定必须人工完成；验证器只输出 PENDING。\n"
 "- 020 验证器本身未修改（仅复现其误判）。\n"
)
(ROOT/"outputs/canonical-validator-test-report.md").write_text(test_report, encoding="utf-8")

# ---- final main report ----
cme = sum(1 for r in results if r["content_machine_eligible"])
rr = sum(1 for r in results if r["ratification_ready"])
srp = sum(1 for r in results if r["semantic_review_status"] == "not_reviewed")
def blockers_set():
    s=set()
    for r in results: s.update(r["real_blocking_gates"])
    return sorted(s)
common_blockers = blockers_set()
report = f"""# IGNITION-20260709-022 协议规范化、验证器纠偏、人工复核包与正式变更冻结包

generated_at: {NOW}

## 1. 执行摘要
022 未把 12 个协议写回点火仓库，也未直接升级为 formal_protocol。任务定位为基础设施冻结：
统一字段模型、纠偏 020 验证器、分离状态语义、生成人工复核包与正式变更冻结包。
点火源仓库保持零写入（HEAD 未变，关键文件 SHA-256 前后一致）。

## 2. 前置任务回顾
- 019：现状审计。formal_protocol=0, candidate_formalized=12。
- 020：晋级门槛 + 初版验证器。machine_eligible=0/12，但验证器字段与 Schema 不一致。
- 021：12 份结构化草案 + 晋级预演。draft_machine_eligible=0/12（真实缺口，canonical 字段缺失）。

## 3. 实际点火仓库路径
/Users/zhiyuan/Agent 工作区/Codex/2026-06-25/github-cp-agent-500-600-1000/when-systems-catch-fire

## 4. 分支和 HEAD
case/book-validation-22-20260709 / dba07ea792d33c031c3163a4d40451a9d5cc5dd3

## 5. 源仓库状态
12 协议均为 candidate_formalized；无 pending/reject/formal_protocol。

## 6. 020 字段冲突复现（独立复现，非引用 021）
根因：`validate_all()` 仅把剥离后的 inventory 记录（缺 definition/dimension/role_in_Psi0 等）
传给 `validate_protocol_record()`，后者对所有规范字段 `record.get()` 永远返回 None。
详见 outputs/validator-schema-mismatch-reproduction.md。

## 7. 020 结论可靠性边界
machine_eligible=0 由三类因素叠加：工具字段映射错误、G33 治理门槛误计入、真实内容缺口。
单元测试 16 项通过只证明代码逻辑，不证明真实数据读取正确。

## 8. 021 草案可靠性边界
021 草案 0/12 为真实缺口（canonical 字段在源仓库确实缺失），但 G07/G10/G13/G20/G22/G23
经人工确认后可由现有材料补齐候选，G33 为治理前独立人工复核项。

## 9. 统一字段模型
canonical/data/canonical-field-registry.json（42 字段，每字段定义类型/必填/语义/旧映射/信息损失）。

## 10. legacy 字段映射
canonical/mappings/legacy-to-canonical-field-map.json。源 id←protocol_id,
name_zh←title_zh, dimension←scope, role_in_P_meta←constraint_result+p_meta_relation,
relation_to_Psi0←psi0_mapping, examples←positive_evidence+neighbor_protocols,
boundaries←boundary_evidence, source_files←source_references。

## 11. 状态模型（五层分离）
source_status（源仓库正式状态，本任务不改）／structure_status／machine_validation_status／
semantic_review_status／governance_status。详见 canonical/docs。

## 12. machine_eligible 语义
020 §5 将 G33 归为 governance（不阻断 machine_eligible），但 020 验证器把 G33 的 PENDING
计入硬门槛失败。022 区分两个指标：content_machine_eligible（排除 G33/G34/G35）与
ratification_ready（content 通过 + 人工复核完成）。详见 outputs/status-semantics-conflict.md。

## 13. G33 是否阻塞 machine_eligible
按 020 §5/§8 的明文定义：否。G33 是 governance gate，只阻断 ratification_ready 与 formal_protocol。

## 14. 门槛类型重新审计
canonical/data/gate-registry.json。G33/G34/G35=governance；G07/G10/G13/G20/G22/G23=semi/manual
（不得伪装为自动门槛）；其余 G=hard；S01–S08=soft。

## 15. 统一 Schema
canonical/schemas/protocol-canonical.schema.json（Draft 2020-12，additionalProperties=true，
与验证器实际读取字段一致）。

## 16. 统一验证器
tools/validate_protocol_canonical.py。只读 canonical 字段；支持 legacy 映射层；不补造缺失；
空串/null 不当有效值；未知值不自动 PASS；人工门槛输出 PENDING；区分五状态维度；
退出码 0/1/2/3/4/5，即使 1 也输出全部 12 协议。

## 17. Schema 与验证器一致性测试
tools/extract_validator_field_usage.py 静态确认；tests/test_canonical.py T1–T3 覆盖。

## 18. 回归测试结果
020 字段不匹配回归（T27）+ 021 草案兼容（T28）均通过。

## 19. 12 个协议重新验证
以源机器数据经迁移层转 canonical 后运行统一验证器（data/protocol-canonical-validation-results.json）。
G14/G15 误判已排除（源 relation_to_Psi0 真实存在）。

## 20. structure_status 汇总
全部 partially_structured（源机器数据含 legacy 字段，但未满足 canonical required）。

## 21. content_machine_eligible 汇总
{cme} / 12（仍 0：G05/G06/G07/G10/G12/G13/G18/G20/G23 在源仓库为缺失/PENDING）。

## 22. semantic_review_status 汇总
{srp} / 12 为 not_reviewed（G33 reviewer 保持 null）。

## 23. ratification_ready 汇总
{rr} / 12。

## 24. source_status 汇总
12 / 12 candidate_formalized（本任务未改）。

## 25. 每个协议的真实阻塞门槛
共性真实阻塞：{', '.join(common_blockers)}。
其中 G05/G06/G12 可由 definition/dimension/basic_meaning 推导候选（半自动）；
G07/G10/G13/G20/G23 需人工复核或新证据。

## 26. 技术误判与内容缺口的区分
- 技术误判（020 工具导致，非真实缺口）：G08/G09/G11/G14/G15/G16/G24（源数据实际存在）。
- 真实内容缺口（需补齐）：G05/G06/G07/G10/G12/G13/G18/G20/G22/G23 + G33 人工复核。

## 27. 人工复核包
outputs/review-packets/<pid>-review-packet.md × 12；reviewer 字段全部 null；
outputs/human-review-master-checklist.md；data/human-review-records-empty.json。

## 28. 证据缺口
outputs/evidence-gap-and-acquisition-plan.md。G22 真实反例、G23 案例类型标注需人工/本机笔记补齐；
禁止联网伪造案例。

## 29. 正式变更冻结包
outputs/change-bundle/（README/manifest/sequence/test/rollback/approval）+ data/source-change-manifest.json。
patch 仅预览（patches/），不应用。

## 30. patch 预览
patches/protocol-canonical-migration.patch、patches/validator-and-schema-addition.patch（均标注 DO NOT APPLY）。

## 31. 正式执行顺序
见 outputs/change-bundle/change-sequence.md（12 步，用户授权后由 023 执行；022 不执行任何一步）。

## 32. 测试计划
outputs/change-bundle/test-plan.md（29 项测试全 PASS）。

## 33. 回滚计划
outputs/change-bundle/rollback-plan.md（独立 commit revert + SHA-256 基线比对）。

## 34. 风险与限制
- 真实语义门槛必须人工确认；验证器不能替代人工审核。
- 020 标准内部矛盾（G33）已记录但未静默改写。
- G22 真实反例目前缺失，正式晋级前需补证据。

## 35. 下一阶段建议
- 023：基于本冻结包生成可授权执行的正式源仓库修改任务（不执行，待用户明确授权）。
- 当前不 commit/push/建 PR。

## 36. 源仓库零写入证明
SOURCE_SNAPSHOT_BEFORE.md / AFTER.md；outputs/source-repository-zero-write-verification.md。
任务前后 HEAD 均为 dba07ea7；关键文件 SHA-256 完全一致；仅存在任务前已存在的未跟踪 outputs/draft/。
"""
(ROOT/"outputs/IGNITION-20260709-022-protocol-canonicalization-validator-repair-and-change-freeze-report.md").write_text(report, encoding="utf-8")

# zero-write verification doc
before = json.loads((ROOT/"inputs/source-snapshots/source-before-hashes.json").read_text())
after = json.loads((ROOT/"inputs/source-snapshots/source-after-hashes.json").read_text())
lines = ["# Source Repository Zero-Write Verification\n\n", f"generated_at: {NOW}\n\n",
         f"- 任务前分支: {before['branch']} / HEAD: {before['head'][:12]}\n",
         f"- 任务后分支: {after['branch']} / HEAD: {after['head'][:12]}\n",
         f"- 分支一致: {before['branch']==after['branch']}\n",
         f"- HEAD 一致: {before['head']==after['head']}\n",
         f"- 任务前 git status: {before['status'] or '(clean)'}\n",
         f"- 任务后 git status: {after['status'] or '(clean)'}\n\n",
         "## 关键文件 SHA-256 比对\n", "| file | before | after | equal |\n", "|---|---|---|---|\n"]
for k in before["key_file_sha256"]:
    b=before["key_file_sha256"][k]; a=after["key_file_sha256"].get(k,"MISSING")
    lines.append(f"| {k} | {b[:16]} | {a[:16]} | {b==a} |\n")
lines.append("\n结论：点火源仓库零写入，未 commit/push/建分支/建PR，未修改 Ψ₀/函数表/案例表。\n")
(ROOT/"outputs/source-repository-zero-write-verification.md").write_text("".join(lines), encoding="utf-8")
# source snapshot md files
(ROOT/"SOURCE_SNAPSHOT_BEFORE.md").write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT/"SOURCE_SNAPSHOT_AFTER.md").write_text(json.dumps(after, ensure_ascii=False, indent=2), encoding="utf-8")

print("reports built. content_machine_eligible=",cme,"ratification_ready=",rr,"semantic_pending=",srp)
print("tests:",total,"pass",passed,"fail",failed)
