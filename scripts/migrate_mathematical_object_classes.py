#!/usr/bin/env python3
"""Migration wrapper for mathematical object class reclassification."""

from __future__ import annotations

import argparse
import json

from object_classification_utils import (
    CROSSWALK_JSON,
    CROSSWALK_JSONL,
    REPORT_JSON,
    REPORT_MD,
    build_candidates,
    build_report_payload,
    render_report_md,
    write_json,
    write_jsonl,
    write_text,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate mathematical object classes.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    payload = build_report_payload()
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    write_json(CROSSWALK_JSON, payload["items"])
    write_jsonl(CROSSWALK_JSONL, payload["items"])
    write_json(REPORT_JSON, payload)
    write_text(REPORT_MD, render_report_md(payload))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
