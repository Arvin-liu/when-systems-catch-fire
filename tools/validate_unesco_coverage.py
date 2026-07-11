#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "outputs" / "research" / "ignition-gap-map-unesco-coverage-20260712.json"

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


class ValidationError(Exception):
    pass


def fail(msg: str) -> None:
    raise ValidationError(msg)


def main() -> int:
    payload = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list):
        fail("missing records array")
    if len(records) != 250:
        fail(f"record count {len(records)} != 250")
    seen = set()
    for row in records:
        code = row.get("unesco_code")
        if code in seen:
            fail(f"duplicate code {code}")
        seen.add(code)
        if row.get("status") not in ALLOWED_STATUSES:
            fail(f"bad status {row.get('status')} for {code}")
        refs = row.get("evidence_refs") or []
        if not refs:
            fail(f"empty evidence_refs for {code}")
        for ref in refs:
            if ref.get("kind") == "source_table":
                if "source_note_id" not in ref or "line_no" not in ref:
                    fail(f"bad source_table ref for {code}")
            if ref.get("kind") == "repo_artifact":
                path = ref.get("path", "")
                if path.startswith("/") or path.startswith("file:"):
                    fail(f"absolute path in evidence ref for {code}")
    summary = payload.get("summary", {})
    total = sum(summary.get(status, 0) for status in ALLOWED_STATUSES)
    if total != 250:
        fail(f"summary total {total} != 250")
    print("ALL_UNESCO_COVERAGE_VALID")
    print(f"records={len(records)}")
    print(f"touched_rows={payload.get('touched_rows')}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"UNESCO_COVERAGE_INVALID: {exc}", file=sys.stderr)
        raise SystemExit(1)
