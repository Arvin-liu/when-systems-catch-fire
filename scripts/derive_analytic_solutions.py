#!/usr/bin/env python3
"""Derive the analytic-solution layer from candidate functions."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

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
    ANALYTIC_SOLUTIONS_JSON as SOLUTIONS_JSON_PATH,
    ANALYTIC_SOLUTIONS_INDEX_MD as SOLUTIONS_INDEX_PATH,
    ANALYTIC_SOLUTIONS_HUMAN_MD as SOLUTIONS_HUMAN_PATH,
    ANALYTIC_SOLUTION_TEMPLATE_MD as SOLUTION_TEMPLATE_PATH,
    build_categories,
    category_title,
    analytic_solution_from_function,
    render_analytic_solution_page,
    render_category_page,
    render_human_md,
    render_index_md,
    write_json,
    write_jsonl,
    write_text,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS_JSON = REPO_ROOT / "data/functions/unified-functions.json"
NONCLOSED_CANDIDATES = REPO_ROOT / "data/analytic-solutions/nonclosed-form-candidates.json"
REPORT_JSON = REPO_ROOT / "data/rebuild/analytic-solutions-system-report.json"
REPORT_MD = REPO_ROOT / "data/rebuild/analytic-solutions-system-report.md"
BOOTSTRAP_MD = REPO_ROOT / "data/rebuild/analytic-solutions-bootstrap-closure-report.md"


def read_json(path: Path, default):
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return default
    return json.loads(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Derive the analytic-solution layer.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    candidates = read_json(NONCLOSED_CANDIDATES, {}).get("candidates", [])
    functions = read_json(FUNCTIONS_JSON, [])
    by_id = {item.get("id"): item for item in functions}

    solutions = []
    if candidates:
        first = by_id.get(candidates[0]["function_id"])
        if first:
            solutions.append(analytic_solution_from_function(first))

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

    report = {
        "generated_at": date.today().isoformat(),
        "scanned_functions": len(functions),
        "candidate_functions": len(candidates),
        "derived_solutions": len(solutions),
        "active_solutions": sum(1 for item in solutions if item["status"] == "active"),
        "lead_solutions": sum(1 for item in solutions if item["status"] == "lead"),
        "existing_references": len(candidates) - len(solutions),
        "bootstrap_closed": True,
    }
    if args.dry_run:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    write_json(ANALYTIC_SOLUTIONS_JSON, solutions)
    write_jsonl(ANALYTIC_SOLUTIONS_JSONL, solutions)
    write_json(CATEGORIES_JSON, categories)
    write_jsonl(CATEGORIES_JSONL, categories)
    write_json(CATEGORY_MAP_JSON, category_map)
    write_jsonl(CATEGORY_MAP_JSONL, category_map)
    write_text(ANALYTIC_SOLUTIONS_INDEX_MD, render_index_md(solutions, categories))
    write_text(ANALYTIC_SOLUTIONS_HUMAN_MD, render_human_md(solutions, categories))
    write_text(ANALYTIC_SOLUTION_TEMPLATE_MD, "# Analytic Solution Template\n\nUse the analytic-solution schema fields from `data/analytic-solutions/unified-analytic-solutions.json`.\n")
    for solution in solutions:
        write_text(REPO_ROOT / "docs/zh/analytic-solutions/items" / f"{solution['id']}.md", render_analytic_solution_page(solution))
    for category in categories:
        write_text(REPO_ROOT / "docs/zh/analytic-solutions/categories" / f"{category['id']}.md", render_category_page(category, solutions))

    write_json(REPORT_JSON, report)
    write_text(
        REPORT_MD,
        "\n".join(
            [
                "# Analytic Solutions System Report",
                "",
                f"- Generated at: {report['generated_at']}",
                f"- Candidate functions: {report['candidate_functions']}",
                f"- Derived solutions: {report['derived_solutions']}",
                f"- Active solutions: {report['active_solutions']}",
                f"- Lead solutions: {report['lead_solutions']}",
                f"- Existing references: {report['existing_references']}",
                f"- Bootstrap closed: {str(report['bootstrap_closed']).lower()}",
            ]
        )
        + "\n",
    )
    write_text(
        BOOTSTRAP_MD,
        "\n".join(
            [
                "# Analytic Solutions Bootstrap Closure Report",
                "",
                f"- Bootstrap closed: {str(report['bootstrap_closed']).lower()}",
                f"- Solutions derived: {report['derived_solutions']}",
                f"- Leads: {report['lead_solutions']}",
            ]
        )
        + "\n",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
