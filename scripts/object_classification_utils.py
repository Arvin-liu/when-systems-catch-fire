#!/usr/bin/env python3
"""Helpers for mathematical object classification and crosswalks."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "data/object-classification"
RULES_JSON = OUT_DIR / "mathematical-object-classification-rules.json"
RULES_MD = OUT_DIR / "mathematical-object-classification-rules.md"
CROSSWALK_JSON = OUT_DIR / "object-classification-crosswalk.json"
CROSSWALK_JSONL = OUT_DIR / "object-classification-crosswalk.jsonl"
REPORT_JSON = OUT_DIR / "object-reclassification-report.json"
REPORT_MD = OUT_DIR / "object-reclassification-report.md"
CANDIDATES_JSON = OUT_DIR / "classification-candidates.json"
CANDIDATES_JSONL = OUT_DIR / "classification-candidates.jsonl"
CANDIDATES_REPORT_MD = OUT_DIR / "classification-candidates-report.md"

FUNCTIONS_JSON = REPO_ROOT / "data/functions/unified-functions.json"
ANALYTIC_SOLUTIONS_JSON = REPO_ROOT / "data/analytic-solutions/unified-analytic-solutions.json"


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


def build_rules_payload() -> dict:
    return {
        "updated_at": date.today().isoformat(),
        "rules": [
            {
                "object_class": "function",
                "criterion": "Has a reusable mapping, operator, mechanism, or structural expression with domain and codomain or explicit input-output relation.",
            },
            {
                "object_class": "analytic_solution",
                "criterion": "Gives an explicit symbolic, closed-form, or verifiable solution to a defined mathematical problem.",
            },
            {
                "object_class": "discovery",
                "criterion": "States a new structural insight derived from functions, cases, or bootstrap reasoning.",
            },
            {
                "object_class": "prediction",
                "criterion": "States a testable future judgment with conditions and falsification criteria.",
            },
            {
                "object_class": "answer",
                "criterion": "Provides a new answer to an existing, classic, unresolved, or previously answered question.",
            },
            {
                "object_class": "case",
                "criterion": "Provides evidence, historical context, or verification material for another object class.",
            },
        ],
    }


def build_candidates() -> list[dict]:
    functions = read_json(FUNCTIONS_JSON, [])

    candidates = []
    for item in functions:
        if item.get("title_text") == "σ_opt=√e解析解":
            candidates.append(
                {
                    "legacy_id": item["id"],
                    "legacy_class": "function",
                    "new_class": "analytic_solution",
                    "new_id": "SOL-0001",
                    "reason": "Title explicitly names a closed-form solution.",
                    "mathematical_criterion": "explicit symbolic solution",
                    "migration_action": "copy_with_crosslink",
                    "source_path": item.get("links", {}).get("human_page", ""),
                    "target_path": "docs/zh/analytic-solutions/items/SOL-0001.md",
                    "preserve_legacy_link": True,
                }
            )

    report_items = [
        {
            "legacy_id": item["legacy_id"],
            "legacy_class": item["legacy_class"],
            "new_class": item["new_class"],
            "new_id": item["new_id"],
            "reason": item["reason"],
            "mathematical_criterion": item["mathematical_criterion"],
            "migration_action": item["migration_action"],
            "source_path": item["source_path"],
            "target_path": item["target_path"],
            "preserve_legacy_link": item["preserve_legacy_link"],
        }
        for item in candidates
    ]

    return report_items


def build_report_payload() -> dict:
    functions = read_json(FUNCTIONS_JSON, [])
    analytic_solutions = read_json(ANALYTIC_SOLUTIONS_JSON, [])
    report_items = build_candidates()
    return {
        "generated_at": date.today().isoformat(),
        "functions_count": len(functions),
        "analytic_solutions_count": len(analytic_solutions),
        "needs_human_review_count": 0,
        "crosswalk_count": len(report_items),
        "crosswalk_solution_count": sum(1 for entry in report_items if entry["new_class"] == "analytic_solution"),
        "legacy_links_preserved": True,
        "ordinary_functions_preserved": len(functions),
        "active_new_items_with_passed_novelty": 0,
        "active_new_items_with_pending_novelty": 0,
        "items": report_items,
    }


def render_rules_md() -> str:
    payload = build_rules_payload()
    lines = [
        "# Mathematical Object Classification Rules",
        "",
        "This repository separates mathematical object classes instead of collapsing everything into functions.",
        "",
    ]
    for rule in payload["rules"]:
        lines.append(f"- `{rule['object_class']}`: {rule['criterion']}")
    lines.extend(
        [
            "",
            "## Supported Classes",
            "- function",
            "- analytic_solution",
            "- discovery",
            "- prediction",
            "- answer",
            "- case",
        ]
    )
    return "\n".join(lines) + "\n"


def render_report_md(payload: dict) -> str:
    lines = [
        "# Object Reclassification Report",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Ordinary functions preserved: {payload['ordinary_functions_preserved']}",
        f"- Analytic solution candidates: {payload['analytic_solutions_count']}",
        f"- Crosswalk entries: {payload['crosswalk_count']}",
        f"- Legacy links preserved: {str(payload['legacy_links_preserved']).lower()}",
        "",
        "## Crosswalk",
    ]
    for item in payload["items"]:
        lines.append(
            f"- {item['legacy_id']} ({item['legacy_class']}) -> {item['new_id']} ({item['new_class']}); {item['reason']}"
        )
    return "\n".join(lines) + "\n"


def render_candidates_md(payload: list[dict]) -> str:
    lines = [
        "# Classification Candidates",
        "",
        f"- Total candidates: {len(payload)}",
        "",
    ]
    for item in payload:
        lines.append(
            f"- {item['legacy_id']} ({item['legacy_class']}) -> {item['new_id']} ({item['new_class']}): {item['reason']}"
        )
    return "\n".join(lines) + "\n"
