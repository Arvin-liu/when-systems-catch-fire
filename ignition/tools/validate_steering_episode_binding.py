#!/usr/bin/env python3
"""Validate Goal/Episode binding and non-inference across Run results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/steering-episode-goal-binding-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-episode-goal-binding-r1.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.steering import AuthorityProvenance, GoalEpisodeBinder, GoalRecord  # noqa: E402

NOW = "2026-08-21T12:00:00+08:00"
LATER = "2026-08-21T12:01:00+08:00"


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    owner = AuthorityProvenance("OWNER_DECLARED", "owner.synthetic", "auth-binding-1", "synthetic Goal binding", authorized=True)
    binder = GoalEpisodeBinder()
    for row in document["cases"]:
        goal = GoalRecord(row["goal_id"], row["intent_id"], row["statement"], row["namespace"], row["completion_contract_id"], owner, status=row["goal_status"], created_at=NOW, updated_at=NOW)
        binding = binder.bind(goal, row["episode_id"], row["run_ids"], secondary_goal_ids=row["secondary_goal_ids"], executor_instances=row["executor_instances"], created_at=NOW)
        after_episode = binder.update_episode(binding.binding_id, "EPISODE_COMPLETED_VALIDATED", updated_at=LATER)
        after_run = binder.record_run_outcome(binding.binding_id, row["run_ids"][0], "PASS", updated_at=LATER)
        after_handoff = binder.handoff(binding.binding_id, row["run_ids"][0], "instance-handoff", updated_at=LATER)
        receipt = binder.reconcile_run_result(binding.binding_id, row["run_ids"][0], "PASS")
        if binding.objective_digest != goal.objective_digest():
            errors.append(f"{row['episode_id']} objective digest mismatch")
        if after_episode.goal_status_at_bind != goal.status or after_run.goal_status_at_bind != goal.status:
            errors.append(f"{row['episode_id']} episode/run mutated Goal status")
        if after_handoff.handoff_identity_digest != binding.handoff_identity_digest:
            errors.append(f"{row['episode_id']} handoff changed stable identity digest")
        if receipt["goal_status_mutated"] or receipt["completion_inference"] != "INDEPENDENT_CONTRACT_REQUIRED":
            errors.append(f"{row['episode_id']} completion inference boundary failed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_EPISODE_BINDING_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("STEERING_EPISODE_BINDING_OK cases=2 digest=PASS run_pass_non_inference=PASS handoff_identity=UNCHANGED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
