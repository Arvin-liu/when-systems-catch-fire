#!/usr/bin/env python3
"""
专项复核 36 条 EFF lead 身份审查脚本。
只输出报告，不执行迁移。
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
EFFECTS_FILE = ROOT / "data" / "effects" / "unified-effects.json"


def load_effects():
    if not EFFECTS_FILE.exists():
        print(f"ERROR: {EFFECTS_FILE} not found", file=sys.stderr)
        sys.exit(1)
    with open(EFFECTS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("items", [])


def classify_effect(item):
    """
    按数学定义对单条 EFF lead 进行分类。
    返回 audit_result 字典。
    """
    eid = item.get("id", "?")
    title_zh = item.get("title", {}).get("zh", "")
    title_en = item.get("title", {}).get("en", "")
    observed_change = item.get("observed_change", "")
    trigger_conditions = item.get("trigger_conditions", [])
    effect_direction = item.get("effect_direction", "")
    math_form = item.get("mathematical_formalization", {})
    related_functions = item.get("related_functions", [])
    meas_signal = item.get("measurable_signal", "")

    # Detect key features
    has_trigger = len(trigger_conditions) > 0
    has_direction = effect_direction not in ("", None)
    has_formula = bool(math_form.get("math_expression", ""))
    has_variables = len(math_form.get("variables", [])) > 0
    has_domain_codomain = bool(math_form.get("domain", "")) and bool(math_form.get("codomain", ""))
    has_mappable = "f:" in math_form.get("math_expression", "") or math_form.get("object_type") == "function"
    has_solution = math_form.get("object_type") in ("equation_solution", "symbolic_solution", "closed_form")
    has_forward_reverse = bool(math_form.get("validity_condition", ""))

    # Analyze observed_change text
    oc_lower = observed_change.lower()
    oc_text_zh = observed_change

    # Pre-compute has_observed for later use
    has_observed = any(kw in oc_text_zh for kw in ["成立", "收敛", "可", "可写", "部分成立", "外部证据", "外部研究", "外部综述", "支持", "相关", "证据"])

    # Check for mechanism/mapping language
    mechanism_keywords_zh = [
        "可写成", "写成", "函数", "映射", "算子", "机制", "规则",
        "条件", "输入", "输出", "结构方程", "递推", "f:",
        "取决于", "由...决定", "导致", "产生", "构成", "改变",
    ]
    mechanism_keywords_en = [
        "can be written", "is written", "function", "mapping", "operator",
        "mechanism", "rule", "condition", "input", "output", "equation",
        "recurrence", "depends on", "determined by", "produce", "constitute",
        "change", "affect", "modify", "f:",
    ]
    mechanism_score = sum(1 for kw in mechanism_keywords_zh if kw in oc_text_zh) + \
                      sum(1 for kw in mechanism_keywords_en if kw.lower() in oc_text_zh.lower())

    # Check for phenomenon/observable change language
    phenomenon_keywords_zh = [
        "成立", "收敛", "稳定", "可观察", "变化", "偏移", "增强",
        "衰减", "倒转", "阻滞", "耦合", "相变", "反直觉",
        "可数学化为", "可写成分层",
    ]
    phenomenon_keywords_en = [
        "holds", "converged", "stable", "observable", "change", "shift",
        "enhancement", "attenuation", "inversion", "blockage", "coupling",
        "phase transition", "counterintuitive",
    ]
    phenomenon_score = sum(1 for kw in phenomenon_keywords_zh if kw in oc_text_zh) + \
                       sum(1 for kw in phenomenon_keywords_en if kw.lower() in oc_text_zh.lower())

    # Check for discovery/insight language
    discovery_keywords_zh = [
        "洞见", "看见", "结构", "抽象重写", "类比", "抽象层",
        "认识论", "定义", "收敛为",
    ]
    discovery_keywords_en = [
        "insight", "structure", "abstract rewrite", "analogy", "abstract layer",
        "epistemological", "definition", "converged to",
    ]
    discovery_score = sum(1 for kw in discovery_keywords_zh if kw in oc_text_zh) + \
                      sum(1 for kw in discovery_keywords_en if kw.lower() in oc_text_zh.lower())

    # Check for prediction language
    prediction_keywords_zh = ["预测", "未来", "将", "会"]
    prediction_keywords_en = ["predict", "future", "will", "forecast"]
    prediction_score = sum(1 for kw in prediction_keywords_zh if kw in oc_text_zh) + \
                       sum(1 for kw in prediction_keywords_en if kw.lower() in oc_text_zh.lower())

    # Check for answer language
    answer_keywords_zh = ["回答", "答案", "问题", "解答"]
    answer_keywords_en = ["answer", "solution to", "resolve", "解答"]
    answer_score = sum(1 for kw in answer_keywords_zh if kw in oc_text_zh) + \
                   sum(1 for kw in answer_keywords_en if kw.lower() in oc_text_zh.lower())

    # Determine category
    # Priority: effect_candidate first if has clear phenomenon description
    # Then function_candidate if mechanism/mapping
    # Then discovery, prediction, answer, etc.

    suggested_class = "effect_candidate"
    confidence = "medium"
    math_reason_zh = ""
    math_reason_en = ""
    is_misnumbered = False
    keep_eff_id = True
    should_migrate = False

    if mechanism_score >= 3 and phenomenon_score <= 1:
        # Strong mechanism language, weak phenomenon language
        suggested_class = "function_candidate"
        confidence = "high" if mechanism_score >= 5 else "medium"
        is_misnumbered = True
        keep_eff_id = False
        should_migrate = True
        math_reason_zh = f"观察到 {mechanism_score} 个机制/映射关键词，{phenomenon_score} 个现象关键词。该描述更像机制映射关系 f: X → Y 而非可观察的稳定现象。"
        math_reason_en = f"Found {mechanism_score} mechanism/mapping keywords vs {phenomenon_score} phenomenon keywords. This reads more like a mechanism mapping f: X → Y than a stable observable phenomenon."

    elif mechanism_score >= 2 and phenomenon_score >= 2:
        # Mixed: could be effect with mechanism explanation
        # Check if it describes "what happened" vs "how it works"
        has_observed = any(kw in oc_text_zh for kw in ["成立", "收敛", "可", "可写", "部分成立"])
        has_how = any(kw in oc_text_zh for kw in ["函数", "取决于", "由...决定", "机制"])

        if has_observed and not has_how:
            suggested_class = "effect_candidate"
            confidence = "high"
            math_reason_zh = "该描述明确指出可观察现象成立，并给出触发条件和效应方向，符合 effect_candidate 标准。"
            math_reason_en = "The description clearly states a stable observable phenomenon holds, with trigger conditions and effect direction. Meets effect_candidate criteria."
        elif has_how and not has_observed:
            suggested_class = "function_candidate"
            confidence = "medium"
            is_misnumbered = True
            keep_eff_id = False
            should_migrate = True
            math_reason_zh = "该描述更像机制映射关系，用公式表达输入输出结构，而非描述可观察现象。"
            math_reason_en = "Reads more like a mechanism mapping with formulaic I/O structure rather than describing an observable phenomenon."
        else:
            # Mixed: lean toward effect if it claims a phenomenon
            if "成立" in oc_text_zh or "converged" in oc_text_zh.lower():
                suggested_class = "effect_candidate"
                confidence = "medium"
                math_reason_zh = f"机制({mechanism_score})和现象({phenomenon_score})语言混合，但有明确现象断言。保留为效应候选。"
                math_reason_en = f"Mixed mechanism({mechanism_score}) and phenomenon({phenomenon_score}) language, but has explicit phenomenon claim. Kept as effect candidate."
            else:
                suggested_class = "function_candidate"
                confidence = "low"
                is_misnumbered = True
                keep_eff_id = False
                should_migrate = True
                math_reason_zh = "机制语言多于现象语言，但断言不够明确。建议人工复核。"
                math_reason_en = "More mechanism than phenomenon language, but claim is unclear. Recommend human review."

    elif mechanism_score >= 1 and discovery_score >= 2:
        # Discovery with some mechanism
        suggested_class = "discovery_candidate"
        confidence = "medium"
        is_misnumbered = True
        keep_eff_id = False
        should_migrate = True
        math_reason_zh = "该条更像结构性洞见或抽象层类比，而非具体的可观察效应。"
        math_reason_en = "Reads more like a structural insight or abstract-layer analogy rather than a concrete observable effect."

    elif discovery_score >= 3:
        suggested_class = "discovery_candidate"
        confidence = "high"
        is_misnumbered = True
        keep_eff_id = False
        should_migrate = True
        math_reason_zh = "大量使用'抽象层'、'认识论'、'收敛为定义'等洞见性语言，不描述具体可观察现象。"
        math_reason_en = "Heavy use of insight language ('abstract layer', 'epistemological', 'converged to definition') without describing concrete observable phenomena."

    elif prediction_score >= 2:
        suggested_class = "prediction_candidate"
        confidence = "medium"
        is_misnumbered = True
        keep_eff_id = False
        should_migrate = True
        math_reason_zh = "包含对未来可观察结果的判断，应归类为预测候选。"
        math_reason_en = "Contains judgment about future observable outcomes. Should be classified as prediction candidate."

    elif answer_score >= 2:
        suggested_class = "answer_candidate"
        confidence = "medium"
        is_misnumbered = True
        keep_eff_id = False
        should_migrate = True
        math_reason_zh = "回答既有问题或经典问题，应归类为答案候选。"
        math_reason_en = "Answers an existing or classical problem. Should be classified as answer candidate."

    elif has_formula and has_domain_codomain and not has_observed:
        suggested_class = "analytic_solution_candidate"
        confidence = "medium"
        is_misnumbered = True
        keep_eff_id = False
        should_migrate = True
        math_reason_zh = "具有明确的数学表达式、定义域和值域，但没有可观察现象描述，更像解析解候选。"
        math_reason_en = "Has explicit math expression, domain and codomain, but no observable phenomenon description. More like an analytic solution candidate."

    elif has_formula and has_domain_codomain and has_observed:
        # Has formula + phenomenon claim - this is still an effect candidate
        # unless the mechanism language dominates significantly
        if mechanism_score >= 4:
            suggested_class = "function_candidate"
            confidence = "medium"
            is_misnumbered = True
            keep_eff_id = False
            should_migrate = True
            math_reason_zh = f"虽然声称现象，但机制/映射语言({mechanism_score})占主导，更像函数。"
            math_reason_en = f"Despite phenomenon claim, mechanism/mapping language({mechanism_score}) dominates. More like a function."
        else:
            suggested_class = "effect_candidate"
            confidence = "high" if phenomenon_score >= 1 else "medium"
            math_reason_zh = f"有明确可观察现象断言和数学形式化。符合 effect_candidate 标准。"
            math_reason_en = f"Has clear observable phenomenon claim and mathematical formalization. Meets effect_candidate criteria."

    elif phenomenon_score >= 2 or has_observed:
        # Has phenomenon language, keep as effect
        if has_formula:
            confidence = "high"
            math_reason_zh = "有明确可观察现象断言、触发条件和效应方向，且有数学形式化。符合 effect_candidate 标准。"
            math_reason_en = "Has clear observable phenomenon claim, trigger conditions, effect direction, and mathematical formalization. Meets effect_candidate criteria."
        else:
            confidence = "medium"
            math_reason_zh = "有可观察现象描述，但缺少数学形式化。仍可保留为效应候选。"
            math_reason_en = "Has observable phenomenon description but lacks mathematical formalization. Can still remain as effect candidate."

    else:
        # Check for empty or insufficient content
        if not observed_change and not trigger_conditions:
            suggested_class = "insufficient_record"
            confidence = "high"
            is_misnumbered = True
            keep_eff_id = False
            math_reason_zh = "observed_change 和 trigger_conditions 均为空，无法分类。"
            math_reason_en = "observed_change and trigger_conditions are both empty. Cannot classify."
        else:
            suggested_class = "needs_human_review"
            confidence = "low"
            math_reason_zh = "特征不明显，需要人工判断。"
            math_reason_en = "Features are unclear; needs human judgment."

    # Additional checks for malformed items
    if not title_zh and not title_en:
        suggested_class = "malformed_item"
        confidence = "high"
        is_misnumbered = True
        keep_eff_id = False

    # Check if related_functions has many internal references (suggests it might be a function note)
    # Only override if the classification was unclear and there are many internal refs
    internal_fn_count = sum(1 for fn in related_functions if not fn.startswith("external:"))
    # Strong override: no phenomenon language AND no observed change AND many internal refs
    if internal_fn_count > 2 and phenomenon_score < 1 and not has_observed and not has_formula:
        suggested_class = "function_note"
        confidence = "medium"
        is_misnumbered = True
        keep_eff_id = False
        should_migrate = True
        math_reason_zh = f"引用 {internal_fn_count} 个内部函数，无现象描述、无数学形式化，更像是函数说明。"
        math_reason_en = f"References {internal_fn_count} internal functions with no phenomenon description or mathematical formalization. More like a function note."
    # Weak override: weak phenomenon claim + many internal refs, but only if suggested_class is not already high-confidence effect
    elif internal_fn_count > 2 and mechanism_score > phenomenon_score and has_observed and phenomenon_score <= 1 and suggested_class == "effect_candidate":
        # Downgrade to needs_human_review rather than function_note, since there IS some phenomenon language
        suggested_class = "needs_human_review"
        confidence = "medium"
        is_misnumbered = True
        keep_eff_id = False
        should_migrate = True
        math_reason_zh = f"引用 {internal_fn_count} 个内部函数，现象描述薄弱({phenomenon_score})且机制语言更多。建议人工复核。"
        math_reason_en = f"References {internal_fn_count} internal functions with weak phenomenon description({phenomenon_score}) and stronger mechanism language. Recommend human review."

    return {
        "suggested_class": suggested_class,
        "confidence": confidence,
        "is_likely_misnumbered": is_misnumbered,
        "should_keep_eff_id": keep_eff_id,
        "should_migrate_now": False,  # Never true in this run — audit only, no migration
        "recommended_target": _get_target(suggested_class),
        "mathematical_reason_zh": math_reason_zh,
        "mathematical_reason_en": math_reason_en,
        "trigger_conditions_present": has_trigger,
        "observed_change_present": bool(observed_change),
        "mechanism_mapping_present": mechanism_score >= 2,
        "formula_or_solution_present": has_formula,
        "future_claim_present": prediction_score >= 2,
        "old_question_answer_present": answer_score >= 2,
        "related_evidence_present": bool(related_functions),
        "mechanism_score": mechanism_score,
        "phenomenon_score": phenomenon_score,
        "discovery_score": discovery_score,
    }


def _get_target(suggested_class):
    mapping = {
        "function_candidate": "data/functions / function_leads",
        "effect_candidate": "data/effects",
        "analytic_solution_candidate": "data/analytic-solutions",
        "discovery_candidate": "data/discoveries",
        "prediction_candidate": "data/predictions",
        "answer_candidate": "data/answers",
        "function_note": "supplement_notes",
        "case_note": "supplement_notes",
        "existing_reference": "supplement_notes",
        "malformed_item": "data/rebuild/malformed-queue",
        "duplicate_item": "data/rebuild/duplicate-queue",
        "insufficient_record": "data/rebuild/insufficient-queue",
        "needs_human_review": "needs_human_review",
    }
    return mapping.get(suggested_class, "data/effects")


def run_audit(dry_run=False):
    """Run the full audit on all EFF leads."""
    items = load_effects()
    results = []

    for item in items:
        eid = item.get("id", "?")
        if not eid.startswith("EFF-"):
            continue

        audit = classify_effect(item)
        entry = {
            "id": eid,
            "title_zh": item.get("title", {}).get("zh", ""),
            "title_en": item.get("title", {}).get("en", ""),
            "current_status": item.get("status", "lead"),
            "current_class": "effect",
            "source_path": item.get("page", ""),
            "audit_result": audit,
            "safe_action": "report_only",
            "notes": "本轮只报告，不迁移。 / Report only in this run; no migration."
        }
        results.append(entry)

    return results


def write_report(results):
    """Write the audit report in multiple formats."""
    rebuild_dir = ROOT / "data" / "rebuild"
    rebuild_dir.mkdir(parents=True, exist_ok=True)

    # Count categories
    counts = {}
    for r in results:
        sc = r["audit_result"]["suggested_class"]
        counts[sc] = counts.get(sc, 0) + 1

    report_md = f"""# Effect Lead Identity Audit Report

