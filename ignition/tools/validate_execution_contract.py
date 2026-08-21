#!/usr/bin/env python3
"""Validate the Task132 execution contract before canonical advancement."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
CONTRACT_PATH = ROOT / "data/operations/iterations/132/execution-contract-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/execution-contract-r1.schema.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    contract = document if document is not None else load_json(CONTRACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(contract)]
    if errors:
        return errors
    if contract["formal_baseline"]["sha"] != "e04752d20d071bac8f0c4a1e5cff20fb3004dae1":
        errors.append("formal baseline must remain the verified Task131 main SHA")
    if contract["identity_impact"] != "PRESENTATION_ONLY":
        errors.append("Task132 identity impact must remain PRESENTATION_ONLY")
    if "Owner authority" not in contract["claim_ceiling"] or "epistemic" not in contract["claim_ceiling"]:
        errors.append("claim ceiling must preserve the authority and epistemic boundary")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("EXECUTION_CONTRACT_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("EXECUTION_CONTRACT_OK task_id=IGNITION-20260822-132")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
