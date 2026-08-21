#!/usr/bin/env python3
"""Validate explainable lexicographic priority policy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/priority-policy-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-priority-policy-r1.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.steering import AuthorityProvenance, OwnerOverride, PriorityInputs, PriorityPolicy  # noqa: E402

NOW = "2026-08-21T12:00:00+08:00"


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-priority-1", "synthetic override", authorized=True)
    override = OwnerOverride("override-1", "goal-owner-override", 0, "explicitly inspect this goal now", owner, NOW)
    candidates = [PriorityInputs(**row, owner_override=override if row["goal_id"] == "goal-owner-override" else None) for row in document["cases"]]
    decisions = PriorityPolicy().order(candidates)
    if decisions[0].goal_id != "goal-owner-override":
        errors.append("explicit Owner override did not remain visible in order")
    denied = next(item for item in decisions if item.goal_id == "goal-permission-denied")
    if denied.eligible:
        errors.append("permission-ineligible goal was selected")
    if denied.inputs.deadline_state != "OVERDUE":
        errors.append("deadline input was not preserved")
    if decisions[0].telemetry_score is None:
        errors.append("telemetry tie-break is missing")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_PRIORITY_INVALID")
        for error in errors: print(f"- {error}")
        return 1
    print("STEERING_PRIORITY_OK policy=LEXICOGRAPHIC_RULES_R1 permission_ceiling=PASS score=TELEMETRY_ONLY override=VISIBLE_RETRACTABLE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