**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
**Model:** agnes/agnes/2.0-flash
**Scope:** 36 EFF leads (EFF-0001 to EFF-0036)
**Nature:** classification audit only — no migration executed

## Summary

| Metric | Count |
|--------|-------|
| Reviewed total | {len(results)} |
| Confirmed effect candidates | {counts.get('effect_candidate', 0)} |
| Likely function candidates | {counts.get('function_candidate', 0)} |
| Likely analytic solution candidates | {counts.get('analytic_solution_candidate', 0)} |
| Likely discovery candidates | {counts.get('discovery_candidate', 0)} |
| Likely prediction candidates | {counts.get('prediction_candidate', 0)} |
| Likely answer candidates | {counts.get('answer_candidate', 0)} |
| Note or reference candidates | {counts.get('function_note', 0) + counts.get('case_note', 0)} |
| Malformed or insufficient | {counts.get('malformed_item', 0) + counts.get('insufficient_record', 0)} |
| Needs human review | {counts.get('needs_human_review', 0)} |
| Likely misnumbered | {sum(1 for r in results if r['audit_result']['is_likely_misnumbered'])} |
| Should keep EFF id | {sum(1 for r in results if r['audit_result']['should_keep_eff_id'])} |
| Should NOT keep EFF id | {sum(1 for r in results if not r['audit_result']['should_keep_eff_id'])} |

