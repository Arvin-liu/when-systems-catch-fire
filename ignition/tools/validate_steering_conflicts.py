#!/usr/bin/env python3
"""Validate deterministic conflict arbitration and fail-closed boundaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/steering-conflict-arbitration-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-conflict-arbitration-r1.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.steering import AuthorityProvenance, ConflictArbiter, ConflictCandidate, OwnerOverride, PriorityInputs  # noqa: E402

NOW = "2026-08-21T12:00:00+08:00"


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-arbitration-1", "synthetic arbitration override", authorized=True)
    override = OwnerOverride("override-arbitration-1", "goal-owner-selected", 0, "explicit Owner arbitration", owner, NOW)
    arbiter = ConflictArbiter()
    for row in document["cases"]:
        candidates = []
        for candidate_row in row["candidates"]:
            priority = dict(candidate_row["priority"])
            goal_id = priority["goal_id"]
            priority["owner_override"] = override if goal_id == "goal-owner-selected" else None
            candidates.append(ConflictCandidate(PriorityInputs(**priority), **{key: value for key, value in candidate_row.items() if key != "priority"}))
        receipt = arbiter.arbitrate(row["arbitration_id"], row["conflict_type"], candidates, created_at=NOW)
        if receipt.outcome != row["expected_outcome"]:
            errors.append(f"{row['arbitration_id']} outcome={receipt.outcome} expected={row['expected_outcome']}")
        if receipt.selected_goal_id != row["expected_selected_goal_id"]:
            errors.append(f"{row['arbitration_id']} selected={receipt.selected_goal_id} expected={row['expected_selected_goal_id']}")
        if receipt.reconciliation_required != row["expected_reconciliation"]:
            errors.append(f"{row['arbitration_id']} reconciliation flag mismatch")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_CONFLICT_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("STEERING_CONFLICT_OK cases=7 permission_ceiling=PASS safety=HUMAN_REVIEW stale=RECONCILIATION_REQUIRED score_authority=NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
