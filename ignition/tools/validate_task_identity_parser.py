#!/usr/bin/env python3
"""Run the positive, negative and separation fixtures for task identity parsing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from tools import task_identity
except ImportError:
    import task_identity


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FIXTURE_PATH = ROOT / "data/operations/iterations/133/fixtures/task-identity-parser-fixtures-r1.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(fixtures: dict[str, Any] | None = None) -> list[str]:
    fixtures = fixtures or load_json(FIXTURE_PATH)
    errors: list[str] = []
    for case in fixtures["positive"]:
        try:
            parsed = task_identity.parse_task_id(case["task_id"])
        except task_identity.TaskIdentityError as exc:
            errors.append(f"positive {case['case_id']} unexpectedly failed: {exc}")
            continue
        if parsed["canonical"] != case["task_id"] or parsed["date"] != case["expected_date"] or parsed["ordinal"] != case["expected_ordinal"]:
            errors.append(f"positive {case['case_id']} parsed unexpectedly: {parsed}")

    for case in fixtures["negative"]:
        declared = {key: case[key] for key in ("declared_date", "declared_ordinal") if key in case}
        if declared:
            case_errors = task_identity.validate_declared_identity(case["task_id"], **declared)
        else:
            try:
                task_identity.parse_task_id(case["task_id"])
            except task_identity.TaskIdentityError as exc:
                case_errors = [str(exc)]
            else:
                case_errors = []
        if not case_errors:
            errors.append(f"negative {case['case_id']} unexpectedly passed")
        elif case.get("error_contains") not in " ".join(case_errors):
            errors.append(f"negative {case['case_id']} had wrong error: {case_errors}")

    for case in fixtures["binding_cases"]:
        case_errors = task_identity.validate_binding_records(case["records"])
        passed = not case_errors
        expected = case["expected"] == "PASS"
        if passed != expected:
            errors.append(f"binding {case['case_id']} expected {case['expected']} but got {case_errors}")
        if case.get("error_contains") and case["error_contains"] not in " ".join(case_errors):
            errors.append(f"binding {case['case_id']} had wrong error: {case_errors}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK_IDENTITY_PARSER_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK_IDENTITY_PARSER_FIXTURES_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