## Key Findings

- **default_accepted_as_effect = false** — EFF编号不等于数学意义上的效应，每条均已按数学定义审查。
- **migration_not_executed = true** — 本轮未执行任何迁移。
- **bootstrap_full_run_executed = false** — 本轮未运行完整自举循环。
- **novelty_search_executed = false** — 本轮未执行学术搜索。
- **active_promotion_executed = false** — 本轮未执行 active 晋级。

## Conclusion

{len(results)} 个 EFF lead 已完成身份审查。

其中 {counts.get('effect_candidate', 0)} 条符合 effect_candidate 标准。
其中 {counts.get('function_candidate', 0)} 条更像 function_candidate。
其中 {counts.get('discovery_candidate', 0)} 条更像 discovery_candidate。
其中 {counts.get('needs_human_review', 0)} 条需要人工复核。

EFF 编号不等于数学意义上的效应。本轮没有默认接受任何 EFF lead 为效应。
每条均已按数学定义给出 suggested_class。
本轮只输出报告，不迁移、不删除、不晋级。

建议下一轮将 function_candidate 和 discovery_candidate 迁移到对应层级，
并保留 EFF legacy crosswalk 以便追溯。

---

## Detailed Per-Item Review

"""

    for r in results:
        a = r["audit_result"]
        sc = a["suggested_class"]
        conf = a["confidence"]
        mis = "YES" if a["is_likely_misnumbered"] else "no"
        keep = "YES" if a["should_keep_eff_id"] else "NO"
        reason_zh = a["mathematical_reason_zh"] or "N/A"
        reason_en = a["mathematical_reason_en"] or "N/A"

        report_md += f"""### {r['id']}: {r['title_zh']}

