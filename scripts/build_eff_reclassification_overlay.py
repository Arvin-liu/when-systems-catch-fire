#!/usr/bin/env python3
"""Build EFF lead reclassification overlay and candidate queues."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "data" / "analysis" / "eff-collision"
NORMALIZED = ROOT / "data" / "normalized-jsonl"
OUT = ROOT / "data" / "reclassification" / "eff-leads"
REBUILD = ROOT / "data" / "rebuild"
SCHEMA = "eff-lead-reclassification-v1"


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
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return [] if allow_empty else []
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def required_inputs() -> list[Path]:
    return [
        ANALYSIS / "eff-migration-plan.jsonl",
        ANALYSIS / "eff-collision-summary.json",
        ANALYSIS / "eff-vs-functions.jsonl",
        ANALYSIS / "eff-vs-cases.jsonl",
        ANALYSIS / "eff-vs-other-objects.jsonl",
        ANALYSIS / "eff-internal-dedup.jsonl",
        NORMALIZED / "effect-leads.jsonl",
        NORMALIZED / "functions.jsonl",
        NORMALIZED / "cases.jsonl",
        NORMALIZED / "effects.jsonl",
        NORMALIZED / "discoveries.jsonl",
        NORMALIZED / "baseline.json",
    ]


def load_inputs() -> dict[str, Any]:
    missing = [str(path.relative_to(ROOT)) for path in required_inputs() if not path.exists()]
    if missing:
        raise SystemExit("missing_input: " + ", ".join(missing))
    effects = {row["id"]: row for row in read_jsonl(NORMALIZED / "effects.jsonl")}
    effect_leads = {row["id"]: row for row in read_jsonl(NORMALIZED / "effect-leads.jsonl")}
    plans = read_jsonl(ANALYSIS / "eff-migration-plan.jsonl")
    functions = {row["id"]: row for row in read_jsonl(NORMALIZED / "functions.jsonl")}
    cases = {row["id"]: row for row in read_jsonl(NORMALIZED / "cases.jsonl")}
    return {
        "plans": plans,
        "summary": read_json(ANALYSIS / "eff-collision-summary.json", {}),
        "function_matches": {row["eff_id"]: row for row in read_jsonl(ANALYSIS / "eff-vs-functions.jsonl")},
        "case_matches": {row["eff_id"]: row for row in read_jsonl(ANALYSIS / "eff-vs-cases.jsonl")},
        "other_matches": {row["eff_id"]: row for row in read_jsonl(ANALYSIS / "eff-vs-other-objects.jsonl")},
        "dedup": read_jsonl(ANALYSIS / "eff-internal-dedup.jsonl", allow_empty=True),
        "effects": effects,
        "effect_leads": effect_leads,
        "functions": functions,
        "cases": cases,
    }


def base_overlay_record(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "eff_id": plan["eff_id"],
        "original_object_class": "effect_lead",
        "original_status": "lead",
        "best_suggested_class": plan.get("best_suggested_class"),
        "confidence": plan.get("confidence", "low"),
        "recommended_target_layer": plan.get("recommended_target_layer"),
        "recommended_action": plan.get("recommended_action"),
        "migration_now": False,
        "active_promotion_now": False,
        "academic_search_executed": False,
        "academic_novelty_passed": False,
        "requires_academic_search_before_active": True,
        "requires_dual_channel_bootstrap_before_active": True,
        "covered_by": plan.get("covered_by", []),
        "near_duplicates": plan.get("near_duplicates", []),
        "related_cases": plan.get("related_cases", []),
        "source_collision_plan": "data/analysis/eff-collision/eff-migration-plan.jsonl",
        "source_commit": git_head(),
        "generated_at": utc_now(),
        "schema_version": SCHEMA,
        "inference_not_conclusion": True,
        "reason_zh": plan.get("reason_zh", ""),
        "reason_en": plan.get("reason_en", ""),
    }


def effect_payload(eid: str, inputs: dict[str, Any]) -> dict[str, Any]:
    effect = inputs["effects"].get(eid, {})
    lead = inputs["effect_leads"].get(eid, {})
    return {
        "candidate_name": effect.get("name") or lead.get("name") or eid,
        "definition": effect.get("definition") or lead.get("definition") or "",
        "expression": effect.get("expression") or lead.get("expression") or "",
        "trigger_conditions": effect.get("trigger_conditions") or [],
        "observed_change": effect.get("observed_change") or "",
        "effect_direction": effect.get("effect_direction") or "",
        "measurable_signal": effect.get("measurable_signal") or "",
        "related_functions": effect.get("related_functions") or lead.get("related_functions") or [],
        "related_cases": effect.get("related_cases") or lead.get("related_cases") or [],
        "related_effects": effect.get("related_effects") or [],
    }


def build_records(inputs: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    overlay = []
    function_queue = []
    discovery_queue = []
    effect_queue = []
    for plan in inputs["plans"]:
        eid = plan["eff_id"]
        payload = effect_payload(eid, inputs)
        overlay.append(base_overlay_record(plan))
        klass = plan.get("best_suggested_class")
        if klass == "function_candidate":
            function_queue.append(
                {
                    "candidate_id": f"FUNC-LEAD-{eid}",
                    "source_eff_id": eid,
                    "object_class": "function_candidate",
                    "candidate_name": payload["candidate_name"],
                    "definition": payload["definition"],
                    "expression": payload["expression"],
                    "derivation": flatten(inputs["effects"].get(eid, {}).get("derivation", "")),
                    "related_cases": plan.get("related_cases", []),
                    "covered_by_existing_functions": plan.get("covered_by", []),
                    "near_duplicate_functions": [inputs["function_matches"].get(eid, {}).get("matched_function_id", "")],
                    "recommended_action": plan.get("recommended_action"),
                    "migration_now": False,
                    "active_promotion_now": False,
                    "requires_academic_search_before_active": True,
                    "requires_dual_channel_bootstrap_before_active": True,
                    "source_collision_plan": "data/analysis/eff-collision/eff-migration-plan.jsonl",
                    "schema_version": SCHEMA,
                    "inference_not_conclusion": True,
                }
            )
        elif klass == "discovery_candidate":
            discovery_queue.append(
                {
                    "candidate_id": f"DISC-LEAD-{eid}",
                    "source_eff_id": eid,
                    "object_class": "discovery_candidate",
                    "candidate_name": payload["candidate_name"],
                    "description": payload["definition"],
                    "related_functions": payload["related_functions"],
                    "related_cases": payload["related_cases"],
                    "related_effects": [eid],
                    "recommended_action": plan.get("recommended_action"),
                    "migration_now": False,
                    "active_promotion_now": False,
                    "requires_academic_search_before_active": True,
                    "requires_dual_channel_bootstrap_before_active": True,
                    "source_collision_plan": "data/analysis/eff-collision/eff-migration-plan.jsonl",
                    "schema_version": SCHEMA,
                    "inference_not_conclusion": True,
                }
            )
        elif klass == "effect_candidate":
            effect_queue.append(
                {
                    "candidate_id": f"EFF-CAND-{eid}",
                    "source_eff_id": eid,
                    "object_class": "effect_candidate",
                    "candidate_name": payload["candidate_name"],
                    "trigger_conditions": payload["trigger_conditions"],
                    "observed_change": payload["observed_change"],
                    "effect_direction": payload["effect_direction"],
                    "measurable_signal": payload["measurable_signal"],
                    "related_functions": payload["related_functions"],
                    "related_cases": payload["related_cases"],
                    "recommended_action": "keep_as_effect_lead",
                    "migration_now": False,
                    "active_promotion_now": False,
                    "requires_academic_search_before_active": True,
                    "requires_dual_channel_bootstrap_before_active": True,
                    "source_collision_plan": "data/analysis/eff-collision/eff-migration-plan.jsonl",
                    "schema_version": SCHEMA,
                    "inference_not_conclusion": True,
                }
            )
    dedup_groups = []
    group_index = 1
    for row in inputs["dedup"]:
        if row.get("match_type") == "distinct_item":
            continue
        members = [row["eff_id_a"], row["eff_id_b"]]
        dedup_groups.append(
            {
                "group_id": f"EFF-DEDUP-{group_index:04d}",
                "members": members,
                "dedup_type": row["match_type"],
                "representative_candidate": members[0],
                "merge_now": False,
                "recommended_action": "review_later",
                "reason_zh": row.get("reason_zh", "基于碰撞分析的相似组，后续人工复核。"),
                "reason_en": row.get("reason_en", "Similarity group derived from collision analysis for later human review."),
                "source": "data/analysis/eff-collision/eff-internal-dedup.jsonl",
                "schema_version": SCHEMA,
                "inference_not_conclusion": True,
            }
        )
        group_index += 1
    return {
        "overlay": overlay,
        "function_queue": function_queue,
        "discovery_queue": discovery_queue,
        "effect_queue": effect_queue,
        "dedup_groups": dedup_groups,
    }


def build_summary(records: dict[str, list[dict[str, Any]]], inputs: dict[str, Any]) -> dict[str, Any]:
    class_counts = Counter(row["best_suggested_class"] for row in records["overlay"])
    return {
        "report_name": "eff-lead-reclassification-overlay",
        "generated_at": utc_now(),
        "source_commit": git_head(),
        "schema_version": SCHEMA,
        "total_eff_leads": len(records["overlay"]),
        "function_candidates": len(records["function_queue"]),
        "discovery_candidates": len(records["discovery_queue"]),
        "effect_candidates": len(records["effect_queue"]),
        "dedup_candidate_groups": len(records["dedup_groups"]),
        "class_counts": dict(class_counts),
        "migration_executed": False,
        "active_promotion_executed": False,
        "academic_search_executed": False,
        "academic_novelty_passed_generated": False,
        "canonical_eff_modified": False,
        "collision_summary": "data/analysis/eff-collision/eff-collision-summary.json",
        "input_collision_counts": inputs["summary"].get("output_counts", {}),
    }


def render_readme(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# EFF Lead 重分类覆盖层 / EFF Lead Reclassification Overlay",
            "",
            "中文：本目录保存 EFF/Q 碰撞分析后的重分类覆盖记录和候选队列。它不是最终迁移层，也不是 active 对象层。",
            "English: This directory stores reclassification overlay records and candidate queues derived from EFF/Q collision analysis. It is not a final migration layer and not an active object layer.",
            "",
            "中文：所有记录都是推论而非定论。任何候选对象进入 active 前，必须另行通过学术搜索和正反自举验证。",
            "English: All records are inferences, not conclusions. Any candidate object must separately pass academic search and dual-channel bootstrap verification before becoming active.",
            "",
            "中文：EFF 编号不证明对象是效应。",
            "English: EFF numbering does not prove that an object is an effect.",
            "",
            "## Snapshot",
            "",
            f"- total_eff_leads: {summary['total_eff_leads']}",
            f"- function_candidates: {summary['function_candidates']}",
            f"- discovery_candidates: {summary['discovery_candidates']}",
            f"- effect_candidates: {summary['effect_candidates']}",
            f"- dedup_candidate_groups: {summary['dedup_candidate_groups']}",
            "",
        ]
    )


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# EFF Lead Reclassification Overlay Report",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- Source commit: `{summary['source_commit']}`",
        f"- Total EFF leads: {summary['total_eff_leads']}",
        f"- Function candidates: {summary['function_candidates']}",
        f"- Discovery candidates: {summary['discovery_candidates']}",
        f"- Effect candidates: {summary['effect_candidates']}",
        f"- Dedup candidate groups: {summary['dedup_candidate_groups']}",
        "",
        "## Safety",
        "",
        "- migration_executed: false",
        "- active_promotion_executed: false",
        "- academic_search_executed: false",
        "- academic_novelty_passed_generated: false",
        "- canonical_eff_modified: false",
        "",
    ]
    return "\n".join(lines)


def update_derived_views(summary: dict[str, Any]) -> None:
    derived_paths = [
        "data/reclassification/eff-leads/eff-lead-reclassification.jsonl",
        "data/reclassification/eff-leads/function-candidate-queue.jsonl",
        "data/reclassification/eff-leads/discovery-candidate-queue.jsonl",
        "data/reclassification/eff-leads/effect-candidate-queue.jsonl",
        "data/reclassification/eff-leads/eff-dedup-candidate-groups.jsonl",
        "data/reclassification/eff-leads/reclassification-summary.json",
    ]
    views = []
    for path_str in derived_paths:
        path = ROOT / path_str
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        line_count = len(text.splitlines()) if text.strip() else 0
        views.append(
            {
                "path": path_str,
                "line_count": line_count,
                "sha256": sha256(path),
                "view_type": "derived_reclassification_overlay",
                "canonical_object_count": False,
                "source": "data/analysis/eff-collision/",
            }
        )
    for target in [NORMALIZED / "manifest.json", NORMALIZED / "baseline.json"]:
        payload = read_json(target, {})
        payload["derived_views"] = [view for view in payload.get("derived_views", []) if view.get("view_type") != "derived_reclassification_overlay"]
        payload["derived_views"].extend(views)
        payload["derived_views_updated_at"] = summary["generated_at"]
        write_json(target, payload)


def build(write_outputs: bool) -> dict[str, Any]:
    inputs = load_inputs()
    records = build_records(inputs)
    summary = build_summary(records, inputs)
    if write_outputs:
        write_jsonl(OUT / "eff-lead-reclassification.jsonl", records["overlay"])
        write_jsonl(OUT / "function-candidate-queue.jsonl", records["function_queue"])
        write_jsonl(OUT / "discovery-candidate-queue.jsonl", records["discovery_queue"])
        write_jsonl(OUT / "effect-candidate-queue.jsonl", records["effect_queue"])
        write_jsonl(OUT / "eff-dedup-candidate-groups.jsonl", records["dedup_groups"])
        write_json(OUT / "reclassification-summary.json", summary)
        write_text(OUT / "README.md", render_readme(summary))
        write_json(REBUILD / "eff-lead-reclassification-overlay-report.json", summary)
        write_text(REBUILD / "eff-lead-reclassification-overlay-report.md", render_report(summary))
        update_derived_views(summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EFF lead reclassification overlay.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if not args.dry_run and not args.all:
        parser.print_help()
        return 2
    summary = build(write_outputs=args.all)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
