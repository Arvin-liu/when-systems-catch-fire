#!/usr/bin/env python3
"""Project functions/cases onto answer candidates and render a bootstrap report."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from display_utils import format_bilingual_title


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_MD = REPO_ROOT / "data/rebuild/function-projection-answer-report.md"
REPORT_JSON = REPO_ROOT / "data/rebuild/function-projection-answer-report.json"

FUNCTIONS_JSON = REPO_ROOT / "data/functions/unified-functions.json"
CASES_JSON = REPO_ROOT / "data/cases/unified-cases.json"
ANSWERS_JSON = REPO_ROOT / "data/answers/unified-answers.json"
DISCOVERIES_JSON = REPO_ROOT / "data/discoveries/unified-discoveries.json"
PREDICTIONS_JSON = REPO_ROOT / "data/predictions/unified-predictions.json"

TOKEN_RE = re.compile(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9_+\-]*")


def load_json(path: Path, default):
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return default
    return json.loads(text)


def text_blob(obj: dict, fields: list[str]) -> str:
    parts: list[str] = []
    for field in fields:
        value = obj.get(field)
        if isinstance(value, dict):
            parts.extend(str(v) for v in value.values() if isinstance(v, str))
        elif isinstance(value, list):
            parts.extend(str(v) for v in value if isinstance(v, str))
        elif isinstance(value, str):
            parts.append(value)
    return "\n".join(parts)


def tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text or "") if len(token.strip()) >= 2}


def build_source_index(items: list[dict], fields: list[str]) -> list[tuple[dict, set[str]]]:
    indexed: list[tuple[dict, set[str]]] = []
    for item in items:
        blob = text_blob(item, fields)
        indexed.append((item, tokens(blob)))
    return indexed


def rank_sources(answer_tokens: set[str], indexed_sources: list[tuple[dict, set[str]]], limit: int = 5) -> list[dict]:
    scored: list[tuple[int, dict]] = []
    for item, source_tokens in indexed_sources:
        score = len(answer_tokens & source_tokens)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1].get("id", "")))
    ranked: list[dict] = []
    for score, item in scored[:limit]:
        ranked.append(
            {
                "id": item.get("id", ""),
                "title": item.get("title", {}),
                "page": item.get("page") or item.get("links", {}).get("human_page", ""),
                "score": score,
            }
        )
    return ranked


def build_candidates(functions: list[dict], cases: list[dict], answers: list[dict]) -> list[dict]:
    function_index = build_source_index(functions, ["title", "content", "explanation", "title_text"])
    case_index = build_source_index(cases, ["title", "content", "explanation", "title_text", "case_description_raw", "key_discovery_raw"])

    candidates: list[dict] = []
    for answer in answers:
        answer_blob = text_blob(
            answer,
            ["title", "question", "answer", "prior_answers", "new_explanation", "basis", "testability", "source_refs", "categories"],
        )
        answer_tokens = tokens(answer_blob)
        projected_functions = rank_sources(answer_tokens, function_index)
        projected_cases = rank_sources(answer_tokens, case_index)
        total_score = sum(item["score"] for item in projected_functions[:3]) + sum(item["score"] for item in projected_cases[:3])
        if not total_score:
            continue
        candidates.append(
            {
                "id": answer.get("id", ""),
                "title": answer.get("title", {}),
                "status": answer.get("status", ""),
                "academic_novelty": answer.get("academic_novelty", {}),
                "categories": answer.get("categories", []),
                "projected_from": {
                    "functions": projected_functions,
                    "cases": projected_cases,
                    "discoveries": [],
                    "predictions": [],
                },
                "old_answer_queries": [
                    answer.get("question", {}).get("zh", ""),
                    answer.get("title", {}).get("zh", ""),
                    answer.get("basis", {}).get("zh", ""),
                ],
                "candidate_new_answer": {
                    "zh": answer.get("answer", {}).get("zh", ""),
                    "en": answer.get("answer", {}).get("en", ""),
                },
                "source_refs": answer.get("source_refs", []),
                "score": total_score,
                "page": answer.get("page", ""),
            }
        )
    candidates.sort(key=lambda item: (-item["score"], item["id"]))
    return candidates


def build_report(candidates: list[dict], functions: list[dict], cases: list[dict], answers: list[dict], discoveries: list[dict], predictions: list[dict]) -> tuple[str, dict]:
    novelty_counts = Counter(item.get("academic_novelty", {}).get("status", "unknown") for item in answers)
    report = {
        "generated_at": "2026-06-13",
        "functions_loaded": len(functions),
        "cases_loaded": len(cases),
        "answers_loaded": len(answers),
        "discoveries_loaded": len(discoveries),
        "predictions_loaded": len(predictions),
        "answer_candidates": len(candidates),
        "answers_with_projection": len(candidates),
        "curated_answers": sum(1 for item in answers if item.get("status") == "active" and item.get("academic_novelty", {}).get("status") == "passed"),
        "lead_answers": sum(1 for item in answers if item.get("status") != "active" or item.get("academic_novelty", {}).get("status") != "passed"),
        "novelty_counts": dict(novelty_counts),
        "academic_novelty_passed": novelty_counts.get("passed", 0),
        "academic_novelty_inconclusive": novelty_counts.get("inconclusive", 0),
        "academic_novelty_pending": novelty_counts.get("pending", 0),
        "academic_novelty_failed": novelty_counts.get("failed", 0),
    }
    lines = [
        "# Function Projection Answer Report",
        "",
        f"- functions_loaded: {report['functions_loaded']}",
        f"- cases_loaded: {report['cases_loaded']}",
        f"- answers_loaded: {report['answers_loaded']}",
        f"- discoveries_loaded: {report['discoveries_loaded']}",
        f"- predictions_loaded: {report['predictions_loaded']}",
        f"- answer_candidates: {report['answer_candidates']}",
        f"- answers_with_projection: {report['answers_with_projection']}",
        f"- curated_answers: {report['curated_answers']}",
        f"- lead_answers: {report['lead_answers']}",
        f"- academic_novelty_passed: {report['academic_novelty_passed']}",
        f"- academic_novelty_inconclusive: {report['academic_novelty_inconclusive']}",
        f"- academic_novelty_pending: {report['academic_novelty_pending']}",
        f"- academic_novelty_failed: {report['academic_novelty_failed']}",
        "",
        "## Top Candidates",
        "",
    ]
    if candidates:
        lines.append("| ID | Title | Score | Projected From | Novelty |")
        lines.append("|---|---:|---:|---|---|")
        for item in candidates[:30]:
            title = format_bilingual_title(item["title"].get("zh"), item["title"].get("en"))
            projected_functions = ", ".join(entry["id"] for entry in item["projected_from"]["functions"][:3]) or "-"
            projected_cases = ", ".join(entry["id"] for entry in item["projected_from"]["cases"][:3]) or "-"
            projected_from = f"F:{projected_functions}; C:{projected_cases}"
            novelty = item["academic_novelty"].get("status", "unknown")
            lines.append(f"| {item['id']} | {title} | {item['score']} | {projected_from} | {novelty} |")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Rules Confirmed",
            "",
            "- Functions and cases are used as projections into candidate old-question domains.",
            "- Existing answers are compared against projected candidates before any curation decision.",
            "- Academic novelty status remains authoritative; this report does not mark inconclusive items as passed.",
            "",
        ]
    )
    return "\n".join(lines), report


def write_reports(report_text: str, payload: dict) -> None:
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(report_text, encoding="utf-8", newline="\n")
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build answers from function projection.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    functions = load_json(FUNCTIONS_JSON, [])
    cases = load_json(CASES_JSON, [])
    answers = load_json(ANSWERS_JSON, [])
    discoveries = load_json(DISCOVERIES_JSON, [])
    predictions = load_json(PREDICTIONS_JSON, [])

    candidates = build_candidates(functions, cases, answers)
    report_text, payload = build_report(candidates, functions, cases, answers, discoveries, predictions)

    if args.check:
        if not REPORT_MD.exists() or not REPORT_JSON.exists():
            print(report_text)
            return 1
        current_md = REPORT_MD.read_text(encoding="utf-8")
        current_json = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
        if current_md != report_text or current_json != payload:
            print(report_text)
            return 1
        print("Function projection answer report is up to date")
        return 0

    write_reports(report_text, payload)
    print(
        json.dumps(
            {
                "dry_run": args.dry_run,
                "answer_candidates": len(candidates),
                "report_md": str(REPORT_MD.relative_to(REPO_ROOT)),
                "report_json": str(REPORT_JSON.relative_to(REPO_ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
