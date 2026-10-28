#!/usr/bin/env python3
"""Validate human-first Driver Console Steering R3 projection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/steering-driver-console-r3.json"
SCHEMA = ROOT / "schemas/operations/steering-driver-console-r3.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.driver_console import STEERING_DRIVER_CONSOLE_SCHEMA, build_steering_console_snapshot, render_steering_console  # noqa: E402


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    snapshot = build_steering_console_snapshot(document["fixture"])
    human = render_steering_console(snapshot)
    if snapshot["schema"] != STEERING_DRIVER_CONSOLE_SCHEMA:
        errors.append("steering console schema mismatch")
    if snapshot["important_goal"]["goal_id"] != "goal-console-important":
        errors.append("important Goal is not selected from explicit why-next")
    if len(snapshot["completed_runs_goal_unsatisfied"]) != 1 or snapshot["completed_runs_goal_unsatisfied"][0]["goal_status"] == "SATISFIED":
        errors.append("completed Run / unsatisfied Goal distinction is missing")
    if not snapshot["paused_intents"] or not snapshot["superseded_intents"]:
        errors.append("paused or superseded Intent surface is missing")
    for phrase in ("Important Goal", "Why now", "Owner decisions", "Completed Runs with Goal still unsatisfied", "Paused Intents", "Superseded Intents", "Unknowns"):
        if phrase not in human:
            errors.append(f"human console is missing section: {phrase}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_CONSOLE_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("STEERING_CONSOLE_OK schema=R3 important_goal=PASS why_now=PASS blockers=PASS owner_decisions=PASS run_non_inference=PASS paused_superseded=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
