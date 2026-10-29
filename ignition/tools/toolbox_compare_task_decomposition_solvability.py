#!/usr/bin/env python3
"""Compare caller-declared task decomposition alternatives without executing them."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import deque
from typing import Any, Mapping


SCHEMA_VERSION = "task-decomposition-solvability-input-r0"
OUTPUT_SCHEMA_VERSION = "task-decomposition-solvability-output-r0"
MAX_INPUT_BYTES = 262_144
MAX_ALTERNATIVES = 16
MAX_WORK_UNITS_PER_ALTERNATIVE = 64
MAX_CATALOG_ENTRIES = 128
MAX_INTEGER_DIGITS = 32
IDENTIFIER_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]{0,95}\Z")
AVAILABILITY = {"AVAILABLE", "UNAVAILABLE", "UNKNOWN"}
COST_KEYS = ("action_count", "wall_clock_seconds", "output_bytes")


class DecompositionError(ValueError):
    """Malformed request or unsupported bounded input."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DecompositionError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _bounded_int(token: str) -> int:
    digits = token.lstrip("-")
    if len(digits) > MAX_INTEGER_DIGITS:
        raise DecompositionError(f"integer value exceeds {MAX_INTEGER_DIGITS} digits")
    return int(token)


def _reject_constant(token: str) -> Any:
    raise DecompositionError(f"non-standard JSON number is not allowed: {token}")


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER_RE.fullmatch(value):
        raise DecompositionError(f"{field} must be a bounded stable identifier")
    return value


def _string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        qualifier = "array" if allow_empty else "non-empty array"
        raise DecompositionError(f"{field} must be a {qualifier}")
    items = [_identifier(item, f"{field} item") for item in value]
    if len(items) != len(set(items)):
        raise DecompositionError(f"{field} must not contain duplicates")
    return items


def _number(value: Any, field: str, *, integer: bool = False) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DecompositionError(f"{field} must be a finite non-negative number")
    if (isinstance(value, float) and (not math.isfinite(value) or value >= 1e32)) or value < 0:
        raise DecompositionError(f"{field} must be a finite non-negative number")
    if isinstance(value, int) and len(str(value)) > MAX_INTEGER_DIGITS:
        raise DecompositionError(f"{field} exceeds the {MAX_INTEGER_DIGITS}-digit integer limit")
    if integer and not isinstance(value, int):
        raise DecompositionError(f"{field} must be a non-negative integer")
    return value


def _exact_keys(value: Any, keys: set[str], field: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise DecompositionError(f"{field} keys must be exactly {sorted(keys)}")
    return value


def _catalog(
    value: Any,
    field: str,
    *,
    validator: bool,
) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list) or not value or len(value) > MAX_CATALOG_ENTRIES:
        raise DecompositionError(f"{field} must contain 1..{MAX_CATALOG_ENTRIES} entries")
    result: dict[str, dict[str, Any]] = {}
    if validator:
        expected = {"validator_id", "availability", "accepted_input_types", "validated_output_types"}
        id_field = "validator_id"
        output_field = "validated_output_types"
    else:
        expected = {"capability_id", "availability", "accepted_input_types", "produced_output_types"}
        id_field = "capability_id"
        output_field = "produced_output_types"
    for index, raw in enumerate(value):
        item = _exact_keys(raw, expected, f"{field}[{index}]")
        identifier = _identifier(item[id_field], f"{field}[{index}].{id_field}")
        if identifier in result:
            raise DecompositionError(f"{field} identifiers must be unique")
        if not isinstance(item["availability"], str) or item["availability"] not in AVAILABILITY:
            raise DecompositionError(f"{field}[{index}].availability is invalid")
        accepted = _string_list(item["accepted_input_types"], f"{field}[{index}].accepted_input_types", allow_empty=True)
        produced = _string_list(item[output_field], f"{field}[{index}].{output_field}")
        result[identifier] = {
            "availability": item["availability"],
            "accepted_input_types": set(accepted),
            output_field: set(produced),
        }
    return result


