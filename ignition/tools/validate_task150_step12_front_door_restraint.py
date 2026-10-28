#!/usr/bin/env python3
"""Fail-closed validation for the Task150 Step12 front-door restraint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step12-front-door-restraint.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step12-front-door-restraint-r1.schema.json"


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

    formal = document["formal_observation"]
    if formal["task150_front_door_changed_paths"]:
        errors.append("Task150 changed a formal front-door path")
    if formal["task150_root_readme_added"] or formal["task150_readme_en_added"] or formal["task150_product_added"]:
        errors.append("Task150 added a root README, README_EN or PRODUCT front door")
    if any(item["baseline_unchanged"] is not True for item in formal["checked_formal_front_doors"]):
        errors.append("a checked formal front door drifted from the Task150 baseline")

    upstream = document["upstream_observation"]
    if any(item["modified_by_task150"] is not False for item in upstream["front_doors"]):
        errors.append("an upstream front door was modified by Task150")

    scan = document["claim_scan"]
    if any(scan[key] is not False for key in ("task150_added_provider_homepage_claim", "task150_added_current_provider_claim", "task150_added_default_renderer_claim", "task150_added_public_capability_claim")):
        errors.append("Task150 added a forbidden front-door claim")
    if scan["human_front_door_acceptance"] != "NOT_INFERRED":
        errors.append("human/Owner front-door acceptance was inferred")

    scope = document["scope_freeze"]
    if scope["current_admission"] != "NOT_ADMITTED" or scope["default_renderer"] != "NOT_SELECTED" or scope["provider_homepage"] != "NO_CLAIM":
        errors.append("Current, default renderer or homepage boundary changed")
    if scope["agent_reach"] != "NO_CHANGE" or scope["authenticated_channels"] != "NO_AUTHENTICATED_ADMISSION" or scope["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("Agent Reach, authentication or live invocation boundary changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP12_FRONT_DOOR_RESTRAINT_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK150_STEP12_FRONT_DOOR_RESTRAINT_OK changed_paths=0 homepage_claim=false current_claim=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
