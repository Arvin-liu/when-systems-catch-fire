#!/usr/bin/env python3
"""Fail-closed validator for the Task 119 boundary manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from generate_agentization_boundary import ADDED_R0_IDS, OUTPUT, REGISTRY, build


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/architecture/agentization-boundary-r0.schema.json"


def validate() -> dict:
    manifest = json.loads(OUTPUT.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    try:
        from jsonschema import Draft202012Validator
    except Exception as exc:  # pragma: no cover - CI installs jsonschema
        raise RuntimeError("jsonschema is required for the boundary gate") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(manifest), key=lambda item: list(item.path))
    if errors:
        raise ValueError("boundary schema errors: " + "; ".join(error.message for error in errors))
    registry_by_id = {item["component_id"]: item for item in registry["components"]}
    records = manifest["components"]
    if set(registry_by_id) != {record["component_id"] for record in records}:
        raise ValueError("boundary manifest does not cover exactly the live registry")
    if len(records) != len({record["component_id"] for record in records}):
        raise ValueError("boundary manifest repeats a component")
    generated = build()
    if manifest != generated:
        raise ValueError("boundary manifest is not the deterministic registry projection")
    for record in records:
        source = registry_by_id[record["component_id"]]
        if record["canonical_ref"] != source["canonical_target"]:
            raise ValueError(f"canonical ref drift for {record['component_id']}")
        if record["current_move_disposition"] == "KEEP_CURRENT_PATH_R0" and record["component_id"] in ADDED_R0_IDS:
            raise ValueError(f"new agent component incorrectly marked KEEP_CURRENT_PATH_R0: {record['component_id']}")
        if record["primary_role"] == "AGENT_RUNTIME" and record["kernel_dependency_direction"] != "CONSUMES_GENERIC_CONTRACT":
            raise ValueError(f"runtime boundary direction is invalid: {record['component_id']}")
        if record["primary_role"] == "GENERIC_KERNEL" and record["domain_binding"] != "domain_neutral":
            raise ValueError(f"generic kernel is domain-bound: {record['component_id']}")
    counts: dict[str, int] = {role: 0 for role in manifest["role_vocabulary"]}
    for record in records:
        counts[record["primary_role"]] += 1
    return {"status": "PASS", "component_count": len(records), "role_counts": counts, "physical_migration": manifest["physical_migration"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True) if args.json else f"AGENTIZATION_BOUNDARY_VALID={result['component_count']} role_counts={result['role_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
