#!/usr/bin/env python3
"""Validate the Analytic Solutions layer."""

from __future__ import annotations

import argparse
import json

from analytic_solution_utils import (
    ANALYTIC_SOLUTIONS_HUMAN_MD,
    ANALYTIC_SOLUTIONS_INDEX_MD,
    ANALYTIC_SOLUTIONS_JSON,
    ANALYTIC_SOLUTIONS_JSONL,
    ANALYTIC_SOLUTION_TEMPLATE_MD,
    build_categories,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the analytic-solution layer.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    items = []
    if ANALYTIC_SOLUTIONS_JSON.exists():
        items = json.loads(ANALYTIC_SOLUTIONS_JSON.read_text(encoding="utf-8"))
    categories = build_categories(items)
    counts = {
        "active": sum(1 for item in items if item["status"] == "active"),
        "lead": sum(1 for item in items if item["status"] == "lead"),
        "categories": len(categories),
    }
    print(json.dumps(counts, ensure_ascii=False, indent=2))

    if args.check:
        required = [ANALYTIC_SOLUTIONS_JSON, ANALYTIC_SOLUTIONS_JSONL, ANALYTIC_SOLUTIONS_INDEX_MD, ANALYTIC_SOLUTIONS_HUMAN_MD, ANALYTIC_SOLUTION_TEMPLATE_MD]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            print("Missing analytic solution files:", missing)
            return 1
        for item in items:
            if item.get("status") == "active":
                novelty = item.get("academic_novelty", {}).get("status")
                if novelty != "passed":
                    print("Active analytic solution without passed novelty:", item.get("id"))
                    return 1
                if not item.get("formula", {}).get("latex"):
                    print("Active analytic solution missing formula:", item.get("id"))
                    return 1
                if not item.get("derivation"):
                    print("Active analytic solution missing derivation:", item.get("id"))
                    return 1
                if not item.get("verification"):
                    print("Active analytic solution missing verification:", item.get("id"))
                    return 1
        print("Analytic solutions validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
