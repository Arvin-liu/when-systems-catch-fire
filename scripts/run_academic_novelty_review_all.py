#!/usr/bin/env python3
"""Run academic novelty review for discoveries, predictions, answers, and effects.

This script records a disposition queue instead of rewriting canonical object
classes. Strong academic overlap is routed to downgrade review; weak overlap is
human review; no same-object match remains eligible for the current claim class.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "novelty-gate"
REBUILD = ROOT / "data" / "rebuild"
REVIEW_JSON = OUT_DIR / "all-object-academic-novelty-review.json"
REVIEW_JSONL = OUT_DIR / "all-object-academic-novelty-review.jsonl"
REVIEW_MD = OUT_DIR / "all-object-academic-novelty-review.md"
QUEUE_JSONL = OUT_DIR / "novelty-disposition-queue.jsonl"
REPORT_JSON = REBUILD / "all-object-academic-novelty-review-report.json"
REPORT_MD = REBUILD / "all-object-academic-novelty-review-report.md"

DATASETS = {
    "discovery": ROOT / "data" / "discoveries" / "unified-discoveries.json",
    "prediction": ROOT / "data" / "predictions" / "unified-predictions.json",
    "answer": ROOT / "data" / "answers" / "unified-answers.json",
    "effect": ROOT / "data" / "effects" / "unified-effects.json",
}
REQUEST_TIMEOUT_SECONDS = 12

OBJECT_ID_RE = re.compile(r"\b(?:D\d+|T\d+|MF-\d+|C-\d{4}|DISC-\d{4}|PRED-\d{4}|ANS-\d{4}|EFF-\d{4}|SOL-\d{4})\b")
TAG_RE = re.compile(r"<[^>]+>")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def read_json(path: Path, default: Any) -> Any:
    text = path.read_text(encoding="utf-8").strip() if path.exists() else ""
    return json.loads(text) if text else default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows)
    path.write_text(body + ("\n" if body else ""), encoding="utf-8")


def normalize_text(text: str) -> str:
    text = TAG_RE.sub(" ", text)
    text = OBJECT_ID_RE.sub(" ", text)
    text = text.replace("｜", " ").replace("|", " ")
    return re.sub(r"\s+", " ", text.strip().lower())


def cjk_grams(text: str) -> list[str]:
    chars = re.findall(r"[\u4e00-\u9fff]", text)
    return ["".join(chars[idx : idx + 2]) for idx in range(max(len(chars) - 1, 0))]


def score_tokens(text: str) -> list[str]:
    text = normalize_text(text)
    tokens = [token for token in re.findall(r"[a-z0-9]+", text) if len(token) >= 3]
    tokens.extend(cjk_grams(text))
    return tokens


def score_match(query: str, title: str, subtitle: str = "") -> float:
    query_norm = normalize_text(query)
    title_norm = normalize_text(title)
    subtitle_norm = normalize_text(subtitle)
    if not query_norm or not title_norm:
        return 0.0
    if query_norm == title_norm:
        return 1.0
    query_tokens = set(score_tokens(query_norm))
    candidate_tokens = set(score_tokens(title_norm + " " + subtitle_norm))
    if not query_tokens or not candidate_tokens:
        return 0.0
    overlap = len(query_tokens & candidate_tokens) / max(len(query_tokens), 1)
    containment = 0.0
    if len(query_norm) >= 12 and query_norm in title_norm:
        containment = 0.85
    if len(title_norm) >= 12 and title_norm in query_norm:
        containment = 0.85
    return max(overlap, containment)


def text_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values: list[str] = []
        for key in ("en", "zh"):
            inner = value.get(key)
            if isinstance(inner, str):
                values.append(inner)
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(text_values(item))
        return values
    return []


def clean_query(text: str) -> str:
    text = normalize_text(text)
    text = re.sub(r"\b(?:zh|en)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def query_fields(object_class: str) -> list[str]:
    return {
        "discovery": ["title", "summary", "content", "why_it_matters", "inference_chain"],
        "prediction": ["title", "statement", "basis", "test_condition", "falsification_condition"],
        "answer": ["title", "question", "answer", "prior_answers", "new_explanation", "testability"],
        "effect": ["title", "observed_change", "trigger_conditions", "measurable_signal", "discipline"],
    }[object_class]


def related_title_queries(item: dict) -> list[str]:
    queries: list[str] = []
    for key in ("related_functions", "related_cases", "related_discoveries", "related_predictions", "related_answers"):
        value = item.get(key)
        if not isinstance(value, list):
            continue
        for related in value[:4]:
            if isinstance(related, dict):
                queries.extend(text_values(related.get("title")))
    return queries


def generate_queries(object_class: str, item: dict, max_queries: int) -> list[str]:
    candidates: list[str] = []
    for field in query_fields(object_class):
        candidates.extend(text_values(item.get(field)))
    candidates.extend(related_title_queries(item))

    queries: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        cleaned = clean_query(candidate)
        if not cleaned:
            continue
        words = cleaned.split()
        variants = [cleaned]
        if len(words) > 10:
            variants.append(" ".join(words[:10]))
        if len(words) > 6:
            variants.append(" ".join(words[:6]))
        for variant in variants:
            if len(variant) < 4 or variant in seen:
                continue
            seen.add(variant)
            queries.append(variant)
            if len(queries) >= max_queries:
                return queries
    return queries


def http_json(url: str) -> tuple[dict[str, Any] | None, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (OpenClaw academic novelty review)"})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = response.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return None, str(exc)
    try:
        return json.loads(payload), None
    except Exception as exc:
        return None, f"json decode failed: {exc}"


def abstract_from_openalex(item: dict) -> str:
    inverted = item.get("abstract_inverted_index")
    if not isinstance(inverted, dict):
        return ""
    positions: list[tuple[int, str]] = []
    for word, indexes in inverted.items():
        if isinstance(indexes, list):
            positions.extend((int(index), str(word)) for index in indexes if isinstance(index, int))
    return " ".join(word for _, word in sorted(positions)[:80])


def search_openalex(query: str, limit: int) -> tuple[list[dict], list[str]]:
    url = "https://api.openalex.org/works?search=" + urllib.parse.quote(query) + f"&per-page={limit}"
    payload, error = http_json(url)
    if error or not payload:
        return [], [f"OpenAlex: {error or 'empty response'}"]
    rows = []
    for item in payload.get("results", [])[:limit]:
        title = item.get("display_name") or ""
        subtitle = abstract_from_openalex(item)
        rows.append(
            {
                "source": "OpenAlex",
                "query": query,
                "title": title,
                "url": item.get("id") or "",
                "publication_year": item.get("publication_year"),
                "score": round(score_match(query, title, subtitle), 4),
                "reason": "title_or_abstract_overlap",
            }
        )
    return rows, []


def search_crossref(query: str, limit: int) -> tuple[list[dict], list[str]]:
    url = "https://api.crossref.org/works?query.title=" + urllib.parse.quote(query) + f"&rows={limit}"
    payload, error = http_json(url)
    if error or not payload:
        return [], [f"Crossref: {error or 'empty response'}"]
    rows = []
    for item in payload.get("message", {}).get("items", [])[:limit]:
        title = (item.get("title") or [""])[0]
        doi = item.get("DOI") or ""
        rows.append(
            {
                "source": "Crossref",
                "query": query,
                "title": title,
                "url": f"https://doi.org/{doi}" if doi else "",
                "publication_year": (item.get("published-print") or item.get("published-online") or {}).get("date-parts", [[None]])[0][0],
                "score": round(score_match(query, title), 4),
                "reason": "title_overlap",
            }
        )
    return rows, []


def dedupe_matches(matches: list[dict], limit: int) -> list[dict]:
    seen = set()
    deduped = []
    for match in sorted(matches, key=lambda row: row.get("score", 0.0), reverse=True):
        key = (match.get("source"), normalize_text(match.get("title", "")), match.get("url", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(match)
        if len(deduped) >= limit:
            break
    return deduped


def classify_result(matches: list[dict], errors: list[str]) -> tuple[str, str, bool]:
    if not matches and errors:
        return "search_unavailable_inconclusive", "needs_human_review", False
    best = max((float(match.get("score", 0.0)) for match in matches), default=0.0)
    if best >= 0.72:
        return "same_or_strong_academic_overlap_found", "downgrade_to_function_supplement_review", False
    if best >= 0.35:
        return "possible_academic_overlap_found", "needs_human_review", False
    return "no_same_academic_match_found", "retain_current_claim_class_candidate", True


def review_item(object_class: str, item: dict, max_queries: int, per_source_limit: int, match_limit: int, delay_seconds: float) -> dict:
    queries = generate_queries(object_class, item, max_queries=max_queries)
    matches: list[dict] = []
    errors: list[str] = []
    for query in queries:
        openalex_rows, openalex_errors = search_openalex(query, per_source_limit)
        crossref_rows, crossref_errors = search_crossref(query, per_source_limit)
        matches.extend(openalex_rows)
        matches.extend(crossref_rows)
        errors.extend(openalex_errors)
        errors.extend(crossref_errors)
        if delay_seconds:
            time.sleep(delay_seconds)
    nearest = dedupe_matches(matches, match_limit)
    result, disposition, claim_allowed = classify_result(nearest, errors)
    return {
        "object_class": object_class,
        "object_id": item.get("id"),
        "current_status": item.get("status"),
        "title": item.get("title"),
        "query_terms": queries,
        "sources_checked": ["OpenAlex", "Crossref"],
        "search_errors": errors,
        "nearest_matches": nearest,
        "best_score": max((match.get("score", 0.0) for match in nearest), default=0.0),
        "novelty_review_result": result,
        "recommended_disposition": disposition,
        "claim_allowed_after_academic_search": claim_allowed,
        "canonical_rewrite_now": False,
        "inference_not_conclusion": True,
    }


def load_targets() -> list[tuple[str, dict]]:
    targets: list[tuple[str, dict]] = []
    for object_class, path in DATASETS.items():
        rows = read_json(path, [])
        for row in rows:
            targets.append((object_class, row))
    return targets


def summary_for(rows: list[dict]) -> dict:
    by_class: dict[str, int] = {}
    by_result: dict[str, int] = {}
    by_disposition: dict[str, int] = {}
    for row in rows:
        by_class[row["object_class"]] = by_class.get(row["object_class"], 0) + 1
        by_result[row["novelty_review_result"]] = by_result.get(row["novelty_review_result"], 0) + 1
        by_disposition[row["recommended_disposition"]] = by_disposition.get(row["recommended_disposition"], 0) + 1
    return {
        "total_reviewed": len(rows),
        "by_object_class": dict(sorted(by_class.items())),
        "by_novelty_review_result": dict(sorted(by_result.items())),
        "by_recommended_disposition": dict(sorted(by_disposition.items())),
        "canonical_rewrites_executed": False,
        "direct_academic_search_executed": True,
    }


def render_md(report: dict, rows: list[dict]) -> str:
    summary = report["summary"]
    lines = [
        "# All-Object Academic Novelty Review",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- HEAD: `{report['source_commit']}`",
        f"- Total reviewed: {summary['total_reviewed']}",
        "- Sources checked: OpenAlex, Crossref",
        "- Canonical rewrites executed: false",
        "",
        "## Summary",
        "",
        "| Key | Value | Count |",
        "|---|---|---:|",
    ]
    for bucket_name in ("by_object_class", "by_novelty_review_result", "by_recommended_disposition"):
        for key, value in summary[bucket_name].items():
            lines.append(f"| `{bucket_name}` | `{key}` | {value} |")
    lines.extend(["", "## Disposition Queue", "", "| Object | Class | Result | Disposition | Best score |", "|---|---|---|---|---:|"])
    for row in rows:
        object_id = row["object_id"]
        lines.append(
            f"| {object_id} | `{row['object_class']}` | `{row['novelty_review_result']}` | `{row['recommended_disposition']}` | {row['best_score']} |"
        )
    return "\n".join(lines) + "\n"


def run(args: argparse.Namespace) -> dict:
    targets = load_targets()
    if args.limit:
        targets = targets[: args.limit]
    indexed_rows: list[tuple[int, dict]] = []

    def review_target(index: int, object_class: str, item: dict) -> tuple[int, dict]:
        return index, review_item(
            object_class,
            item,
            max_queries=args.max_queries_per_item,
            per_source_limit=args.per_source_limit,
            match_limit=args.match_limit,
            delay_seconds=args.delay_seconds,
        )

    if args.workers <= 1:
        for index, (object_class, item) in enumerate(targets, 1):
            _, row = review_target(index, object_class, item)
            indexed_rows.append((index, row))
            if args.progress and (index == 1 or index % args.progress == 0 or index == len(targets)):
                print(json.dumps({"progress": index, "total": len(targets), "last": row["object_id"], "result": row["novelty_review_result"]}, ensure_ascii=False), flush=True)
    else:
        completed = 0
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = [
                executor.submit(review_target, index, object_class, item)
                for index, (object_class, item) in enumerate(targets, 1)
            ]
            for future in as_completed(futures):
                index, row = future.result()
                completed += 1
                indexed_rows.append((index, row))
                if args.progress and (completed == 1 or completed % args.progress == 0 or completed == len(targets)):
                    print(
                        json.dumps(
                            {
                                "progress": completed,
                                "total": len(targets),
                                "last": row["object_id"],
                                "result": row["novelty_review_result"],
                            },
                            ensure_ascii=False,
                        ),
                        flush=True,
                    )

    rows = [row for _, row in sorted(indexed_rows, key=lambda pair: pair[0])]

    report = {
        "report_name": "all-object-academic-novelty-review",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": git_head(),
        "datasets": {key: rel(path) for key, path in DATASETS.items()},
        "review_parameters": {
            "max_queries_per_item": args.max_queries_per_item,
            "per_source_limit": args.per_source_limit,
            "match_limit": args.match_limit,
            "limit": args.limit,
        },
        "summary": summary_for(rows),
        "results": rows,
    }

    if not args.dry_run:
        write_json(REVIEW_JSON, report)
        write_jsonl(REVIEW_JSONL, rows)
        write_jsonl(QUEUE_JSONL, rows)
        write_json(REPORT_JSON, report)
        md = render_md(report, rows)
        REVIEW_MD.write_text(md, encoding="utf-8")
        REPORT_MD.write_text(md, encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run academic novelty review for all claimed-new object layers")
    parser.add_argument("--all", action="store_true", help="Run all configured layers")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    parser.add_argument("--limit", type=int, default=0, help="Limit targets for testing")
    parser.add_argument("--max-queries-per-item", type=int, default=2)
    parser.add_argument("--per-source-limit", type=int, default=3)
    parser.add_argument("--match-limit", type=int, default=5)
    parser.add_argument("--delay-seconds", type=float, default=0.0)
    parser.add_argument("--progress", type=int, default=10)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    if not args.all:
        parser.error("--all is required")

    report = run(args)
    print(json.dumps({"summary": report["summary"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
