#!/usr/bin/env python3
"""Fail-closed validation for the Task150 Draft-only PR closeout."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step15-draft-closeout.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step15-draft-closeout-r1.schema.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)
    ]
    if errors:
        return errors

    pr = document["pull_request"]
    if pr["state"] != "OPEN" or pr["is_draft"] is not True or pr["merged"] is not False or pr["merge_commit"] is not None:
        errors.append("Draft PR is not open and unmerged")
    if pr["base_ref"] != "main" or pr["base_sha"] != "d7372c27abe456b5b8c058675630d8038f91b448":
        errors.append("PR base drifted from the Task149 A8 exact main baseline")
    if pr["checks_at_creation"] != "QUEUED_NOT_TREATED_AS_PASS":
        errors.append("queued checks were overclaimed as completion")

    closeout = document["closeout"]
    if closeout["decision"] != "DEFER" or closeout["stop_state"] != "AWAIT_OWNER_ARCHIFY_BOUNDED_ADMISSION_REVIEW" or closeout["next_action"] != "OWNER_REVIEW_ONLY":
        errors.append("Draft closeout did not stop at Owner review")
    if closeout["registry_write"] is not False or closeout["current_capability"] is not False or closeout["default_renderer"] is not False:
        errors.append("registry, Current or default renderer was enabled")
    if closeout["authenticated_channels"] != "NO_AUTHENTICATED_ADMISSION" or closeout["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("authentication or live invocation boundary changed")
    if closeout["owner_review_state"] != "PENDING" or closeout["task151"] != "FORBIDDEN":
        errors.append("Owner review or successor-task boundary changed")

    scope = document["scope_freeze"]
    if scope["current_admission"] != "NOT_ADMITTED" or scope["default_renderer"] != "NOT_SELECTED" or scope["provider_homepage"] != "NO_CLAIM":
        errors.append("Current, renderer or homepage scope changed")
    if scope["agent_reach"] != "NO_CHANGE" or scope["agent_reach_authenticated"] != "DEFER" or scope["authenticated_channels"] != "NO_AUTHENTICATED_ADMISSION":
        errors.append("Agent Reach scope changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP15_DRAFT_CLOSEOUT_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK150_STEP15_DRAFT_CLOSEOUT_OK pr=200 draft=true merged=false stop=OWNER_REVIEW")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
