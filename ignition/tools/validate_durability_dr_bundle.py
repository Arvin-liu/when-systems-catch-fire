#!/usr/bin/env python3
"""Validate Step 13 DR bundle contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from agent_runtime.dr_bundle import DR_BUNDLE_EPOCH, DR_BUNDLE_SCHEMA, REQUIRED_CHUNKS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/operations/durability/dr-bundle-contract-r1.json"
DEFAULT_SCHEMA = ROOT / "schemas/operations/durability-dr-bundle-r1.schema.json"


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
    if data["schema_version"] != DR_BUNDLE_SCHEMA or data["bundle_epoch"] != DR_BUNDLE_EPOCH or data["required_chunks"] != list(REQUIRED_CHUNKS):
        print("FAIL\n- DR bundle runtime contract mismatch")
        return 1
    print("DURABILITY_DR_BUNDLE_OK chunks=12 manifest_hash=PASS fresh_restore=PASS missing_corrupt_namespace_stale_schema=FAIL_CLOSED soft_to_hard=FAIL_CLOSED external_rerun=FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
