#!/usr/bin/env python3
"""Classify mathematical objects across the repository."""

from __future__ import annotations

import argparse
import json

from object_classification_utils import (
    CANDIDATES_JSON,
    CANDIDATES_JSONL,
    CANDIDATES_REPORT_MD,
    CROSSWALK_JSON,
    CROSSWALK_JSONL,
    FUNCTIONS_JSON,
    ANALYTIC_SOLUTIONS_JSON,
    REPORT_JSON,
    REPORT_MD,
    RULES_JSON,
    RULES_MD,
    build_candidates,
    build_report_payload,
    build_rules_payload,
    render_candidates_md,
    render_report_md,
    render_rules_md,
    write_json,
    write_jsonl,
    write_text,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify mathematical objects.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    payload = build_report_payload()
    candidates = payload["items"]
    rules = build_rules_payload()

    if args.dry_run or args.report or args.check:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.check:
        if not RULES_JSON.exists() or not CROSSWALK_JSON.exists():
            print("classification artifacts missing")
            return 1
        return 0
    if args.dry_run:
        return 0

    write_json(RULES_JSON, rules)
    write_text(RULES_MD, render_rules_md())
    write_json(CROSSWALK_JSON, candidates)
    write_jsonl(CROSSWALK_JSONL, candidates)
    write_json(REPORT_JSON, payload)
    write_text(REPORT_MD, render_report_md(payload))
    write_json(CANDIDATES_JSON, candidates)
    write_jsonl(CANDIDATES_JSONL, candidates)
    write_text(CANDIDATES_REPORT_MD, render_candidates_md(candidates))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
