#!/usr/bin/env python3
"""Validate Task142's fail-closed pre-live gate and its no-invocation decision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from agent_federation.executor_conformance import run_matrix, validate_matrix
from agent_federation.local_executor_census import validate_path
from tools.validate_executor_admission_contract import validate as validate_admission_contract
from tools.validate_formal_task_lifecycle import validate as validate_lifecycle
from tools.validate_open_obligation_registry import validate as validate_obligations


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/operations/task142-pre-live-gate-r1.schema.json"
CENSUS = ROOT / "data/operations/iterations/142/local-executor-census-r2.json"
CONFORMANCE = ROOT / "data/operations/executor-conformance-matrix-r1.json"


def validate(document: dict[str, Any]) -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document)]
    if document.get("decision") == "SKIPPED_UNSAFE_OR_UNAVAILABLE" and document.get("live_authorized") is not False:
        errors.append("skipped pre-live gate cannot authorize live execution")
    if document.get("attempt_policy", {}).get("attempt_a_started") or document.get("attempt_policy", {}).get("attempt_b_started"):
        errors.append("pre-live gate cannot record a started attempt")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    document = json.loads(args.path.read_text(encoding="utf-8"))
    errors = validate(document)
    errors.extend(f"lifecycle: {error}" for error in validate_lifecycle())
    errors.extend(f"obligation: {error}" for error in validate_obligations())
    try:
        validate_path(CENSUS, expected_task_id="IGNITION-20260827-142", expected_step="11")
    except Exception as exc:
        errors.append(f"census: {exc}")
    matrix = json.loads(CONFORMANCE.read_text(encoding="utf-8"))
    errors.extend(f"conformance: {error}" for error in validate_matrix(matrix))
    if validate_matrix(run_matrix()) != validate_matrix(matrix):
        errors.append("stored offline conformance matrix is not reproducible")
    errors.extend(f"admission: {error}" for error in validate_admission_contract())
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    if census["selection"]["live_selection_status"] != "NO_AUTHORIZED_FAMILY" or census["selection"]["live_selectable_executor_ids"]:
        errors.append("pre-live gate does not match the fresh no-authorized-family census")
    if errors:
        for error in errors:
            print(f"- {error}")
        return 1
    print("TASK142_PRE_LIVE_GATE_OK decision=SKIPPED_UNSAFE_OR_UNAVAILABLE live_authorized=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