def _parse_cost(value: Any, field: str) -> dict[str, int | float | None]:
    item = _exact_keys(value, set(COST_KEYS), field)
    parsed: dict[str, int | float | None] = {}
    for key in COST_KEYS:
        if item[key] is None:
            parsed[key] = None
        else:
            parsed[key] = _number(item[key], f"{field}.{key}", integer=key != "wall_clock_seconds")
    return parsed


def parse_request(raw: bytes) -> tuple[dict[str, Any], str]:
    if len(raw) > MAX_INPUT_BYTES:
        raise DecompositionError(f"input exceeds {MAX_INPUT_BYTES} bytes")
    try:
        payload = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_int=_bounded_int,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise DecompositionError(f"input must be valid UTF-8 JSON: {exc}") from exc
    expected = {
        "schema_version",
        "task_id",
        "task_revision",
        "task_input_types",
        "required_output_types",
        "resource_budget",
        "capability_contracts",
        "validator_contracts",
        "alternatives",
    }
    request = _exact_keys(payload, expected, "request")
    if request["schema_version"] != SCHEMA_VERSION:
        raise DecompositionError(f"schema_version must equal {SCHEMA_VERSION}")
    task_id = _identifier(request["task_id"], "task_id")
    if not isinstance(request["task_revision"], str) or not request["task_revision"].strip() or len(request["task_revision"]) > 128:
        raise DecompositionError("task_revision must be a nonblank string of at most 128 characters")
    task_inputs = set(_string_list(request["task_input_types"], "task_input_types", allow_empty=True))
    required_outputs = _string_list(request["required_output_types"], "required_output_types")
    budget_raw = _exact_keys(
        request["resource_budget"],
        {"max_action_count", "max_wall_clock_seconds", "max_output_bytes"},
        "resource_budget",
    )
    budget = {
        "max_action_count": _number(budget_raw["max_action_count"], "resource_budget.max_action_count", integer=True),
        "max_wall_clock_seconds": _number(budget_raw["max_wall_clock_seconds"], "resource_budget.max_wall_clock_seconds"),
        "max_output_bytes": _number(budget_raw["max_output_bytes"], "resource_budget.max_output_bytes", integer=True),
    }
    capabilities = _catalog(request["capability_contracts"], "capability_contracts", validator=False)
    validators = _catalog(request["validator_contracts"], "validator_contracts", validator=True)
    alternatives_raw = request["alternatives"]
    if not isinstance(alternatives_raw, list) or not 2 <= len(alternatives_raw) <= MAX_ALTERNATIVES:
        raise DecompositionError(f"alternatives must contain 2..{MAX_ALTERNATIVES} entries")
    alternatives: list[dict[str, Any]] = []
    alternative_ids: set[str] = set()
    for alt_index, alt_raw in enumerate(alternatives_raw):
        alt = _exact_keys(alt_raw, {"alternative_id", "work_units"}, f"alternatives[{alt_index}]")
        alt_id = _identifier(alt["alternative_id"], f"alternatives[{alt_index}].alternative_id")
        if alt_id in alternative_ids:
            raise DecompositionError("alternative_id values must be unique")
        alternative_ids.add(alt_id)
        units_raw = alt["work_units"]
        if not isinstance(units_raw, list) or not units_raw or len(units_raw) > MAX_WORK_UNITS_PER_ALTERNATIVE:
            raise DecompositionError(
                f"alternatives[{alt_index}].work_units must contain 1..{MAX_WORK_UNITS_PER_ALTERNATIVE} entries"
            )
        units: list[dict[str, Any]] = []
        unit_ids: set[str] = set()
        for unit_index, unit_raw in enumerate(units_raw):
            field = f"alternatives[{alt_index}].work_units[{unit_index}]"
            unit = _exact_keys(
                unit_raw,
                {
                    "unit_id",
                    "depends_on",
                    "required_input_types",
                    "produced_output_types",
                    "capability_id",
                    "validator_ids",
                    "estimated_cost",
                },
                field,
            )
            unit_id = _identifier(unit["unit_id"], f"{field}.unit_id")
            if unit_id in unit_ids:
                raise DecompositionError(f"{field}.unit_id values must be unique within an alternative")
            unit_ids.add(unit_id)
            depends_on = _string_list(unit["depends_on"], f"{field}.depends_on", allow_empty=True)
            if unit_id in depends_on:
                raise DecompositionError(f"{field}.depends_on cannot contain its own unit_id")
            units.append(
                {
                    "unit_id": unit_id,
                    "depends_on": depends_on,
                    "required_input_types": set(
                        _string_list(unit["required_input_types"], f"{field}.required_input_types", allow_empty=True)
                    ),
                    "produced_output_types": set(
                        _string_list(unit["produced_output_types"], f"{field}.produced_output_types")
                    ),
                    "capability_id": _identifier(unit["capability_id"], f"{field}.capability_id"),
                    "validator_ids": _string_list(unit["validator_ids"], f"{field}.validator_ids", allow_empty=True),
                    "estimated_cost": _parse_cost(unit["estimated_cost"], f"{field}.estimated_cost"),
                }
            )
        alternatives.append({"alternative_id": alt_id, "work_units": units})
    return {
        "task_id": task_id,
        "task_revision": request["task_revision"],
        "task_input_types": task_inputs,
        "required_output_types": set(required_outputs),
        "resource_budget": budget,
        "capability_contracts": capabilities,
        "validator_contracts": validators,
        "alternatives": alternatives,
    }, hashlib.sha256(raw).hexdigest()


