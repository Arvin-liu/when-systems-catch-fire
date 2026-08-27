#!/usr/bin/env python3
"""Validate the current formal execution contract.

The current contract is resolved from canonical Current task identity.  Older
task-specific schemas and validators remain historical records and are not
reused as the current source.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

try:
    from tools import task_identity
except ImportError:  # direct script / tools-on-PYTHONPATH execution
    import task_identity


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
LINEAGE_PATH = ROOT / "data/operations/current-task-lineage-status.json"


def _current_identity() -> tuple[str, int]:
    lineage = load_json(LINEAGE_PATH)
    task_id = lineage["task_identity"]["current_formal_task"]
    return task_id, task_identity.parse_task_id(task_id)["ordinal"]


def _current_paths() -> tuple[Path, Path, str, int]:
    task_id, ordinal = _current_identity()
    return (
        ROOT / f"data/operations/iterations/{ordinal}/execution-contract-r1.json",
        ROOT / "schemas/operations/execution-contract-r1.schema.json",
        task_id,
        ordinal,
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


# These names are intentionally materialized from the canonical source at
# import time so callers and tests can inspect the current contract path.
CONTRACT_PATH, SCHEMA_PATH, CURRENT_TASK_ID, CURRENT_ORDINAL = _current_paths()


def validate(document: dict[str, Any] | None = None) -> list[str]:
    contract = document if document is not None else load_json(CONTRACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(contract)]
    if errors:
        return errors
    lineage = load_json(LINEAGE_PATH)
    identity = lineage.get("task_identity", {})
    expectations = contract.get("identity_expectations", {})
    if contract.get("task_id") != CURRENT_TASK_ID:
        errors.append(f"execution contract task must match canonical Current task {CURRENT_TASK_ID}")
    for field in ("current_formal_task", "release_candidate_task", "publication_witness_task"):
        if expectations.get(field) != CURRENT_TASK_ID:
            errors.append(f"identity expectation {field} must match canonical Current task {CURRENT_TASK_ID}")
    if expectations.get("latest_architecture_changing_task") != identity.get("latest_architecture_changing_task"):
        errors.append("latest architecture-changing task must match canonical task identity")
    if expectations.get("previous_canonical_current_task") != identity.get("previous_canonical_current_task"):
        errors.append("previous canonical Current task must match canonical task identity")
    if expectations.get("previous_formal_task") != identity.get("previous_formal_task"):
        errors.append("previous formal task must match canonical task identity")
    baseline_audit = ROOT / f"data/operations/iterations/{CURRENT_ORDINAL}/step00-baseline-audit.json"
    if baseline_audit.is_file():
        audit = load_json(baseline_audit)
        # Task137 used a ``baseline`` object; Task138 records the same
        # observation under ``formal_repository``. Keep the binding strict
        # while accepting both historical receipt shapes.
        baseline = (
            audit.get("baseline")
            or audit.get("formal_repository")
            or audit.get("formal_baseline")
            or audit.get("task144_baseline")
            or {}
        )
        expected_baseline = (
            baseline.get("expected_main_sha")
            or baseline.get("origin_main_sha")
            or baseline.get("baseline_sha")
            or baseline.get("formal_head_sha")
            or baseline.get("formal_origin_main_expected")
            or baseline.get("formal_baseline_sha")
        )
        if expected_baseline and contract.get("formal_baseline", {}).get("sha") != expected_baseline:
            errors.append("formal baseline must remain the verified current-task starting main SHA")
    current_impact = lineage.get("current_task", {}).get("identity_impact")
    if current_impact and contract.get("identity_impact") != current_impact:
        errors.append("execution contract identity impact differs from canonical Current task")
    if "Owner authority" not in contract["claim_ceiling"] or "epistemic" not in contract["claim_ceiling"]:
        errors.append("claim ceiling must preserve the authority and epistemic boundary")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("EXECUTION_CONTRACT_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"EXECUTION_CONTRACT_OK task_id={CURRENT_TASK_ID}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
