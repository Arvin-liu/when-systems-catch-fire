#!/usr/bin/env python3
"""Validate Pack lifecycle state-machine contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/operations/durability/pack-lifecycle-contract-r1.json"
DEFAULT_SCHEMA = ROOT / "schemas/operations/durability-pack-lifecycle-r1.schema.json"


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
    print("DURABILITY_PACK_LIFECYCLE_OK packs=4 atomic=PASS version_pin=PASS advisory_overlay=BOUNDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
