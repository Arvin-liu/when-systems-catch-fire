#!/usr/bin/env python3
"""Validate the explicit semantic model for Current iteration identities."""

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
MODEL_PATH = ROOT / "data/operations/iteration-boundary-semantics-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/iteration-boundary-semantics-r1.schema.json"

FIELD_ORDER = (
    "current_formal_task_id",
    "current_formal_task_ordinal",
    "latest_architecture_changing_task_id",
    "latest_architecture_task_ordinal",
    "current_method_version",
    "current_iteration_boundary",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve(relative_path: str) -> Path:
    path = (REPO_ROOT / relative_path).resolve()
    path.relative_to(REPO_ROOT.resolve())
    return path


def validate(document: dict[str, Any] | None = None) -> list[str]:
    model = document if document is not None else load_json(MODEL_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(model)]
    if errors:
        return errors

    if tuple(model["field_order"]) != FIELD_ORDER:
        errors.append("field_order must keep formal id, formal ordinal, architecture id, architecture ordinal, method, alias")
    fields = model["fields"]
    expected_sources = {
        "current_formal_task_id": ("ignition/data/operations/current-task-lineage-status.json", "/task_identity/current_formal_task"),
        "latest_architecture_changing_task_id": ("ignition/data/operations/current-task-lineage-status.json", "/task_identity/latest_architecture_changing_task"),
        "current_method_version": ("ignition/ITERATION.md", None),
    }
    for field_id, (path_text, pointer) in expected_sources.items():
        source = fields[field_id].get("source", {})
        if source.get("path") != path_text:
            errors.append(f"{field_id} source path is not canonical: {source.get('path')}")
        if pointer is not None and source.get("json_pointer") != pointer:
            errors.append(f"{field_id} JSON pointer is not canonical: {source.get('json_pointer')}")
        try:
            if not resolve(path_text).is_file():
                errors.append(f"{field_id} source is missing: {path_text}")
        except ValueError as exc:
            errors.append(str(exc))

    for field_id, role in {
        "current_formal_task_ordinal": "current_formal_task_id",
        "latest_architecture_task_ordinal": "latest_architecture_changing_task_id",
        "current_iteration_boundary": "current_formal_task_ordinal",
    }.items():
        if fields[field_id].get("source_role") != role:
            errors.append(f"{field_id} must derive from {role}")

    alias = fields["current_iteration_boundary"]
    if alias.get("status") != "DEPRECATED_COMPATIBILITY_ALIAS" or alias.get("deprecated") is not True:
        errors.append("current_iteration_boundary must be explicitly deprecated compatibility alias")
    if alias.get("must_equal") != "current_formal_task_ordinal":
        errors.append("current_iteration_boundary must equal current_formal_task_ordinal")
    if model["compatibility_policy"]["current_iteration_boundary"]["alias_of"] != "current_formal_task_ordinal":
        errors.append("compatibility policy must alias current_formal_task_ordinal")
    separation = model["separation"]
    if separation["formal_and_architecture_ordinals_are_independent"] is not True or separation["equality_required"] is not False:
        errors.append("formal and architecture ordinals must be explicitly independent")
    if fields["current_formal_task_ordinal"].get("value_type") != "integer" or fields["latest_architecture_task_ordinal"].get("value_type") != "integer":
        errors.append("named ordinal fields must have integer value_type")
    if "value" in alias or "value" in fields["current_formal_task_ordinal"] or "value" in fields["latest_architecture_task_ordinal"]:
        errors.append("ordinal values must not be manually stored in the semantic model")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("ITERATION_BOUNDARY_SEMANTICS_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("ITERATION_BOUNDARY_SEMANTICS_MODEL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
