#!/usr/bin/env python3
"""Render discovery index pages and internal category maps.

This is the dedicated discovery rendering entrypoint used by the bootstrap
maintenance loop. It keeps the human-facing discovery index, item pages,
internal category maps, and bootstrap report in sync with the structured
discovery data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from discovery_category_utils import (
    BOOTSTRAP_REPORT_MD,
    CATEGORIES_JSON,
    CATEGORIES_JSONL,
    CATEGORY_MAP_JSON,
    CATEGORY_MAP_JSONL,
    DISCOVERY_INDEX_MD,
    DISCOVERY_LIST_MD,
    DISCOVERY_DIR,
    CATEGORY_DEFINITIONS,
    build_category_map,
    classify_bootstrap_items,
    read_json,
    render_bootstrap_report,
    render_discovery_page,
    render_discovery_index_md,
    render_discoveries_list,
    update_category_map_with_discovery,
    write_text,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate rendered outputs without writing")
    args = parser.parse_args()

    functions = read_json(REPO_ROOT / "data/functions/unified-functions.json", [])
    cases = read_json(REPO_ROOT / "data/cases/unified-cases.json", [])
    discoveries = read_json(REPO_ROOT / "data/discoveries/unified-discoveries.json", [])

    classification = classify_bootstrap_items(functions, cases)
    category_map = build_category_map(functions, cases, classification)
    for discovery in discoveries:
        category_map = update_category_map_with_discovery(category_map, discovery)

    planned_writes = [
        (CATEGORIES_JSON, json.dumps(CATEGORY_DEFINITIONS, ensure_ascii=False, indent=2) + "\n"),
        (CATEGORIES_JSONL, "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in CATEGORY_DEFINITIONS) + "\n"),
        (CATEGORY_MAP_JSON, json.dumps(category_map, ensure_ascii=False, indent=2) + "\n"),
        (CATEGORY_MAP_JSONL, "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in category_map) + "\n"),
        (DISCOVERY_LIST_MD, render_discoveries_list(discoveries, category_map)),
        (DISCOVERY_INDEX_MD, render_discovery_index_md(discoveries)),
        (BOOTSTRAP_REPORT_MD, render_bootstrap_report(category_map)),
    ]

    item_dir = DISCOVERY_DIR / "items"
    item_dir.mkdir(parents=True, exist_ok=True)
    for discovery in discoveries:
        planned_writes.append((item_dir / f"{discovery['id']}.md", render_discovery_page(discovery)))

    changed = []
    for path, content in planned_writes:
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            changed.append(path.relative_to(REPO_ROOT).as_posix())
            if not args.check:
                write_text(path, content)

    if args.check:
        if changed:
            print("Discovery render would change:")
            for item in changed:
                print(f"- {item}")
            raise SystemExit(1)
        print(f"render check passed for {len(category_map)} discovery categories")
        return

    print(f"rendered {len(category_map)} discovery categories")


if __name__ == "__main__":
    main()
