#!/usr/bin/env python3
"""Helpers for the Analytic Solutions layer."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path

from display_utils import format_bilingual_title


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "data/analytic-solutions"
DOC_DIR = REPO_ROOT / "docs/zh/analytic-solutions"
ITEM_DIR = DOC_DIR / "items"
CATEGORY_DIR = DOC_DIR / "categories"

ANALYTIC_SOLUTIONS_JSON = OUT_DIR / "unified-analytic-solutions.json"
ANALYTIC_SOLUTIONS_JSONL = OUT_DIR / "unified-analytic-solutions.jsonl"
ANALYTIC_SOLUTIONS_INDEX_MD = OUT_DIR / "unified-analytic-solutions-index.md"
ANALYTIC_SOLUTIONS_HUMAN_MD = REPO_ROOT / "ANALYTIC_SOLUTIONS.md"
CATEGORIES_JSON = OUT_DIR / "categories.json"
CATEGORIES_JSONL = OUT_DIR / "categories.jsonl"
CATEGORY_MAP_JSON = OUT_DIR / "category-map.json"
CATEGORY_MAP_JSONL = OUT_DIR / "category-map.jsonl"
ANALYTIC_SOLUTION_TEMPLATE_MD = DOC_DIR / "ANALYTIC_SOLUTION_TEMPLATE.md"


TERM_ZH = {
    "physics": "物理",
    "mathematics": "数学",
    "ai": "AI",
    "systems": "系统",
}


def read_json(path: Path, default):
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return default
    return json.loads(text)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, payloads: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for item in payloads:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def category_title(category_id: str) -> dict[str, str]:
    parts = [part for part in category_id.split("-") if part]
    if not parts:
        return {"zh": "未分类", "en": "Unsorted"}
    zh = "与".join(TERM_ZH.get(part, part) for part in parts)
    en = " and ".join(part.capitalize() if part != "ai" else "AI" for part in parts)
    return {"zh": zh, "en": en}


def analytic_solution_from_function(function_item: dict) -> dict:
    title = function_item.get("title", {})
    category_id = "physics" if "解析解" in (function_item.get("title_text") or "") else "mathematics"
    return {
        "id": "SOL-0001",
        "type": "analytic_solution",
        "status": "lead",
        "source_status": function_item.get("status"),
        "title": {
            "zh": title.get("zh") or function_item.get("title_text") or "解析解候选",
            "en": title.get("en") or "Analytic solution candidate",
        },
        "problem": {
            "zh": "从源函数中提取明确的解析解表达。",
            "en": "Extract an explicit analytic-solution expression from the source function.",
        },
        "formula": {
            "latex": "\\sigma_{opt}=\\sqrt{e}",
            "text": "σ_opt = √e",
        },
        "derivation": [
            "The source record already names the closed-form solution explicitly.",
            "No additional algebraic manipulation is required to identify the closed form.",
            "Keep the legacy function page as a crosswalk reference.",
        ],
        "verification": "The formula is trivially self-consistent as a direct symbolic expression.",
        "assumptions": "Legacy source record already states the solution form.",
        "limitations": "Novelty is not yet confirmed; treat this as a lead until a literature search passes.",
        "academic_novelty": {
            "status": "pending",
            "checked_at": "",
            "query_terms": [title.get("zh") or "σ_opt=√e解析解"],
            "sources_checked": [],
            "nearest_matches": [],
            "novelty_claim": {"zh": "", "en": ""},
            "reviewer_note": "Needs academic novelty review before promotion to active.",
        },
        "related_functions": [function_item.get("id")],
        "related_cases": [],
        "related_effects": [],
        "source_refs": [function_item.get("source", {}).get("source_file", "")],
        "categories": [category_id],
        "page": "docs/zh/analytic-solutions/items/SOL-0001.md",
        "created_at": date.today().isoformat(),
        "updated_at": date.today().isoformat(),
        "license": "CC-BY-NC-4.0",
    }


def build_categories(items: list[dict]) -> list[dict]:
    counts = Counter()
    for item in items:
        for category_id in item.get("categories", []):
            counts[category_id] += 1
    categories = []
    for category_id in sorted(counts):
        categories.append(
            {
                "id": category_id,
                "title": category_title(category_id),
                "page": f"docs/zh/analytic-solutions/categories/{category_id}.md",
                "lead_count": counts[category_id],
                "active_count": sum(1 for item in items if category_id in item.get("categories", []) and item.get("status") == "active"),
            }
        )
    return categories


def render_analytic_solution_page(solution: dict) -> str:
    title = format_bilingual_title(solution["title"].get("zh"), solution["title"].get("en"))
    novelty = solution.get("academic_novelty", {})
    lines = [
        f"# {title}",
        "",
        f"- ID: `{solution['id']}`",
        f"- Status: `{solution['status']}`",
        f"- Source status: `{solution.get('source_status', '')}`",
        f"- Categories: {', '.join(solution.get('categories', [])) or 'None'}",
        f"- Academic novelty: `{novelty.get('status', '')}`",
        "",
        "## Problem",
        f"- {solution.get('problem', {}).get('zh', '')}",
        "",
        "## Formula",
        f"- LaTeX: `{solution.get('formula', {}).get('latex', '')}`",
        f"- Text: {solution.get('formula', {}).get('text', '')}",
        "",
        "## Derivation",
    ]
    for step in solution.get("derivation", []):
        lines.append(f"- {step}")
    lines.extend(
        [
            "",
            "## Verification",
            f"- {solution.get('verification', '')}",
            "",
            "## Assumptions and Limitations",
            f"- Assumptions: {solution.get('assumptions', '')}",
            f"- Limitations: {solution.get('limitations', '')}",
            "",
            "## Related Objects",
            f"- Related functions: {', '.join(solution.get('related_functions', [])) or 'None'}",
            f"- Related cases: {', '.join(solution.get('related_cases', [])) or 'None'}",
            f"- Related effects: {', '.join(solution.get('related_effects', [])) or 'None'}",
            "",
            "## Sources",
            f"- Source refs: {', '.join(solution.get('source_refs', [])) or 'None'}",
        ]
    )
    return "\n".join(lines) + "\n"


def render_category_page(category: dict, items: list[dict]) -> str:
    matched = [item for item in items if category["id"] in item.get("categories", [])]
    lines = [
        f"# {format_bilingual_title(category['title'].get('zh'), category['title'].get('en'))}",
        "",
        f"- ID: `{category['id']}`",
        f"- Lead count: {category.get('lead_count', len(matched))}",
        f"- Active count: {category.get('active_count', 0)}",
        "",
        "## Items",
    ]
    if matched:
        for item in sorted(matched, key=lambda row: row["id"]):
            lines.append(f"- [{item['id']} {format_bilingual_title(item['title'].get('zh'), item['title'].get('en'))}](../items/{item['id']}.md)")
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def render_index_md(items: list[dict], categories: list[dict]) -> str:
    lines = [
        "# Analytic Solutions Index",
        "",
        f"- Total leads: {sum(1 for item in items if item['status'] == 'lead')}",
        f"- Total active: {sum(1 for item in items if item['status'] == 'active')}",
        "",
        "## Categories",
    ]
    for category in categories:
        lines.append(f"- [{format_bilingual_title(category['title'].get('zh'), category['title'].get('en'))}]({category['page']}) - {category.get('lead_count', 0)} leads")
    lines.extend(["", "## Items"])
    for item in sorted(items, key=lambda row: row["id"]):
        lines.append(f"- {item['id']} {format_bilingual_title(item['title'].get('zh'), item['title'].get('en'))}")
    return "\n".join(lines) + "\n"


def render_human_md(items: list[dict], categories: list[dict]) -> str:
    lines = [
        "# Analytic Solutions / 解析解",
        "",
        "## Summary",
        f"- Leads: {sum(1 for item in items if item['status'] == 'lead')}",
        f"- Active: {sum(1 for item in items if item['status'] == 'active')}",
        "",
        "## Categories",
    ]
    for category in categories:
        lines.append(f"- [{format_bilingual_title(category['title'].get('zh'), category['title'].get('en'))}]({category['page']}) - {category.get('lead_count', 0)} leads")
    lines.extend(["", "## Items"])
    for item in sorted(items, key=lambda row: row["id"]):
        lines.append(f"- [{item['id']} {format_bilingual_title(item['title'].get('zh'), item['title'].get('en'))}]({item['page']})")
    return "\n".join(lines) + "\n"
