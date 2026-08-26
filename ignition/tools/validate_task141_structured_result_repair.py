#!/usr/bin/env python3
"""Validate Task141 Step07 strict result contract and fake conformance receipt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/operations/iterations/141/step07-structured-result-repair.json"


class Task141StructuredResultRepairError(RuntimeError):
    """Raised when the structured-result repair receipt overclaims or is incomplete."""


def run_validation() -> dict[str, Any]:
    document = json.loads(PATH.read_text(encoding="utf-8"))
    if document.get("task_id") != "IGNITION-20260826-141" or document.get("step") != "07" or document.get("status") != "PASS":
        raise Task141StructuredResultRepairError("Task141 Step07 binding/status is invalid")
    contract = document["contract"]
    if contract["additional_properties"] or contract["validation_order"] != "strict_object_contract_before_privacy_sanitization":
        raise Task141StructuredResultRepairError("strict contract ordering or additional-property policy is missing")
    matrix = document["fake_executor_conformance"]
    if any(matrix[key] != expected for key, expected in (("failures", 0), ("errors", 0), ("skips", 0))):
        raise Task141StructuredResultRepairError("fake executor conformance is not clean")
    cases = {item["case"]: item for item in matrix["cases"]}
    expected = {
        "exact_result": ("COMPLETED_VALIDATED", "NONE"),
        "semantically_wrong_but_schema_valid": ("VALIDATION_FAILED", "UNKNOWN_UNCLASSIFIED"),
        "extra_field": ("MALFORMED_RESULT", "STRUCTURED_RESULT_SCHEMA_FAILURE"),
        "malformed_json": ("MALFORMED_RESULT", "STRUCTURED_RESULT_PARSE_FAILURE"),
        "nonzero_without_structured_result": ("MALFORMED_RESULT", "PROCESS_EXIT_NONZERO_NO_STRUCTURED_RESULT"),
        "timeout": ("TIMED_OUT_EFFECT_UNKNOWN", "OBSERVATION_INCOMPLETE"),
    }
    for case, (state, diagnostic) in expected.items():
        if cases.get(case, {}).get("terminal_state") != state or cases.get(case, {}).get("diagnostic_class") != diagnostic:
            raise Task141StructuredResultRepairError(f"fake conformance case {case} diverged")
    return {
        "status": "PASS",
        "tests_run": matrix["tests_run"],
        "failures": matrix["failures"],
        "errors": matrix["errors"],
        "skips": matrix["skips"],
        "strict_additional_properties": contract["additional_properties"],
        "claim_ceiling": document["claim_ceiling"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    print(json.dumps(run_validation(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
