#!/usr/bin/env python3
"""Validate the default-deny namespace contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/operations/durability/namespace-contract-r1.json"
DEFAULT_SCHEMA = ROOT / "schemas/operations/durability-namespace-r1.schema.json"


def validate(data: dict, schema: dict) -> list[str]:
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(data)]
    if data.get("default_policy") != "DENY_CROSS_NAMESPACE":
        errors.append("namespace default policy must be deny")
    if "explicit" not in str(data.get("cross_namespace_rule", "")).casefold() or "expiry" not in str(data.get("cross_namespace_rule", "")).casefold():
        errors.append("cross namespace rule lacks explicit scoped expiry")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    errors = validate(json.loads(args.data.read_text(encoding="utf-8")), json.loads(args.schema.read_text(encoding="utf-8")))
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("DURABILITY_NAMESPACE_OK default=DENY_CROSS_NAMESPACE principal_types=4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
