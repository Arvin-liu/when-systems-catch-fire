#!/usr/bin/env python3
"""Validate and run the IGNITION-127 offline continuity pilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from agent_runtime.pilots.durability_lifecycle_127 import PILOT_SCHEMA, run_pilot


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/operations/durability/continuity-pilot-r1.json"
DEFAULT_SCHEMA = ROOT / "schemas/operations/durability-continuity-pilot-r1.schema.json"


def validate_result(data: Mapping[str, Any], result: Mapping[str, Any]) -> list[str]:
    expected = data["expected"]
    errors: list[str] = []
    if result.get("schema") != PILOT_SCHEMA or result.get("status") != expected["status"]:
        errors.append("pilot schema or status mismatch")
    if result.get("namespace", {}).get("namespace_count") != expected["namespace_count"]:
        errors.append("namespace count mismatch")
    if result.get("namespace", {}).get("workspace_count") != expected["workspace_count"]:
        errors.append("workspace count mismatch")
    snapshot = result.get("snapshot", {})
    if snapshot.get("captured_events") != expected["snapshot_captured_events"] or snapshot.get("tail_events", 0) < expected["minimum_tail_events"]:
        errors.append("snapshot/tail continuity evidence mismatch")
    if result.get("recovery", {}).get("normal_restart", {}).get("phase_count") != expected["recovery_phase_count"]:
        errors.append("recovery phase count mismatch")
    disaster = result.get("disaster_recovery", {})
    if disaster.get("chunk_count") != expected["dr_bundle_chunks"] or disaster.get("fresh_directory_restore") != "PASS":
        errors.append("disaster recovery bundle mismatch")
    if result.get("dispatch", {}).get("unresolved_refs") != [expected["unresolved_dispatch_ref"]]:
        errors.append("reconciliation reference mismatch")
    if result.get("scenario", {}).get("external_invocation") != expected["external_invocation"]:
        errors.append("external invocation rule violated")
    if disaster.get("external_reexecution") != expected["external_reexecution"]:
        errors.append("external reexecution rule violated")
    if result.get("soft_governance", {}).get("restored_status") != expected["soft_status"]:
        errors.append("soft governance status mismatch")
    if disaster.get("canonical_digest") != expected["canonical_digest"] or not disaster.get("canonical_digest_match"):
        errors.append("canonical digest mismatch")
    missing = [gate for gate in data["required_gates"] if result.get("checks", {}).get(gate) is not True]
    if missing:
        errors.append("failed gates: " + ",".join(missing))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    schema_errors = [error.message for error in Draft202012Validator(schema).iter_errors(data)]
    if schema_errors:
        print("FAIL")
        for error in schema_errors:
            print(f"- {error}")
        return 1
    result = run_pilot(recorded_at=data["recorded_at"])
    errors = validate_result(data, result)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "DURABILITY_CONTINUITY_PILOT_OK "
        f"namespaces={result['namespace']['namespace_count']} "
        f"workspaces={result['namespace']['workspace_count']} "
        f"snapshot_tail=PASS recovery_phases={result['recovery']['normal_restart']['phase_count']} "
        f"dr_chunks={result['disaster_recovery']['chunk_count']} "
        f"reconciliation={result['dispatch']['unresolved_refs'][0]} "
        f"external_invocation={result['scenario']['external_invocation']} "
        f"soft_governance={result['soft_governance']['restored_status']} "
        f"canonical_digest={result['disaster_recovery']['canonical_digest']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