def _graph(units: list[dict[str, Any]]) -> tuple[list[str], list[str], dict[str, set[str]]]:
    by_id = {unit["unit_id"]: unit for unit in units}
    errors: list[str] = []
    children: dict[str, list[str]] = {unit_id: [] for unit_id in by_id}
    indegree = {unit_id: 0 for unit_id in by_id}
    for unit in units:
        for dependency in unit["depends_on"]:
            if dependency not in by_id:
                errors.append(f"DEPENDENCY_NOT_FOUND:{unit['unit_id']}:{dependency}")
                continue
            children[dependency].append(unit["unit_id"])
            indegree[unit["unit_id"]] += 1
    ready = deque(unit["unit_id"] for unit in units if indegree[unit["unit_id"]] == 0)
    order: list[str] = []
    while ready:
        unit_id = ready.popleft()
        order.append(unit_id)
        for child in children[unit_id]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if len(order) != len(units):
        errors.append("DEPENDENCY_CYCLE")
    ancestors: dict[str, set[str]] = {}
    if not errors:
        for unit_id in order:
            unit = by_id[unit_id]
            ancestor_ids: set[str] = set()
            for dependency in unit["depends_on"]:
                ancestor_ids.add(dependency)
                ancestor_ids.update(ancestors[dependency])
            ancestors[unit_id] = ancestor_ids
    return order, errors, ancestors


