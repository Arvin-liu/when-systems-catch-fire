#!/usr/bin/env python3
"""Validate the live Task135 formal execution contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

try:
    from tools import task_identity
except ImportError:
    import task_identity


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
CONTRACT_PATH = ROOT / "data/operations/iterations/135/execution-contract-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/execution-contract-135-r1.schema.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    contract = document if document is not None else load_json(CONTRACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(contract)]
    if errors:
        return errors
    expectations = contract["identity_expectations"]
    for field in ("current_formal_task", "latest_architecture_changing_task", "previous_canonical_current_task", "previous_formal_task", "release_candidate_task", "publication_witness_task"):
        try:
            task_identity.parse_task_id(expectations[field])
        except task_identity.TaskIdentityError as exc:
            errors.append(f"{field} is not parseable: {exc}")
    if contract["identity_impact"] != "PRESENTATION_ONLY":
        errors.append("Task135 identity impact must remain PRESENTATION_ONLY")
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
        print("EXECUTION_CONTRACT_135_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("EXECUTION_CONTRACT_135_OK task_id=IGNITION-20260822-135")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
