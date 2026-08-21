#!/usr/bin/env python3
"""Validate bounded federation Intent Capsule construction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/steering-intent-capsule-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-intent-capsule-r1.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.steering import AuthorityProvenance, GoalRecord, IntentRecord, IntentCapsule, build_intent_capsule  # noqa: E402

NOW = "2026-08-21T12:00:00+08:00"


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    row = document["fixture"]
    owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-capsule-1", "synthetic capsule authority", authorized=True)
    intent = IntentRecord(row["intent_id"], row["intent_statement"], row["namespace"], owner, status="ACTIVE", created_at=NOW, updated_at=NOW)
    goal = GoalRecord(row["goal_id"], intent.intent_id, row["goal_statement"], row["namespace"], "contract-capsule-1", owner, status="ACTIVE", created_at=NOW, updated_at=NOW)
    capsule = build_intent_capsule(intent, goal, success_criteria=row["success_criteria"], permission_summary=row["permission_summary"], blocker_refs=row["blocker_refs"], temporal_refs=row["temporal_refs"], report_contract_refs=row["report_contract_refs"], minimal_context_refs=row["minimal_context_refs"], created_at=NOW)
    restored = IntentCapsule.from_dict(capsule.to_dict())
    if restored != capsule or not capsule.capsule_digest:
        errors.append("capsule digest or round-trip mismatch")
    if capsule.executor_can_mutate_canonical or capsule.executor_report_boundary()["canonical_mutation_allowed"]:
        errors.append("executor canonical mutation boundary widened")
    if set(capsule.to_dict()) != {"schema", "capsule_id", "intent_id", "goal_id", "intent_summary", "goal_summary", "success_criteria", "permission_summary", "blocker_refs", "temporal_refs", "report_contract_refs", "minimal_context_refs", "namespace_ref", "created_at", "executor_can_mutate_canonical", "authority_boundary", "capsule_digest"}:
        errors.append("capsule contains an unbounded field")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_CAPSULE_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("STEERING_CAPSULE_OK digest=PASS bounded_fields=PASS report_only=PASS canonical_mutation=DENY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
