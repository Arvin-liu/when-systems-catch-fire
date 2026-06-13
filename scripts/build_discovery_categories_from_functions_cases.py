#!/usr/bin/env python3
"""Build discovery category entrances from the current functions and cases tables."""

from __future__ import annotations

from pathlib import Path

from discovery_category_utils import (
    BOOTSTRAP_REPORT_MD,
    CATEGORY_DIR,
    CATEGORIES_JSON,
    CATEGORIES_JSONL,
    CATEGORY_MAP_JSON,
    CATEGORY_MAP_JSONL,
    DISCOVERY_LIST_MD,
    DISCOVERY_INDEX_MD,
    CATEGORY_DEFINITIONS,
    build_category_map,
    classify_bootstrap_items,
    read_json,
    render_bootstrap_report,
    render_category_page,
    render_discovery_index_md,
    render_discoveries_list,
    write_json,
    write_jsonl,
    write_text,
)


def main() -> None:
    functions = read_json(Path(__file__).resolve().parents[1] / "data/functions/unified-functions.json", [])
    cases = read_json(Path(__file__).resolve().parents[1] / "data/cases/unified-cases.json", [])

    classification = classify_bootstrap_items(functions, cases)
    category_map = build_category_map(functions, cases, classification)

    write_json(CATEGORIES_JSON, CATEGORY_DEFINITIONS)
    write_jsonl(CATEGORIES_JSONL, CATEGORY_DEFINITIONS)
    write_json(CATEGORY_MAP_JSON, category_map)
    write_jsonl(CATEGORY_MAP_JSONL, category_map)
    write_text(DISCOVERY_LIST_MD, render_discoveries_list(read_json(Path(__file__).resolve().parents[1] / "data/discoveries/unified-discoveries.json", []), category_map))
    write_text(DISCOVERY_INDEX_MD, render_discovery_index_md(read_json(Path(__file__).resolve().parents[1] / "data/discoveries/unified-discoveries.json", [])))

    CATEGORY_DIR.mkdir(parents=True, exist_ok=True)
    for category in category_map:
        write_text(CATEGORY_DIR / f"{category['category_id']}.md", render_category_page(category))

    write_text(BOOTSTRAP_REPORT_MD, render_bootstrap_report(category_map))

    print(f"built {len(category_map)} discovery categories")


if __name__ == "__main__":
    main()
