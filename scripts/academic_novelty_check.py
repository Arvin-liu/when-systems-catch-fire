#!/usr/bin/env python3
"""Run a lightweight academic novelty check for discovery or prediction entries.

The checker is intentionally conservative: it gathers nearby academic search
results from free public sources, records the nearest matches, and defaults to
pending or inconclusive when novelty cannot be confirmed with confidence.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASETS = {
    "prediction": REPO_ROOT / "data/predictions/unified-predictions.json",
    "discovery": REPO_ROOT / "data/discoveries/unified-discoveries.json",
    "answer": REPO_ROOT / "data/answers/unified-answers.json",
}


def read_json(path: Path, default):
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    return json.loads(text) if text else default


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    body = "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body + ("\n" if body else ""), encoding="utf-8", newline="\n")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def word_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9\u4e00-\u9fff]+", text.lower())
    result = []
    for token in tokens:
        if len(token) >= 3 or re.search(r"[\u4e00-\u9fff]", token):
            result.append(token)
    return result


def generate_query_terms(item: dict) -> list[str]:
    parts = []
    for key in [
        "title",
        "statement",
        "basis",
        "test_condition",
        "falsification_condition",
        "content",
        "why_it_matters",
        "question",
        "answer",
        "prior_answers",
        "new_explanation",
        "testability",
    ]:
        value = item.get(key)
        if isinstance(value, dict):
            parts.extend([value.get("zh", ""), value.get("en", "")])
    candidates = []
    for part in parts:
        if not part:
            continue
        candidates.append(part)
        tokens = word_tokens(part)
        if tokens:
            candidates.append(" ".join(tokens[:8]))
            candidates.append(" ".join(tokens[:5]))
    deduped = []
    seen = set()
    for candidate in candidates:
        normalized = normalize_text(candidate)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(candidate)
    return deduped[:8]


def http_json(url: str) -> dict[str, Any] | None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (OpenClaw)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None
    try:
        return json.loads(payload)
    except Exception:
        return None


def score_match(query: str, title: str, subtitle: str = "") -> float:
    query_norm = normalize_text(query)
    title_norm = normalize_text(title)
    subtitle_norm = normalize_text(subtitle)
    if not query_norm or not title_norm:
        return 0.0
    if query_norm == title_norm:
        return 1.0
    query_tokens = set(word_tokens(query_norm))
    title_tokens = set(word_tokens(title_norm))
    if not query_tokens or not title_tokens:
        return 0.0
    overlap = len(query_tokens & title_tokens) / max(len(query_tokens), 1)
    if subtitle_norm:
        subtitle_tokens = set(word_tokens(subtitle_norm))
        overlap = max(overlap, len(query_tokens & subtitle_tokens) / max(len(query_tokens), 1))
    return overlap


def search_openalex(query: str, limit: int = 3) -> list[dict]:
    url = "https://api.openalex.org/works?search=" + urllib.parse.quote(query) + f"&per-page={limit}"
    payload = http_json(url)
    if not payload:
        return []
    results = []
    for item in payload.get("results", [])[:limit]:
        title = item.get("display_name", "")
        results.append(
            {
                "source": "OpenAlex",
                "title": title,
                "url": item.get("id", ""),
                "reason_not_same": "title overlap only" if title else "search hit",
                "score": score_match(query, title),
            }
        )
    return results


def search_crossref(query: str, limit: int = 3) -> list[dict]:
    url = "https://api.crossref.org/works?query.title=" + urllib.parse.quote(query) + f"&rows={limit}"
    payload = http_json(url)
    if not payload:
        return []
    results = []
    items = payload.get("message", {}).get("items", [])[:limit]
    for item in items:
        title = (item.get("title") or [""])[0]
        doi = item.get("DOI", "")
        results.append(
            {
                "source": "Crossref",
                "title": title,
                "url": f"https://doi.org/{doi}" if doi else "",
                "reason_not_same": "title overlap only" if title else "search hit",
                "score": score_match(query, title),
            }
        )
    return results


def build_novelty_record(item: dict) -> dict:
    query_terms = generate_query_terms(item)
    search_terms = query_terms[:3] or [item.get("title", {}).get("en", "") or item.get("title", {}).get("zh", "")]
    nearest_matches: list[dict] = []
    sources = []
    for term in search_terms:
        nearest_matches.extend(search_openalex(term))
        nearest_matches.extend(search_crossref(term))
        sources.extend(["OpenAlex", "Crossref"])

    seen = set()
    filtered = []
    for match in sorted(nearest_matches, key=lambda row: row.get("score", 0.0), reverse=True):
        key = (match.get("source", ""), match.get("title", "").lower(), match.get("url", ""))
        if key in seen:
            continue
        seen.add(key)
        filtered.append({k: v for k, v in match.items() if k != "score"})
        if len(filtered) >= 5:
            break

    exact_title = any(normalize_text(match.get("title", "")) == normalize_text(item.get("title", {}).get("en", "") or item.get("title", {}).get("zh", "")) for match in filtered)
    if filtered and exact_title:
        status = "failed"
        reviewer_note = "exact or near-exact academic title match found"
    elif filtered:
        status = "inconclusive"
        reviewer_note = "academic search returned nearby results but no exact match"
    else:
        status = "pending"
        reviewer_note = "academic search unavailable or returned no usable results"

    return {
        "status": status,
        "checked_at": date.today().isoformat(),
        "query_terms": query_terms,
        "sources_checked": sorted(set(sources)) or ["OpenAlex", "Crossref"],
        "nearest_matches": filtered,
        "novelty_claim": {
            "zh": "现有学术搜索未发现相同解释 / 相同预测。",
            "en": "No identical explanation or prediction was found in the academic search.",
        },
        "reviewer_note": reviewer_note,
    }


def apply_record(item: dict, novelty: dict) -> dict:
    updated = dict(item)
    updated["academic_novelty"] = novelty
    return updated


def locate(dataset_type: str, entry_id: str) -> tuple[Path, int]:
    path = DATASETS[dataset_type]
    rows = read_json(path, [])
    for idx, row in enumerate(rows):
        if row.get("id") == entry_id:
            return path, idx
    raise SystemExit(f"{entry_id} not found in {path.relative_to(REPO_ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check academic novelty for curated discovery or prediction entries.")
    parser.add_argument("--type", choices=["discovery", "prediction", "answer"], help="Entry type to inspect.")
    parser.add_argument("--id", dest="entry_id", help="Specific entry id to inspect.")
    parser.add_argument("--all-discoveries", action="store_true", help="Process all discovery entries.")
    parser.add_argument("--all-predictions", action="store_true", help="Process all prediction entries.")
    parser.add_argument("--all-answers", action="store_true", help="Process all answer entries.")
    parser.add_argument("--check", action="store_true", help="Print a dry preview and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files.")
    args = parser.parse_args()

    targets: list[tuple[str, dict, int | None]] = []
    if args.all_discoveries or args.all_predictions or args.all_answers:
        for dataset_type in (
            (["discovery"] if args.all_discoveries else [])
            + (["prediction"] if args.all_predictions else [])
            + (["answer"] if args.all_answers else [])
        ):
            rows = read_json(DATASETS[dataset_type], [])
            for idx, row in enumerate(rows):
                targets.append((dataset_type, row, idx))
    else:
        if not args.type or not args.entry_id:
            raise SystemExit("--type and --id are required unless using --all-discoveries or --all-predictions")
        rows = read_json(DATASETS[args.type], [])
        for idx, row in enumerate(rows):
            if row.get("id") == args.entry_id:
                targets.append((args.type, row, idx))
                break
        if not targets:
            raise SystemExit(f"{args.entry_id} not found")

    results = []
    for dataset_type, row, idx in targets:
        novelty = build_novelty_record(row)
        results.append({"type": dataset_type, "id": row.get("id"), "academic_novelty": novelty})
        if not args.dry_run and not args.check:
            rows = read_json(DATASETS[dataset_type], [])
            rows[idx]["academic_novelty"] = novelty
            write_json(DATASETS[dataset_type], rows)
            write_jsonl(DATASETS[dataset_type].with_suffix(".jsonl"), rows)

    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
