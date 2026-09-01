#!/usr/bin/env python3
"""Validate the Task149 Step05 canonical-data to Archify-IR receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/step05-archify-adapter-ir-receipt.json"
SCHEMA_PATH = ROOT / "schemas/operations/task149-step05-archify-adapter-ir-r0.schema.json"
IR_PATH = ROOT / "data/operations/iterations/149/archify-typed-ir-r0.json"
ARCHITECTURE_PATH = ROOT / "data/architecture/overall-architecture.json"
SYSTEM_MAP_PATH = ROOT / "data/architecture/interactive-system-map.json"

EXPECTED_FORMAL_PREVIOUS = "a051ad31b72d5cbb8deeaf2007b0e09431f8a4ba"
EXPECTED_FORMAL_BASELINE = "14c2595d796494286caf31378173fd9dd027edcf"
EXPECTED_ARCHIFY_REVISION = "2bfb47132c057195d8dddb3e25ae966dd7c7a72e"
EXPECTED_ARCHIFY_SCHEMA_SHA = "8c96140b6af8d93fb825a3c63e46b74176c9485185c978074ffe89e0f614576c"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    if document.get("formal_previous_commit") != EXPECTED_FORMAL_PREVIOUS:
        errors.append("Step05 must follow the published Step04 commit")
    if document.get("formal_baseline_sha") != EXPECTED_FORMAL_BASELINE:
        errors.append("IR source revision must remain the fresh Task148 Current main")
    if document.get("upstream_revision") != EXPECTED_ARCHIFY_REVISION:
        errors.append("Archify must remain pinned to the observed revision")
    if document.get("upstream_schema_surface", {}).get("sha256") != EXPECTED_ARCHIFY_SCHEMA_SHA:
        errors.append("Archify architecture schema evidence changed")
    by_path = {item.get("path"): item for item in document.get("source_inputs", [])}
    for path, local_path in (("ignition/data/architecture/overall-architecture.json", ARCHITECTURE_PATH), ("ignition/data/architecture/interactive-system-map.json", SYSTEM_MAP_PATH)):
        if by_path.get(path, {}).get("sha256") != digest(local_path):
            errors.append(f"source hash mismatch: {path}")
    ir = load_json(IR_PATH) if IR_PATH.exists() else {}
    if document.get("typed_ir", {}).get("sha256") != digest(IR_PATH):
        errors.append("typed IR hash does not match the generated file")
    architecture = load_json(ARCHITECTURE_PATH)
    if document.get("typed_ir", {}).get("component_count") != len(ir.get("components", [])) or len(ir.get("components", [])) != len(architecture.get("nodes", [])):
        errors.append("typed component count must cover every canonical architecture node")
    if document.get("typed_ir", {}).get("connection_count") != len(ir.get("connections", [])) or len(ir.get("connections", [])) != len(architecture.get("edges", [])):
        errors.append("typed connection count must cover every canonical architecture edge")
    derived_layout = document.get("derived_layout", {})
    if derived_layout.get("viewBox") != [1400, 800] or ir.get("meta", {}).get("viewBox") != [1400, 800]:
        errors.append("Step05 must retain the validated compact 1400x800 viewBox")
    if derived_layout.get("componentSize") != [190, 48]:
        errors.append("Step05 must retain the validated 190x48 component size")
    if derived_layout.get("explicitComponentPositionCount") != len(ir.get("components", [])):
        errors.append("derived component-position count must match the typed IR")
    if derived_layout.get("explicitConnectionGeometryCount") != len(ir.get("connections", [])):
        errors.append("derived connection-geometry count must match the typed IR")
    if any("pos" not in component or "size" not in component for component in ir.get("components", [])):
        errors.append("every typed component must retain explicit derived geometry")
    if any("labelAt" not in connection for connection in ir.get("connections", [])):
        errors.append("every typed connection must retain an explicit derived label position")
    if any("sublabel" in component for component in ir.get("components", [])):
        errors.append("duplicate component sublabels must remain omitted from the compact IR")
    ids = [item.get("id") for item in ir.get("components", [])]
    if len(ids) != len(set(ids)) or not all(ids):
        errors.append("typed component IDs must be non-empty and unique")
    valid_ids = set(ids)
    if any(item.get("from") not in valid_ids or item.get("to") not in valid_ids for item in ir.get("connections", [])):
        errors.append("typed connection endpoints must resolve to typed components")
    if document.get("archify_external_validation", {}).get("status") != "PENDING_STEP06":
        errors.append("Step05 must not claim external Archify validation before Step06")
    source_evidence = document.get("source_evidence", {})
    if source_evidence.get("status") != "PARTIAL_BY_CANONICAL_TARGETS":
        errors.append("source evidence coverage must remain explicit and bounded")
    if source_evidence.get("verified_component_count", 0) < 1:
        errors.append("at least one actual formal-repository file must be bound as source evidence")
    if source_evidence.get("omitted_non_file_target_count") != len(source_evidence.get("omitted_non_file_targets", [])):
        errors.append("omitted source-target count must match the omission ledger")
    boundary = document.get("boundary", {})
    if any(boundary.get(key) is not False for key in ("network_used_by_adapter", "authentication_used", "permission_granted")):
        errors.append("Step05 adapter must remain network/auth/permission side-effect free")
    if boundary.get("current_integration") != "NOT_CURRENT_INTEGRATION":
        errors.append("Step05 must not become Current integration")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_STEP05_ARCHIFY_ADAPTER_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    receipt = load_json(ARTIFACT_PATH)
    typed = receipt["typed_ir"]
    print(f"TASK149_STEP05_ARCHIFY_ADAPTER_OK components={typed['component_count']} connections={typed['connection_count']} ir={typed['sha256'][:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
