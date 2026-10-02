#!/usr/bin/env python3
"""Run the synthetic, target-blind Task229 route-interface conformance corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from build_typed_case_binding import MAPPING_VERSION, build_binding
from route_reference_interpreter import (
    RouteInterfaceError,
    canonical_json_bytes,
    interpret,
    load_json_file,
)
from validate_route_trace_r1 import validate_trace


SUBTREE = Path(__file__).resolve().parents[1]
FIXTURE_PATH = SUBTREE / "fixtures" / "synthetic-route-conformance-r1.json"
REQUIRED_FIXTURES = {
    "all_present_selector_match",
    "all_present_fallback",
    "missing_one_selector_input",
    "missing_boolean_is_not_false",
    "explicit_false_is_present",
    "explicit_null_permitted",
    "explicit_null_not_permitted",
    "stop_match",
    "missing_stop_input",
    "multiple_selector_matches",
    "stop_selector_conflict",
    "unknown_input_id",
    "duplicate_input_id",
    "type_mismatch_no_coercion",
    "unit_mismatch_no_conversion",
    "preserved_baseline_mismatch",
    "prose_binding_conflict_marker",
}


def _actual_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    return "unsupported"


def _value_type_for_mapping(value: Any, declared: Any) -> str:
    if isinstance(declared, str):
        allowed = (declared,)
    elif isinstance(declared, list) and declared:
        allowed = tuple(item for item in declared if isinstance(item, str))
    else:
        return "unsupported"
    actual = _actual_type(value)
    if actual in allowed:
        return actual
    if actual == "integer" and "number" in allowed:
        return "number"
    return allowed[0] if allowed else "unsupported"


def _mapping_for(policy: dict[str, Any], source_case: dict[str, Any], mutation: dict[str, Any] | None) -> dict[str, Any]:
    entries = []
    values = source_case.get("values", {})
    required = policy.get("selector", {}).get("required_inputs", [])
    for declaration in required:
        input_id = declaration["input_id"]
        present = input_id in values
        entry = {
            "input_id": input_id,
            "present": present,
            "source_pointer": f"/values/{input_id.replace('~', '~0').replace('/', '~1')}" if present else None,
            "value_type": _value_type_for_mapping(values[input_id], declaration["value_type"]) if present else (
                declaration["value_type"] if isinstance(declaration["value_type"], str) else (
                    declaration["value_type"][0] if declaration["value_type"] else "unsupported"
                )
            ),
            "unit": declaration.get("unit"),
        }
        entries.append(entry)
    mapping = {
        "mapping_version": MAPPING_VERSION,
        "case_id": source_case["case_id"],
        "source_case_id": source_case["source_case_id"],
        "policy_id": policy["policy_id"],
        "bindings": entries,
    }
    if mutation:
        kind = mutation["kind"]
        if kind == "append_unknown":
            entries.append({"input_id": "SYN_UNKNOWN", "present": False, "source_pointer": None, "value_type": "string", "unit": None})
        elif kind == "duplicate_first":
            entries.append(dict(entries[0]))
        elif kind in ("wrong_type", "wrong_unit", "bad_pointer"):
            target = next(item for item in entries if item["input_id"] == mutation["input_id"])
            if kind == "wrong_type":
                target["value_type"] = mutation["value_type"]
            elif kind == "wrong_unit":
                target["unit"] = mutation["unit"]
            else:
                target["source_pointer"] = "/values/SYN_NOT_PRESENT"
        elif kind == "omit_last":
            entries.pop()
        else:
            raise RouteInterfaceError("FIXTURE_SCHEMA_FAILURE", "unknown mapping mutation")
    return mapping


def _mutate_trace(trace: dict[str, Any], mutation: str | None) -> dict[str, Any]:
    candidate = json.loads(json.dumps(trace))
    if mutation == "baseline":
        candidate["preserved_baseline_action_ids"] = ["SYN_WRONG_BASELINE"]
    elif mutation == "add_missing_to_evaluated":
        candidate["evaluated_input_ids"] = sorted(set(candidate["evaluated_input_ids"]) | set(candidate["missing_input_ids"]))
    elif mutation == "duplicate_missing":
        if not candidate["missing_input_ids"]:
            raise RouteInterfaceError("FIXTURE_SCHEMA_FAILURE", "duplicate-missing mutation requires a missing ID")
        candidate["missing_input_ids"].append(candidate["missing_input_ids"][0])
    elif mutation is not None:
        raise RouteInterfaceError("FIXTURE_SCHEMA_FAILURE", "unknown trace mutation")
    return candidate


def run_corpus(corpus: Any, corpus_bytes: bytes) -> dict[str, Any]:
    if not isinstance(corpus, dict) or corpus.get("corpus_version") != "task229-synthetic-route-conformance-r1":
        raise RouteInterfaceError("FIXTURE_SCHEMA_FAILURE", "synthetic fixture corpus version is unsupported")
    if corpus.get("source_class") != "synthetic_only":
        raise RouteInterfaceError("FIXTURE_SOURCE_FAILURE", "fixture corpus is not declared synthetic-only")
    lowered = corpus_bytes.lower()
    if any(term in lowered for term in (b"target", b"evaluator", b"score", b"sealed")):
        raise RouteInterfaceError("FIXTURE_SOURCE_FAILURE", "synthetic fixture corpus contains forbidden result material")
    policies = corpus.get("policies")
    fixtures = corpus.get("fixtures")
    if not isinstance(policies, dict) or not isinstance(fixtures, list) or len(fixtures) < 16:
        raise RouteInterfaceError("FIXTURE_SCHEMA_FAILURE", "fixture corpus is incomplete")
    fixture_ids = [item.get("fixture_id") for item in fixtures if isinstance(item, dict)]
    if len(fixture_ids) != len(fixtures) or len(set(fixture_ids)) != len(fixture_ids):
        raise RouteInterfaceError("FIXTURE_SCHEMA_FAILURE", "fixture IDs are missing or duplicated")
    if not REQUIRED_FIXTURES.issubset(set(fixture_ids)):
        raise RouteInterfaceError("FIXTURE_COVERAGE_FAILURE", "one or more required fixture cases are absent")

    results: list[dict[str, Any]] = []
    positive_count = 0
    negative_count = 0
    for fixture in fixtures:
        fixture_id = fixture["fixture_id"]
        fixture_class = fixture.get("class")
        if fixture_class not in ("positive", "negative"):
            raise RouteInterfaceError("FIXTURE_SCHEMA_FAILURE", "fixture class must be positive or negative")
        if fixture_class == "positive":
            positive_count += 1
        else:
            negative_count += 1
        policy = policies.get(fixture.get("policy_ref"))
        source_case = fixture.get("source_case")
        expected = fixture.get("expected")
        if not isinstance(policy, dict) or not isinstance(source_case, dict) or not isinstance(expected, dict):
            raise RouteInterfaceError("FIXTURE_SCHEMA_FAILURE", "fixture references missing policy/source/expectation data")
        policy_bytes = canonical_json_bytes(policy)
        source_case_bytes = canonical_json_bytes(source_case)
        mapping = _mapping_for(policy, source_case, fixture.get("mapping_mutation"))
        mapping_bytes = canonical_json_bytes(mapping)
        actual: dict[str, Any] = {"build_code": None, "execution_code": None, "validator_code": None}
        try:
            binding = build_binding(policy, policy_bytes, source_case, source_case_bytes, mapping)
        except RouteInterfaceError as exc:
            actual["build_code"] = exc.code
            if expected.get("build_error") != exc.code:
                raise AssertionError(f"{fixture_id}: expected build {expected.get('build_error')}, got {exc.code}") from exc
            results.append({"fixture_id": fixture_id, "class": fixture_class, "status": "PASS", "actual": actual})
            continue
        if expected.get("build_error"):
            raise AssertionError(f"{fixture_id}: expected build failure {expected['build_error']} but binding was built")
        binding_again = build_binding(policy, policy_bytes, source_case, source_case_bytes, mapping)
        if canonical_json_bytes(binding) != canonical_json_bytes(binding_again):
            raise AssertionError(f"{fixture_id}: binding rebuild was not deterministic")
        actual["binding_rebuild_sha256"] = hashlib.sha256(canonical_json_bytes(binding)).hexdigest()
        if fixture.get("runtime_marker"):
            if not isinstance(fixture.get("synthetic_prose"), str):
                raise AssertionError(f"{fixture_id}: prose conflict fixture lacks synthetic prose")
            conflict_input = fixture.get("conflict_input", {})
            input_id = conflict_input.get("input_id")
            if input_id not in binding["bindings"] or binding["bindings"][input_id]["value"] != conflict_input.get("value"):
                raise AssertionError(f"{fixture_id}: conflict marker changed the authoritative bound value")
            binding["interface_conflict_marker"] = fixture["runtime_marker"]

        first = interpret(policy, binding, policy_bytes)
        second = interpret(policy, binding, policy_bytes)
        if canonical_json_bytes(first) != canonical_json_bytes(second):
            raise AssertionError(f"{fixture_id}: interpreter rebuild was not deterministic")
        actual["execution_status"] = first["execution_status"]
        if first["execution_status"] == "FAIL_CLOSED":
            actual["execution_code"] = first["error"]["code"]
            if expected.get("execution_error") != actual["execution_code"]:
                raise AssertionError(f"{fixture_id}: expected execution failure {expected.get('execution_error')}, got {actual['execution_code']}")
            if actual["execution_code"] == "ROUTE_AMBIGUOUS" and first.get("missing_input_report") is None:
                raise AssertionError(f"{fixture_id}: ambiguity omitted its condition/missingness report")
            results.append({"fixture_id": fixture_id, "class": fixture_class, "status": "PASS", "actual": actual})
            continue
        if expected.get("execution_error"):
            raise AssertionError(f"{fixture_id}: expected execution failure {expected['execution_error']} but a route was emitted")

        trace = first["route_trace"]
        for field in ("route_type", "evaluated_input_ids", "missing_input_ids"):
            if trace[field] != expected.get(field):
                raise AssertionError(f"{fixture_id}: {field} differs from fixture expectation")
        set_expectations = fixture.get("expected_condition_set", {})
        observed_sets = {item["route_id"]: item["result"] for item in first["condition_set_evaluations"]}
        for route_id, result in set_expectations.items():
            if observed_sets.get(route_id) != result:
                raise AssertionError(f"{fixture_id}: condition-set result differs for {route_id}")

        candidate_trace = _mutate_trace(trace, fixture.get("trace_mutation"))
        validation = validate_trace(policy, binding, candidate_trace, policy_bytes)
        actual["route_type"] = trace["route_type"]
        actual["evaluated_input_ids"] = trace["evaluated_input_ids"]
        actual["missing_input_ids"] = trace["missing_input_ids"]
        actual["validator_code"] = None if validation["status"] == "PASS" else validation["code"]
        if expected.get("validator_error"):
            if validation["status"] != "FAIL" or validation["code"] != expected["validator_error"]:
                raise AssertionError(f"{fixture_id}: expected validator failure {expected['validator_error']}, got {validation}")
        elif validation["status"] != "PASS":
            raise AssertionError(f"{fixture_id}: reference route trace did not validate")
        results.append({"fixture_id": fixture_id, "class": fixture_class, "status": "PASS", "actual": actual})

    return {
        "report_version": "task229-synthetic-route-conformance-report-r1",
        "fixture_corpus_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
        "fixture_count": len(fixtures),
        "positive_fixture_count": positive_count,
        "negative_fixture_count": negative_count,
        "all_fixtures_passed_expected_outcome": all(item["status"] == "PASS" for item in results),
        "all_route_rebuilds_byte_deterministic": True,
        "target_or_evaluator_material_in_fixture_corpus": False,
        "successor_sessions_run": 0,
        "evaluators_run": 0,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", default=str(FIXTURE_PATH), help="synthetic fixture corpus JSON")
    parser.add_argument("--output", help="write deterministic conformance report JSON")
    args = parser.parse_args()
    try:
        corpus, corpus_bytes = load_json_file(args.fixtures)
        report = run_corpus(corpus, corpus_bytes)
    except (RouteInterfaceError, AssertionError) as exc:
        code = exc.code if isinstance(exc, RouteInterfaceError) else "CONFORMANCE_ASSERTION_FAILED"
        print(json.dumps({"status": "FAIL", "code": code, "message": str(exc)}, sort_keys=True))
        return 1
    output = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    print(json.dumps({
        "status": "PASS" if report["all_fixtures_passed_expected_outcome"] else "FAIL",
        "fixtures": report["fixture_count"],
        "positive": report["positive_fixture_count"],
        "negative": report["negative_fixture_count"],
        "deterministic": report["all_route_rebuilds_byte_deterministic"],
    }, sort_keys=True))
    return 0 if report["all_fixtures_passed_expected_outcome"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