def _analyze_alternative(request: dict[str, Any], alternative: dict[str, Any]) -> dict[str, Any]:
    units = alternative["work_units"]
    by_id = {unit["unit_id"]: unit for unit in units}
    order, graph_errors, ancestors = _graph(units)
    blockers = list(graph_errors)
    unknowns: list[str] = []
    provided_outputs: set[str] = set()
    unit_results: list[dict[str, Any]] = []
    for unit_id in order or [unit["unit_id"] for unit in units]:
        unit = by_id[unit_id]
        unit_blockers: list[str] = []
        unit_unknowns: list[str] = []
        capability = request["capability_contracts"].get(unit["capability_id"])
        if capability is None:
            unit_blockers.append("CAPABILITY_NOT_DECLARED")
        else:
            if capability["availability"] == "UNAVAILABLE":
                unit_blockers.append("CAPABILITY_DECLARED_UNAVAILABLE")
            elif capability["availability"] == "UNKNOWN":
                unit_unknowns.append("CAPABILITY_AVAILABILITY_UNKNOWN")
            available_inputs = set(request["task_input_types"])
            if not graph_errors:
                for ancestor_id in ancestors[unit_id]:
                    available_inputs.update(by_id[ancestor_id]["produced_output_types"])
            missing = sorted(unit["required_input_types"] - available_inputs)
            if missing:
                unit_blockers.append("REQUIRED_INPUT_TYPES_NOT_REACHABLE:" + ",".join(missing))
            unsupported = sorted(unit["required_input_types"] - capability["accepted_input_types"])
            if unsupported:
                unit_blockers.append("CAPABILITY_REJECTS_INPUT_TYPES:" + ",".join(unsupported))
            unsupported_outputs = sorted(unit["produced_output_types"] - capability["produced_output_types"])
            if unsupported_outputs:
                unit_blockers.append("CAPABILITY_CANNOT_PRODUCE_OUTPUT_TYPES:" + ",".join(unsupported_outputs))
        covered_outputs: set[str] = set()
        uncertain_validation_outputs: set[str] = set()
        if not unit["validator_ids"]:
            unit_blockers.append("NO_OUTPUT_VALIDATOR_DECLARED")
        for validator_id in unit["validator_ids"]:
            validator = request["validator_contracts"].get(validator_id)
            if validator is None:
                unit_blockers.append(f"VALIDATOR_NOT_DECLARED:{validator_id}")
            else:
                unsupported_inputs = sorted(unit["produced_output_types"] - validator["accepted_input_types"])
                unsupported_outputs = sorted(unit["produced_output_types"] - validator["validated_output_types"])
                if unsupported_inputs or unsupported_outputs:
                    unit_blockers.append(
                        f"VALIDATOR_CONTRACT_MISMATCH:{validator_id}:"
                        + ",".join(sorted(set(unsupported_inputs + unsupported_outputs)))
                    )
                elif validator["availability"] == "UNAVAILABLE":
                    unit_blockers.append(f"VALIDATOR_DECLARED_UNAVAILABLE:{validator_id}")
                elif validator["availability"] == "UNKNOWN":
                    unit_unknowns.append(f"VALIDATOR_AVAILABILITY_UNKNOWN:{validator_id}")
                    uncertain_validation_outputs.update(unit["produced_output_types"])
                else:
                    covered_outputs.update(unit["produced_output_types"])
        missing_validation = sorted(unit["produced_output_types"] - covered_outputs - uncertain_validation_outputs)
        if missing_validation:
            unit_blockers.append("OUTPUT_TYPES_NOT_VALIDATED:" + ",".join(missing_validation))
        provided_outputs.update(unit["produced_output_types"])
        blockers.extend(f"{unit_id}:{reason}" for reason in unit_blockers)
        unknowns.extend(f"{unit_id}:{reason}" for reason in unit_unknowns)
        unit_results.append(
            {
                "unit_id": unit_id,
                "capability_id": unit["capability_id"],
                "validator_ids": unit["validator_ids"],
                "status": "BLOCKED_AS_DECLARED" if unit_blockers else "SOLVABILITY_UNKNOWN" if unit_unknowns else "SOLVABLE_AS_DECLARED",
                "blockers": unit_blockers,
                "unknowns": unit_unknowns,
                "required_input_types": sorted(unit["required_input_types"]),
                "produced_output_types": sorted(unit["produced_output_types"]),
            }
        )
    missing_required_outputs = sorted(request["required_output_types"] - provided_outputs)
    if missing_required_outputs:
        blockers.append("REQUIRED_TASK_OUTPUTS_NOT_PRODUCED:" + ",".join(missing_required_outputs))
    total_cost = {key: 0 for key in COST_KEYS}
    cost_complete = True
    for unit in units:
        for key in COST_KEYS:
            value = unit["estimated_cost"][key]
            if value is None:
                cost_complete = False
            else:
                total_cost[key] += value
    resource_status = "UNKNOWN"
    if cost_complete:
        over = []
        if total_cost["action_count"] > request["resource_budget"]["max_action_count"]:
            over.append("ACTION_COUNT")
        if total_cost["wall_clock_seconds"] > request["resource_budget"]["max_wall_clock_seconds"]:
            over.append("WALL_CLOCK_SECONDS")
        if total_cost["output_bytes"] > request["resource_budget"]["max_output_bytes"]:
            over.append("OUTPUT_BYTES")
        if over:
            resource_status = "EXCEEDS_DECLARED_BUDGET"
            blockers.append("RESOURCE_BUDGET_EXCEEDED:" + ",".join(over))
        else:
            resource_status = "WITHIN_DECLARED_BUDGET"
    if blockers:
        status = "UNSOLVABLE_AS_DECLARED"
    elif unknowns or resource_status == "UNKNOWN":
        status = "SOLVABILITY_UNKNOWN"
    else:
        status = "SOLVABLE_AS_DECLARED"
    return {
        "alternative_id": alternative["alternative_id"],
        "status": status,
        "dependency_order": order,
        "unit_results": unit_results,
        "blockers": blockers,
        "unknowns": unknowns,
        "required_output_types": sorted(request["required_output_types"]),
        "resource_estimate": {
            "status": resource_status,
            "basis": "Caller-declared per-unit estimates summed serially; no execution or calibration was performed.",
            "total": total_cost if cost_complete else None,
            "budget": request["resource_budget"],
        },
    }


