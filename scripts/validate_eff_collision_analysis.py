#!/usr/bin/env python3
"""Validate EFF collision analysis outputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "data" / "analysis" / "eff-collision"
NORMALIZED = ROOT / "data" / "normalized-jsonl"

REQUIRED = [
    "eff-vs-functions.jsonl",
    "eff-vs-cases.jsonl",
    "eff-vs-other-objects.jsonl",
    "eff-internal-dedup.jsonl",
    "eff-collision-summary.json",
    "eff-migration-plan.jsonl",
    "eff-collision-report.md",
]
FORBIDDEN_LANGUAGE = [
    "academic_novelty.passed",
    "migration_now\":true",
    "migration_now: true",
    "active_promotion_executed\":true",
    "definitive proof",
    "unique explanation",
    "necessary entailment",
    "必然推出",
    "必然指向",
    "唯一解释",
    "双向证明",
]


def read_jsonl(path: Path, allow_empty: bool = False) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        if allow_empty:
            return []
        raise AssertionError(f"{path.relative_to(ROOT)} empty")
    rows = []
    for line_number, line in enumerate(text.splitlines(), 1):
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise AssertionError(f"{path.relative_to(ROOT)}:{line_number} not object")
        rows.append(obj)
    return rows


def normalized_eff_count() -> int:
    path = NORMALIZED / "effect-leads.jsonl"
    return len([line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()])


def validate() -> list[str]:
    errors = []
    for name in REQUIRED:
        if not (BASE / name).exists():
            errors.append(f"Missing {name}")
    if errors:
        return errors

    plans = read_jsonl(BASE / "eff-migration-plan.jsonl")
    expected = normalized_eff_count()
    if len(plans) != expected:
        errors.append(f"migration plan count mismatch: {len(plans)} != {expected}")
    seen = set()
    for plan in plans:
        eff_id = plan.get("eff_id", "")
        if not re.fullmatch(r"EFF-\d{4}", eff_id):
            errors.append(f"bad eff_id: {eff_id}")
        if eff_id in seen:
            errors.append(f"duplicate migration plan: {eff_id}")
        seen.add(eff_id)
        if plan.get("migration_now") is not False:
            errors.append(f"migration_now must be false: {eff_id}")
        if plan.get("inference_not_conclusion") is not True:
            errors.append(f"inference_not_conclusion missing: {eff_id}")
        if plan.get("requires_academic_search_before_active") is not True:
            errors.append(f"academic search required: {eff_id}")
        if plan.get("requires_dual_channel_bootstrap_before_active") is not True:
            errors.append(f"bootstrap required: {eff_id}")
        if not plan.get("best_suggested_class"):
            errors.append(f"missing best_suggested_class: {eff_id}")
        if plan.get("current_status") == "active" or plan.get("best_suggested_class") == "active":
            errors.append(f"active promotion detected: {eff_id}")

    for name in ["eff-vs-functions.jsonl", "eff-vs-other-objects.jsonl"]:
        for row in read_jsonl(BASE / name):
            if row.get("migration_now") is not False:
                errors.append(f"migration_now must be false in {name}: {row.get('eff_id')}")
            if row.get("inference_not_conclusion") is not True:
                errors.append(f"inference_not_conclusion missing in {name}: {row.get('eff_id')}")

    for row in read_jsonl(BASE / "eff-vs-cases.jsonl"):
        if row.get("migration_now") is not False:
            errors.append(f"migration_now must be false in eff-vs-cases: {row.get('eff_id')}")
        if row.get("entailment_status") != "non_entailing":
            errors.append(f"case entailment_status must be non_entailing: {row.get('eff_id')}")

    for row in read_jsonl(BASE / "eff-internal-dedup.jsonl", allow_empty=True):
        if row.get("merge_now") is not False:
            errors.append(f"merge_now must be false: {row.get('eff_id_a')} {row.get('eff_id_b')}")

    summary = json.loads((BASE / "eff-collision-summary.json").read_text(encoding="utf-8"))
    expected_false = [
        "migration_executed",
        "academic_search_executed",
        "novelty_passed_generated",
        "active_promotion_executed",
        "full_bootstrap_executed",
        "function_case_relation_synthesized",
    ]
    for key in expected_false:
        if summary.get(key) is not False:
            errors.append(f"{key} must be false")
    if summary.get("collision_analysis_only") is not True:
        errors.append("collision_analysis_only must be true")

    combined_text = "\n".join((BASE / name).read_text(encoding="utf-8") for name in REQUIRED)
    lowered = combined_text.lower()
    for phrase in FORBIDDEN_LANGUAGE:
        if phrase.lower() in lowered:
            errors.append(f"forbidden phrase found: {phrase}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate EFF collision analysis outputs.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.print_help()
        return 2
    errors = validate()
    if errors:
        print("EFF collision analysis validation failed")
        for error in errors:
            print(f"- {error}")
        return 1
    print("EFF collision analysis validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
