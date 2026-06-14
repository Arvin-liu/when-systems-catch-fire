#!/usr/bin/env python3
"""Validate the Effects layer."""

from __future__ import annotations

import argparse
import json

from effects_utils import (
    CATEGORIES_JSON,
    CATEGORY_MAP_JSON,
    EFFECTS_HUMAN_MD,
    EFFECTS_INDEX_MD,
    EFFECTS_JSON,
    EFFECTS_JSONL,
    EFFECT_TEMPLATE_MD,
    build_effects,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Effects layer.")
    parser.add_argument("--check", action="store_true", help="Validate the rendered files.")
    args = parser.parse_args()

    effects, categories = build_effects()
    counts = {
        "active": sum(1 for item in effects if item["status"] == "active"),
        "lead": sum(1 for item in effects if item["status"] == "lead"),
        "categories": len(categories),
    }
    print(json.dumps(counts, ensure_ascii=False, indent=2))

    if args.check:
        required = [EFFECTS_JSON, EFFECTS_JSONL, EFFECTS_INDEX_MD, EFFECTS_HUMAN_MD, CATEGORIES_JSON, CATEGORY_MAP_JSON, EFFECT_TEMPLATE_MD]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            print("Missing effects files:", missing)
            return 1
        print("Effects layer validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
