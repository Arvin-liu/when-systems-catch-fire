#!/usr/bin/env python3
"""Validate the provider-neutral executor admission contract and decisions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

try:
    from agent_federation.executor_admission_contract import validate_contract_shape
except ImportError:
    from ignition.agent_federation.executor_admission_contract import validate_contract_shape


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
CONTRACT_PATH = ROOT / "data/operations/executor-admission-contract-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/executor-admission-contract-r1.schema.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    contract = document if document is not None else load_json(CONTRACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(contract)]
    if errors:
        return errors
    candidate_ids = [row["executor_id"] for row in contract["candidates"]]
    if len(candidate_ids) != len(set(candidate_ids)):
        errors.append("executor admission contract has duplicate candidate ids")
    errors.extend(validate_contract_shape(contract))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("EXECUTOR_ADMISSION_CONTRACT_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    contract = load_json(CONTRACT_PATH)
    decisions = {row["executor_id"]: row["live_eligibility"] for row in contract["candidates"]}
    print(f"EXECUTOR_ADMISSION_CONTRACT_OK candidates={len(decisions)} eligible={sum(value == 'ELIGIBLE_FOR_LIVE_READONLY' for value in decisions.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
