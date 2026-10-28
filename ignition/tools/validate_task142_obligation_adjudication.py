#!/usr/bin/env python3
"""Validate the Task142 open-obligation adjudication and its unchanged live counts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from agent_federation.live_current_projection import validate_projection


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/operations/task142-obligation-adjudication-r1.schema.json"
REGISTRY = ROOT / "data/operations/open-obligation-registry-r1.json"
PROJECTION = ROOT / "data/operations/iterations/141/live-current-projection-r3.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    document: dict[str, Any] = json.loads(args.path.read_text(encoding="utf-8"))
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    adjudication = registry.get("last_adjudication", {})
    for key in ("task_id", "decision", "previous_status", "current_status", "validated_completion_count", "live_attempt_started", "new_obligation_ids"):
        if adjudication.get(key) != document.get(key):
            errors.append(f"registry last_adjudication.{key} differs from the Step16 artifact")
    projection = validate_projection(json.loads(PROJECTION.read_text(encoding="utf-8")))
    if projection["counts"]["validated_completion_count"] != 0 or projection["counts"]["total_attempts"] != 6 or projection["counts"]["unreconciled_count"] != 0 or projection["counts"]["observation_incomplete_count"] != 2:
        errors.append("Step16 does not preserve the 6/0/0/2 live counts")
    if errors:
        for error in errors:
            print(f"- {error}")
        return 1
    print("TASK142_OBLIGATION_ADJUDICATION_OK decision=OPEN_RETAINED validated_completion_count=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
