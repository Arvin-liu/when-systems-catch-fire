#!/usr/bin/env python3
"""Validate EFF lead reclassification overlay outputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "data" / "reclassification" / "eff-leads"
ANALYSIS = ROOT / "data" / "analysis" / "eff-collision"
REQUIRED = [
    "eff-lead-reclassification.jsonl",
    "function-candidate-queue.jsonl",
    "discovery-candidate-queue.jsonl",
    "effect-candidate-queue.jsonl",
    "eff-dedup-candidate-groups.jsonl",
    "reclassification-summary.json",
    "README.md",
]


def read_jsonl(path: Path, allow_empty: bool = False) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return [] if allow_empty else []
    rows = []
    for line_number, line in enumerate(text.splitlines(), 1):
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise AssertionError(f"{path.relative_to(ROOT)}:{line_number} not object")
        rows.append(obj)
    return rows


def validate() -> list[str]:
    errors = []
    for name in REQUIRED:
        if not (BASE / name).exists():
            errors.append(f"Missing {name}")
    if errors:
        return errors
    records = read_jsonl(BASE / "eff-lead-reclassification.jsonl")
    function_queue = read_jsonl(BASE / "function-candidate-queue.jsonl", allow_empty=True)
    discovery_queue = read_jsonl(BASE / "discovery-candidate-queue.jsonl", allow_empty=True)
    effect_queue = read_jsonl(BASE / "effect-candidate-queue.jsonl", allow_empty=True)
    dedup = read_jsonl(BASE / "eff-dedup-candidate-groups.jsonl", allow_empty=True)
    summary = json.loads((BASE / "reclassification-summary.json").read_text(encoding="utf-8"))
    collision_summary = json.loads((ANALYSIS / "eff-collision-summary.json").read_text(encoding="utf-8"))

    if len(records) != summary.get("total_eff_leads"):
        errors.append("record count mismatch")
    output_counts = collision_summary.get("output_counts", {})
    if len(function_queue) != output_counts.get("function_candidates"):
        errors.append("function candidate count mismatch")
    if len(discovery_queue) != output_counts.get("discovery_candidates"):
        errors.append("discovery candidate count mismatch")
    if len(effect_queue) != output_counts.get("effect_candidates"):
        errors.append("effect candidate count mismatch")
    for row in records:
        eff_id = row.get("eff_id", "")
        if not re.fullmatch(r"EFF-\d{4}", eff_id):
            errors.append(f"bad eff_id {eff_id}")
        for key in ["migration_now", "active_promotion_now", "academic_novelty_passed"]:
            if row.get(key) is not False:
                errors.append(f"{key} must be false for {eff_id}")
        for key in ["requires_academic_search_before_active", "requires_dual_channel_bootstrap_before_active", "inference_not_conclusion"]:
            if row.get(key) is not True:
                errors.append(f"{key} must be true for {eff_id}")
        if row.get("original_status") == "active" or row.get("recommended_action") == "active":
            errors.append(f"active status detected for {eff_id}")
    for filename, rows in [
        ("function-candidate-queue.jsonl", function_queue),
        ("discovery-candidate-queue.jsonl", discovery_queue),
        ("effect-candidate-queue.jsonl", effect_queue),
    ]:
        for row in rows:
            if row.get("migration_now") is not False:
                errors.append(f"{filename} migration_now must be false")
            if row.get("active_promotion_now") is not False:
                errors.append(f"{filename} active_promotion_now must be false")
            if row.get("requires_academic_search_before_active") is not True:
                errors.append(f"{filename} academic search required")
            if row.get("requires_dual_channel_bootstrap_before_active") is not True:
                errors.append(f"{filename} bootstrap required")
            if row.get("inference_not_conclusion") is not True:
                errors.append(f"{filename} inference flag missing")
    for row in dedup:
        if row.get("merge_now") is not False:
            errors.append(f"dedup merge_now must be false for {row.get('group_id')}")
        if row.get("inference_not_conclusion") is not True:
            errors.append(f"dedup inference flag missing for {row.get('group_id')}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate EFF lead reclassification overlay.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.print_help()
        return 2
    errors = validate()
    if errors:
        print("EFF reclassification overlay validation failed")
        for error in errors:
            print(f"- {error}")
        return 1
    print("EFF reclassification overlay validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
