#!/usr/bin/env python3
"""Validate the Step 09 executor admission contract without live calls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from agent_runtime.executor_admission import ExecutorAdmission, ExecutorAdmissionError


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/operations/durability/executor-admission-contract-r1.json"
DEFAULT_SCHEMA = ROOT / "schemas/operations/durability-executor-admission-r1.schema.json"


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
    parsed = []
    for item in data["executor_fixtures"]:
        try:
            parsed.append(ExecutorAdmission.from_dict(item))
        except ExecutorAdmissionError as exc:
            print(f"FAIL\n- invalid fixture: {exc}")
            return 1
    if len(parsed) != 4 or any(item.status != "ADMITTED" for item in parsed):
        print("FAIL\n- fixture admission state is not four admitted offline records")
        return 1
    freeze = data["reference_executor_freeze"]
    if "remote_git" not in freeze["forbidden_capabilities"] or freeze["status"] != "FROZEN":
        print("FAIL\n- Reference Executor freeze is incomplete")
        return 1
    print("DURABILITY_EXECUTOR_ADMISSION_OK fixtures=4 conformance_epoch=1 drift=FAIL_CLOSED revocation=FAIL_CLOSED reference_freeze=PASS live_invocation=NOT_REQUIRED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
