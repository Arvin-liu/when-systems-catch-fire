#!/usr/bin/env python3
"""Append an effect record to the Effects layer."""

from __future__ import annotations

import argparse
import json
from datetime import date

from effects_utils import (
    EFFECTS_JSON,
    EFFECTS_JSONL,
    build_effects,
    novelty_payload,
    read_json,
    write_json,
    write_jsonl,
    write_text,
    render_category_page,
    render_effect_page,
    render_human_md,
    render_index_md,
    CATEGORIES_JSON,
    CATEGORIES_JSONL,
    CATEGORY_MAP_JSON,
    CATEGORY_MAP_JSONL,
    EFFECTS_INDEX_MD,
    EFFECTS_HUMAN_MD,
    EFFECT_TEMPLATE_MD,
    ITEM_DIR,
    CATEGORY_DIR,
    discipline_title,
)


def next_effect_id(items: list[dict]) -> str:
    nums = [int(item["id"].split("-")[1]) for item in items if item.get("id", "").startswith("EFF-")]
    return f"EFF-{(max(nums) + 1 if nums else 1):04d}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a new effect candidate.")
    parser.add_argument("--title-zh", required=True)
    parser.add_argument("--title-en", required=True)
    parser.add_argument("--discipline", required=True)
    parser.add_argument("--trigger-condition", action="append", default=[])
    parser.add_argument("--observed-change", required=True)
    parser.add_argument("--effect-direction", default="other")
    parser.add_argument("--measurable-signal", required=True)
    parser.add_argument("--related-functions", default="")
    parser.add_argument("--related-cases", default="")
    parser.add_argument("--related-discoveries", default="")
    parser.add_argument("--related-predictions", default="")
    parser.add_argument("--source-refs", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    effects, categories = build_effects()
    effect_id = next_effect_id(effects)
    effect = {
        "id": effect_id,
        "type": "effect",
        "status": "lead",
        "bootstrap_status": "manual",
        "title": {"zh": args.title_zh, "en": args.title_en},
        "discipline": args.discipline,
        "categories": [args.discipline],
        "trigger_conditions": args.trigger_condition,
        "observed_change": args.observed_change,
        "effect_direction": args.effect_direction,
        "measurable_signal": args.measurable_signal,
        "related_functions": [x.strip() for x in args.related_functions.split(",") if x.strip()],
        "related_cases": [x.strip() for x in args.related_cases.split(",") if x.strip()],
        "related_discoveries": [x.strip() for x in args.related_discoveries.split(",") if x.strip()],
        "related_predictions": [x.strip() for x in args.related_predictions.split(",") if x.strip()],
        "related_analytic_solutions": [],
        "source_refs": [x.strip() for x in args.source_refs.split(",") if x.strip()],
        "external_sources": [],
        "mathematical_formalization": {
            "object_type": "effect",
            "symbol": f"E_{{{effect_id}}}",
            "variables": [],
            "math_expression": args.measurable_signal,
            "domain": "",
            "codomain": "",
            "validity_condition": "J_n^+(E)=1 ∧ J_n^-(E)=0",
        },
        "mathematical_derivation": {
            "status": "manual",
            "kind": "manual_effect_entry",
            "depends_on": [],
            "steps_math": [],
            "proof_obligations": [],
            "forward_check": {"status": "pending", "condition": ""},
            "reverse_check": {"status": "pending", "condition": ""},
            "convergence": "",
        },
        "academic_novelty": novelty_payload(args.title_zh, args.observed_change, [x.strip() for x in args.source_refs.split(",") if x.strip()], []),
        "page": f"docs/zh/effects/items/{effect_id}.md",
        "created_at": date.today().isoformat(),
        "updated_at": date.today().isoformat(),
        "license": "CC-BY-NC-4.0",
    }
    if args.dry_run:
        print(json.dumps(effect, ensure_ascii=False, indent=2))
        return 0

    effects.append(effect)
    category_map = [
        {
            "id": category["id"],
            "title": category["title"],
            "page": category["page"],
            "lead_count": category["lead_count"],
            "active_count": category["active_count"],
            "effect_ids": [item["id"] for item in effects if category["id"] in item.get("categories", [])],
        }
        for category in categories
    ]
    write_json(EFFECTS_JSON, effects)
    write_jsonl(EFFECTS_JSONL, effects)
    write_json(CATEGORIES_JSON, categories)
    write_jsonl(CATEGORIES_JSONL, categories)
    write_json(CATEGORY_MAP_JSON, category_map)
    write_jsonl(CATEGORY_MAP_JSONL, category_map)
    write_text(EFFECTS_INDEX_MD, render_index_md(effects, categories))
    write_text(EFFECTS_HUMAN_MD, render_human_md(effects, categories))
    write_text(EFFECT_TEMPLATE_MD, "# Effect Template\n\nUse the effect schema fields from `data/effects/unified-effects.json`.\n")
    write_text(ITEM_DIR / f"{effect['id']}.md", render_effect_page(effect))
    for category in categories:
        write_text(CATEGORY_DIR / f"{category['id']}.md", render_category_page(category, effects))
    print(json.dumps(effect, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