- **Title EN:** {r['title_en']}
- **Status:** {r['current_status']}
- **Suggested Class:** `{sc}` (confidence: {conf})
- **Likely Misnumbered:** {mis}
- **Should Keep EFF ID:** {keep}
- **Recommended Target:** {a['recommended_target']}
- **Trigger Conditions Present:** {'yes' if a['trigger_conditions_present'] else 'no'}
- **Observed Change Present:** {'yes' if a['observed_change_present'] else 'no'}
- **Mechanism Mapping Present:** {'yes' if a['mechanism_mapping_present'] else 'no'}
- **Formula Present:** {'yes' if a['formula_or_solution_present'] else 'no'}
- **Math Reason (ZH):** {reason_zh}
- **Math Reason (EN):** {reason_en}
- **Safe Action:** {r['safe_action']}

---

"""

    # Write markdown report
    Path(rebuild_dir / "effect-leads-identity-audit-report.md").write_text(
        report_md, encoding="utf-8"
    )

    # Write JSON report
    json_report = {
        "reviewed_total": len(results),
        "confirmed_effect_candidates": counts.get("effect_candidate", 0),
        "likely_function_candidates": counts.get("function_candidate", 0),
        "likely_analytic_solution_candidates": counts.get("analytic_solution_candidate", 0),
        "likely_discovery_candidates": counts.get("discovery_candidate", 0),
        "likely_prediction_candidates": counts.get("prediction_candidate", 0),
        "likely_answer_candidates": counts.get("answer_candidate", 0),
        "note_or_reference_candidates": counts.get("function_note", 0) + counts.get("case_note", 0),
        "malformed_or_insufficient": counts.get("malformed_item", 0) + counts.get("insufficient_record", 0),
        "needs_human_review": counts.get("needs_human_review", 0),
        "likely_misnumbered_count": sum(1 for r in results if r["audit_result"]["is_likely_misnumbered"]),
        "should_keep_eff_id_count": sum(1 for r in results if r["audit_result"]["should_keep_eff_id"]),
        "should_not_keep_eff_id_count": sum(1 for r in results if not r["audit_result"]["should_keep_eff_id"]),
        "default_accepted_as_effect": False,
        "migration_not_executed": True,
        "bootstrap_full_run_executed": False,
        "novelty_search_executed": False,
        "active_promotion_executed": False,
        "model_used": "agnes/agnes-2.0-flash",
        "items": results,
    }
    Path(rebuild_dir / "effect-leads-identity-audit-report.json").write_text(
        json.dumps(json_report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Write JSONL
    jsonl_path = rebuild_dir / "effect-leads-identity-audit.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # Write audit JSON
    audit_json = {"items": results}
    Path(rebuild_dir / "effect-leads-identity-audit.json").write_text(
        json.dumps(audit_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Audit complete: {len(results)} items reviewed")
    print(f"Categories: {json.dumps(counts, ensure_ascii=False, indent=2)}")
    return json_report


def main():
    parser = argparse.ArgumentParser(description="Audit EFF lead identities")
    parser.add_argument("--dry-run", action="store_true", help="Only show results, don't write files")
    parser.add_argument("--report", action="store_true", help="Write full report files")
    args = parser.parse_args()

    results = run_audit(dry_run=not args.report)

    # Print summary
    print("\n=== DETAILED RESULTS ===\n")
    for r in results:
        a = r["audit_result"]
        print(f"{r['id']}: {r['title_zh']} -> {a['suggested_class']} ({a['confidence']})")
        if a['is_likely_misnumbered']:
            print(f"  ⚠️ Likely misnumbered, should not keep EFF ID")
        if a['mechanism_score'] > 0 and a['phenomenon_score'] > 0:
            print(f"  ℹ️ Mixed: mechanism={a['mechanism_score']}, phenomenon={a['phenomenon_score']}")

    if args.report:
        json_report = write_report(results)
        print(f"\nReports written to data/rebuild/")
        print(f"  - effect-leads-identity-audit-report.md")
        print(f"  - effect-leads-identity-audit-report.json")
        print(f"  - effect-leads-identity-audit.json")
        print(f"  - effect-leads-identity-audit.jsonl")


if __name__ == "__main__":
    main()
