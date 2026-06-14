#!/usr/bin/env python3
"""Analyze EFF/Q leads against normalized JSONL objects without migration."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
NORMALIZED = ROOT / "data" / "normalized-jsonl"
REBUILD = ROOT / "data" / "rebuild"
OUT = ROOT / "data" / "analysis" / "eff-collision"

TOKEN_RE = re.compile(r"[\u4e00-\u9fff]|[a-z0-9_]+", re.IGNORECASE)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")

FUNCTION_LIKE = {"机制", "映射", "函数", "输入", "输出", "变量", "关系", "约束", "反馈", "门控", "转化", "传播", "计算", "结构", "operator", "mapping", "function"}
EFFECT_LIKE = {"变化", "增强", "衰减", "偏移", "倒转", "阻滞", "相变", "耦合", "可观察", "现象", "信号", "effect", "observable", "phenomenon"}
DISCOVERY_LIKE = {"发现", "看见", "结构", "洞见", "同构", "框架", "解释路径", "discovery", "insight", "framework"}
ANSWER_LIKE = {"问题", "回答", "为什么", "答案", "解释", "question", "answer", "why"}
SOLUTION_LIKE = {"解析解", "闭式", "公式", "推导", "方程", "积分", "反函数", "solution", "closed", "equation"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    return json.loads(text) if text else default


def read_jsonl(path: Path, allow_empty: bool = False) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        if allow_empty:
            return []
        return []
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows)
    path.write_text(body + ("\n" if body else ""), encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(flatten(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(flatten(v) for v in value)
    return str(value)


@lru_cache(maxsize=20000)
def clean_text(text: str) -> str:
    text = MARKDOWN_LINK_RE.sub(r"\1", text or "")
    return " ".join(TOKEN_RE.findall(text.lower()))


def tokens(text: str) -> set[str]:
    return set(clean_text(text).split())


def similarity(a: str, b: str) -> float:
    a_clean = clean_text(a)
    b_clean = clean_text(b)
    if not a_clean or not b_clean:
        return 0.0
    a_tokens = set(a_clean.split())
    b_tokens = set(b_clean.split())
    jaccard = len(a_tokens & b_tokens) / max(len(a_tokens | b_tokens), 1)
    if len(a_clean) + len(b_clean) <= 300:
        seq = difflib.SequenceMatcher(None, a_clean, b_clean).ratio()
    else:
        seq = jaccard
    return round((0.62 * jaccard) + (0.38 * seq), 4)


def object_text(obj: dict[str, Any]) -> str:
    fields = [
        "id",
        "name",
        "name_en",
        "definition",
        "definition_en",
        "description",
        "description_en",
        "derivation",
        "expression",
        "observed_change",
        "effect_direction",
        "trigger_conditions",
        "measurable_signal",
        "question",
        "answer",
        "condition",
        "future_observation",
        "problem",
        "solution",
        "current_label",
        "suggested_class",
        "audit_reason_zh",
        "audit_reason_en",
    ]
    return " ".join(flatten(obj.get(field)) for field in fields if obj.get(field))


def display_name(obj: dict[str, Any]) -> str:
    return flatten(obj.get("name")) or flatten(obj.get("title")) or obj.get("id", "")


def keyword_score(text: str, keywords: set[str]) -> int:
    lowered = text.lower()
    return sum(1 for keyword in keywords if keyword.lower() in lowered)


def load_audit() -> tuple[dict[str, dict[str, Any]], list[str]]:
    missing = []
    audit_by_id: dict[str, dict[str, Any]] = {}
    for path in [
        REBUILD / "effect-leads-identity-audit.jsonl",
        REBUILD / "effect-leads-identity-audit.json",
        REBUILD / "effect-leads-identity-audit-report.json",
        REBUILD / "normalized-jsonl-final-audit-report.json",
        REBUILD / "worktree-dirty-inventory-report.json",
    ]:
        if not path.exists():
            missing.append(str(path.relative_to(ROOT)))
    report = read_json(REBUILD / "effect-leads-identity-audit-report.json", {})
    for item in report.get("items", []):
        audit_by_id[item.get("id", "")] = item
    return audit_by_id, missing


def merged_eff_records() -> tuple[list[dict[str, Any]], dict[str, int], list[str]]:
    effect_leads = read_jsonl(NORMALIZED / "effect-leads.jsonl")
    effects = {row["id"]: row for row in read_jsonl(NORMALIZED / "effects.jsonl")}
    audit_by_id, missing = load_audit()
    merged = []
    for lead in effect_leads:
        eid = lead["id"]
        effect = effects.get(eid, {})
        audit = audit_by_id.get(eid, {})
        audit_result = audit.get("audit_result") or {}
        merged_item = {
            **lead,
            "name": effect.get("name") or audit.get("title_zh") or lead.get("name") or eid,
            "name_en": effect.get("name_en") or audit.get("title_en") or lead.get("name_en") or "",
            "definition": effect.get("definition") or lead.get("definition") or audit_result.get("mathematical_reason_zh") or "",
            "definition_en": effect.get("definition_en") or "",
            "expression": effect.get("expression") or lead.get("expression") or "",
            "derivation": effect.get("derivation") or lead.get("derivation") or "",
            "observed_change": effect.get("observed_change") or "",
            "trigger_conditions": effect.get("trigger_conditions") or "",
            "measurable_signal": effect.get("measurable_signal") or "",
            "related_functions": effect.get("related_functions") or lead.get("related_functions") or [],
            "related_cases": effect.get("related_cases") or lead.get("related_cases") or [],
            "suggested_class_before_collision": audit_result.get("suggested_class") or lead.get("suggested_class") or "needs_human_review",
            "audit_confidence": audit_result.get("confidence") or "low",
            "audit_reason_zh": audit_result.get("mathematical_reason_zh") or lead.get("audit_reason_zh") or "",
            "audit_reason_en": audit_result.get("mathematical_reason_en") or lead.get("audit_reason_en") or "",
            "source_path": audit.get("source_path") or effect.get("canonical_source") or lead.get("canonical_source") or "",
        }
        merged_item["analysis_text"] = object_text(merged_item)
        merged.append(merged_item)
    counts = {
        "effect_leads": len(effect_leads),
        "effects": len(effects),
    }
    return merged, counts, missing


def best_match(source: dict[str, Any], targets: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, float, float, bool]:
    best: dict[str, Any] | None = None
    best_score = 0.0
    best_title = 0.0
    expression_match = False
    source_text = source.get("analysis_text") or object_text(source)
    for target in targets:
        title_score = similarity(display_name(source), display_name(target))
        text_score = similarity(source_text, object_text(target))
        score = round((0.42 * title_score) + (0.58 * text_score), 4)
        src_expr = clean_text(flatten(source.get("expression")))
        tgt_expr = clean_text(flatten(target.get("expression")))
        expr_match = bool(src_expr and tgt_expr and (src_expr == tgt_expr or similarity(src_expr, tgt_expr) >= 0.92))
        if expr_match:
            score = max(score, 0.86)
        if score > best_score:
            best = target
            best_score = score
            best_title = title_score
            expression_match = expr_match
    return best, best_score, best_title, expression_match


def function_match_type(eff: dict[str, Any], score: float, expression_match: bool) -> str:
    suggested = eff.get("suggested_class_before_collision")
    text = eff.get("analysis_text", "")
    functionish = keyword_score(text, FUNCTION_LIKE)
    effectish = keyword_score(text, EFFECT_LIKE)
    if expression_match or score >= 0.62:
        return "covered_by_existing_function"
    if score >= 0.44:
        return "near_duplicate_function"
    if score >= 0.32 and functionish >= effectish:
        return "function_extension_note"
    if suggested == "function_candidate" or (functionish >= 3 and functionish > effectish):
        return "new_function_candidate"
    if score < 0.22 and suggested != "function_candidate":
        return "not_function_like"
    return "needs_human_review"


def recommended_function_action(match_type: str) -> str:
    return {
        "covered_by_existing_function": "merge_into_existing_function_note_later",
        "near_duplicate_function": "needs_human_review",
        "function_extension_note": "merge_into_existing_function_note_later",
        "new_function_candidate": "convert_to_function_candidate_later",
        "not_function_like": "keep_as_effect_lead",
        "needs_human_review": "needs_human_review",
    }[match_type]


def classify_other_match(eff: dict[str, Any], target: dict[str, Any], score: float) -> str:
    klass = target.get("object_class", "")
    suggested = eff.get("suggested_class_before_collision", "")
    text = eff.get("analysis_text", "")
    if klass == "effect" and (target.get("id") == eff.get("id") or score >= 0.55):
        return "existing_effect_overlap"
    if suggested == "discovery_candidate" or keyword_score(text, DISCOVERY_LIKE) >= 3:
        return "discovery_candidate"
    if suggested == "answer_candidate" or keyword_score(text, ANSWER_LIKE) >= 3:
        return "answer_candidate"
    if suggested == "analytic_solution_candidate" or keyword_score(text, SOLUTION_LIKE) >= 3:
        return "analytic_solution_candidate"
    if score >= 0.45:
        return "supplement_note"
    return "needs_human_review"


def case_match_type(score: float) -> str:
    if score >= 0.34:
        return "case_supported_inference"
    if score >= 0.24:
        return "case_note_candidate"
    return "case_missing"


def internal_match_type(score: float, a: dict[str, Any], b: dict[str, Any]) -> str:
    if score >= 0.82:
        return "duplicate_eff_lead"
    if score >= 0.62:
        return "near_duplicate_eff_lead"
    if score >= 0.50:
        return "same_mechanism_different_name"
    a_tokens = tokens(a.get("analysis_text", ""))
    b_tokens = tokens(b.get("analysis_text", ""))
    if a_tokens and b_tokens:
        smaller, larger = sorted([a_tokens, b_tokens], key=len)
        if len(smaller & larger) / max(len(smaller), 1) >= 0.72:
            return "parent_child_relation"
    return "distinct_item"


def suggested_target_layer(suggested_class: str) -> str:
    return {
        "function_candidate": "functions",
        "effect_candidate": "effects",
        "discovery_candidate": "discoveries",
        "answer_candidate": "answers",
        "analytic_solution_candidate": "analytic-solutions",
        "supplement_note": "notes",
        "needs_human_review": "review",
    }.get(suggested_class, "review")


def recommended_plan_action(suggested_class: str) -> str:
    if suggested_class == "effect_candidate":
        return "keep"
    if suggested_class == "supplement_note":
        return "downgrade_to_note_later"
    if suggested_class == "needs_human_review":
        return "needs_human_review"
    return "migrate_later"


def analyze(write_outputs: bool) -> dict[str, Any]:
    effs, eff_counts, missing_inputs = merged_eff_records()
    functions = read_jsonl(NORMALIZED / "functions.jsonl")
    cases = read_jsonl(NORMALIZED / "cases.jsonl")
    effects = read_jsonl(NORMALIZED / "effects.jsonl")
    discoveries = read_jsonl(NORMALIZED / "discoveries.jsonl")
    answers = read_jsonl(NORMALIZED / "answers.jsonl")
    analytic_solutions = read_jsonl(NORMALIZED / "analytic-solutions.jsonl")
    predictions = read_jsonl(NORMALIZED / "predictions.jsonl")
    baseline = read_json(NORMALIZED / "baseline.json", {})

    function_rows = []
    case_rows = []
    other_rows = []
    dedup_rows = []
    plan_rows = []
    function_best: dict[str, dict[str, Any]] = {}
    case_best: dict[str, dict[str, Any]] = {}

    for eff in effs:
        matched_func, func_score, title_score, expression_match = best_match(eff, functions)
        match_type = function_match_type(eff, func_score, expression_match)
        function_row = {
            "eff_id": eff["id"],
            "candidate_name": eff.get("name", ""),
            "suggested_class_before_collision": eff.get("suggested_class_before_collision", ""),
            "matched_function_id": matched_func.get("id", "") if matched_func else "",
            "matched_function_name": display_name(matched_func) if matched_func else "",
            "match_type": match_type,
            "title_similarity": title_score,
            "definition_similarity": func_score,
            "expression_match": expression_match,
            "reason_zh": f"基于标题、定义、表达式与函数层文本的规则相似度，当前最佳函数候选为 {matched_func.get('id', 'none') if matched_func else 'none'}，该判断是推论而非定论。",
            "reason_en": f"Rule-based title, definition, and expression similarity selected {matched_func.get('id', 'none') if matched_func else 'none'} as the best function-side candidate; this is an inference, not a conclusion.",
            "recommended_action": recommended_function_action(match_type),
            "migration_now": False,
            "inference_not_conclusion": True,
        }
        function_rows.append(function_row)
        function_best[eff["id"]] = function_row

        matched_case, case_score, _, _ = best_match(eff, cases)
        ctype = case_match_type(case_score)
        case_row = {
            "eff_id": eff["id"],
            "case_id": matched_case.get("id", "") if matched_case else "",
            "match_type": ctype,
            "similarity": case_score,
            "relation_status": "inference_not_conclusion",
            "entailment_status": "non_entailing",
            "reason_zh": "案例侧只记录可复核的推论映射或缺口，不把案例写成证明。",
            "reason_en": "The case-side row records an auditable inference mapping or gap; it does not treat the case as proof.",
            "migration_now": False,
        }
        case_rows.append(case_row)
        case_best[eff["id"]] = case_row

        other_targets = effects + discoveries + answers + analytic_solutions + predictions
        matched_other, other_score, _, _ = best_match(eff, other_targets)
        other_type = classify_other_match(eff, matched_other or {}, other_score)
        other_rows.append(
            {
                "eff_id": eff["id"],
                "object_id": matched_other.get("id", "") if matched_other else "",
                "object_class": matched_other.get("object_class", "") if matched_other else "",
                "match_type": other_type,
                "similarity": other_score,
                "reason_zh": "跨对象层匹配用于判断是否已有对象覆盖、是否更像发现/答案/解析解或是否只是补充说明。",
                "reason_en": "Cross-layer matching checks whether an existing object overlaps or whether the lead is closer to a discovery, answer, analytic solution, or supplement note.",
                "migration_now": False,
                "inference_not_conclusion": True,
            }
        )

    for idx, left in enumerate(effs):
        for right in effs[idx + 1 :]:
            score = similarity(left.get("analysis_text", ""), right.get("analysis_text", ""))
            dedup_rows.append(
                {
                    "eff_id_a": left["id"],
                    "eff_id_b": right["id"],
                    "match_type": internal_match_type(score, left, right),
                    "similarity": score,
                    "reason_zh": "EFF lead 内部相似度用于后续人工合并判断；本轮不合并。",
                    "reason_en": "Internal similarity supports later human merge decisions; this run does not merge anything.",
                    "merge_now": False,
                }
            )

    duplicates_by_eff: dict[str, list[str]] = defaultdict(list)
    for row in dedup_rows:
        if row["match_type"] != "distinct_item":
            duplicates_by_eff[row["eff_id_a"]].append(row["eff_id_b"])
            duplicates_by_eff[row["eff_id_b"]].append(row["eff_id_a"])

    for eff in effs:
        suggested = eff.get("suggested_class_before_collision") or "needs_human_review"
        frow = function_best[eff["id"]]
        crow = case_best[eff["id"]]
        covered_by = []
        if frow["match_type"] in {"covered_by_existing_function", "near_duplicate_function", "function_extension_note"}:
            covered_by.append(frow["matched_function_id"])
        if eff["id"] in {row.get("id") for row in effects}:
            covered_by.append(eff["id"])
        plan_rows.append(
            {
                "eff_id": eff["id"],
                "current_layer": "effect_lead",
                "current_status": "lead",
                "best_suggested_class": suggested,
                "confidence": eff.get("audit_confidence") or "low",
                "covered_by": sorted(set(x for x in covered_by if x)),
                "near_duplicates": sorted(set(duplicates_by_eff.get(eff["id"], []))),
                "related_cases": [crow["case_id"]] if crow["match_type"] == "case_supported_inference" and crow["case_id"] else [],
                "recommended_target_layer": suggested_target_layer(suggested),
                "recommended_action": recommended_plan_action(suggested),
                "migration_now": False,
                "requires_academic_search_before_active": True,
                "requires_dual_channel_bootstrap_before_active": True,
                "reason_zh": f"沿用身份审查建议 `{suggested}`，并结合函数/案例/对象层相似度。该建议只用于后续迁移任务。",
                "reason_en": f"Uses the identity-audit suggestion `{suggested}` with function, case, and object-layer similarity. This recommendation is only for a later migration task.",
                "inference_not_conclusion": True,
            }
        )

    class_counts = Counter(row["best_suggested_class"] for row in plan_rows)
    near_duplicate_count = sum(1 for row in dedup_rows if row["match_type"] != "distinct_item")
    summary = {
        "report_name": "eff-collision-summary",
        "generated_at": utc_now(),
        "source_commit": git_head(),
        "baseline_source_commit": baseline.get("source_commit"),
        "collision_analysis_only": True,
        "migration_executed": False,
        "academic_search_executed": False,
        "novelty_passed_generated": False,
        "active_promotion_executed": False,
        "full_bootstrap_executed": False,
        "function_case_relation_synthesized": False,
        "missing_input": missing_inputs,
        "input_counts": {
            "effect_leads": eff_counts["effect_leads"],
            "functions": len(functions),
            "cases": len(cases),
            "effects": len(effects),
            "discoveries": len(discoveries),
            "answers": len(answers),
            "analytic_solutions": len(analytic_solutions),
            "predictions": len(predictions),
        },
        "output_counts": {
            "function_candidates": class_counts.get("function_candidate", 0),
            "effect_candidates": class_counts.get("effect_candidate", 0),
            "discovery_candidates": class_counts.get("discovery_candidate", 0),
            "answer_candidates": class_counts.get("answer_candidate", 0),
            "analytic_solution_candidates": class_counts.get("analytic_solution_candidate", 0),
            "supplement_note_candidates": class_counts.get("supplement_note", 0),
            "needs_human_review": class_counts.get("needs_human_review", 0),
            "near_duplicates": near_duplicate_count,
        },
        "function_match_counts": dict(Counter(row["match_type"] for row in function_rows)),
        "case_match_counts": dict(Counter(row["match_type"] for row in case_rows)),
        "other_match_counts": dict(Counter(row["match_type"] for row in other_rows)),
        "internal_dedup_counts": dict(Counter(row["match_type"] for row in dedup_rows)),
    }

    report = render_report(summary, plan_rows, function_rows, case_rows, other_rows, dedup_rows)

    if write_outputs:
        write_jsonl(OUT / "eff-vs-functions.jsonl", function_rows)
        write_jsonl(OUT / "eff-vs-cases.jsonl", case_rows)
        write_jsonl(OUT / "eff-vs-other-objects.jsonl", other_rows)
        write_jsonl(OUT / "eff-internal-dedup.jsonl", dedup_rows)
        write_json(OUT / "eff-collision-summary.json", summary)
        write_jsonl(OUT / "eff-migration-plan.jsonl", plan_rows)
        write_text(OUT / "eff-collision-report.md", report)
    return summary


def render_report(
    summary: dict[str, Any],
    plans: list[dict[str, Any]],
    function_rows: list[dict[str, Any]],
    case_rows: list[dict[str, Any]],
    other_rows: list[dict[str, Any]],
    dedup_rows: list[dict[str, Any]],
) -> str:
    by_class = defaultdict(list)
    for plan in plans:
        by_class[plan["best_suggested_class"]].append(plan)
    high_function = [row for row in function_rows if row["match_type"] in {"covered_by_existing_function", "near_duplicate_function", "function_extension_note"}]
    mapped_cases = [row for row in case_rows if row["match_type"] == "case_supported_inference"]
    internal = [row for row in dedup_rows if row["match_type"] != "distinct_item"]
    needs_review = [plan for plan in plans if plan["best_suggested_class"] == "needs_human_review"]

    def plan_list(items: list[dict[str, Any]]) -> list[str]:
        if not items:
            return ["- None"]
        return [f"- `{item['eff_id']}` → `{item['best_suggested_class']}` ({item['confidence']})" for item in items]

    lines = [
        "# EFF/Q 推论 vs normalized-jsonl 碰撞分析报告",
        "",
        f"- 输入基线 commit / Input baseline commit: `{summary.get('baseline_source_commit')}`",
        f"- 分析运行 commit / Analysis run commit: `{summary['source_commit']}`",
        "- This is a collision analysis, not a final classification.",
        "- This is an inference, not a conclusion.",
        "- Migration must be performed in a separate task.",
        "- Active status requires academic search and dual-channel bootstrap verification.",
        "- 本轮不执行迁移、不删除、不晋级 active。",
        "",
        "## 输入 / Inputs",
        "",
        f"- effect-leads analyzed: {summary['input_counts']['effect_leads']}",
        f"- functions compared: {summary['input_counts']['functions']}",
        f"- cases compared: {summary['input_counts']['cases']}",
        f"- effects compared: {summary['input_counts']['effects']}",
        f"- discoveries compared: {summary['input_counts']['discoveries']}",
        f"- answers compared: {summary['input_counts']['answers']}",
        f"- analytic solutions compared: {summary['input_counts']['analytic_solutions']}",
        "",
        "## 输出摘要 / Output Summary",
        "",
    ]
    for key, value in summary["output_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Likely Function Candidates", ""])
    lines.extend(plan_list(by_class["function_candidate"]))
    lines.extend(["", "## Likely Effect Candidates", ""])
    lines.extend(plan_list(by_class["effect_candidate"]))
    lines.extend(["", "## Likely Discovery / Answer / Analytic Solution Candidates", ""])
    combined = by_class["discovery_candidate"] + by_class["answer_candidate"] + by_class["analytic_solution_candidate"]
    lines.extend(plan_list(combined))
    lines.extend(["", "## 与已有函数高度重合 / High Function Overlap", ""])
    if high_function:
        for row in high_function:
            lines.append(f"- `{row['eff_id']}` ↔ `{row['matched_function_id']}` `{row['match_type']}` score={row['definition_similarity']}")
    else:
        lines.append("- None")
    lines.extend(["", "## 与已有案例的推论映射 / Case-Side Inference Mappings", ""])
    if mapped_cases:
        for row in mapped_cases:
            lines.append(f"- `{row['eff_id']}` ↔ `{row['case_id']}` score={row['similarity']} status=`non_entailing`")
    else:
        lines.append("- None")
    lines.extend(["", "## EFF 内部重复或近似重复 / Internal Similarity Groups", ""])
    if internal:
        for row in internal[:80]:
            lines.append(f"- `{row['eff_id_a']}` ↔ `{row['eff_id_b']}` `{row['match_type']}` score={row['similarity']}")
        if len(internal) > 80:
            lines.append(f"- Additional internal similarity rows omitted from this Markdown summary: {len(internal) - 80}")
    else:
        lines.append("- None")
    lines.extend(["", "## Needs Human Review", ""])
    lines.extend(plan_list(needs_review))
    lines.extend(
        [
            "",
            "## 不执行迁移声明 / No-Migration Statement",
            "",
            "- migration_executed: false",
            "- academic_search_executed: false",
            "- novelty_passed_generated: false",
            "- active_promotion_executed: false",
            "- full_bootstrap_executed: false",
            "- 所有建议均为 inference_not_conclusion=true。",
            "",
            "## 下一步建议 / Next Steps",
            "",
            "- 另开迁移任务处理 `function_candidate`、`discovery_candidate` 或需要合并的对象。",
            "- 迁移前先人工复核高相似函数、案例映射和内部重复组。",
            "- 任何进入 active 的对象必须先通过学术搜索与正反自举验证。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze EFF/Q leads against normalized JSONL objects.")
    parser.add_argument("--dry-run", action="store_true", help="Compute summary without writing files.")
    parser.add_argument("--all", action="store_true", help="Write all analysis outputs.")
    args = parser.parse_args()
    if not args.dry_run and not args.all:
        parser.print_help()
        return 2
    summary = analyze(write_outputs=args.all)
    print(json.dumps({"input_counts": summary["input_counts"], "output_counts": summary["output_counts"], "missing_input": summary["missing_input"]}, ensure_ascii=False, indent=2))
    if args.all:
        print(f"Wrote analysis outputs to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
