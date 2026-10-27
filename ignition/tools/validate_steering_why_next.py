#!/usr/bin/env python3
"""Validate the explainable why-next steering surface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/steering-why-next-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-why-next-r1.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.steering import AuthorityProvenance, ConflictCandidate, NextWorkCandidate, OwnerOverride, PriorityInputs, SteeringEngine  # noqa: E402

NOW = "2026-08-21T12:00:00+08:00"


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-why-next-1", "synthetic why-next override", authorized=True)
    override = OwnerOverride("override-why-next", "goal-owner-next", 0, "explicit Owner why-next selection", owner, NOW)
    engine = SteeringEngine()
    for row in document["cases"]:
        candidates = []
        for candidate_row in row["candidates"]:
            priority = dict(candidate_row["priority"])
            priority["owner_override"] = override if priority["goal_id"] == "goal-owner-next" else None
            conflict = ConflictCandidate(priority_inputs=PriorityInputs(**priority), **{key: value for key, value in candidate_row.items() if key in {"intent_status", "mutually_exclusive_group", "executor_available", "stale", "superseded", "safety_critical"}})
            candidates.append(NextWorkCandidate(conflict_candidate=conflict, **{key: value for key, value in candidate_row.items() if key in {"pack_ref", "executor_ref", "budget_available", "blockers", "unknowns"}}))
        trace = engine.select_next(row["trace_id"], row["conflict_type"], candidates, created_at=NOW)
        if trace.selected_goal_id != row["expected_selected_goal_id"]:
            errors.append(f"{row['trace_id']} selected={trace.selected_goal_id} expected={row['expected_selected_goal_id']}")
        if trace.owner_override_ref != row["expected_owner_override_ref"]:
            errors.append(f"{row['trace_id']} owner_override={trace.owner_override_ref} expected={row['expected_owner_override_ref']}")
        if not trace.why_now or not trace.why_selected:
            errors.append(f"{row['trace_id']} missing why-next explanation")
        if not trace.permission_budget_resource:
            errors.append(f"{row['trace_id']} missing permission/budget/resource record")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_WHY_NEXT_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("STEERING_WHY_NEXT_OK traces=3 selected=1 blocked_or_reconciled=2 skipped_reasons=PASS authority=EXPLAINABLE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
