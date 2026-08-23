#!/usr/bin/env python3
"""Validate the declarative bindings for formal-task identity roles."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
MODEL_PATH = ROOT / "data/operations/task-identity-model-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/task-identity-model-r1.schema.json"

ROLE_KEYS = (
    "current_formal_task",
    "latest_architecture_changing_task",
    "release_candidate_task",
    "publication_witness_task",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    model = document if document is not None else load_json(MODEL_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(model)]
    if errors:
        return errors
    bindings = model["role_bindings"]
    if tuple(bindings) != ROLE_KEYS:
        errors.append("task identity role order must be current formal, architecture, candidate, witness")
    expected_roles = {
        "current_formal_task": "CURRENT_FORMAL_TASK",
        "latest_architecture_changing_task": "LATEST_ARCHITECTURE_CHANGING_TASK",
        "release_candidate_task": "RELEASE_CANDIDATE_TASK",
        "publication_witness_task": "PUBLICATION_WITNESS_TASK",
    }
    for key, role in expected_roles.items():
        if bindings[key]["role"] != role:
            errors.append(f"role binding {key} must declare role {role}")
    if bindings["current_formal_task"]["source_path"] != "ignition/data/operations/current-task-lineage-status.json":
        errors.append("current_formal_task must be sourced from canonical task lineage")
    if bindings["current_formal_task"]["json_pointer"] != "/current_task/task_id":
        errors.append("current_formal_task JSON pointer is not canonical")
    if bindings["latest_architecture_changing_task"]["source_path"] != "ignition/data/operations/current-task-lineage-status.json":
        errors.append("latest_architecture_changing_task must be sourced from canonical task lineage")
    if bindings["latest_architecture_changing_task"]["json_pointer"] != "/task_identity/latest_architecture_changing_task":
        errors.append("latest_architecture_changing_task JSON pointer is not canonical")
    if bindings["release_candidate_task"]["source_path"] != "ignition/data/operations/iterations/135/execution-contract-r1.json":
        errors.append("release_candidate_task must be sourced from the Task135 execution contract")
    if not bindings["publication_witness_task"]["source_path"].startswith("Arvin-liu/1111:"):
        errors.append("publication_witness_task must remain in the control repository")
    if model["historical_lineage_source"]["preserve_history"] is not True:
        errors.append("historical lineage must be preserved")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK_IDENTITY_MODEL_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK_IDENTITY_MODEL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
