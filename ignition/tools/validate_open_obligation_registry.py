#!/usr/bin/env python3
"""Validate open obligations independently from formal task terminality."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

try:
    from agent_federation.live_current_projection import validate_projection
except ImportError:
    from ignition.agent_federation.live_current_projection import validate_projection


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REGISTRY_PATH = ROOT / "data/operations/open-obligation-registry-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/open-obligation-registry-r1.schema.json"
LINEAGE_PATH = ROOT / "data/operations/current-task-lineage-status.json"
PROJECTION_PATH = ROOT / "data/operations/iterations/141/live-current-projection-r3.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    registry = document if document is not None else load_json(REGISTRY_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(registry)]
    if errors:
        return errors
    lineage = load_json(LINEAGE_PATH)
    if registry["current_task_id"] != lineage["current_task"]["task_id"]:
        errors.append("obligation registry current_task_id differs from current task lineage")
    adjudication = registry["last_adjudication"]
    if adjudication["task_id"] != registry["current_task_id"]:
        errors.append("last obligation adjudication is not bound to the current task")
    if adjudication["current_status"] == "OPEN" and adjudication["decision"] != "OPEN_RETAINED":
        errors.append("an open obligation adjudication must be OPEN_RETAINED")
    if adjudication["current_status"] == "CLOSED" and adjudication["decision"] != "CLOSED_WITH_NEW_OBLIGATIONS":
        errors.append("a closed obligation adjudication must declare its successor decision")
    ids = [row["obligation_id"] for row in registry["obligations"]]
    if len(ids) != len(set(ids)):
        errors.append("obligation registry contains duplicate obligation ids")
    live = next((row for row in registry["obligations"] if row["obligation_id"] == "LIVE_EXTERNAL_INVOCATION"), None)
    if live is None:
        errors.append("LIVE_EXTERNAL_INVOCATION obligation is missing")
    else:
        projection = validate_projection(load_json(PROJECTION_PATH))
        counts = projection["counts"]
        if live["current_status"] == "CLOSED" and counts["validated_completion_count"] == 0:
            errors.append("live obligation cannot close without a validated completion")
        if live["current_status"] == "OPEN" and counts["validated_completion_count"] > 0:
            errors.append("live obligation must be adjudicated after a validated completion")
        if live["next_eligible_action"] != projection["next_eligible_action"]["action"]:
            errors.append("live obligation next action differs from live projection")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("OPEN_OBLIGATION_REGISTRY_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    source = load_json(REGISTRY_PATH)
    print(f"OPEN_OBLIGATION_REGISTRY_OK open={sum(row['current_status'] == 'OPEN' for row in source['obligations'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
