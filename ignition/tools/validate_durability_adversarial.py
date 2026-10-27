#!/usr/bin/env python3
"""Validate the Step 15 offline adversarial matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from agent_runtime.adversarial import ADVERSARIAL_SCHEMA, AdversarialMatrix, AdversarialMatrixError, REQUIRED_CASE_IDS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/operations/durability/adversarial-matrix-r1.json"
DEFAULT_SCHEMA = ROOT / "schemas/operations/durability-adversarial-matrix-r1.schema.json"


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
    if data.get("schema_version") != ADVERSARIAL_SCHEMA or set(data.get("required_case_ids", [])) != set(REQUIRED_CASE_IDS):
        print("FAIL\n- adversarial case inventory mismatch")
        return 1
    try:
        matrix = AdversarialMatrix.from_dict(data)
        summary = matrix.validate()
    except AdversarialMatrixError as exc:
        print(f"FAIL\n- {exc}")
        return 1
    print(f"ADVERSARIAL_MATRIX_OK cases={summary['case_count']} fail_closed={summary['fail_closed_cases']} reconciliation={summary['reconciliation_cases']} restart_replay={summary['restart_replay_cases']} external_invocation=NOT_RUN claim_ceiling=BOUNDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
