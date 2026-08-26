#!/usr/bin/env python3
"""Run and validate the offline executor conformance matrix."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

try:
    from agent_federation.executor_conformance import run_matrix, validate_matrix
except ImportError:
    from ignition.agent_federation.executor_conformance import run_matrix, validate_matrix


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
SCHEMA_PATH = ROOT / "schemas/operations/executor-conformance-matrix-r1.schema.json"
MATRIX_PATH = ROOT / "data/operations/executor-conformance-matrix-r1.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    matrix = document if document is not None else load_json(MATRIX_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(matrix)]
    errors.extend(validate_matrix(matrix))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--print", dest="print_matrix", action="store_true")
    args = parser.parse_args()
    matrix = load_json(MATRIX_PATH) if args.check else run_matrix()
    if args.print_matrix:
        print(json.dumps(matrix, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    errors = validate(matrix)
    if errors:
        print("EXECUTOR_CONFORMANCE_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("EXECUTOR_CONFORMANCE_OK cases=11 accepted=1 rejected=10 live_process_started=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
