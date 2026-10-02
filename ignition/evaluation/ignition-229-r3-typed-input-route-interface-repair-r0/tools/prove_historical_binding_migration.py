#!/usr/bin/env python3
"""Prove lossless R1 serialization of the frozen Task229 input map."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_typed_case_binding import MAPPING_VERSION, build_binding
from route_reference_interpreter import (
    RouteInterfaceError,
    _declared_types,
    _strict_value_matches,
    canonical_json_bytes,
    load_json_file,
    policy_required_inputs,
    sha256_bytes,
)


POLICY_BY_LINEAGE = {
    "L01": "POLICY_F01_A",
    "L02": "POLICY_F01_B",
    "L03": "POLICY_F02_A",
    "L04": "POLICY_F02_B",
    "L05": "POLICY_F03_A",
    "L06": "POLICY_F03_B",
}
CASE_IDS = ("A", "B", "C")


def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _mapping_type(value: Any, declaration: dict[str, Any]) -> str:
    value_types = _declared_types(declaration["value_type"])
    if not _strict_value_matches(value, declaration["value_type"]):
        raise RouteInterfaceError("TYPE_MISMATCH", "frozen map value conflicts with policy declaration")
    actual = "null" if value is None else "boolean" if isinstance(value, bool) else "integer" if isinstance(value, int) else "number" if isinstance(value, float) else "string" if isinstance(value, str) else "unsupported"
    if actual in value_types:
        return actual
    if actual == "integer" and "number" in value_types:
        return "number"
    raise RouteInterfaceError("TYPE_MISMATCH", "frozen map value has no exact declared type")


def prove_migration(input_map: Any, input_map_bytes: bytes, contract: Any, policy_root: Path) -> dict[str, Any]:
    if not isinstance(contract, dict) or contract.get("contract_version") != "task229-route-interface-contract-r1":
        raise RouteInterfaceError("CONTRACT_MISMATCH", "R1 typed-route contract is missing or unsupported")
    frozen_map = contract.get("frozen_sources", {}).get("historical_input_map", {})
    actual_map_sha = sha256_bytes(input_map_bytes)
    if actual_map_sha != frozen_map.get("sha256"):
        raise RouteInterfaceError("INPUT_MAP_HASH_MISMATCH", "input map bytes differ from the frozen map SHA-256")
    if not isinstance(input_map, dict) or input_map.get("version") != "task229-case-input-values-r0":
        raise RouteInterfaceError("INPUT_MAP_SCHEMA_FAILURE", "historical input map has an unexpected schema")
    values_by_lineage = input_map.get("case_inputs_by_lineage")
    expectations = input_map.get("route_expectations_by_lineage")
    if not isinstance(values_by_lineage, dict) or not isinstance(expectations, dict):
        raise RouteInterfaceError("INPUT_MAP_SCHEMA_FAILURE", "historical map is missing case inputs or route expectations")
    if set(values_by_lineage) != set(POLICY_BY_LINEAGE) or set(expectations) != set(POLICY_BY_LINEAGE):
        raise RouteInterfaceError("INPUT_MAP_LINEAGE_MISMATCH", "historical map lineages differ from the frozen six-lineage set")

    frozen_policy_manifest = {item["policy_id"]: item for item in contract["frozen_sources"]["policies"]}
    policy_cache: dict[str, tuple[dict[str, Any], bytes, dict[str, dict[str, Any]]]] = {}
    for policy_id in POLICY_BY_LINEAGE.values():
        policy_path = policy_root / f"{policy_id}.json"
        policy, policy_raw = load_json_file(policy_path)
        expected = frozen_policy_manifest[policy_id]
        if sha256_bytes(policy_raw) != expected["sha256"] or policy.get("policy_id") != policy_id:
            raise RouteInterfaceError("POLICY_HASH_MISMATCH", f"frozen policy mismatch: {policy_id}")
        policy_cache[policy_id] = (policy, policy_raw, policy_required_inputs(policy))

    case_records: list[dict[str, Any]] = []
    for lineage in sorted(POLICY_BY_LINEAGE):
        policy_id = POLICY_BY_LINEAGE[lineage]
        policy, policy_raw, declarations = policy_cache[policy_id]
        for case_id in CASE_IDS:
            values = values_by_lineage[lineage].get(case_id)
            expected_route = expectations[lineage].get(case_id)
            if not isinstance(values, dict) or not isinstance(expected_route, dict):
                raise RouteInterfaceError("INPUT_MAP_SCHEMA_FAILURE", "historical map case record is missing")
            expected_values = expected_route.get("input_values")
            if not isinstance(expected_values, dict) or canonical_json_bytes(expected_values) != canonical_json_bytes(values):
                raise RouteInterfaceError("INPUT_MAP_VALUE_MISMATCH", "case input values differ from the frozen map's own route record")
            if set(values) - set(declarations):
                raise RouteInterfaceError("UNKNOWN_INPUT_ID", "frozen map contains an ID not declared by the policy")

            source_case_id = f"task229:REFERENCE_M1:{lineage}:{case_id}"
            source_case = {"case_id": case_id, "source_case_id": source_case_id, "values": values}
            source_case_bytes = canonical_json_bytes(source_case)
            mapping_entries = []
            for input_id in sorted(declarations):
                declaration = declarations[input_id]
                present = input_id in values
                mapping_entries.append({
                    "input_id": input_id,
                    "present": present,
                    "source_pointer": f"/values/{_pointer_escape(input_id)}" if present else None,
                    "value_type": _mapping_type(values[input_id], declaration) if present else _declared_types(declaration["value_type"])[0],
                    "unit": declaration["unit"],
                })
            mapping = {
                "mapping_version": MAPPING_VERSION,
                "case_id": case_id,
                "source_case_id": source_case_id,
                "policy_id": policy_id,
                "bindings": mapping_entries,
            }
            binding = build_binding(policy, policy_raw, source_case, source_case_bytes, mapping)
            migrated_values = {input_id: record["value"] for input_id, record in binding["bindings"].items()}
            same_keys = sorted(values) == binding["present_input_ids"]
            same_values = canonical_json_bytes(values) == canonical_json_bytes(migrated_values)
            expected_missing = sorted(set(declarations) - set(values))
            missing_matches = expected_missing == binding["missing_input_ids"]
            if not (same_keys and same_values and missing_matches):
                raise RouteInterfaceError("MIGRATION_VALUE_MISMATCH", "R1 binding changed or lost a frozen input-map value")
            case_records.append({
                "lineage_id": lineage,
                "case_id": case_id,
                "policy_id": policy_id,
                "policy_sha256": binding["policy_sha256"],
                "source_case_id": source_case_id,
                "source_case_record_sha256": binding["source_case_sha256"],
                "binding_sha256": sha256_bytes(canonical_json_bytes(binding)),
                "frozen_map_values_sha256": sha256_bytes(canonical_json_bytes(values)),
                "migrated_binding_values_sha256": sha256_bytes(canonical_json_bytes(migrated_values)),
                "present_input_ids": binding["present_input_ids"],
                "missing_input_ids": binding["missing_input_ids"],
                "values_identical": same_values and same_keys,
                "missingness_identical": missing_matches,
            })

    return {
        "proof_version": "task229-historical-binding-migration-proof-r1",
        "proof_class": "READ_ONLY_TARGET_BLIND_BINDING_SERIALIZATION",
        "frozen_input_map": {
            "commit": frozen_map["commit"],
            "path": frozen_map["path"],
            "sha256": actual_map_sha,
            "bytes_modified": False,
            "values_regenerated_from_prose": False,
        },
        "policy_base": contract["frozen_sources"]["task228_policy_base"],
        "policy_hashes_verified": {policy_id: frozen_policy_manifest[policy_id]["sha256"] for policy_id in sorted(policy_cache)},
        "binding_builder_version": "task229-typed-binding-builder-r1",
        "cases": case_records,
        "summary": {
            "case_count": len(case_records),
            "expected_case_count": 18,
            "all_values_identical": all(item["values_identical"] for item in case_records),
            "all_missingness_identical": all(item["missingness_identical"] for item in case_records),
            "policy_count": len(policy_cache),
            "target_criteria_read": False,
            "evaluator_material_read": False,
            "successor_sessions_run": 0,
            "evaluators_run": 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-map", required=True, help="exact frozen historical map JSON")
    parser.add_argument("--policy-root", required=True, help="directory containing the six frozen Task228 policy JSON files")
    parser.add_argument("--output", required=True, help="write deterministic migration proof JSON here")
    args = parser.parse_args()
    contract_path = Path(__file__).resolve().parents[1] / "typed-route-interface-contract-r1.json"
    try:
        input_map, input_map_raw = load_json_file(args.input_map)
        contract, _ = load_json_file(contract_path)
        report = prove_migration(input_map, input_map_raw, contract, Path(args.policy_root))
    except RouteInterfaceError as exc:
        print(json.dumps({"status": "FAIL", "code": exc.code, "message": exc.message}, sort_keys=True))
        return 2
    output = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    Path(args.output).write_text(output, encoding="utf-8")
    print(json.dumps({"status": "PASS", "cases": report["summary"]["case_count"], "all_values_identical": report["summary"]["all_values_identical"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
