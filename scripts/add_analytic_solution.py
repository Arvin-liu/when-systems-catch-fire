#!/usr/bin/env python3
"""Append an analytic-solution candidate."""

from __future__ import annotations

import argparse
import json
from datetime import date

from analytic_solution_utils import (
    ANALYTIC_SOLUTIONS_HUMAN_MD,
    ANALYTIC_SOLUTIONS_INDEX_MD,
    ANALYTIC_SOLUTIONS_JSON,
    ANALYTIC_SOLUTIONS_JSONL,
    ANALYTIC_SOLUTION_TEMPLATE_MD,
    CATEGORIES_JSON,
    CATEGORIES_JSONL,
    CATEGORY_MAP_JSON,
    CATEGORY_MAP_JSONL,
    analytic_solution_from_function,
    build_categories,
    category_title,
    render_analytic_solution_page,
    render_category_page,
    render_human_md,
    render_index_md,
    write_json,
    write_jsonl,
    write_text,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a new analytic solution candidate.")
    parser.add_argument("--function-id", required=True)
    parser.add_argument("--title-zh", required=True)
    parser.add_argument("--title-en", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    solution = {
        "id": "SOL-0001",
        "type": "analytic_solution",
        "status": "lead",
        "source_status": "manual",
        "title": {"zh": args.title_zh, "en": args.title_en or "Analytic solution candidate"},
        "problem": {"zh": "", "en": ""},
        "formula": {"latex": "", "text": ""},
        "derivation": [],
        "verification": "",
        "assumptions": "",
        "limitations": "",
        "academic_novelty": {
            "status": "pending",
            "checked_at": "",
            "query_terms": [args.title_zh],
            "sources_checked": [],
            "nearest_matches": [],
            "novelty_claim": {"zh": "", "en": ""},
            "reviewer_note": "Needs academic novelty review before promotion to active.",
        },
        "related_functions": [args.function_id],
        "related_cases": [],
        "related_effects": [],
        "source_refs": [],
        "categories": ["physics"],
        "page": "docs/zh/analytic-solutions/items/SOL-0001.md",
        "created_at": date.today().isoformat(),
        "updated_at": date.today().isoformat(),
        "license": "CC-BY-NC-4.0",
    }
    if args.dry_run:
        print(json.dumps(solution, ensure_ascii=False, indent=2))
        return 0

    solutions = [solution]
    categories = build_categories(solutions)
    category_map = [
        {
            "id": category["id"],
            "title": category["title"],
            "page": category["page"],
            "lead_count": category["lead_count"],
            "active_count": category["active_count"],
            "solution_ids": [item["id"] for item in solutions if category["id"] in item.get("categories", [])],
        }
        for category in categories
    ]

    write_json(ANALYTIC_SOLUTIONS_JSON, solutions)
    write_jsonl(ANALYTIC_SOLUTIONS_JSONL, solutions)
    write_json(CATEGORIES_JSON, categories)
    write_jsonl(CATEGORIES_JSONL, categories)
    write_json(CATEGORY_MAP_JSON, category_map)
    write_jsonl(CATEGORY_MAP_JSONL, category_map)
    write_text(ANALYTIC_SOLUTIONS_INDEX_MD, render_index_md(solutions, categories))
    write_text(ANALYTIC_SOLUTIONS_HUMAN_MD, render_human_md(solutions, categories))
    write_text(ANALYTIC_SOLUTION_TEMPLATE_MD, "# Analytic Solution Template\n\nUse the analytic-solution schema fields from `data/analytic-solutions/unified-analytic-solutions.json`.\n")
    write_text(REPO_ROOT / "docs/zh/analytic-solutions/items" / "SOL-0001.md", render_analytic_solution_page(solution))
    for category in categories:
        write_text(REPO_ROOT / "docs/zh/analytic-solutions/categories" / f"{category['id']}.md", render_category_page(category, solutions))
    print(json.dumps(solution, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    from analytic_solution_utils import REPO_ROOT
    raise SystemExit(main())
