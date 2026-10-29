#!/usr/bin/env python3
"""Validate Goal lifecycle and non-inference gates for IGNITION-129."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/goal-lifecycle-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-goal-lifecycle-r1.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.steering import AuthorityProvenance, GoalRegistry, GoalRegistryError  # noqa: E402


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    registry = GoalRegistry.from_dict(document)
    goal = registry.get("goal-synthetic-brief")
    owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-goal-001", "synthetic activation", authorized=True)
    registry.transition(goal.goal_id, "ACTIVE", provenance=owner, reason="explicit synthetic activation", updated_at="2026-08-21T12:01:00+08:00")
    registry.transition(goal.goal_id, "BLOCKED", provenance=AuthorityProvenance("SYSTEM_DERIVED_PROPOSAL", "system.fixture", "block-001", "dependency is absent"), reason="prerequisite missing", updated_at="2026-08-21T12:02:00+08:00")
    try:
        registry.transition(goal.goal_id, "SATISFIED", provenance=owner, reason="run passed", evidence_refs=("run-pass",), updated_at="2026-08-21T12:03:00+08:00")
    except GoalRegistryError:
        pass
    else:
        errors.append("direct SATISFIED transition was accepted")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_GOAL_LIFECYCLE_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("STEERING_GOAL_LIFECYCLE_OK transitions=ACTIVE,BLOCKED direct_satisfied=FAIL_CLOSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
