#!/usr/bin/env python3
"""Fail-closed residual identity and delta gate for IGNITION-134.

The ledger records observations derived from named validators; it is not a
second source of failure facts.  Fingerprints cover the observed object set,
count and failure dimensions.  An inherited residual may persist only when
that tuple is unchanged.  Growth, replacement, dimension changes, forged
fingerprints, source-command changes without migration, and newly appearing
residuals fail closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
LEDGER_PATH = ROOT / "data/operations/residual-ledger-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/residual-ledger-r1.schema.json"
EXPECTED_TASK_ID = "IGNITION-20260822-134"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fingerprint(*, count: int, objects: list[str], failure_dimensions: list[str]) -> str:
    payload = {
        "count": count,
        "objects": sorted(set(objects)),
        "failure_dimensions": sorted(set(failure_dimensions)),
    }
    return hashlib.sha256(canonical(payload)).hexdigest()


def _set(entry: dict[str, Any], key: str) -> set[str]:
    value = entry.get(key, [])
    return {str(item) for item in value}


def compare_entry(entry: dict[str, Any], *, expected_task_id: str = EXPECTED_TASK_ID) -> dict[str, Any]:
    residual_id = entry.get("residual_id", "<missing>")
    baseline_objects = _set(entry, "baseline_objects")
    current_objects = _set(entry, "current_objects")
    baseline_dimensions = _set(entry, "baseline_failure_dimensions")
    current_dimensions = _set(entry, "current_failure_dimensions")
    baseline_count = entry.get("baseline_count")
    current_count = entry.get("current_count")
    errors: list[str] = []

    if isinstance(baseline_count, int) and baseline_count != len(baseline_objects):
        errors.append(f"{residual_id}:BASELINE_COUNT_OBJECT_SET_MISMATCH")
    if isinstance(current_count, int) and current_count != len(current_objects):
        errors.append(f"{residual_id}:CURRENT_COUNT_OBJECT_SET_MISMATCH")

    expected_baseline = fingerprint(count=len(baseline_objects), objects=sorted(baseline_objects), failure_dimensions=sorted(baseline_dimensions))
    expected_current = fingerprint(count=len(current_objects), objects=sorted(current_objects), failure_dimensions=sorted(current_dimensions))
    if entry.get("baseline_fingerprint") != expected_baseline:
        errors.append(f"{residual_id}:BASELINE_FINGERPRINT_FORGED")
    if entry.get("current_fingerprint") != expected_current:
        errors.append(f"{residual_id}:CURRENT_FINGERPRINT_FORGED")

    if entry.get("baseline_source_command") != entry.get("current_source_command") and "migration" not in entry:
        errors.append(f"{residual_id}:SOURCE_COMMAND_CHANGED_WITHOUT_MIGRATION")

    added_objects = sorted(current_objects - baseline_objects)
    removed_objects = sorted(baseline_objects - current_objects)
    added_dimensions = sorted(current_dimensions - baseline_dimensions)
    removed_dimensions = sorted(baseline_dimensions - current_dimensions)
    changed = bool(added_objects or added_dimensions or (isinstance(current_count, int) and isinstance(baseline_count, int) and current_count > baseline_count))
    if changed:
        errors.append(f"{residual_id}:RESIDUAL_GROWTH_UNCLASSIFIED")

    baseline_is_empty = not baseline_objects and not baseline_dimensions and baseline_count == 0
    current_is_empty = not current_objects and not current_dimensions and current_count == 0
    status = entry.get("status")
    if baseline_is_empty and not current_is_empty:
        if status != "NEW_REGRESSION" or entry.get("origin_task") != expected_task_id:
            errors.append(f"{residual_id}:NEW_RESIDUAL_REQUIRES_CLASSIFICATION")
        else:
            errors.append(f"{residual_id}:NEW_REGRESSION_RELEASE_BLOCKING")
    if current_is_empty and status != "RESOLVED_CURRENT":
        errors.append(f"{residual_id}:RESOLUTION_STATUS_INVALID")
    if not current_is_empty and not changed and status == "RESOLVED_CURRENT":
        errors.append(f"{residual_id}:RESOLVED_STATUS_WITH_LIVE_OBJECTS")

    return {
        "residual_id": residual_id,
        "baseline_count": len(baseline_objects),
        "current_count": len(current_objects),
        "added_objects": added_objects,
        "removed_objects": removed_objects,
        "added_failure_dimensions": added_dimensions,
        "removed_failure_dimensions": removed_dimensions,
        "changed": changed,
        "errors": errors,
    }


def validate(document: dict[str, Any] | None = None) -> tuple[list[str], dict[str, Any]]:
    ledger = document if document is not None else load_json(LEDGER_PATH)
    errors: list[str] = []
    if SCHEMA_PATH.is_file():
        errors.extend(error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(ledger))
    if ledger.get("task_id") != EXPECTED_TASK_ID:
        errors.append(f"LEDGER_TASK_ID_MISMATCH:expected={EXPECTED_TASK_ID}:observed={ledger.get('task_id')}")
    entries = ledger.get("residuals", [])
    seen: set[str] = set()
    comparisons: list[dict[str, Any]] = []
    for entry in entries:
        residual_id = entry.get("residual_id")
        if residual_id in seen:
            errors.append(f"DUPLICATE_RESIDUAL_ID:{residual_id}")
        seen.add(residual_id)
        comparison = compare_entry(entry)
        comparisons.append(comparison)
        errors.extend(comparison["errors"])
    return sorted(set(errors)), {"ledger": ledger, "comparisons": comparisons}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors, report = validate()
    if errors:
        print("RESIDUAL_LEDGER_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print(json.dumps(report["comparisons"], ensure_ascii=False, sort_keys=True))
        return 1
    unchanged = sum(not item["changed"] and item["current_count"] == item["baseline_count"] for item in report["comparisons"])
    resolved = sum(item["current_count"] == 0 for item in report["comparisons"])
    print(f"RESIDUAL_LEDGER_OK entries={len(report['comparisons'])} inherited_unchanged={unchanged} resolved={resolved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
