#!/usr/bin/env python3
"""Shared helpers for repository-wide counts and overview rendering."""

from __future__ import annotations

import json
import re
from pathlib import Path

from answer_utils import (
    ANSWERS_JSON,
    CATEGORY_MAP_JSON as ANSWERS_CATEGORY_MAP,
    read_json as read_answer_json,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS_META_JSON = REPO_ROOT / "data/functions/meta-functions.json"
BOOTSTRAP_META_TABLE_JSON = REPO_ROOT / "data/functions/bootstrap-meta-function-table.json"
DISCOVERIES_JSON = REPO_ROOT / "data/discoveries/unified-discoveries.json"
DISCOVERIES_CATEGORY_MAP = REPO_ROOT / "data/discoveries/category-map.json"
PREDICTIONS_JSON = REPO_ROOT / "data/predictions/unified-predictions.json"
PREDICTIONS_CATEGORY_MAP = REPO_ROOT / "data/predictions/category-map.json"
ANSWERS_JSON = REPO_ROOT / "data/answers/unified-answers.json"
ANSWERS_CATEGORY_MAP_JSON = REPO_ROOT / "data/answers/category-map.json"
ANALYTIC_SOLUTIONS_JSON = REPO_ROOT / "data/analytic-solutions/unified-analytic-solutions.json"
FUNCTIONS_JSON = REPO_ROOT / "data/functions/unified-functions.json"
CASES_JSON = REPO_ROOT / "data/cases/unified-cases.json"
README = REPO_ROOT / "README.md"


START_MARKER = "<!-- REPOSITORY_OVERVIEW_START -->"
END_MARKER = "<!-- REPOSITORY_OVERVIEW_END -->"


def read_json(path: Path, default):
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return default
    return json.loads(text)


def novelty_counts(items: list[dict]) -> dict[str, int]:
    counts = {"passed": 0, "pending": 0, "inconclusive": 0, "failed": 0}
    for item in items:
        status = item.get("academic_novelty", {}).get("status", "pending")
        if status in counts:
            counts[status] += 1
    return counts


def active_and_lead_counts(items: list[dict]) -> dict[str, int]:
    return {
        "active": sum(1 for item in items if item.get("status") == "active"),
        "leads": sum(1 for item in items if item.get("status") != "active"),
    }


def count_repository_objects(repo_root: Path = REPO_ROOT) -> dict[str, dict[str, int]]:
    meta_functions = read_json(repo_root / "data/functions/meta-functions.json", [])
    bootstrap_meta_table = read_json(repo_root / "data/functions/bootstrap-meta-function-table.json", [])
    discoveries = read_json(repo_root / "data/discoveries/unified-discoveries.json", [])
    predictions = read_json(repo_root / "data/predictions/unified-predictions.json", [])
    answers = read_json(repo_root / "data/answers/unified-answers.json", [])
    analytic_solutions = read_json(repo_root / "data/analytic-solutions/unified-analytic-solutions.json", [])
    functions = read_json(repo_root / "data/functions/unified-functions.json", [])
    cases = read_json(repo_root / "data/cases/unified-cases.json", [])
    discovery_categories = read_json(repo_root / "data/discoveries/category-map.json", [])
    prediction_categories = read_json(repo_root / "data/predictions/category-map.json", [])
    answer_categories = read_json(repo_root / "data/answers/category-map.json", [])

    discovery_novelty = novelty_counts(discoveries)
    prediction_novelty = novelty_counts(predictions)
    answer_novelty = novelty_counts(answers)
    analytic_solution_counts = active_and_lead_counts(analytic_solutions)

    return {
        "discoveries": {
            "curated": len(discoveries),
            "leads": sum(len(entry.get("discovery_leads", [])) for entry in discovery_categories),
            "passed_novelty": discovery_novelty["passed"],
            "pending_novelty": discovery_novelty["pending"],
            "inconclusive_novelty": discovery_novelty["inconclusive"],
            "failed_novelty": discovery_novelty["failed"],
        },
        "predictions": {
            "curated": len(predictions),
            "leads": sum(len(entry.get("prediction_leads", [])) for entry in prediction_categories),
            "passed_novelty": prediction_novelty["passed"],
            "pending_novelty": prediction_novelty["pending"],
            "inconclusive_novelty": prediction_novelty["inconclusive"],
            "failed_novelty": prediction_novelty["failed"],
        },
        "answers": {
            "curated": sum(1 for item in answers if item.get("status") == "active" and item.get("academic_novelty", {}).get("status") == "passed"),
            "leads": sum(1 for item in answers if not (item.get("status") == "active" and item.get("academic_novelty", {}).get("status") == "passed")),
            "passed_novelty": answer_novelty["passed"],
            "pending_novelty": answer_novelty["pending"],
            "inconclusive_novelty": answer_novelty["inconclusive"],
            "failed_novelty": answer_novelty["failed"],
        },
        "analytic_solutions": {
            "active": analytic_solution_counts["active"],
            "leads": analytic_solution_counts["leads"],
        },
        "functions": {
            "meta": len(meta_functions),
            "bootstrap_internal": max(len(bootstrap_meta_table) - 1, 0),
            "bootstrap_total": len(bootstrap_meta_table),
            "ordinary": len(functions),
            "total": len(meta_functions) + len(functions),
            "display": format_function_summary(len(meta_functions), max(len(bootstrap_meta_table) - 1, 0), len(functions)),
        },
        "cases": {
            "total": len(cases),
        },
    }


def format_function_summary(meta_count: int, bootstrap_internal_count: int, ordinary_count: int) -> str:
    if meta_count <= 0:
        if bootstrap_internal_count <= 0:
            return f"{ordinary_count} functions"
        return f"{bootstrap_internal_count} bootstrap items, {ordinary_count} functions"
    meta_label = "meta-function" if meta_count == 1 else "meta-functions"
    bootstrap_label = "bootstrap item" if bootstrap_internal_count == 1 else "bootstrap items"
    ordinary_label = "ordinary function" if ordinary_count == 1 else "ordinary functions"
    if bootstrap_internal_count > 0:
        return f"{meta_count} {meta_label}, {bootstrap_internal_count} {bootstrap_label}, {ordinary_count} {ordinary_label}"
    return f"{meta_count} {meta_label}, {ordinary_count} {ordinary_label}"


def format_discovery_summary(counts: dict[str, int]) -> str:
    return f"{counts['curated']} curated discoveries, {counts['leads']} leads"


def format_prediction_summary(counts: dict[str, int]) -> str:
    parts = [f"{counts['curated']} predictions"]
    novelty_bits = []
    if counts.get("passed_novelty", 0):
        novelty_bits.append(f"{counts['passed_novelty']} passed novelty")
    if counts.get("pending_novelty", 0):
        novelty_bits.append(f"{counts['pending_novelty']} pending novelty review")
    if counts.get("inconclusive_novelty", 0):
        novelty_bits.append(f"{counts['inconclusive_novelty']} inconclusive novelty")
    if counts.get("failed_novelty", 0):
        novelty_bits.append(f"{counts['failed_novelty']} failed novelty")
    if novelty_bits:
        parts.append(", ".join(novelty_bits))
    return ", ".join(parts)


def format_answer_summary(counts: dict[str, int]) -> str:
    parts = [f"{counts['curated']} answers", f"{counts['leads']} leads"]
    novelty_bits = []
    if counts.get("passed_novelty", 0):
        novelty_bits.append(f"{counts['passed_novelty']} passed novelty")
    if counts.get("pending_novelty", 0):
        novelty_bits.append(f"{counts['pending_novelty']} pending novelty review")
    if counts.get("inconclusive_novelty", 0):
        novelty_bits.append(f"{counts['inconclusive_novelty']} inconclusive novelty")
    if counts.get("failed_novelty", 0):
        novelty_bits.append(f"{counts['failed_novelty']} failed novelty")
    if novelty_bits:
        parts.append(", ".join(novelty_bits))
    return ", ".join(parts)


def format_analytic_solution_summary(counts: dict[str, int]) -> str:
    lead_label = "lead" if counts["leads"] == 1 else "leads"
    if counts["active"] > 0:
        active_label = "analytic solution" if counts["active"] == 1 else "analytic solutions"
        return f"{counts['active']} active {active_label}, {counts['leads']} {lead_label}"
    return f"{counts['leads']} {lead_label}"


def render_repository_overview_block(counts: dict[str, dict[str, int]]) -> str:
    lines = [
        START_MARKER,
        "| 区域 / Area | 当前数量 / Current Count | 说明 / Description |",
        "| --- | ---: | --- |",
        f"| [发现 / Discoveries](DISCOVERIES.md) | {format_discovery_summary(counts['discoveries'])} | 从函数、案例与自举循环中产生的新发现。 / New discoveries generated from bootstrap cycles between functions and cases. |",
        f"| [预测 / Predictions](PREDICTIONS.md) | {format_prediction_summary(counts['predictions'])} | 由函数、案例、发现与自举循环推出的可检验未来判断。 / Testable future judgments derived from functions, cases, discoveries, and bootstrap cycles. |",
        f"| [新答案 / New Answers](ANSWERS.md) | {format_answer_summary(counts['answers'])} | 对既有问题、经典问题、未解问题或已有答案的新回答。 / New answers to existing, classic, unresolved, or previously answered questions. |",
        f"| [解析解 / Analytic Solutions](ANALYTIC_SOLUTIONS.md) | {format_analytic_solution_summary(counts['analytic_solutions'])} | 对明确数学问题的符号解、闭式解或可验证表达。 / Symbolic, closed-form, or verifiable solutions to explicit mathematical problems. |",
        f"| [函数表 / Functions](FUNCTIONS.md) | {counts['functions']['display']} | 函数、机制、结构与公式。 / Functions, mechanisms, structures, and formulas. |",
        f"| [案例表 / Cases](CASES.md) | {counts['cases']['total']} cases | 案例、证据、历史对象与验证材料。 / Cases, evidence, historical objects, and verification materials. |",
        END_MARKER,
    ]
    return "\n".join(lines)


def replace_marked_block(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    anchor = "## 入口 / Entrance"
    if anchor in text:
        head, tail = text.split(anchor, 1)
        tail_lines = tail.lstrip("\n")
        return head + anchor + "\n\n" + replacement + "\n" + tail_lines
    return text


def render_readme_overview(readme_path: Path = README) -> str:
    counts = count_repository_objects(readme_path.parent)
    current = readme_path.read_text(encoding="utf-8")
    replacement = render_repository_overview_block(counts)
    return replace_marked_block(current, START_MARKER, END_MARKER, replacement)


def readme_overview_matches(readme_path: Path = README) -> bool:
    current = readme_path.read_text(encoding="utf-8")
    return render_readme_overview(readme_path) == current


def update_readme_overview(readme_path: Path = README) -> bool:
    current = readme_path.read_text(encoding="utf-8")
    updated = render_readme_overview(readme_path)
    if updated == current:
        return False
    readme_path.write_text(updated, encoding="utf-8", newline="\n")
    return True
