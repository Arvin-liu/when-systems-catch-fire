#!/usr/bin/env python3
"""Validate that Task 129 residuals remain classified and non-regressive."""

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
DATA_PATH = ROOT / "data/operations/iterations/130/step11-residual-reclassification-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/step11-residual-reclassification-r1.schema.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate() -> list[str]:
    data = load_json(DATA_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(data)]
    if errors:
        return errors
    expected = {"HUMAN_SURFACE_SOURCE_HASH_DRIFT_11", "TASK127_PROJECTION_MANIFEST_MISSING_96", "PRODUCTION_EXECUTION_AUTHORITY_SHORT_WINDOW", "KNOWLEDGE_EXPERIENCE_TWO_PASS_SHORT_WINDOW", "FULL_DISCOVERY_LONG_RUNNING_BOUNDARY"}
    actual = {row["residual_id"] for row in data["residuals"]}
    if actual != expected:
        errors.append(f"residual ids differ: expected={sorted(expected)} actual={sorted(actual)}")
    if any(row["classification"] == "CURRENT_REGRESSION" for row in data["residuals"]):
        errors.append("current regression cannot be used as a residual classification")
    receipt = REPO_ROOT / data["source_receipt"]
    if not receipt.is_file():
        errors.append(f"source receipt missing: {data['source_receipt']}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("STEP11_RESIDUAL_RECLASSIFICATION_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("STEP11_RESIDUAL_RECLASSIFICATION_OK new_regressions=0 residual_classes=5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
