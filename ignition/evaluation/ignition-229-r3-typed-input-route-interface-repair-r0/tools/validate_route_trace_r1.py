#!/usr/bin/env python3
"""Fail-closed semantic validator for a Task229 route trace R1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from route_reference_interpreter import RouteInterfaceError, interpret, load_json_file


def validate_trace(policy: Any, binding: Any, candidate_trace: Any, policy_bytes: bytes | None = None) -> dict[str, Any]:
    expected = interpret(policy, binding, policy_bytes)
    if expected["execution_status"] != "ROUTE_TRACE_READY":
        error = expected["error"] or {"code": "UNKNOWN_FAIL_CLOSED", "message": "reference interpreter failed closed"}
        return {"status": "FAIL", "code": "REFERENCE_FAILS_CLOSED", "reference_error": error}
    if not isinstance(candidate_trace, dict):
        return {"status": "FAIL", "code": "TRACE_SCHEMA_FAILURE", "message": "trace must be an object"}
    reference_trace = expected["route_trace"]
    expected_keys = set(reference_trace)
    if set(candidate_trace) != expected_keys:
        return {
            "status": "FAIL",
            "code": "TRACE_SCHEMA_FAILURE",
            "message": "trace fields do not exactly match route-trace-r1.schema.json",
            "missing_fields": sorted(expected_keys - set(candidate_trace)),
            "unknown_fields": sorted(set(candidate_trace) - expected_keys),
        }
    for field in ("evaluated_input_ids", "missing_input_ids", "preserved_baseline_action_ids"):
        value = candidate_trace.get(field)
        if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
            return {"status": "FAIL", "code": "TRACE_SCHEMA_FAILURE", "message": f"{field} must be an array of IDs"}
        if len(value) != len(set(value)):
            return {"status": "FAIL", "code": "TRACE_SCHEMA_FAILURE", "message": f"{field} contains duplicate IDs"}
    if candidate_trace != reference_trace:
        mismatched = sorted(key for key in expected_keys if candidate_trace.get(key) != reference_trace.get(key))
        return {"status": "FAIL", "code": "TRACE_SEMANTIC_MISMATCH", "mismatched_fields": mismatched}
    return {
        "status": "PASS",
        "code": "ROUTE_TRACE_R1_MATCHES_REFERENCE",
        "route_trace": reference_trace,
        "missing_input_report": expected["missing_input_report"],
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", required=True, help="frozen policy JSON")
    parser.add_argument("--binding", required=True, help="typed binding JSON")
    parser.add_argument("--trace", required=True, help="successor route_trace object JSON")
    parser.add_argument("--output", help="write validation receipt JSON to this path")
    args = parser.parse_args()
    try:
        policy, policy_raw = load_json_file(args.policy)
        binding, _ = load_json_file(args.binding)
        trace, _ = load_json_file(args.trace)
        result = validate_trace(policy, binding, trace, policy_raw)
    except RouteInterfaceError as exc:
        result = {"status": "FAIL", "code": exc.code, "message": exc.message}
    output = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
