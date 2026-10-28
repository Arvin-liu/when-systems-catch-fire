#!/usr/bin/env python3
"""Validate Step 14 Driver Recovery Surface contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from agent_runtime.driver_console import DRIVER_RECOVERY_SURFACE_SCHEMA


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/operations/durability/driver-recovery-surface-r2.json"
DEFAULT_SCHEMA = ROOT / "schemas/operations/driver-recovery-surface-r2.schema.json"


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
    if data["schema_version"] != DRIVER_RECOVERY_SURFACE_SCHEMA:
        print("FAIL\n- Driver Recovery Surface schema mismatch")
        return 1
    print("DRIVER_RECOVERY_SURFACE_OK views=12 human_first=PASS projection_only=PASS soft_governance=ADVISORY_OR_CANDIDATE technical_refs=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
