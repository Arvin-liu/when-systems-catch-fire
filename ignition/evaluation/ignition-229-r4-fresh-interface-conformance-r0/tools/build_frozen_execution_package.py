#!/usr/bin/env python3
"""Build the frozen Task229-R4 live-input package and validation run matrix.

This build step reads only the pinned Task229 historical input map, six pinned
Task228 policies, the R3 typed-binding builder, the R3 deterministic reference
interpreter, the R3 contract, and the R3 migration proof. It performs no live
successor call and no evaluator call.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

R3_REL = Path("ignition/evaluation/ignition-229-r3-typed-input-route-interface-repair-r0")
CONTRACT_NAME = "typed-route-interface-contract-r1.json"
PROOF_NAME = "historical-binding-migration-proof-r1.json"
CASE_PROSE = "No narrative case details are supplied beyond the explicit typed binding."
MAP_COMMIT = "4ee132e8d50e8805c466cb5d681aaa18c34c9f68"
R3_HEAD = "9ef9a1b6ce47702a88af39f437dc3bbee33772fb"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode("utf-8") + b"\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-map", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--output-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    output_root = args.output_root.resolve()
    r3_root = repo_root / R3_REL
    sys.path.insert(0, str((r3_root / "tools").resolve()))

    from build_typed_case_binding import MAPPING_VERSION, build_binding
    from prove_historical_binding_migration import (
        CASE_IDS,
        POLICY_BY_LINEAGE,
        _mapping_type,
        _pointer_escape,
    )
    from route_reference_interpreter import (
        canonical_json_bytes,
        interpret,
        policy_required_inputs,
        sha256_bytes,
        _declared_types,
    )

    contract_path = r3_root / CONTRACT_NAME
    proof_path = r3_root / PROOF_NAME
    contract_raw = contract_path.read_bytes()
    proof_raw = proof_path.read_bytes()
    contract = json.loads(contract_raw)
    proof = json.loads(proof_raw)
    input_map_raw = args.input_map.read_bytes()
    input_map = json.loads(input_map_raw)

    frozen_map = contract["frozen_sources"]["historical_input_map"]
    if frozen_map["commit"] != MAP_COMMIT or sha256(input_map_raw) != frozen_map["sha256"]:
        raise SystemExit("INPUT_MAP_HASH_MISMATCH")
    if contract.get("contract_version") != "task229-route-interface-contract-r1":
        raise SystemExit("CONTRACT_VERSION_MISMATCH")
    if input_map.get("version") != "task229-case-input-values-r0":
        raise SystemExit("INPUT_MAP_SCHEMA_FAILURE")
    if proof.get("summary", {}).get("case_count") != 18:
        raise SystemExit("R3_MIGRATION_PROOF_NOT_18_OF_18")
    if proof.get("summary", {}).get("all_values_identical") is not True:
        raise SystemExit("R3_MIGRATION_VALUES_NOT_IDENTICAL")
    if proof.get("summary", {}).get("all_missingness_identical") is not True:
        raise SystemExit("R3_MIGRATION_MISSINGNESS_NOT_IDENTICAL")

    policy_manifest = {item["policy_id"]: item for item in contract["frozen_sources"]["policies"]}
    policy_cache: dict[str, tuple[dict[str, Any], bytes]] = {}
    for policy_id in POLICY_BY_LINEAGE.values():
        manifest = policy_manifest[policy_id]
        policy_raw = (repo_root / manifest["path"]).read_bytes()
        if sha256(policy_raw) != manifest["sha256"]:
            raise SystemExit("POLICY_HASH_MISMATCH:" + policy_id)
        policy = json.loads(policy_raw)
        if policy.get("policy_id") != policy_id:
            raise SystemExit("POLICY_ID_MISMATCH:" + policy_id)
        policy_cache[policy_id] = (policy, policy_raw)

    proof_by_key = {
        (row["lineage_id"], row["case_id"]): row
        for row in proof["cases"]
    }
    matrix_units: list[dict[str, Any]] = []
    input_lines: list[bytes] = []
    prose_sha = sha256(CASE_PROSE.encode("utf-8"))
    prompt_sha = sha256((r3_root / "successor-prompt-template-r1.md").read_bytes())
    response_schema_sha = sha256((r3_root / "successor-response-schema-r1.json").read_bytes())
    route_schema_sha = sha256((r3_root / "route-trace-r1.schema.json").read_bytes())

    for lineage in sorted(POLICY_BY_LINEAGE):
        policy_id = POLICY_BY_LINEAGE[lineage]
        policy, policy_raw = policy_cache[policy_id]
        declarations = policy_required_inputs(policy)
        for case_id in CASE_IDS:
            values = input_map["case_inputs_by_lineage"][lineage][case_id]
            if not isinstance(values, dict):
                raise SystemExit("INPUT_MAP_CASE_NOT_OBJECT")
            source_case_id = f"task229:REFERENCE_M1:{lineage}:{case_id}"
            source_case = {
                "case_id": case_id,
                "source_case_id": source_case_id,
                "values": values,
            }
            source_case_raw = canonical_json_bytes(source_case)
            binding_entries = []
            for input_id in sorted(declarations):
                declaration = declarations[input_id]
                present = input_id in values
                binding_entries.append({
                    "input_id": input_id,
                    "present": present,
                    "source_pointer": f"/values/{_pointer_escape(input_id)}" if present else None,
                    "value_type": (
                        _mapping_type(values[input_id], declaration)
                        if present
                        else _declared_types(declaration["value_type"])[0]
                    ),
                    "unit": declaration["unit"],
                })
            mapping = {
                "mapping_version": MAPPING_VERSION,
                "case_id": case_id,
                "source_case_id": source_case_id,
                "policy_id": policy_id,
                "bindings": binding_entries,
            }
            binding = build_binding(policy, policy_raw, source_case, source_case_raw, mapping)
            binding_raw = canonical_json_bytes(binding)
            binding_sha = sha256_bytes(binding_raw)
            proof_row = proof_by_key[(lineage, case_id)]
            if binding_sha != proof_row["binding_sha256"]:
                raise SystemExit("R3_BINDING_DIGEST_MISMATCH:" + lineage + ":" + case_id)
            if binding["source_case_sha256"] != proof_row["source_case_record_sha256"]:
                raise SystemExit("R3_SOURCE_CASE_DIGEST_MISMATCH:" + lineage + ":" + case_id)

            reference = interpret(policy, binding, policy_raw)
            if reference["execution_status"] not in {"ROUTE_TRACE_READY", "ROUTE_AMBIGUOUS"}:
                raise SystemExit("REFERENCE_NOT_EXECUTABLE:" + lineage + ":" + case_id)
            trace_raw = canonical_json_bytes(reference["route_trace"])
            trace_sha = sha256_bytes(trace_raw)
            reference_raw = canonical_json_bytes(reference)
            reference_sha = sha256_bytes(reference_raw)
            run_id = f"R4-{lineage}-{case_id}"
            policy_sha = sha256(policy_raw)
            source_case_sha = binding["source_case_sha256"]
            input_hashes = {
                "policy_sha256": policy_sha,
                "binding_sha256": binding_sha,
                "source_case_record_sha256": source_case_sha,
                "case_prose_sha256": prose_sha,
                "reference_execution_sha256": reference_sha,
                "prompt_template_sha256": prompt_sha,
                "response_schema_sha256": response_schema_sha,
                "route_trace_schema_sha256": route_schema_sha,
            }
            successor_inputs = {
                "policy_json_utf8": policy_raw.decode("utf-8", errors="strict"),
                "typed_binding_json_utf8": binding_raw.decode("utf-8", errors="strict"),
                "case_prose": CASE_PROSE,
                "reference_execution_json_utf8": reference_raw.decode("utf-8", errors="strict"),
            }
            input_row = {
                "run_id": run_id,
                "successor_inputs": successor_inputs,
                "input_hashes": input_hashes,
            }
            input_lines.append(canonical_bytes(input_row) + b"\n")
            matrix_units.append({
                "run_id": run_id,
                "lineage_id": lineage,
                "case_id": case_id,
                "policy_id": policy_id,
                "policy_sha256": policy_sha,
                "binding_sha256": binding_sha,
                "source_case_binding_provenance_sha256": source_case_sha,
                "case_prose_sha256": prose_sha,
                "reference_execution_sha256": reference_sha,
                "expected_reference_status": reference["execution_status"],
                "expected_deterministic_route_trace_sha256": trace_sha,
                "prompt_template_sha256": prompt_sha,
                "response_schema_sha256": response_schema_sha,
                "route_trace_schema_sha256": route_schema_sha,
                "present_input_ids": binding["present_input_ids"],
                "missing_input_ids": binding["missing_input_ids"],
            })

    if len(matrix_units) != 18:
        raise SystemExit("RUN_UNIT_COUNT_MISMATCH")
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "execution-inputs.jsonl").write_bytes(b"".join(input_lines))
    write_json(output_root / "run-matrix.json", {
        "schema_version": "task229-r4-run-matrix-r0",
        "source_r3_head": R3_HEAD,
        "case_order": "lineage ascending L01-L06; within each lineage A, B, C",
        "run_unit_count": len(matrix_units),
        "invocations_per_unit": 1,
        "historical_case_prose_used": False,
        "case_prose_sha256": prose_sha,
        "neutral_case_prose": CASE_PROSE,
        "units": matrix_units,
    })
    print(
        "R4_EXECUTION_PACKAGE_BUILT"
        f" run_units={len(matrix_units)}"
        f" execution_inputs_sha256={sha256((output_root / 'execution-inputs.jsonl').read_bytes())}"
        f" run_matrix_sha256={sha256((output_root / 'run-matrix.json').read_bytes())}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
