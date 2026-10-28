#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step23 candidate Registry admission."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.validate_ignition_operation_capability_registry import validate as validate_registry


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step23-candidate-registry-admission.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step23-candidate-registry-admission-r1.schema.json"
REGISTRY_PATH = ROOT / "data/operations/ignition-operation-capability-registry-r1.json"

EXPECTED_STEP22_HEAD = "1a0f850af834ee88dc93ac23ec3881683991d6ac"
EXPECTED_REGISTRY_BEFORE = "35ec66971f66df89874b82f53ff1b1af1cf0d45d7fac131bbadfffa2485a3d22"
EXPECTED_REGISTRY_AFTER = "ec285324bbdff4a718f7ffd761a61f8d393b77b8e15967bfd2e207a6d9950ea4"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)
    ]
    if errors:
        return errors

    if document["formal_previous_commit"] != EXPECTED_STEP22_HEAD:
        errors.append("Step23 must start from the proven Step22 formal head")

    registry_record = document["registry"]
    if registry_record["sha256_before"] != EXPECTED_REGISTRY_BEFORE:
        errors.append("Registry before digest is not the proven 19-operation digest")
    if registry_record["sha256_after"] != EXPECTED_REGISTRY_AFTER or sha256(REGISTRY_PATH) != EXPECTED_REGISTRY_AFTER:
        errors.append("Registry after digest drifted")
    registry = load_json(REGISTRY_PATH)
    if len(registry["operations"]) != 20 or registry["coverage"]["operation_count"] != 20:
        errors.append("Registry operation count is not exactly 20")
    if registry["coverage"]["non_pack_operation_count"] != 10:
        errors.append("Registry non-Pack operation count is not exactly 10")
    registry_errors = validate_registry(copy.deepcopy(registry))
    if registry_errors:
        errors.append("canonical Registry validator failed: " + "; ".join(registry_errors))

    operation_ids = [row["operation_id"] for row in registry["operations"]]
    operation = next((row for row in registry["operations"] if row["operation_id"] == "visualization.render_derived_system_view"), None)
    if operation is None:
        errors.append("provider-neutral visualization operation is absent")
    else:
        if operation["current_status"] != "CURRENT_BOUNDED":
            errors.append("visualization operation status is not CURRENT_BOUNDED")
        if operation["pack_binding"] is not None:
            errors.append("visualization operation must not be Pack-bound")
        if operation["default_execution_mode"] != "READ_ONLY_RUN":
            errors.append("visualization operation must remain READ_ONLY_RUN")
        if operation["repository_mutation_permission"] != "FORBIDDEN" or operation["external_action_permission"] != "FORBIDDEN":
            errors.append("visualization operation cannot authorize side effects")
        if operation["ai_callability"] != "PUBLIC_BOUNDED":
            errors.append("visualization operation must remain PUBLIC_BOUNDED")
    if operation_ids != sorted(operation_ids) or len(operation_ids) != len(set(operation_ids)):
        errors.append("Registry operation IDs are not sorted and unique")
    if any("archify" in operation_id.lower() for operation_id in operation_ids):
        errors.append("provider-specific Archify operation ID was registered")
    if any("delta" in operation_id.lower() for operation_id in operation_ids):
        errors.append("Architecture Delta operation was registered")

    boundary = document["admission_boundary"]
    if not boundary["entry_is_candidate_only_until_ready_merge_and_current_lifecycle"]:
        errors.append("Registry entry was not kept candidate-only")
    if boundary["formal_ready"] or boundary["merged_to_main"] or boundary["current_on_main"]:
        errors.append("Step23 claimed Ready, merge or Current on main")
    if boundary["default_renderer"] != "NOT_SELECTED" or boundary["architecture_authority"]:
        errors.append("default renderer or architecture authority boundary widened")
    if boundary["delta_operation_registered"] or boundary["provider_specific_operation_registered"]:
        errors.append("Delta or provider-specific registration crossed the boundary")

    scope = document["scope_freeze"]
    if scope["agent_reach"] != "NO_CHANGE" or scope["authenticated_channel_admission"] != "NO_CHANGE":
        errors.append("Agent Reach or authentication boundary changed")
    if scope["live_external_invocation"] != "OPEN_OWNER_DEFERRED_NOT_RUN" or scope["task151"] != "FORBIDDEN":
        errors.append("live invocation or Task151 boundary changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP23_CANDIDATE_REGISTRY_ADMISSION_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK150_STEP23_CANDIDATE_REGISTRY_ADMISSION_OK operations=20 new=visualization.render_derived_system_view status=CURRENT_BOUNDED candidate_only=true delta_registered=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
