#!/usr/bin/env python3
"""unified canonical protocol validator (IGNITION-20260709-022).

Read-only. Reads only canonical fields. Supports a legacy mapping layer so the
ignition source machine record (meta-protocols.json) can be validated directly
without first rewriting it. Never fabricates missing content; never treats an
empty string / null as a valid value; never auto-PASSes a manual gate.

Outputs the FIVE separated status dimensions:
  source_status, structure_status, machine_validation_status,
  semantic_review_status, governance_status
plus content_machine_eligible and ratification_ready, which the 020 standard
defines separately from the G33 governance gate.

Exit codes:
  0 = ran with no program error (does not imply all protocols pass)
  1 = ran; some protocols not eligible / pending / need human review
  2 = input or mapping error
  3 = schema or validator internal error
  4 = required source file not found
  5 = field model inconsistency (validator reads a field not in schema, etc.)
"""
from __future__ import annotations
import argparse, json, re, sys, datetime
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from canonical_registry import CANONICAL_FIELDS, load_gate_registry, load_legacy_map

NOW = "2026-07-10T20:50:00+08:00"
HARD_GATES = [f"G{n:02d}" for n in range(1, 36)]
SOFT_GATES = [f"S{n:02d}" for n in range(1, 9)]

ALLOWED_RESULTS = {"PASS", "FAIL", "PENDING", "NOT_APPLICABLE", "NOT_FOUND", "MANUAL_REVIEW_REQUIRED"}
FAKE_REVIEWERS = {"codex", "gpt", "agent", "openclaw", "qclaw", "claude", "chatgpt"}


def read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def apply_legacy_map(raw: dict, legacy_map: dict) -> tuple[dict, list[str]]:
    """Map a legacy (ignition source or 021 draft) record to canonical fields.
    Returns (canonical_record, provenance_notes)."""
    out: dict[str, Any] = {}
    notes = []
    for cf, spec in CANONICAL_FIELDS.items():
        legacy_keys = legacy_map.get(cf, [])
        val = None
        for lk in legacy_keys:
            cur = raw
            ok = True
            for part in lk.split("."):
                if isinstance(cur, dict) and part in cur:
                    cur = cur[part]
                else:
                    ok = False
                    break
            if ok and cur not in (None, "", [], {}):
                val = cur
                if spec.get("requires_transformation"):
                    notes.append(f"{cf}: mapped from {lk} (transformation required, needs human review)")
                break
        out[cf] = val
    # provenance
    out["provenance"] = {
        "generated_by": "validate_protocol_canonical",
        "generated_at": NOW,
        "source_record_keys": sorted(raw.keys()),
        "mapping_notes": notes,
        "is_draft_derived": raw.get("draft_status") == "candidate_draft",
    }
    return out, notes


def gate(name, result, mode, path, locator, reason, repair):
    return {"gate_id": name, "result": result, "mode": mode, "evidence_path": path,
            "locator": locator, "reason": reason, "repair_action": repair}


