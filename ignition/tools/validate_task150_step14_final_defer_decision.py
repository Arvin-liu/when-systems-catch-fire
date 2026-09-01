#!/usr/bin/env python3
"""Fail-closed validation for the Task150 Step14 final DEFER decision."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step14-final-defer-decision.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step14-final-defer-decision-r1.schema.json"


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

    decision = document["decision"]
    if decision["outcome"] != "DEFER" or decision["candidate_status"] != "EXPERIMENTAL_CANDIDATE_NOT_REGISTERED":
        errors.append("final decision did not remain DEFER/not-registered")
    if decision["current_capability"] is not False or decision["default_renderer"] is not False or decision["registry_write"] is not False:
        errors.append("Current, default renderer or registry admission was enabled")
    if decision["ready_or_merge_authorization"] is not False:
        errors.append("Ready or merge authorization was granted")
    if decision["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("live external invocation changed")

    owner = document["owner_decision_context"]
    if owner["archify"]["fit"] != "FIT_WITH_LIMITS" or owner["archify"]["continuation"] != "CONTINUE_EXPERIMENT":
        errors.append("Archify owner context drifted from fit-with-limits/continue-experiment")
    if owner["agent_reach_public"]["fit"] != "FIT_WITH_LIMITS" or owner["agent_reach_public"]["continuation"] != "CONTINUE_EXPERIMENT" or owner["agent_reach_public"]["task150_change"] != "NO_CHANGE":
        errors.append("public Agent Reach owner context drifted")
    auth = owner["agent_reach_authenticated"]
    if auth["decision"] != "DEFER" or auth["authenticated_channel_admission"] != "NO_AUTHENTICATED_ADMISSION" or auth["task150_change"] != "NO_CHANGE":
        errors.append("authenticated Agent Reach remained open")

    gates = document["gate_summary"]
    if gates["delta_viewport_containment_zero_failure"] != "FAIL" or gates["owner_visual_acceptance"] != "PENDING":
        errors.append("the blocking/pending gates were not retained")
    if document["blocking_evidence"]["delta_diagnostics"] != 3 or document["blocking_evidence"]["standalone_containment"] != "PASS" or document["blocking_evidence"]["delta_semantic_compare"] != "PASS_28_OF_28":
        errors.append("blocking evidence drifted")

    scope = document["scope_freeze"]
    if scope["current_admission"] != "NOT_ADMITTED" or scope["default_renderer"] != "NOT_SELECTED" or scope["provider_homepage"] != "NO_CLAIM":
        errors.append("Current, renderer or homepage scope changed")
    if scope["authenticated_channels"] != "NO_AUTHENTICATED_ADMISSION" or scope["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("authentication or live invocation scope changed")
    if scope["task151"] != "FORBIDDEN" or scope["successor_task"] != "NOT_CREATED":
        errors.append("successor task was admitted")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP14_FINAL_DEFER_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK150_STEP14_FINAL_DEFER_OK current=false registry_write=false auth=DEFER")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
