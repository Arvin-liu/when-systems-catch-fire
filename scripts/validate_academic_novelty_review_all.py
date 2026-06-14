#!/usr/bin/env python3
"""Validate all-object academic novelty review outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEW_JSON = ROOT / "data" / "novelty-gate" / "all-object-academic-novelty-review.json"
QUEUE_JSONL = ROOT / "data" / "novelty-gate" / "novelty-disposition-queue.jsonl"
DATASETS = {
    "discovery": ROOT / "data" / "discoveries" / "unified-discoveries.json",
    "prediction": ROOT / "data" / "predictions" / "unified-predictions.json",
    "answer": ROOT / "data" / "answers" / "unified-answers.json",
    "effect": ROOT / "data" / "effects" / "unified-effects.json",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise AssertionError(f"empty line in {path.relative_to(ROOT)}:{line_number}")
        rows.append(json.loads(line))
    return rows


def expected_ids() -> set[tuple[str, str]]:
    expected: set[tuple[str, str]] = set()
    for object_class, path in DATASETS.items():
        for item in read_json(path):
            expected.add((object_class, item["id"]))
    return expected


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate all-object academic novelty review")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")

    errors: list[str] = []
    if not REVIEW_JSON.exists():
        errors.append("missing data/novelty-gate/all-object-academic-novelty-review.json")
    if not QUEUE_JSONL.exists():
        errors.append("missing data/novelty-gate/novelty-disposition-queue.jsonl")
    if errors:
        print(json.dumps({"passed": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1

    report = read_json(REVIEW_JSON)
    rows = read_jsonl(QUEUE_JSONL)
    expected = expected_ids()
    actual = {(row.get("object_class"), row.get("object_id")) for row in rows}
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        errors.append(f"queue object set mismatch: missing={missing[:20]} extra={extra[:20]}")
    if len(report.get("results", [])) != len(rows):
        errors.append("review JSON results and queue JSONL row counts differ")
    if report.get("summary", {}).get("total_reviewed") != len(expected):
        errors.append("summary total_reviewed does not match source datasets")

    for row in rows:
        object_id = row.get("object_id", "?")
        if row.get("canonical_rewrite_now") is not False:
            errors.append(f"{object_id}: canonical_rewrite_now must be false")
        if row.get("inference_not_conclusion") is not True:
            errors.append(f"{object_id}: inference_not_conclusion must be true")
        result = row.get("novelty_review_result")
        disposition = row.get("recommended_disposition")
        if result == "same_or_strong_academic_overlap_found" and disposition != "downgrade_to_function_supplement_review":
            errors.append(f"{object_id}: strong overlap must route to downgrade review")
        if result == "no_same_academic_match_found" and disposition != "retain_current_claim_class_candidate":
            errors.append(f"{object_id}: no same academic match must retain current claim class candidate")
        if result == "possible_academic_overlap_found" and disposition != "needs_human_review":
            errors.append(f"{object_id}: possible overlap must route to human review")
        if row.get("claim_allowed_after_academic_search") is True and result != "no_same_academic_match_found":
            errors.append(f"{object_id}: claim_allowed_after_academic_search true only allowed for no_same_academic_match_found")
        if not row.get("query_terms"):
            errors.append(f"{object_id}: query_terms must not be empty")

    if errors:
        print(json.dumps({"passed": False, "errors": errors[:50], "error_count": len(errors)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"passed": True, "reviewed": len(rows)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
