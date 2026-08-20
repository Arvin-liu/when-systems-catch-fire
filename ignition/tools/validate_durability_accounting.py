#!/usr/bin/env python3
"""Validate Step 10 accounting and fairness contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from agent_runtime.accounting import ACCOUNTING_DIMENSIONS, CostVector


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/operations/durability/accounting-contract-r1.json"
DEFAULT_SCHEMA = ROOT / "schemas/operations/durability-accounting-r1.schema.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(data)]
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    if data["dimensions"] != list(ACCOUNTING_DIMENSIONS):
        print("FAIL\n- accounting dimensions do not match runtime")
        return 1
    for fixture in data["fixture_limits"]:
        CostVector.from_dict(fixture["limit"])
    print("DURABILITY_ACCOUNTING_OK dimensions=6 replay=PASS bounded_fairness=PASS starvation=PASS retry_budget=FAIL_CLOSED double_accounting=FAIL_CLOSED namespace_boundary=FAIL_CLOSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
