#!/usr/bin/env python3
"""Validate and append a new answer record."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from answer_utils import (
    ANSWERS_JSON,
    ANSWERS_JSONL,
    ANSWERS_INDEX_MD,
    CATEGORY_DEFINITIONS,
    CATEGORY_MAP_JSON,
    CATEGORY_MAP_JSONL,
    build_category_map,
    normalize_source_refs,
    next_answer_id,
    read_json,
    render_answer_index,
    render_answer_index_md,
    render_answer_page,
    render_category_page,
    write_json,
    write_jsonl,
    write_text,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS_JSON = REPO_ROOT / "data/functions/unified-functions.json"
CASES_JSON = REPO_ROOT / "data/cases/unified-cases.json"
DISCOVERIES_JSON = REPO_ROOT / "data/discoveries/unified-discoveries.json"
PREDICTIONS_JSON = REPO_ROOT / "data/predictions/unified-predictions.json"


def csv_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def build_payload(args: argparse.Namespace, answers: list[dict]) -> dict:
    answer_id = next_answer_id(answers)
    novelty_status = args.novelty_status or "pending"
    status = args.status or "draft"
    if novelty_status != "passed" and status == "active":
        status = "answer_pending_novelty_review"

    payload = {
        "id": answer_id,
        "title": {"zh": args.title_zh, "en": args.title_en},
        "question": {"zh": args.question_zh, "en": args.question_en},
        "answer": {"zh": args.answer_zh, "en": args.answer_en},
        "prior_answers": {"zh": args.prior_answers_zh, "en": args.prior_answers_en},
        "new_explanation": {"zh": args.new_explanation_zh, "en": args.new_explanation_en},
        "basis": {"zh": args.basis_zh, "en": args.basis_en},
        "testability": {"zh": args.testability_zh, "en": args.testability_en},
        "categories": csv_list(args.categories),
        "related_functions": csv_list(args.functions),
        "related_cases": csv_list(args.cases),
        "related_discoveries": csv_list(args.discoveries),
        "related_predictions": csv_list(args.predictions),
        "source_refs": normalize_source_refs(csv_list(args.source)),
        "academic_novelty": {
            "status": novelty_status,
            "checked_at": args.checked_at or "",
            "query_terms": csv_list(args.academic_query),
            "sources_checked": csv_list(args.academic_source),
            "nearest_matches": [] if not args.nearest_match else [{"title": args.nearest_match, "url": "", "reason_not_same": ""}],
            "novelty_claim": {"zh": args.novelty_claim_zh, "en": args.novelty_claim_en},
            "reviewer_note": args.reviewer_note,
        },
        "confidence": args.confidence,
        "status": status,
        "created_at": args.created_at or date.today().isoformat(),
        "updated_at": args.updated_at or date.today().isoformat(),
        "page": f"docs/zh/answers/items/{answer_id}.md",
    }
    if novelty_status != "passed" and payload["status"] == "active":
        payload["status"] = "answer_pending_novelty_review"
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a new answer record.")
    parser.add_argument("--title-zh", required=True)
    parser.add_argument("--title-en", required=True)
    parser.add_argument("--question-zh", required=True)
    parser.add_argument("--question-en", required=True)
    parser.add_argument("--answer-zh", required=True)
    parser.add_argument("--answer-en", required=True)
    parser.add_argument("--prior-answers-zh", required=True)
    parser.add_argument("--prior-answers-en", required=True)
    parser.add_argument("--new-explanation-zh", required=True)
    parser.add_argument("--new-explanation-en", required=True)
    parser.add_argument("--basis-zh", required=True)
    parser.add_argument("--basis-en", required=True)
    parser.add_argument("--testability-zh", required=True)
    parser.add_argument("--testability-en", required=True)
    parser.add_argument("--functions", default="")
    parser.add_argument("--cases", default="")
    parser.add_argument("--discoveries", default="")
    parser.add_argument("--predictions", default="")
    parser.add_argument("--categories", default="other")
    parser.add_argument("--source", default="")
    parser.add_argument("--academic-query", default="")
    parser.add_argument("--academic-source", default="")
    parser.add_argument("--nearest-match", default="")
    parser.add_argument("--novelty-status", default="pending")
    parser.add_argument("--novelty-claim-zh", default="")
    parser.add_argument("--novelty-claim-en", default="")
    parser.add_argument("--reviewer-note", default="")
    parser.add_argument("--confidence", default="medium")
    parser.add_argument("--status", default="draft")
    parser.add_argument("--checked-at", default="")
    parser.add_argument("--created-at", default="")
    parser.add_argument("--updated-at", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    answers = read_json(ANSWERS_JSON, [])
    payload = build_payload(args, answers)
    normalized = dict(payload)
    normalized["page"] = f"docs/zh/answers/items/{normalized['id']}.md"
    answers.append(normalized)

    if args.dry_run:
        print(json.dumps(normalized, ensure_ascii=False, indent=2))
        return 0

    functions = read_json(FUNCTIONS_JSON, [])
    cases = read_json(CASES_JSON, [])
    discoveries = read_json(DISCOVERIES_JSON, [])
    predictions = read_json(PREDICTIONS_JSON, [])
    category_map = build_category_map(answers, CATEGORY_DEFINITIONS, functions, cases, discoveries, predictions)

    write_json(ANSWERS_JSON, answers)
    write_jsonl(ANSWERS_JSONL, answers)
    write_json(CATEGORY_MAP_JSON, category_map)
    write_jsonl(CATEGORY_MAP_JSONL, category_map)
    write_text(ANSWERS_INDEX_MD, render_answer_index_md(answers))
    write_text(REPO_ROOT / "ANSWERS.md", render_answer_index(answers, category_map))
    write_text(REPO_ROOT / "docs/zh/answers/items" / f"{normalized['id']}.md", render_answer_page(normalized))
    for category in category_map:
        write_text(REPO_ROOT / "docs/zh/answers/categories" / f"{category['id']}.md", render_category_page(category))
    print(json.dumps(normalized, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
