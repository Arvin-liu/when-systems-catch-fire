#!/usr/bin/env python3
"""Validate the deterministic offline cross-domain steering pilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/steering-offline-pilot-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-offline-pilot-r1.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.pilots.steering_portfolio_129 import PILOT_SCHEMA, run_pilot  # noqa: E402


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    result = run_pilot()
    if result["schema"] != PILOT_SCHEMA or not result["offline_only"]:
        errors.append("pilot is not explicitly offline")
    if result["selected_goal_id"] != document["expected_selected_goal_id"]:
        errors.append("pilot selected an unexpected Goal")
    if set(result["domains"]) != set(document["required_domains"]):
        errors.append("pilot domain matrix is incomplete")
    completion = result["completion"]
    if completion["run_pass_outcome"] != document["expected_run_pass_outcome"] or completion["owner_independent_outcome"] != document["expected_owner_outcome"]:
        errors.append("pilot completion non-inference or Owner decision boundary failed")
    lifecycle = result["lifecycle"]
    if lifecycle["paused"] != "PAUSED" or lifecycle["resumed"] != "ACTIVE" or lifecycle["episode_terminal"] != "EPISODE_COMPLETED_VALIDATED" or lifecycle["run_pass_goal_mutated"]:
        errors.append("pilot failure/pause/resume lifecycle boundary failed")
    if not result["durability"]["replay_same_selection"] or result["durability"]["event_count"] != 2:
        errors.append("pilot snapshot/replay did not reproduce selection")
    boundaries = result["candidate_boundaries"]
    for goal_id in ("goal-repository", "goal-knowledge", "goal-superseded", "goal-unavailable"):
        if boundaries[goal_id]["eligible"]:
            errors.append(f"pilot boundary unexpectedly eligible: {goal_id}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_PILOT_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("STEERING_PILOT_OK offline=PASS domains=7 selected=goal-writing run_pass=UNVERIFIABLE owner_completion=SATISFIED pause_resume=PASS replay_selection=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
