#!/usr/bin/env python3
"""Validate the independent formal task terminality source."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

try:
    from tools import validate_current_task_lineage as lineage
except ImportError:
    import validate_current_task_lineage as lineage


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
LIFECYCLE_PATH = ROOT / "data/operations/formal-task-lifecycle-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/formal-task-lifecycle-r1.schema.json"
LINEAGE_PATH = ROOT / "data/operations/current-task-lineage-status.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    lifecycle = document if document is not None else load_json(LIFECYCLE_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(lifecycle)]
    if errors:
        return errors
    lineage_source = load_json(LINEAGE_PATH)
    if lifecycle["current_task_id"] != lineage_source["current_task"]["task_id"]:
        errors.append("formal lifecycle current_task_id differs from current task lineage")
    records = {row["task_id"]: row for row in lifecycle["tasks"]}
    if len(records) != len(lifecycle["tasks"]):
        errors.append("formal lifecycle contains duplicate task ids")
    current = records.get(lifecycle["current_task_id"])
    if current is None:
        errors.append("formal lifecycle is missing its current task record")
        return errors
    lineage_task = lineage_source["current_task"]
    if current["execution_status"] != lineage_task["execution_status"]:
        errors.append("formal lifecycle status differs from current task lineage")
    if current["terminal"] != lineage_task["terminal"]:
        errors.append("formal lifecycle terminality differs from current task lineage")
    if current["execution_status"] == "IN_PROGRESS" and current["terminal"]:
        errors.append("IN_PROGRESS formal task cannot be terminal")
    if current["execution_status"] in {"COMPLETED_WITH_CLASSIFIED_RESIDUALS", "COMPLETED_WITH_OPEN_OBLIGATIONS"} and not current["terminal"]:
        errors.append("completed formal task must be terminal")
    if current["execution_status"] == "COMPLETED_WITH_OPEN_OBLIGATIONS" and not current["open_obligation_ids"]:
        errors.append("terminal-with-open-obligations task must reference at least one obligation")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    _ = args
    errors = validate()
    if errors:
        print("FORMAL_TASK_LIFECYCLE_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    source = load_json(LIFECYCLE_PATH)
    print(f"FORMAL_TASK_LIFECYCLE_OK task={source['current_task_id']} terminal={str(source['tasks'][0]['terminal']).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
