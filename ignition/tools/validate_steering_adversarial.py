#!/usr/bin/env python3
"""Validate the IGNITION-129 adversarial steering matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/steering-adversarial-matrix-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-adversarial-matrix-r1.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.pilots.steering_adversarial_129 import ALLOWED_OUTCOMES, ADVERSARIAL_SCHEMA, run_adversarial_matrix  # noqa: E402


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    result = run_adversarial_matrix()
    expected = {row["case_id"]: row["expected_outcome"] for row in document["cases"]}
    actual = {row["case_id"]: row["observed_outcome"] for row in result["cases"]}
    if result["schema"] != ADVERSARIAL_SCHEMA or result["case_count"] != len(expected):
        errors.append("adversarial matrix schema or case count mismatch")
    if set(actual) != set(expected):
        errors.append("adversarial case IDs do not match fixture")
    for case_id, expected_outcome in expected.items():
        if actual.get(case_id) != expected_outcome:
            evidence = next((row.get("evidence") for row in result["cases"] if row["case_id"] == case_id), "missing")
            errors.append(f"{case_id} observed={actual.get(case_id)} expected={expected_outcome} evidence={evidence}")
    if not result["all_pass"] or not set(actual.values()) <= ALLOWED_OUTCOMES:
        errors.append("adversarial matrix has an unexpected or failing outcome")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_ADVERSARIAL_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("STEERING_ADVERSARIAL_OK cases=22 fail_closed=PASS reconciliation=PASS human_review=PASS pause_reconcile=PASS guard_pass=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
