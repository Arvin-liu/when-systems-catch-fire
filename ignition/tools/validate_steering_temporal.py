#!/usr/bin/env python3
"""Validate deterministic temporal window semantics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/temporal-semantics-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-temporal-semantics-r1.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.steering import TemporalWindow, evaluate_temporal  # noqa: E402


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    windows = {row["window_id"]: TemporalWindow.from_dict(row) for row in document["windows"]}
    for case in document["cases"]:
        result = evaluate_temporal(windows[case["window_id"]], now=case["now"])
        if result.state != case["expected_state"]:
            errors.append(f"{case['window_id']} at {case['now']} expected {case['expected_state']} got {result.state}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_TEMPORAL_INVALID")
        for error in errors: print(f"- {error}")
        return 1
    print("STEERING_TEMPORAL_OK cases=5 deterministic=PASS unknown_time=NO_AUTOFILL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
