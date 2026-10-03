#!/usr/bin/env python3
"""Deterministic, target-blind reference interpreter for Task229 route R1."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "task229-route-interface-contract-r1"
BINDING_VERSION = "task229-route-input-binding-r1"
BUILDER_VERSION = "task229-typed-binding-builder-r1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
JSON_TYPES = {"boolean", "string", "integer", "number", "null"}


class RouteInterfaceError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RouteInterfaceError("INVALID_JSON_VALUE", "value is not canonical JSON") from exc


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RouteInterfaceError("DUPLICATE_JSON_KEY", "JSON object contains a duplicate key")
        result[key] = value
    return result


def _reject_non_json_constant(value: str) -> None:
    raise RouteInterfaceError("INVALID_JSON_VALUE", "non-finite JSON number is forbidden")


def load_json_file(path: str | Path) -> tuple[Any, bytes]:
    raw = Path(path).read_bytes()
    try:
        parsed = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_json_constant,
        )
    except RouteInterfaceError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RouteInterfaceError("INVALID_JSON", "input is not valid UTF-8 JSON") from exc
    return parsed, raw


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def _value_type(value: Any) -> str:
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


def _declared_types(value_type: Any) -> tuple[str, ...]:
    if isinstance(value_type, str):
        declared = [value_type]
    elif isinstance(value_type, list) and value_type and all(isinstance(item, str) for item in value_type):
        declared = value_type
    else:
        raise RouteInterfaceError("UNKNOWN_TYPE", "policy value_type is missing or ambiguous")
    if len(set(declared)) != len(declared) or any(item not in JSON_TYPES for item in declared):
        raise RouteInterfaceError("UNKNOWN_TYPE", "policy declares a duplicate or unsupported value type")
    return tuple(declared)


def _strict_value_matches(value: Any, value_type: Any) -> bool:
    allowed = _declared_types(value_type)
    actual = _value_type(value)
    if "number" in allowed and isinstance(value, (int, float)) and not isinstance(value, bool):
        return isinstance(value, int) or math.isfinite(value)
    if actual not in allowed:
        return False
    if actual == "number" and not math.isfinite(value):
        return False
    return True


def _require_nonempty_string(value: Any, code: str, message: str) -> str:
    if not isinstance(value, str) or not value:
        raise RouteInterfaceError(code, message)
    return value


def policy_required_inputs(policy: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(policy, dict):
        raise RouteInterfaceError("POLICY_SCHEMA_FAILURE", "policy must be an object")
    raw = policy.get("selector", {}).get("required_inputs") if isinstance(policy.get("selector"), dict) else None
    if not isinstance(raw, list):
        raise RouteInterfaceError("POLICY_SCHEMA_FAILURE", "policy selector.required_inputs must be an array")
    declarations: dict[str, dict[str, Any]] = {}
    for entry in raw:
        if not isinstance(entry, dict):
            raise RouteInterfaceError("POLICY_SCHEMA_FAILURE", "required input declaration must be an object")
        input_id = _require_nonempty_string(entry.get("input_id"), "POLICY_SCHEMA_FAILURE", "required input ID is missing")
        if input_id in declarations:
            raise RouteInterfaceError("POLICY_TYPE_AMBIGUITY", "policy repeats a required input ID")
        if "unit" not in entry:
            raise RouteInterfaceError("POLICY_SCHEMA_FAILURE", "required input declaration lacks unit")
        if entry["unit"] is not None and not isinstance(entry["unit"], str):
            raise RouteInterfaceError("POLICY_SCHEMA_FAILURE", "required input unit must be a string or null")
        value_types = _declared_types(entry.get("value_type"))
        declarations[input_id] = {
            "value_type": value_types[0] if len(value_types) == 1 else list(value_types),
            "unit": entry["unit"],
        }
    return declarations


def _route_specs(policy: dict[str, Any], declarations: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selector = policy.get("selector")
    if not isinstance(selector, dict):
        raise RouteInterfaceError("POLICY_SCHEMA_FAILURE", "policy selector must be an object")
    rules = selector.get("rule", [])
    stops = policy.get("stop_conditions", [])
    if not isinstance(rules, list) or not isinstance(stops, list):
        raise RouteInterfaceError("POLICY_SCHEMA_FAILURE", "selector rules and stop conditions must be arrays")

    def validate_specs(items: list[Any], id_key: str, route_kind: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for item in items:
            if not isinstance(item, dict):
                raise RouteInterfaceError("POLICY_SCHEMA_FAILURE", f"{route_kind} entry must be an object")
            route_id = _require_nonempty_string(item.get(id_key), "POLICY_SCHEMA_FAILURE", f"{route_kind} ID is missing")
            if route_id in seen_ids:
                raise RouteInterfaceError("POLICY_SCHEMA_FAILURE", f"{route_kind} IDs are duplicated")
            seen_ids.add(route_id)
            if route_kind == "selector":
                _require_nonempty_string(item.get("action_ref"), "POLICY_SCHEMA_FAILURE", "selector action_ref is missing")
            conditions = item.get("when")
            if not isinstance(conditions, list) or not conditions:
                raise RouteInterfaceError("POLICY_SCHEMA_FAILURE", "route condition set must be a nonempty array")
            for condition in conditions:
                if not isinstance(condition, dict):
                    raise RouteInterfaceError("POLICY_SCHEMA_FAILURE", "route condition must be an object")
                input_id = _require_nonempty_string(condition.get("input_id"), "POLICY_SCHEMA_FAILURE", "condition input ID is missing")
                declaration = declarations.get(input_id)
                if declaration is None:
                    raise RouteInterfaceError("UNKNOWN_INPUT_ID", "condition references an undeclared policy input")
                if condition.get("operator") != "eq":
                    raise RouteInterfaceError("UNKNOWN_OPERATOR", "only the eq operator is supported")
                if "unit" not in condition or condition["unit"] != declaration["unit"]:
                    raise RouteInterfaceError("UNIT_MISMATCH", "condition unit differs from the policy input declaration")
                if "value" not in condition or not _strict_value_matches(condition["value"], declaration["value_type"]):
                    raise RouteInterfaceError("TYPE_MISMATCH", "condition literal conflicts with the policy input type")
            result.append(item)
        return result

    return validate_specs(stops, "stop_id", "stop"), validate_specs(rules, "rule_id", "selector")


def _baseline_action_ids(policy: dict[str, Any]) -> list[str]:
    preserved = policy.get("preserved_rules")
    if not isinstance(preserved, list):
        raise RouteInterfaceError("POLICY_SCHEMA_FAILURE", "policy preserved_rules must be an array")
    ids: set[str] = set()
    for entry in preserved:
        if not isinstance(entry, dict):
            raise RouteInterfaceError("POLICY_SCHEMA_FAILURE", "preserved rule must be an object")
        ids.add(_require_nonempty_string(entry.get("baseline_action"), "POLICY_SCHEMA_FAILURE", "baseline action ID is missing"))
    return sorted(ids)


def _validate_binding(
    policy: dict[str, Any],
    binding: Any,
    policy_sha256: str,
) -> tuple[
    dict[str, dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[str],
    list[str],
    list[str],
]:
    if not isinstance(binding, dict):
        raise RouteInterfaceError("BINDING_SCHEMA_FAILURE", "binding must be an object")
    allowed_keys = {
        "binding_version", "case_id", "source_case_id", "source_case_sha256", "policy_id",
        "policy_sha256", "binding_builder", "present_input_ids", "missing_input_ids", "bindings",
        "interface_conflict_marker",
    }
    if set(binding) - allowed_keys:
        raise RouteInterfaceError("BINDING_SCHEMA_FAILURE", "binding contains unknown fields")
    if binding.get("binding_version") != BINDING_VERSION:
        raise RouteInterfaceError("BINDING_VERSION_MISMATCH", "binding version is not R1")
    _require_nonempty_string(binding.get("case_id"), "BINDING_SCHEMA_FAILURE", "case_id is missing")
    _require_nonempty_string(binding.get("source_case_id"), "BINDING_SCHEMA_FAILURE", "source_case_id is missing")
    if not _is_sha256(binding.get("source_case_sha256")):
        raise RouteInterfaceError("BINDING_PROVENANCE_INVALID", "source case SHA-256 is missing or malformed")
    expected_policy_id = _require_nonempty_string(policy.get("policy_id"), "POLICY_SCHEMA_FAILURE", "policy ID is missing")
    if binding.get("policy_id") != expected_policy_id:
        raise RouteInterfaceError("POLICY_ID_MISMATCH", "binding policy ID differs from policy")
    if binding.get("policy_sha256") != policy_sha256 or not _is_sha256(binding.get("policy_sha256")):
        raise RouteInterfaceError("POLICY_HASH_MISMATCH", "binding policy hash differs from exact policy bytes")
    builder = binding.get("binding_builder")
    if not isinstance(builder, dict) or set(builder) != {"version", "sha256"}:
        raise RouteInterfaceError("BINDING_PROVENANCE_INVALID", "binding builder provenance is malformed")
    if builder.get("version") != BUILDER_VERSION or not _is_sha256(builder.get("sha256")):
        raise RouteInterfaceError("BINDING_PROVENANCE_INVALID", "binding builder version or hash is invalid")

    marker = binding.get("interface_conflict_marker")
    if marker not in (None, "PROSE_BINDING_CONFLICT"):
        raise RouteInterfaceError("BINDING_SCHEMA_FAILURE", "unsupported interface conflict marker")
    if marker == "PROSE_BINDING_CONFLICT":
        raise RouteInterfaceError("INTERFACE_CONFLICT", "case prose conflicts with the authoritative typed binding")

    declarations = policy_required_inputs(policy)
    stops, rules = _route_specs(policy, declarations)
    required = set(declarations)
    raw_bindings = binding.get("bindings")
    if not isinstance(raw_bindings, dict):
        raise RouteInterfaceError("BINDING_SCHEMA_FAILURE", "bindings must be an object keyed by input ID")
    present = set(raw_bindings)
    if present - required:
        raise RouteInterfaceError("UNKNOWN_INPUT_ID", "binding contains an input not required by policy")
    missing = required - present
    raw_missing = binding.get("missing_input_ids")
    raw_present = binding.get("present_input_ids")
    for name, value in (("present_input_ids", raw_present), ("missing_input_ids", raw_missing)):
        if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
            raise RouteInterfaceError("BINDING_SCHEMA_FAILURE", f"{name} must be an array of nonempty IDs")
        if len(value) != len(set(value)):
            raise RouteInterfaceError("DUPLICATE_INPUT_ID", f"{name} contains a duplicate ID")
        if value != sorted(value):
            raise RouteInterfaceError("BINDING_SCHEMA_FAILURE", f"{name} must be sorted")
    if raw_present != sorted(present) or raw_missing != sorted(missing):
        raise RouteInterfaceError("MISSINGNESS_MISMATCH", "present/missing ID lists do not exactly match bindings and policy")
    if present & missing:
        raise RouteInterfaceError("MISSINGNESS_MISMATCH", "an ID is both present and missing")

    for input_id, value_record in raw_bindings.items():
        declaration = declarations[input_id]
        if not isinstance(value_record, dict) or set(value_record) != {"present", "value", "value_type", "unit"}:
            raise RouteInterfaceError("BINDING_SCHEMA_FAILURE", "present binding record has incorrect fields")
        if value_record.get("present") is not True:
            raise RouteInterfaceError("MISSINGNESS_MISMATCH", "only present values may appear in bindings")
        if value_record.get("value_type") not in _declared_types(declaration["value_type"]):
            raise RouteInterfaceError("TYPE_MISMATCH", "binding value_type differs from policy declaration")
        if not _strict_value_matches(value_record.get("value"), declaration["value_type"]):
            raise RouteInterfaceError("TYPE_MISMATCH", "binding value requires coercion or conflicts with policy type")
        if value_record.get("unit") != declaration["unit"]:
            raise RouteInterfaceError("UNIT_MISMATCH", "binding unit differs from policy declaration")

    relevant: set[str] = set()
    for route in stops + rules:
        relevant.update(condition["input_id"] for condition in route["when"])
    evaluated = sorted(present & relevant)
    return declarations, stops, rules, evaluated, sorted(missing), _baseline_action_ids(policy)


def _evaluate_condition_set(
    conditions: list[dict[str, Any]],
    route_kind: str,
    route_id: str,
    bindings: dict[str, dict[str, Any]],
    missing: set[str],
    declaration_by_id: dict[str, dict[str, Any]],
) -> tuple[str, list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    missing_ids: set[str] = set()
    for index, condition in enumerate(conditions):
        input_id = condition["input_id"]
        if input_id in missing:
            result = "MISSING_INPUT"
            reason = "INPUT_ABSENT_FROM_TYPED_BINDING"
            missing_ids.add(input_id)
        else:
            actual = bindings[input_id]["value"]
            expected = condition["value"]
            allowed_types = _declared_types(declaration_by_id[input_id]["value_type"])
            both_numbers = (
                "number" in allowed_types
                and isinstance(actual, (int, float))
                and not isinstance(actual, bool)
                and isinstance(expected, (int, float))
                and not isinstance(expected, bool)
            )
            same_typed_value = (both_numbers or _value_type(actual) == _value_type(expected)) and actual == expected
            if same_typed_value:
                result, reason = "MATCH", "STRICT_TYPED_EQUALITY"
            else:
                result, reason = "NO_MATCH", "STRICT_TYPED_EQUALITY"
        results.append({
            "route_kind": route_kind,
            "route_id": route_id,
            "condition_index": index,
            "input_id": input_id,
            "result": result,
            "reason_code": reason,
        })
    statuses = {item["result"] for item in results}
    if "NO_MATCH" in statuses:
        aggregate = "NO_MATCH"
    elif "MISSING_INPUT" in statuses:
        aggregate = "MISSING_INPUT"
    else:
        aggregate = "MATCH"
    return aggregate, results, sorted(missing_ids)


def _interpret(policy: dict[str, Any], binding: dict[str, Any], policy_sha256: str) -> dict[str, Any]:
    declarations, stops, rules, evaluated_input_ids, missing_input_ids, baseline = _validate_binding(
        policy, binding, policy_sha256
    )
    present_bindings = binding["bindings"]
    missing_set = set(missing_input_ids)
    evaluations: list[dict[str, Any]] = []
    set_evaluations: list[dict[str, Any]] = []
    matched_stops: list[dict[str, Any]] = []
    matched_rules: list[dict[str, Any]] = []
    condition_missing: set[str] = set()

    for stop in stops:
        route_id = stop["stop_id"]
        result, detail, missing = _evaluate_condition_set(
            stop["when"], "stop", route_id, present_bindings, missing_set, declarations
        )
        evaluations.extend(detail)
        condition_missing.update(missing)
        set_evaluations.append({"route_kind": "stop", "route_id": route_id, "result": result, "missing_input_ids": missing})
        if result == "MATCH":
            matched_stops.append(stop)

    for rule in rules:
        route_id = rule["rule_id"]
        result, detail, missing = _evaluate_condition_set(
            rule["when"], "selector", route_id, present_bindings, missing_set, declarations
        )
        evaluations.extend(detail)
        condition_missing.update(missing)
        set_evaluations.append({"route_kind": "selector", "route_id": route_id, "result": result, "missing_input_ids": missing})
        if result == "MATCH":
            matched_rules.append(rule)

    missing_report = {
        "policy_required_missing_input_ids": missing_input_ids,
        "route_condition_missing_input_ids": sorted(condition_missing),
        "condition_sets": set_evaluations,
    }
    if len(matched_stops) > 1 or len(matched_rules) > 1 or (matched_stops and matched_rules):
        return {
            "execution_status": "FAIL_CLOSED",
            "route_trace": None,
            "condition_evaluations": evaluations,
            "condition_set_evaluations": set_evaluations,
            "missing_input_report": missing_report,
            "error": {
                "code": "ROUTE_AMBIGUOUS",
                "message": "multiple or conflicting route conditions fully match",
            },
        }

    if matched_stops:
        route_type = "stop"
        selected_rule_id = matched_stops[0]["stop_id"]
        selected_action_id = None
    elif matched_rules:
        route_type = "selector"
        selected_rule_id = matched_rules[0]["rule_id"]
        selected_action_id = matched_rules[0]["action_ref"]
    else:
        route_type = "fallback"
        selected_rule_id = None
        selected_action_id = None

    binding_sha256 = sha256_bytes(canonical_json_bytes(binding))
    trace = {
        "contract_version": CONTRACT_VERSION,
        "policy_id": policy["policy_id"],
        "policy_sha256": policy_sha256,
        "binding_sha256": binding_sha256,
        "route_type": route_type,
        "selected_rule_id": selected_rule_id,
        "selected_action_id": selected_action_id,
        "evaluated_input_ids": evaluated_input_ids,
        "missing_input_ids": missing_input_ids,
        "preserved_baseline_action_ids": baseline,
    }
    return {
        "execution_status": "ROUTE_TRACE_READY",
        "route_trace": trace,
        "condition_evaluations": evaluations,
        "condition_set_evaluations": set_evaluations,
        "missing_input_report": missing_report,
        "error": None,
    }


def interpret(policy: Any, binding: Any, policy_bytes: bytes | None = None) -> dict[str, Any]:
    try:
        if not isinstance(policy, dict):
            raise RouteInterfaceError("POLICY_SCHEMA_FAILURE", "policy must be an object")
        policy_raw = policy_bytes if policy_bytes is not None else canonical_json_bytes(policy)
        policy_sha256 = sha256_bytes(policy_raw)
        if not _is_sha256(policy_sha256):
            raise RouteInterfaceError("POLICY_HASH_MISMATCH", "policy hash could not be calculated")
        return _interpret(policy, binding, policy_sha256)
    except RouteInterfaceError as exc:
        return {
            "execution_status": "FAIL_CLOSED",
            "route_trace": None,
            "condition_evaluations": [],
            "condition_set_evaluations": [],
            "missing_input_report": None,
            "error": {"code": exc.code, "message": exc.message},
        }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", required=True, help="frozen policy JSON")
    parser.add_argument("--binding", required=True, help="typed binding JSON")
    parser.add_argument("--output", help="write deterministic result JSON to this path")
    args = parser.parse_args()
    try:
        policy, policy_raw = load_json_file(args.policy)
        binding, _ = load_json_file(args.binding)
        result = interpret(policy, binding, policy_raw)
    except RouteInterfaceError as exc:
        result = {
            "execution_status": "FAIL_CLOSED",
            "route_trace": None,
            "condition_evaluations": [],
            "condition_set_evaluations": [],
            "missing_input_report": None,
            "error": {"code": exc.code, "message": exc.message},
        }
    output = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0 if result["execution_status"] == "ROUTE_TRACE_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
