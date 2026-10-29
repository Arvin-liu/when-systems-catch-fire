#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step10 license and drift evidence."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step10-license-drift.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step10-license-drift-r1.schema.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    if errors:
        return errors
    upstream = document["upstream_observation"]
    if upstream["vendor_source"] is not False or upstream["worktree"] != "CLEAN" or upstream["non_shallow"] is not True:
        errors.append("upstream source was vendored or checkout evidence drifted")
    attribution = document["attribution"]
    if attribution["license"] != "MIT" or attribution["recorded_in_ignition"] is not True:
        errors.append("MIT attribution is incomplete")
    if document["drift_policy"]["automatic_update"] is not False:
        errors.append("automatic upstream update was admitted")
    if document["drift_policy"]["compatibility_check_before_use"] is not True:
        errors.append("fresh compatibility check before new revision use is missing")
    if document["drift_policy"]["future_claim"] != "NO_FUTURE_VERSION_COMPATIBILITY_CLAIM":
        errors.append("future compatibility was overclaimed")
    scope = document["scope_freeze"]
    if scope["current_admission"] != "NOT_ADMITTED" or scope["agent_reach"] != "NO_CHANGE":
        errors.append("Current or Agent Reach scope changed")
    if scope["installation"] != "NO_INSTALL_OR_AUTO_UPGRADE":
        errors.append("installation boundary changed")
    if scope["authenticated_channels"] != "NO_AUTHENTICATED_ADMISSION" or scope["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("authentication or live invocation boundary changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP10_LICENSE_DRIFT_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK150_STEP10_LICENSE_DRIFT_OK license=MIT envelope=PINNED_REVISION_ONLY auto_update=false future_claim=NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