def _dominates(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    metrics = ("action_count", "wall_clock_seconds", "output_bytes")
    left_values = left["resource_estimate"]["total"]
    right_values = right["resource_estimate"]["total"]
    no_worse = all(left_values[key] <= right_values[key] for key in metrics)
    strictly_better = any(left_values[key] < right_values[key] for key in metrics)
    return no_worse and strictly_better


def compare(request: dict[str, Any], input_sha256: str) -> dict[str, Any]:
    alternatives = [_analyze_alternative(request, item) for item in request["alternatives"]]
    feasible = [item for item in alternatives if item["status"] == "SOLVABLE_AS_DECLARED"]
    frontier_ids: list[str] = []
    frontier_status = "NOT_EVALUATED_NO_FEASIBLE_ALTERNATIVE"
    if feasible and all(item["resource_estimate"]["status"] == "WITHIN_DECLARED_BUDGET" for item in feasible):
        frontier_status = "CALLER_ESTIMATE_PARETO_FRONTIER"
        frontier_ids = [
            item["alternative_id"]
            for item in feasible
            if not any(other is not item and _dominates(other, item) for other in feasible)
        ]
    unique_structural_leader = None
    if len(feasible) == 1 and all(
        item["status"] == "UNSOLVABLE_AS_DECLARED"
        for item in alternatives
        if item["alternative_id"] != feasible[0]["alternative_id"]
    ):
        unique_structural_leader = feasible[0]["alternative_id"]
    if unique_structural_leader:
        disposition = "ONE_ALTERNATIVE_SOLVABLE_AS_DECLARED"
    elif feasible:
        disposition = "MULTIPLE_SOLVABLE_ALTERNATIVES_RETAINED"
    elif any(item["status"] == "SOLVABILITY_UNKNOWN" for item in alternatives):
        disposition = "NO_CONFIRMED_SOLVABLE_ALTERNATIVE"
    else:
        disposition = "NO_ALTERNATIVE_SOLVABLE_AS_DECLARED"
    return {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "comparison_status": "CALLER_DECLARED_ALTERNATIVES_COMPARED",
        "task_id": request["task_id"],
        "task_revision": request["task_revision"],
        "input_sha256": input_sha256,
        "alternative_count": len(alternatives),
        "alternatives": alternatives,
        "structural_leader_id": unique_structural_leader,
        "disposition": disposition,
        "resource_frontier": {
            "status": frontier_status,
            "alternative_ids": frontier_ids,
            "basis": "Caller-declared serial estimates only; no empirical success or calibrated cost ranking.",
        },
        "declaration_limits": [
            "Capability and validator availability are caller declarations, not live observations.",
            "Validator contracts were checked structurally; validators were not executed.",
            "Executors were not invoked and no task output was produced.",
        ],
        "validators_executed": False,
        "executors_invoked": False,
        "execution_authorized": False,
        "claim_ceiling": "Deterministic consistency of caller-declared task graphs, capability/validator contracts, and bounded cost estimates only; no actual solvability, success probability, task correctness, executor availability, validator execution, authority, or scientific validity is established.",
    }


def analyze_bytes(raw: bytes) -> dict[str, Any]:
    request, digest = parse_request(raw)
    return compare(request, digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True)
    parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        result = analyze_bytes(raw)
    except DecompositionError as exc:
        result = {
            "schema_version": OUTPUT_SCHEMA_VERSION,
            "status": "INVALID_INPUT",
            "error": str(exc),
            "executors_invoked": False,
            "validators_executed": False,
            "execution_authorized": False,
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
