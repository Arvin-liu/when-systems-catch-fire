#!/usr/bin/env python3
"""Validate the bounded ESI R0 candidate record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD = ROOT / "data/epistemic-governance/esi-candidate-boundary-r0.json"
DEFAULT_SCHEMA = ROOT / "schemas/epistemic-governance/esi-candidate-boundary-r0.schema.json"


def validate(record: dict, schema: dict) -> list[str]:
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(record)]
    ids = [item.get("id") for item in record.get("alternative_explanations", [])]
    if len(ids) != len(set(ids)):
        errors.append("alternative explanation IDs must be unique")
    if record.get("scope", {}).get("mechanism_status") != "CANDIDATE_PHENOMENON" or "not_hard_authority" not in record.get("scope", {}):
        errors.append("candidate record must preserve candidate and non-authority boundaries")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path, nargs="?", default=DEFAULT_RECORD)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    errors = validate(json.loads(args.record.read_text(encoding="utf-8")), json.loads(args.schema.read_text(encoding="utf-8")))
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("ESI_CANDIDATE_OK status=CANDIDATE_ESI_SIGNAL claim_ceiling=bounded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
