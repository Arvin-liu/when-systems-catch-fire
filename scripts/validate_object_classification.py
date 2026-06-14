#!/usr/bin/env python3
"""Validate the mathematical object classification system."""

from __future__ import annotations

import argparse
import json

from object_classification_utils import (
    ANALYTIC_SOLUTIONS_JSON,
    CANDIDATES_JSON,
    CROSSWALK_JSON,
    REPORT_JSON,
    RULES_JSON,
    build_report_payload,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate mathematical object classification.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    report = build_report_payload()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.check:
        missing = [str(path) for path in [RULES_JSON, CROSSWALK_JSON, REPORT_JSON, CANDIDATES_JSON, ANALYTIC_SOLUTIONS_JSON] if not path.exists()]
        if missing:
            print("Missing classification files:", missing)
            return 1
        for item in report["items"]:
            if item["new_class"] == "analytic_solution" and not item.get("preserve_legacy_link"):
                print("Missing legacy link preservation:", item["legacy_id"])
                return 1
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
