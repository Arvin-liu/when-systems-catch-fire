#!/usr/bin/env python3
"""Build a Task229 R1 binding from an explicit source record and mapping."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from route_reference_interpreter import (
    BUILDER_VERSION,
    BINDING_VERSION,
    RouteInterfaceError,
    _declared_types,
    _is_sha256,
    _route_specs,
    _strict_value_matches,
    canonical_json_bytes,
    load_json_file,
    policy_required_inputs,
    sha256_bytes,
)


MAPPING_VERSION = "task229-explicit-input-mapping-r1"


def _nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise RouteInterfaceError("MAPPING_SCHEMA_FAILURE", f"{field} must be a nonempty string")
    return value


def _json_pointer_get(document: Any, pointer: str) -> Any:
    if not isinstance(pointer, str):
        raise RouteInterfaceError("MAPPING_POINTER_INVALID", "source_pointer must be a JSON Pointer string")
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise RouteInterfaceError("MAPPING_POINTER_INVALID", "source_pointer must be an RFC 6901 JSON Pointer")
    current = document
    for encoded in pointer[1:].split("/"):
        if "~" in encoded:
            index = 0
            while index < len(encoded):
                if encoded[index] == "~":
                    if index + 1 >= len(encoded) or encoded[index + 1] not in "01":
                        raise RouteInterfaceError("MAPPING_POINTER_INVALID", "source_pointer contains an invalid escape")
                    index += 2
                else:
                    index += 1
        token = encoded.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise RouteInterfaceError("MAPPING_POINTER_UNRESOLVED", "source_pointer does not resolve")
            current = current[token]
        elif isinstance(current, list):
            if token == "-" or not token.isdigit() or (len(token) > 1 and token.startswith("0")):
                raise RouteInterfaceError("MAPPING_POINTER_UNRESOLVED", "source_pointer array index is invalid")
            position = int(token)
            if position >= len(current):
                raise RouteInterfaceError("MAPPING_POINTER_UNRESOLVED", "source_pointer array index is out of range")
            current = current[position]
        else:
            raise RouteInterfaceError("MAPPING_POINTER_UNRESOLVED", "source_pointer traverses a scalar")
    return current


def build_binding(
    policy: Any,
    policy_bytes: bytes,
    source_case: Any,
    source_case_bytes: bytes,
    mapping: Any,
) -> dict[str, Any]:
    if not isinstance(policy, dict):
        raise RouteInterfaceError("POLICY_SCHEMA_FAILURE", "policy must be an object")
    if not isinstance(source_case, dict):
        raise RouteInterfaceError("SOURCE_CASE_SCHEMA_FAILURE", "source case must be an object")
    if not isinstance(mapping, dict):
        raise RouteInterfaceError("MAPPING_SCHEMA_FAILURE", "mapping declaration must be an object")
    if set(mapping) != {"mapping_version", "case_id", "source_case_id", "policy_id", "bindings"}:
        raise RouteInterfaceError("MAPPING_SCHEMA_FAILURE", "mapping declaration has missing or unknown fields")
    if mapping.get("mapping_version") != MAPPING_VERSION:
        raise RouteInterfaceError("MAPPING_VERSION_MISMATCH", "mapping declaration version is not R1")

    policy_id = _nonempty_string(policy.get("policy_id"), "policy_id")
    case_id = _nonempty_string(source_case.get("case_id"), "source_case.case_id")
    source_case_id = _nonempty_string(source_case.get("source_case_id"), "source_case.source_case_id")
    if mapping.get("policy_id") != policy_id:
        raise RouteInterfaceError("POLICY_ID_MISMATCH", "mapping policy_id differs from policy")
    if mapping.get("case_id") != case_id or mapping.get("source_case_id") != source_case_id:
        raise RouteInterfaceError("SOURCE_CASE_ID_MISMATCH", "mapping case identity differs from source case")

    declarations = policy_required_inputs(policy)
    _route_specs(policy, declarations)
    raw_entries = mapping.get("bindings")
    if not isinstance(raw_entries, list):
        raise RouteInterfaceError("MAPPING_SCHEMA_FAILURE", "mapping bindings must be an array")
    entries: dict[str, dict[str, Any]] = {}
    for entry in raw_entries:
        if not isinstance(entry, dict) or set(entry) != {"input_id", "present", "source_pointer", "value_type", "unit"}:
            raise RouteInterfaceError("MAPPING_SCHEMA_FAILURE", "mapping entry has missing or unknown fields")
        input_id = _nonempty_string(entry.get("input_id"), "mapping input_id")
        if input_id in entries:
            raise RouteInterfaceError("DUPLICATE_INPUT_ID", "mapping declaration repeats an input ID")
        if input_id not in declarations:
            raise RouteInterfaceError("UNKNOWN_INPUT_ID", "mapping declaration contains an ID not required by policy")
        if not isinstance(entry.get("present"), bool):
            raise RouteInterfaceError("MAPPING_SCHEMA_FAILURE", "mapping present flag must be boolean")
        declaration = declarations[input_id]
        value_type = entry.get("value_type")
        if not isinstance(value_type, str) or value_type not in _declared_types(declaration["value_type"]):
            raise RouteInterfaceError("TYPE_MISMATCH", "mapping value_type differs from policy declaration")
        if entry.get("unit") != declaration["unit"]:
            raise RouteInterfaceError("UNIT_MISMATCH", "mapping unit differs from policy declaration")
        if entry["present"]:
            if not isinstance(entry.get("source_pointer"), str):
                raise RouteInterfaceError("MAPPING_SCHEMA_FAILURE", "present mapping requires one explicit source_pointer")
        else:
            if entry.get("source_pointer") is not None:
                raise RouteInterfaceError("MAPPING_SCHEMA_FAILURE", "absent mapping must have source_pointer null")
        entries[input_id] = entry

    if set(entries) != set(declarations):
        raise RouteInterfaceError("MAPPING_INCOMPLETE", "mapping must explicitly declare every policy-required input")

    present_records: dict[str, dict[str, Any]] = {}
    missing_ids: list[str] = []
    for input_id in sorted(declarations):
        entry = entries[input_id]
        if not entry["present"]:
            missing_ids.append(input_id)
            continue
        value = _json_pointer_get(source_case, entry["source_pointer"])
        if not _strict_value_matches(value, entry["value_type"]):
            raise RouteInterfaceError("TYPE_MISMATCH", "source value requires coercion or conflicts with declared type")
        present_records[input_id] = {
            "present": True,
            "value": value,
            "value_type": entry["value_type"],
            "unit": entry["unit"],
        }

    policy_sha256 = sha256_bytes(policy_bytes)
    builder_path = Path(__file__).resolve()
    builder_sha256 = hashlib.sha256(builder_path.read_bytes()).hexdigest()
    if not _is_sha256(builder_sha256):
        raise RouteInterfaceError("BINDING_PROVENANCE_INVALID", "builder source hash could not be calculated")
    return {
        "binding_version": BINDING_VERSION,
        "case_id": case_id,
        "source_case_id": source_case_id,
        "source_case_sha256": sha256_bytes(source_case_bytes),
        "policy_id": policy_id,
        "policy_sha256": policy_sha256,
        "binding_builder": {"version": BUILDER_VERSION, "sha256": builder_sha256},
        "present_input_ids": sorted(present_records),
        "missing_input_ids": missing_ids,
        "bindings": present_records,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", required=True, help="policy JSON with required input declarations")
    parser.add_argument("--source-case", required=True, help="explicit source-case record JSON")
    parser.add_argument("--mapping", required=True, help="explicit mapping declaration JSON")
    parser.add_argument("--output", required=True, help="write deterministic typed binding JSON here")
    args = parser.parse_args()
    try:
        policy, policy_raw = load_json_file(args.policy)
        source_case, source_raw = load_json_file(args.source_case)
        mapping, _ = load_json_file(args.mapping)
        binding = build_binding(policy, policy_raw, source_case, source_raw, mapping)
    except RouteInterfaceError as exc:
        print(json.dumps({"status": "FAIL", "code": exc.code, "message": exc.message}, sort_keys=True))
        return 2
    output = json.dumps(binding, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    Path(args.output).write_text(output, encoding="utf-8")
    print(json.dumps({"status": "PASS", "output_sha256": sha256_bytes(output.encode("utf-8"))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
