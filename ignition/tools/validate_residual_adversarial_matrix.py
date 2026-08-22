#!/usr/bin/env python3
"""Run the 18-case IGNITION-134 residual delta adversarial matrix."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
FIXTURE = ROOT / "data/operations/iterations/134/fixtures/residual-delta-adversarial-matrix-r1.json"
sys.path.insert(0, str(ROOT / "tools"))

from tools import validate_residual_ledger as gate  # noqa: E402


def base_entry() -> dict[str, Any]:
    objects = [f"object-{index:02d}" for index in range(11)]
    dimensions = ["FAILURE_DIMENSION_A"]
    return {
        "residual_id": "RESIDUAL_TEST",
        "origin_task": "IGNITION-20260821-129",
        "classification": "TEST_INHERITED",
        "status": "OPEN_INHERITED",
        "baseline_fingerprint": gate.fingerprint(count=len(objects), objects=objects, failure_dimensions=dimensions),
        "current_fingerprint": gate.fingerprint(count=len(objects), objects=objects, failure_dimensions=dimensions),
        "baseline_count": len(objects),
        "current_count": len(objects),
        "baseline_objects": objects,
        "current_objects": list(objects),
        "baseline_failure_dimensions": dimensions,
        "current_failure_dimensions": list(dimensions),
        "baseline_source_command": "validator --check",
        "current_source_command": "validator --check",
        "validator": "validator.py",
        "provenance_paths": ["ignition/tools/validate_residual_adversarial_matrix.py"],
        "allowed_persistence_rule": "unchanged only",
        "release_impact": "NON_BLOCKING_IF_UNCHANGED",
    }


def refingerprint(entry: dict[str, Any]) -> None:
    entry["baseline_fingerprint"] = gate.fingerprint(
        count=len(entry["baseline_objects"]),
        objects=entry["baseline_objects"],
        failure_dimensions=entry["baseline_failure_dimensions"],
    )
    entry["current_fingerprint"] = gate.fingerprint(
        count=len(entry["current_objects"]),
        objects=entry["current_objects"],
        failure_dimensions=entry["current_failure_dimensions"],
    )


def mutate(entry: dict[str, Any], mutation: str) -> dict[str, Any]:
    entry = copy.deepcopy(entry)
    if mutation == "none":
        return entry
    if mutation == "add_object":
        entry["current_objects"].append("object-11")
        entry["current_count"] = 12
        refingerprint(entry)
    elif mutation == "replace_object":
        entry["current_objects"][-1] = "new-object"
        refingerprint(entry)
    elif mutation == "add_dimension":
        entry["current_failure_dimensions"].append("FAILURE_DIMENSION_B")
        refingerprint(entry)
    elif mutation == "forge_baseline_count":
        entry["baseline_count"] = 10
    elif mutation == "forge_current_count":
        entry["current_count"] = 10
    elif mutation == "forge_baseline_fingerprint":
        entry["baseline_fingerprint"] = "0" * 64
    elif mutation == "forge_current_fingerprint":
        entry["current_fingerprint"] = "0" * 64
    elif mutation in {"new_residual_unclassified", "new_regression_declared", "new_regression_wrong_origin"}:
        entry["baseline_objects"] = []
        entry["baseline_failure_dimensions"] = []
        entry["baseline_count"] = 0
        entry["origin_task"] = "IGNITION-20260822-134" if mutation == "new_regression_declared" else "IGNITION-20260821-129"
        entry["status"] = "NEW_REGRESSION" if mutation != "new_residual_unclassified" else "OPEN_INHERITED"
        refingerprint(entry)
    elif mutation == "change_source_command":
        entry["current_source_command"] = "validator --new-contract"
    elif mutation == "valid_migration":
        entry["current_source_command"] = "validator --new-contract"
        entry["migration"] = {
            "task_id": "IGNITION-20260822-134",
            "reason": "bounded validator command migration",
            "from_source_command": "validator --check",
            "to_source_command": "validator --new-contract",
        }
    elif mutation == "invalid_migration":
        entry["current_source_command"] = "validator --new-contract"
        entry["migration"] = {
            "task_id": "IGNITION-20260822-134",
            "reason": "forged migration metadata",
            "from_source_command": "validator --wrong-old-command",
            "to_source_command": "validator --new-contract",
        }
    elif mutation == "resolve":
        entry["current_objects"] = []
        entry["current_failure_dimensions"] = []
        entry["current_count"] = 0
        entry["status"] = "RESOLVED_CURRENT"
        refingerprint(entry)
    elif mutation == "resolved_live":
        entry["status"] = "RESOLVED_CURRENT"
    elif mutation == "shrink_without_status":
        entry["current_objects"] = entry["current_objects"][:-1]
        entry["current_count"] = 10
        refingerprint(entry)
    elif mutation == "duplicate_id":
        return entry
    else:
        raise ValueError(f"unknown mutation: {mutation}")
    return entry


def run_matrix() -> dict[str, Any]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases = fixture.get("cases", [])
    if len(cases) != 18:
        raise ValueError(f"expected 18 cases, observed {len(cases)}")
    results: list[dict[str, Any]] = []
    for case in cases:
        entry = mutate(base_entry(), case["mutation"])
        if case["mutation"] == "duplicate_id":
            duplicate = copy.deepcopy(entry)
            errors, _ = gate.validate({
                "schema_version": "residual-ledger-r1",
                "task_id": "IGNITION-20260822-134",
                "baseline_ref": {"repository": "Arvin-liu/when-systems-catch-fire", "ref": "refs/heads/main", "sha": "5" * 40},
                "residuals": [entry, duplicate],
                "claim_ceiling": "test",
            })
        else:
            errors = gate.compare_entry(entry)["errors"]
        observed = sorted(set(error.split(":", 1)[-1] for error in errors))
        expected_errors = sorted(case.get("expected_errors", []))
        passed = (not expected_errors and not errors) or (expected_errors and all(any(expected in error for error in errors) for expected in expected_errors))
        results.append({"case_id": case["case_id"], "expected": case["expected"], "observed_errors": observed, "pass": bool(passed)})
        if not passed:
            raise AssertionError(f"{case['case_id']}: expected={expected_errors} observed={errors}")
    return {"case_count": len(results), "passed": sum(item["pass"] for item in results), "results": results}


def main() -> int:
    result = run_matrix()
    print(f"RESIDUAL_ADVERSARIAL_MATRIX_OK cases={result['case_count']} passed={result['passed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
