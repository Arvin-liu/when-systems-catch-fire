#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step09 environment admission."""

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
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step09-environment-admission.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step09-environment-admission-r1.schema.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def admission_result(provider_present: bool, node_present: bool) -> str:
    return "RUN_BOUNDED_READ_ONLY" if provider_present and node_present else "PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT"


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    if errors:
        return errors
    policy = document["admission_policy"]
    if policy["automatic_system_install"] is not False or policy["skill_install"] != "EXPLICIT_REQUEST_ONLY":
        errors.append("automatic or skill installation was admitted")
    for case in document["simulated_admission_cases"]:
        if case["result"] != admission_result(case["provider_present"], case["node_present"]):
            errors.append(f"admission result drifted: {case['id']}")
        if case["system_install"] is not False:
            errors.append(f"system installation was permitted: {case['id']}")
    if document["scope_freeze"]["current_admission"] != "NOT_ADMITTED":
        errors.append("Step09 cannot admit Current")
    if document["scope_freeze"]["agent_reach"] != "NO_CHANGE":
        errors.append("Agent Reach changed")
    if document["scope_freeze"]["authenticated_channels"] != "NO_AUTHENTICATED_ADMISSION":
        errors.append("authenticated admission changed")
    if document["scope_freeze"]["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("live external invocation changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP09_ENVIRONMENT_ADMISSION_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK150_STEP09_ENVIRONMENT_ADMISSION_OK present=RUN_BOUNDED_READ_ONLY absent=PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT install=false current=NOT_ADMITTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
