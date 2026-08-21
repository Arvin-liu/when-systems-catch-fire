#!/usr/bin/env python3
"""Validate the canonical current task-lineage/status record."""

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
STATUS_PATH = ROOT / "data/operations/current-task-lineage-status.json"
SCHEMA_PATH = ROOT / "schemas/operations/current-task-lineage-status-r1.schema.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_repo_path(relative_path: str) -> Path:
    candidate = (REPO_ROOT / relative_path).resolve()
    try:
        candidate.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes repository: {relative_path}") from exc
    return candidate


def validate(document: dict[str, Any] | None = None) -> list[str]:
    if not STATUS_PATH.is_file():
        return [f"missing canonical task-lineage source: {STATUS_PATH.relative_to(REPO_ROOT)}"]
    if not SCHEMA_PATH.is_file():
        return [f"missing task-lineage schema: {SCHEMA_PATH.relative_to(REPO_ROOT)}"]
    source = document if document is not None else load_json(STATUS_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(source)]
    if errors:
        return errors

    current_task = source["current_task"]
    if current_task["execution_status"] == "IN_PROGRESS" and current_task["terminal"]:
        errors.append("IN_PROGRESS current task cannot be terminal")
    if current_task["execution_status"] == "COMPLETED_WITH_CLASSIFIED_RESIDUALS" and not current_task["terminal"]:
        errors.append("completed current task must be terminal")
    if source["current_state"]["current_state_status"] != "CURRENT_WITH_OPEN_OBLIGATIONS":
        errors.append("current state status must remain CURRENT_WITH_OPEN_OBLIGATIONS")
    if source["current_state"]["epistemically_accepted"] != 0:
        errors.append("epistemically_accepted must remain exactly 0")

    lineage_ids = [lineage["lineage_id"] for lineage in source["lineages"]]
    if len(lineage_ids) != len(set(lineage_ids)):
        errors.append("duplicate task lineage id")
    for lineage in source["lineages"]:
        predecessor = lineage["predecessor"]
        successor = lineage["successor"]
        if predecessor["task_file_status"] == "HISTORICAL_UNEXECUTED" and predecessor["requirement_lineage_status"] != "REBASED_INTO_127":
            errors.append("unexecuted 125 file must explicitly carry REBASED_INTO_127 requirement lineage")
        if successor["execution_status"] == "COMPLETED_WITH_CLASSIFIED_RESIDUALS" and successor["new_regressions"] != 0:
            errors.append("127 classified-completion lineage must record new_regressions=0")
        for token in lineage["current_surface_rule"]["forbidden_status_tokens"]:
            if token not in {"DEFERRED_PENDING_REBASE", "DEFERRED"}:
                errors.append(f"unexpected forbidden current-status token: {token}")
        for provenance in lineage["provenance"]:
            if provenance["repository"] == "Arvin-liu/when-systems-catch-fire":
                try:
                    if not resolve_repo_path(provenance["path"]).is_file():
                        errors.append(f"missing local lineage provenance: {provenance['path']}")
                except ValueError as exc:
                    errors.append(str(exc))
    for path in source["protected_historical_paths"]:
        try:
            if not resolve_repo_path(path).is_file():
                errors.append(f"missing protected historical path: {path}")
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("CURRENT_TASK_LINEAGE_STATUS_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("CURRENT_TASK_LINEAGE_STATUS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