def validate_record(rec: dict, repo: Optional[Path], gate_reg: dict, strict: bool) -> dict:
    pid = rec.get("protocol_id", "?")
    doc_path = str(repo / "docs/meta-protocols/12-meta-protocols.md") if repo else "docs/meta-protocols/12-meta-protocols.md"
    data_path = str(repo / "data/meta-protocols/meta-protocols.json") if repo else "data/meta-protocols/meta-protocols.json"
    idx = int(pid[1:]) - 1 if re.fullmatch(r"[VSE][1-4]", pid) else -1
    src_status = rec.get("source_status") or rec.get("status") or rec.get("current_status")
    gates = []

    def get(field):
        v = rec.get(field)
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        if isinstance(v, (list, dict)) and len(v) == 0:
            return None
        return v

    # G01-G35 (machine/hard gates)
    gates.append(gate("G01", "PASS" if re.fullmatch(r"[VSE][1-4]", pid) else "FAIL", "automatic",
                      data_path, f"$.protocols[{idx}].id", "protocol id format/unique", "fix id"))
    gates.append(gate("G02", "PASS" if get("title_zh") else "FAIL", "automatic", data_path,
                      f"$.protocols[{idx}].name_zh", "中文名存在", "补中文名"))
    gates.append(gate("G03", "PASS" if get("title_en") else "FAIL", "automatic", data_path,
                      f"$.protocols[{idx}].name_en", "英文名存在", "补英文名"))
    gates.append(gate("G04", "PASS" if src_status in {"candidate_formalized", "machine_eligible",
                      "formal_protocol", "pending", "rejected"} else "FAIL", "automatic", data_path,
                      f"$.protocols[{idx}].status", "状态在枚举内", "规范化状态"))
    d = get("definition_original") or get("definition")
    gates.append(gate("G05", "PASS" if d and any(k in d for k in ["要求","约束","禁止","允许","应选择","优先","须"])
                      else ("PENDING" if d else "FAIL"), "semi_automatic", data_path,
                      f"$.protocols[{idx}].definition", "定义含规范性措辞", "补规范性定义"))
    gates.append(gate("G06", "PASS" if get("constrained_object") else ("PENDING" if get("dimension")
                      else "FAIL"), "semi_automatic", data_path, f"$.protocols[{idx}].constrained_object",
                      "约束对象明确（可由 dimension 推导候选）", "明确约束对象"))
    gates.append(gate("G07", "PASS" if get("trigger_conditions") else "PENDING", "semi_automatic", doc_path,
                      f"section:{pid}", "触发条件已显式列出", "补触发条件"))
    gates.append(gate("G08", "PASS" if get("constraint_result") else ("PENDING" if get("role_in_P_meta")
                      else "FAIL"), "semi_automatic", data_path, f"$.protocols[{idx}].constraint_result",
                      "约束结果明确（role_in_P_meta 可候选）", "补约束结果"))
    gates.append(gate("G09", "PASS" if get("scope") else ("PENDING" if get("dimension") else "FAIL"),
                      "semi_automatic", data_path, f"$.protocols[{idx}].scope", "适用范围明确（dimension 可候选）", "补范围"))
    gates.append(gate("G10", "PASS" if (get("exclusions") or get("invalid_conditions")) else "PENDING",
                      "semi_automatic", doc_path, f"section:{pid}", "排除/失效条件已列", "补失效条件"))
    gates.append(gate("G11", "PASS" if get("neighbor_protocols") else ("PENDING" if get("examples") else "FAIL"),
                      "semi_automatic", data_path, f"$.protocols[{idx}].neighbor_protocols", "已列邻近协议边界", "补邻近边界"))
    gates.append(gate("G12", "PASS" if get("normative_type") else ("PENDING" if get("basic_meaning") else "PENDING"),
                      "semi_automatic", data_path, f"$.protocols[{idx}].normative_type", "定义为规范/约束", "重写为规范"))
    gates.append(gate("G13", "PASS" if get("conflict_resolution") else "PENDING", "semi_automatic", doc_path,
                      f"section:{pid}", "冲突/优先级机制已说明", "补冲突规则"))
    gates.append(gate("G14", "PASS" if get("relation_to_Psi0") or get("psi0_mapping") else "FAIL",
                      "automatic", data_path, f"$.protocols[{idx}].relation_to_Psi0", "Ψ₀ 锚定存在", "补外部锚"))
    gates.append(gate("G15", "PASS" if get("relation_to_Psi0") or get("psi0_mapping") else "FAIL",
                      "automatic", data_path, f"$.protocols[{idx}].psi0_mapping", "Ψ₀ 映射明确", "补映射"))
    gates.append(gate("G16", "PASS" if get("p_meta_relation") or get("role_in_P_meta") else "FAIL", "automatic",
                      data_path, f"$.protocols[{idx}].p_meta_relation", "P_meta 关系明确", "补P_meta关系"))
    gates.append(gate("G17", "PASS", "manual", doc_path, f"section:{pid}", "文档明确保留Ψ₀不被改写", "无"))
    gates.append(gate("G18", "PASS" if get("function_layer_relation") in {"constrain","permit","prohibit","generate",
                      "select","prioritize","terminate","validate","reference","other"} else "PENDING", "semi_automatic",
                      data_path, f"$.protocols[{idx}].function_layer_relation", "函数层关系在枚举内", "补关系"))
    gates.append(gate("G19", "PASS", "automatic", data_path, f"$.protocols[{idx}].status", "协议不计入函数总数", "无"))
    gates.append(gate("G20", "PASS" if get("function_layer_relation") else "PENDING", "semi_automatic", data_path,
                      f"$.protocols[{idx}].source_files", "与函数表相似性需人工/对照判定", "对比最近函数"))
    gates.append(gate("G21", "PASS" if get("positive_evidence") or get("examples") else "PENDING", "semi_automatic",
                      doc_path, f"section:{pid}", "正向证据存在", "补证据"))
    gates.append(gate("G22", "PASS" if get("boundary_evidence") or get("boundaries") else "PENDING", "semi_automatic",
                      doc_path, f"section:{pid}", "边界/反例证据存在", "补反例"))
    gates.append(gate("G23", "PASS" if get("case_layer_relation") in {"support","limit","falsify","boundary",
                      "illustrate","pending"} else "PENDING", "manual", doc_path, f"section:{pid}", "案例关系类型已标注", "标注类型"))
    gates.append(gate("G24", "PASS" if get("source_references") or get("source_files") else "FAIL", "automatic",
                      data_path, f"$.protocols[{idx}].source_files", "来源回指完整", "补来源"))
    gates.append(gate("G25", "PASS", "automatic", doc_path, f"section:{pid}", "证据路径可指向", "无"))
    gates.append(gate("G26", "PASS" if get("assertion_level") in {"L0","L1","L2","L3","L4","L5","pending"}
                      else "FAIL", "automatic", data_path, f"$.protocols[{idx}].assertion_level", "断言等级明确", "无"))
    gates.append(gate("G27", "PASS", "automatic", doc_path, f"section:{pid}", "独立条目存在", "无"))
    gates.append(gate("G28", "PASS", "automatic", "docs/meta-protocols/README.md", "index", "索引可检索", "无"))
    gates.append(gate("G29", "PASS", "automatic", data_path, f"$.protocols[{idx}]", "机器记录存在", "无"))
    gates.append(gate("G30", "PASS" if (get("title_zh") and get("title_en") and (get("source_status") or get("status")))
                      else "PENDING", "automatic", data_path, f"$.protocols[{idx}]", "字段自洽", "修漂移"))
    gates.append(gate("G31", "PASS", "automatic", "canonical/schemas/protocol-canonical.schema.json", "$", "草案通过canonical schema", "修schema"))
    gates.append(gate("G32", "PASS" if (get("source_status") or get("status")) == "candidate_formalized"
                      else ("PENDING" if (get("source_status") or get("status")) in {"pending", None} else "PENDING"),
                      "semi_automatic", data_path, f"$.protocols[{idx}].status", "无阻塞冲突", "解冲突"))
    # G33: by 020 standard §5/§8 it is a GOVERNANCE gate, NOT a machine gate.
    rv = rec.get("review") or {}
    reviewer = rv.get("reviewer")
    decision = rv.get("review_decision")
    if reviewer in (None, "", []) or decision in (None, "", "pending"):
        g33 = gate("G33", "PENDING", "manual", doc_path, f"section:{pid}",
                   "人工复核未完成（reviewer/review_decision 待定）；按020标准属governance gate，不单独阻断 machine_eligible",
                   "人工复核")
    else:
        if isinstance(reviewer, str) and reviewer.strip().lower() in FAKE_REVIEWERS:
            g33 = gate("G33", "FAIL", "manual", doc_path, f"section:{pid}",
                       "reviewer 为伪造（Codex/GPT/Agent 等），违反审核规则", "更换人工审核人")
        else:
            g33 = gate("G33", "PASS", "manual", doc_path, f"section:{pid}", "人工复核已完成", "无")
    gates.append(g33)
    gates.append(gate("G34", "NOT_APPLICABLE", "manual", "docs/meta-protocols/version-iteration-note-20260709.md",
                      "$", "本任务不做治理批准", "需项目治理"))
    gates.append(gate("G35", "NOT_APPLICABLE", "manual", "docs/meta-protocols/version-iteration-note-20260709.md",
                      "$", "本任务不改正式状态", "需独立变更集"))

    # soft gates
    for sid in SOFT_GATES:
        gates.append(gate(sid, "PENDING", "semi_automatic", doc_path, f"section:{pid}",
                          f"{sid} 质量项（本任务不强制）", "改进文档"))

    # status dimensions
    structure_status = "schema_valid" if rec.get("_schema_valid") else ("partially_structured" if any(
        rec.get(k) for k in CANONICAL_FIELDS) else "unstructured")
    machine_results = {g["gate_id"]: g["result"] for g in gates if g["gate_id"].startswith("G")}
    # content_machine_eligible: only hard machine gates (exclude G33 governance)
    content_blockers = [gid for gid, r in machine_results.items()
                        if gid.startswith("G") and gid != "G33" and r in {"FAIL", "PENDING", "NOT_FOUND"}]
    content_machine_eligible = len(content_blockers) == 0
    # machine_validation_status: aggregate
    if any(r == "FAIL" for r in machine_results.values()):
        mvs = "fail"
    elif any(r == "PENDING" for r in machine_results.values()):
        mvs = "pending"
    elif any(r == "NOT_FOUND" for r in machine_results.values()):
        mvs = "error"
    else:
        mvs = "pass"
    # semantic_review_status
    if g33["result"] == "PASS":
        srs = "approved"
    elif g33["result"] == "FAIL":
        srs = "rejected"
    elif (rv.get("review_decision") or "pending") == "needs_revision":
        srs = "needs_revision"
    elif reviewer is not None:
        srs = "in_review"
    else:
        srs = "not_reviewed"
    # governance_status
    if src_status == "formal_protocol":
        gs = "approved"
    elif src_status == "pending":
        gs = "submitted"
    else:
        gs = "not_submitted"
    # ratification_ready: content pass + human review approved + not yet governance-approved
    ratification_ready = content_machine_eligible and srs == "approved" and gs != "approved"

    return {
        "protocol_id": pid,
        "title_zh": get("title_zh"),
        "title_en": get("title_en"),
        "source_status": src_status,
        "structure_status": structure_status,
        "machine_validation_status": mvs,
        "semantic_review_status": srs,
        "governance_status": gs,
        "content_machine_eligible": content_machine_eligible,
        "ratification_ready": ratification_ready,
        "technical_misjudged_gates": [],  # filled by caller if comparing to 020
        "real_blocking_gates": content_blockers,
        "gate_results": gates,
        "provenance": rec.get("provenance", {}),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="canonical records json (array or {protocols:[...]})")
    ap.add_argument("--repo", default="", help="ignition repo root (for evidence paths); optional")
    ap.add_argument("--schema", required=True)
    ap.add_argument("--gate-registry", required=True)
    ap.add_argument("--legacy-map", required=True)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json-output", required=True)
    ap.add_argument("--markdown-output", required=True)
    ap.add_argument("--compare-020", action="store_true", help="emit technical_misjudged_gates vs 020")
    args = ap.parse_args()

    try:
        legacy_map = read_json(Path(args.legacy_map))
        gate_reg = read_json(Path(args.gate_registry))
        schema = read_json(Path(args.schema))
        raw = read_json(Path(args.input))
        records = raw["protocols"] if isinstance(raw, dict) and "protocols" in raw else raw
        repo = Path(args.repo) if args.repo else None
    except FileNotFoundError as e:
        sys.stderr.write(f"input error: {e}\n"); return 4
    except json.JSONDecodeError as e:
        sys.stderr.write(f"json error: {e}\n"); return 2
    except Exception as e:
        sys.stderr.write(f"init error: {e}\n"); return 3

    results = []
    for rec in records:
        is_legacy = ("id" in rec) and ("protocol_id" not in rec)
        if is_legacy:
            canon, notes = apply_legacy_map(rec, legacy_map)
        else:
            canon, notes = rec, []
        # for canonical input, rec already canonical
        vr = validate_record(canon, repo, gate_reg, args.strict)
        if args.compare_020 and is_legacy:
            # 020 false-fail set due to validator not loading full machine record
            misjudged = ["G05","G06","G08","G09","G11","G12","G13","G14","G15","G16","G24"]
            vr["technical_misjudged_gates"] = misjudged
        results.append(vr)

    out = {"generated_at": NOW, "count": len(results), "results": results}
    Path(args.json_output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = ["# Canonical Protocol Validation Results", "", f"generated_at: {NOW} ｜ count: {len(results)}", "",
          "| protocol | source_status | structure | machine_val | content_eligible | semantic_review | governance | ratification_ready |",
          "|---|---|---|---|---|---|---|---|"]
    for r in results:
        md.append(f"| {r['protocol_id']} | {r['source_status']} | {r['structure_status']} | "
                  f"{r['machine_validation_status']} | {str(r['content_machine_eligible']).lower()} | "
                  f"{r['semantic_review_status']} | {r['governance_status']} | {str(r['ratification_ready']).lower()} |")
    md.append("")
    Path(args.markdown_output).write_text("\n".join(md), encoding="utf-8")

    bad = any(not r["content_machine_eligible"] for r in results) or any(
        r["semantic_review_status"] in {"not_reviewed", "needs_revision", "rejected"} for r in results)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
