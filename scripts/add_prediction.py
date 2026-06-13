#!/usr/bin/env python3
"""Add a prediction record from JSON input.

This helper validates a prediction-shaped JSON payload and can emit a normalized
record to stdout or write it to a file. The bootstrap renderer remains the source
of truth for the curated prediction index.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_FIELDS = [
    "id",
    "title",
    "statement",
    "basis",
    "test_condition",
    "falsification_condition",
    "time_window",
    "categories",
    "related_functions",
    "related_cases",
    "related_discoveries",
    "source_refs",
    "confidence",
    "status",
    "created_at",
    "updated_at",
    "page",
    "academic_novelty",
    "mathematical_formalization",
    "mathematical_derivation",
]


def load_payload(path: str | None) -> dict:
    raw = sys.stdin.read() if path in {None, "-"} else Path(path).read_text(encoding="utf-8")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("prediction payload must be a JSON object")
    return payload


def normalize_prediction(payload: dict) -> dict:
    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")
    normalized = dict(payload)
    normalized.setdefault("slug", normalized["id"].lower())
    normalized.setdefault("links", {"human_page": normalized["page"]})
    novelty = normalized.get("academic_novelty")
    if not isinstance(novelty, dict):
        raise ValueError("academic_novelty must be a JSON object")
    if "status" not in novelty:
        raise ValueError("academic_novelty.status is required")
    formal = normalized.get("mathematical_formalization")
    derivation = normalized.get("mathematical_derivation")
    if not isinstance(formal, dict) or not isinstance(derivation, dict):
        raise ValueError("mathematical_formalization and mathematical_derivation must be JSON objects")
    for field in ["symbol", "math_expression", "domain", "codomain", "validity_condition"]:
        if not formal.get(field):
            raise ValueError(f"mathematical_formalization.{field} is required")
    for field in ["status", "kind", "steps_math", "forward_check", "reverse_check", "convergence"]:
        if not derivation.get(field):
            raise ValueError(f"mathematical_derivation.{field} is required")
    if derivation.get("status") != "converged":
        raise ValueError("mathematical_derivation.status must be converged")
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and emit a prediction JSON record.")
    parser.add_argument("--input", "-i", help="JSON file to read; use '-' or omit to read from stdin.", default="-")
    parser.add_argument("--output", "-o", help="Write the normalized JSON to this file instead of stdout.")
    parser.add_argument("--check", action="store_true", help="Validate the input and exit without writing.")
    parser.add_argument("--academic-query", default="", help="Optional novelty query terms, comma-separated.")
    parser.add_argument("--academic-source", default="", help="Optional novelty source labels, comma-separated.")
    parser.add_argument("--nearest-match", default="", help="Optional nearest match summary.")
    parser.add_argument("--novelty-status", default="", help="Optional novelty status override.")
    parser.add_argument("--novelty-claim-zh", default="", help="Optional Chinese novelty claim.")
    parser.add_argument("--novelty-claim-en", default="", help="Optional English novelty claim.")
    args = parser.parse_args()

    payload = normalize_prediction(load_payload(args.input))
    if args.academic_query or args.academic_source or args.nearest_match or args.novelty_status or args.novelty_claim_zh or args.novelty_claim_en:
        novelty = dict(payload["academic_novelty"])
        if args.academic_query:
            novelty["query_terms"] = [item.strip() for item in args.academic_query.split(",") if item.strip()]
        if args.academic_source:
            novelty["sources_checked"] = [item.strip() for item in args.academic_source.split(",") if item.strip()]
        if args.nearest_match:
            novelty["nearest_matches"] = [{"title": args.nearest_match, "url": "", "reason_not_same": ""}]
        if args.novelty_status:
            novelty["status"] = args.novelty_status
        if args.novelty_claim_zh or args.novelty_claim_en:
            novelty["novelty_claim"] = {
                "zh": args.novelty_claim_zh or payload["academic_novelty"].get("novelty_claim", {}).get("zh", ""),
                "en": args.novelty_claim_en or payload["academic_novelty"].get("novelty_claim", {}).get("en", ""),
            }
        payload["academic_novelty"] = novelty
    if payload.get("academic_novelty", {}).get("status") != "passed":
        if payload.get("status") == "active":
            payload["status"] = "active_pending_novelty_review"
        elif payload.get("status") == "draft":
            payload["status"] = "draft_pending_novelty_review"
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"

    if args.check:
        return 0

    if args.output:
        Path(args.output).write_text(serialized, encoding="utf-8")
    else:
        sys.stdout.write(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
