#!/usr/bin/env python3
"""Render the Effects layer from the 0000 GetNote-derived effect candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from effects_utils import (
    CATEGORIES_JSON,
    CATEGORIES_JSONL,
    CATEGORY_MAP_JSON,
    CATEGORY_MAP_JSONL,
    DOC_DIR,
    EFFECTS_HUMAN_MD,
    EFFECTS_INDEX_MD,
    EFFECTS_JSON,
    EFFECTS_JSONL,
    EFFECT_TEMPLATE_MD,
    ITEM_DIR,
    CATEGORY_DIR,
    build_effects,
    render_category_page,
    render_effect_page,
    render_human_md,
    render_index_md,
    write_json,
    write_jsonl,
    write_text,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the Effects layer.")
    parser.add_argument("--check", action="store_true", help="Validate the currently rendered files.")
    args = parser.parse_args()

    effects, categories = build_effects()
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

    if args.check:
        expected_files = [
            EFFECTS_JSON,
            EFFECTS_JSONL,
            EFFECTS_INDEX_MD,
            EFFECTS_HUMAN_MD,
            CATEGORIES_JSON,
            CATEGORIES_JSONL,
            CATEGORY_MAP_JSON,
            CATEGORY_MAP_JSONL,
            EFFECT_TEMPLATE_MD,
        ]
        if not all(path.exists() for path in expected_files):
            missing = [str(path) for path in expected_files if not path.exists()]
            print("Missing effects files:", missing)
            return 1
        print("Effects layer files exist")
        return 0

    write_json(EFFECTS_JSON, effects)
    write_jsonl(EFFECTS_JSONL, effects)
    write_json(CATEGORIES_JSON, categories)
    write_jsonl(CATEGORIES_JSONL, categories)
    write_json(CATEGORY_MAP_JSON, category_map)
    write_jsonl(CATEGORY_MAP_JSONL, category_map)
    write_text(EFFECTS_INDEX_MD, render_index_md(effects, categories))
    write_text(EFFECTS_HUMAN_MD, render_human_md(effects, categories))
    write_text(EFFECT_TEMPLATE_MD, "# Effect Template\n\nUse the effect schema fields from `data/effects/unified-effects.json`.\n")
    for effect in effects:
        write_text(ITEM_DIR / f"{effect['id']}.md", render_effect_page(effect))
    for category in categories:
        write_text(CATEGORY_DIR / f"{category['id']}.md", render_category_page(category, effects))
    print(json.dumps({"effects": len(effects), "categories": len(categories)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
