#!/usr/bin/env python3
"""Validate the conservative UNESCO coverage ledger."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ALLOWED_STATUSES = {
    "UNASSESSED",
    "NOT_TOUCHED",
    "CASE_ONLY",
    "METAPHOR_ONLY",
    "FUNCTION_PARTIAL",
    "THEORY_CORE_EXTRACTED",
    "EXTERNAL_EVIDENCE_PENDING",
    "COLLISION_VALIDATED",
    "NARRATIVE_READY",
}


def die(message: str) -> None:
    raise SystemExit(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--evidence-map", required=True, type=Path)
    args = parser.parse_args()

    payload = json.loads(args.json.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    if len(records) != 250:
        die(f"expected 250 records, found {len(records)}")

    source_lines = [line for line in args.source.read_text(encoding="utf-8").splitlines() if line.startswith("| ")]
    source_rows = [line for line in source_lines if not line.startswith("| 大类 |")]
    if len(source_rows) != 250:
        die(f"expected 250 source rows, found {len(source_rows)}")

    evidence_map = json.loads(args.evidence_map.read_text(encoding="utf-8"))
    evidence_records = {item["unesco_code"]: item for item in evidence_map.get("records", [])}

    seen = set()
    status_counts = {}
    for record in records:
        code = record.get("unesco_code")
        if code in seen:
            die(f"duplicate code: {code}")
        seen.add(code)
        status = record.get("status")
        if status not in ALLOWED_STATUSES:
            die(f"invalid status for {code}: {status}")
        status_counts[status] = status_counts.get(status, 0) + 1

        required = [
            "unesco_code",
            "discipline_name",
            "major_code",
            "inventory_source",
            "status",
            "review_method",
            "search_terms",
            "coverage_evidence",
            "matched_function_ids",
            "matched_case_ids",
            "matched_collision_artifacts",
            "matched_story_artifacts",
            "theory_match",
            "counterevidence_or_limits",
            "review_reason",
            "confidence_basis",
            "next_action",
        ]
        missing = [field for field in required if field not in record]
        if missing:
            die(f"{code} missing fields: {missing}")

        inv = record["inventory_source"]
        if not isinstance(inv, dict) or "path" not in inv or "note_id" not in inv:
            die(f"{code} invalid inventory_source")

        if status != "UNASSESSED":
            if not record.get("coverage_evidence"):
                die(f"{code} non-UNASSESSED without coverage_evidence")
            if status == "COLLISION_VALIDATED" and not record.get("matched_collision_artifacts"):
                die(f"{code} COLLISION_VALIDATED without matched_collision_artifacts")
            if status == "NARRATIVE_READY" and not record.get("matched_story_artifacts"):
                die(f"{code} NARRATIVE_READY without matched_story_artifacts")
            if status == "FUNCTION_PARTIAL":
                if not (
                    record.get("matched_function_ids")
                    or record.get("matched_case_ids")
                    or record.get("matched_collision_artifacts")
                    or record.get("matched_story_artifacts")
                ):
                    die(f"{code} FUNCTION_PARTIAL without explicit matched evidence")

        if code in evidence_records:
            evidence = evidence_records[code]
            if evidence.get("status") != status:
                die(f"{code} status mismatch with evidence map")
            if not evidence.get("coverage_evidence"):
                die(f"{code} evidence map lacks coverage_evidence")

    summary = payload.get("summary", {})
    if summary.get("total_records") != 250:
        die("summary.total_records must be 250")
    if summary.get("touched_rows") != sum(1 for r in records if r.get("status") != "UNASSESSED"):
        die("summary.touched_rows mismatch")

    derived_counts = {}
    for record in records:
        derived_counts[record["status"]] = derived_counts.get(record["status"], 0) + 1
    if summary.get("status_counts") != derived_counts:
        die("summary.status_counts mismatch")

    forbidden_patterns = [r"/Users/", r"/home/", r"C:\\Users\\", r"file:///"]
    blob = args.json.read_text(encoding="utf-8") + args.source.read_text(encoding="utf-8") + args.evidence_map.read_text(encoding="utf-8")
    for pattern in forbidden_patterns:
        if re.search(pattern, blob):
            die(f"forbidden path pattern found: {pattern}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
