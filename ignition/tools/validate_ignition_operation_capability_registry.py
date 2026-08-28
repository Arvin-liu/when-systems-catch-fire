#!/usr/bin/env python3
"""Validate the canonical AI-facing Ignition operation capability registry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
REGISTRY_PATH = ROOT / "data/operations/ignition-operation-capability-registry-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/ignition-operation-capability-registry-r1.schema.json"
OPEN_OBLIGATION_PATH = ROOT / "data/operations/open-obligation-registry-r1.json"
SYSTEM_IDENTITY_PATH = ROOT / "data/architecture/current-system-identity.json"
CURRENT_FACTS_PATH = ROOT / "data/architecture/current-facts.json"
EXECUTION_CONTRACT_PATH = ROOT / "data/operations/iterations/148/execution-contract-r1.json"

EXPECTED_STATUSES = {
    "CURRENT",
    "CURRENT_BOUNDED",
    "OWNER_DEFERRED",
    "REFERENCE_ONLY",
    "HISTORICAL",
    "UNSUPPORTED",
}
EXPECTED_MODES = {"READ_ONLY_RUN", "REPOSITORY_CHANGE_RUN", "EXTERNAL_ACTION_RUN"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _operation_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["operation_id"]: row for row in registry.get("operations", []) if isinstance(row, dict) and isinstance(row.get("operation_id"), str)}


def _repo_path_exists(path: str) -> bool:
    return (REPO_ROOT / path).is_file()


def _resolve_pointer(document: Any, pointer: str) -> Any:
    value = document
    for raw_part in pointer.lstrip("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            value = value[int(part)]
        else:
            value = value[part]
    return value


def validate(document: dict[str, Any] | None = None) -> list[str]:
    registry = document if document is not None else load_json(REGISTRY_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(registry)
    ]
    if errors:
        return errors

    if registry["canonical_source_path"] != str(REGISTRY_PATH.relative_to(REPO_ROOT)):
        errors.append("canonical_source_path does not identify the sole registry file")
    if set(registry["status_vocabulary"]) != EXPECTED_STATUSES:
        errors.append("status vocabulary is incomplete or contains an undeclared status")
    if set(registry["execution_mode_vocabulary"]) != EXPECTED_MODES:
        errors.append("execution mode vocabulary is incomplete or contains an undeclared mode")

    operations = registry["operations"]
    operation_ids = [row["operation_id"] for row in operations]
    if operation_ids != sorted(operation_ids):
        errors.append("operations must be sorted by stable operation_id")
    if len(operation_ids) != len(set(operation_ids)):
        errors.append("operation ids must be unique")
    status_set = {row["current_status"] for row in operations}
    if status_set != EXPECTED_STATUSES:
        errors.append("registry must contain at least one truthful example of every declared status")

    for row in operations:
        operation_id = row["operation_id"]
        for source in row["authoritative_sources"]:
            if not _repo_path_exists(source["path"]):
                errors.append(f"{operation_id}: authoritative source missing: {source['path']}")
            elif source.get("json_pointer"):
                try:
                    _resolve_pointer(load_json(REPO_ROOT / source["path"]), source["json_pointer"])
                except (KeyError, IndexError, ValueError, TypeError, json.JSONDecodeError):
                    errors.append(f"{operation_id}: authoritative JSON pointer does not resolve: {source['path']}#{source['json_pointer']}")
        for path in row["required_current_reads"]:
            if not _repo_path_exists(path):
                errors.append(f"{operation_id}: required Current read missing: {path}")
        for path in row["applicable_governance"]:
            if not _repo_path_exists(path):
                errors.append(f"{operation_id}: governance source missing: {path}")
        for check in row["validation_checks"]:
            if not _repo_path_exists(check["path"]):
                errors.append(f"{operation_id}: validation check missing: {check['path']}")

        mode = row["default_execution_mode"]
        repository_permission = row["repository_mutation_permission"]
        external_permission = row["external_action_permission"]
        status = row["current_status"]
        if mode == "READ_ONLY_RUN" and repository_permission != "FORBIDDEN":
            errors.append(f"{operation_id}: READ_ONLY_RUN cannot permit repository mutation")
        if mode == "READ_ONLY_RUN" and external_permission != "FORBIDDEN":
            errors.append(f"{operation_id}: READ_ONLY_RUN cannot permit external action")
        if mode == "REPOSITORY_CHANGE_RUN":
            if repository_permission != "EXPLICIT_USER_OR_OWNER_AUTHORIZATION_AND_ITERATION_METHOD":
                errors.append(f"{operation_id}: repository change lacks explicit authority plus Iteration Method binding")
            if external_permission != "FORBIDDEN":
                errors.append(f"{operation_id}: repository change cannot imply external action")
            if not row["explicit_owner_authorization_required"]:
                errors.append(f"{operation_id}: repository change must preserve explicit Owner authorization")
        if mode == "EXTERNAL_ACTION_RUN":
            if external_permission != "EXPLICIT_OWNER_AUTHORIZATION_AND_CURRENT_ADMISSION":
                errors.append(f"{operation_id}: external action lacks explicit Owner and Current admission binding")
            if not row["explicit_owner_authorization_required"]:
                errors.append(f"{operation_id}: external action must require explicit Owner authorization")
            if repository_permission != "FORBIDDEN":
                errors.append(f"{operation_id}: external action cannot imply repository mutation")
        if status == "OWNER_DEFERRED" and row["ai_callability"] != "STATUS_ONLY":
            errors.append(f"{operation_id}: Owner-deferred operation must remain STATUS_ONLY")
        if status in {"REFERENCE_ONLY", "HISTORICAL", "UNSUPPORTED"}:
            if row["ai_callability"] != "STATUS_ONLY":
                errors.append(f"{operation_id}: non-Current boundary entry must be STATUS_ONLY")
            if repository_permission != "FORBIDDEN" or external_permission != "FORBIDDEN":
                errors.append(f"{operation_id}: non-Current boundary entry cannot grant mutation or external action")
        if status in {"CURRENT", "CURRENT_BOUNDED"}:
            if all("/iterations/" in source["path"] for source in row["authoritative_sources"]):
                errors.append(f"{operation_id}: Current status cannot derive only from historical task records")
            if row["ai_callability"] == "STATUS_ONLY":
                errors.append(f"{operation_id}: Current operation cannot be status-only")
        for relation in row["historical_relations"]:
            if not _repo_path_exists(relation["source"]):
                errors.append(f"{operation_id}: historical relation source missing: {relation['source']}")
            target = relation["target_operation_id"]
            if target is not None and target not in operation_ids:
                errors.append(f"{operation_id}: historical relation target is not registered: {target}")

    manifest_paths = registry["coverage"]["pack_manifest_paths"]
    discovered_manifest_paths = sorted(
        str(path.relative_to(REPO_ROOT))
        for path in (ROOT / "packs").glob("*/manifest.json")
    )
    if sorted(manifest_paths) != discovered_manifest_paths:
        errors.append("Pack manifest census differs from the repository discovery set")
    expected_pack_capabilities: dict[str, tuple[str, str]] = {}
    for path in manifest_paths:
        manifest = load_json(REPO_ROOT / path)
        pack_id = manifest["pack_id"]
        for capability_id in manifest["capabilities_provided"]:
            if capability_id in expected_pack_capabilities:
                errors.append(f"duplicate Pack capability declaration: {capability_id}")
            expected_pack_capabilities[capability_id] = (pack_id, path)

    represented_pack_capabilities: dict[str, str] = {}
    for row in operations:
        binding = row["pack_binding"]
        if binding is None:
            continue
        capability_id = binding["manifest_capability_id"]
        represented_pack_capabilities[capability_id] = row["operation_id"]
        expected = expected_pack_capabilities.get(capability_id)
        if expected is None:
            errors.append(f"{row['operation_id']}: Pack binding is not declared by a Current manifest")
        elif expected != (binding["pack_id"], binding["manifest_path"]):
            errors.append(f"{row['operation_id']}: Pack binding differs from manifest authority")
        if row["operation_id"] != capability_id:
            errors.append(f"{row['operation_id']}: Pack-backed stable id must equal the manifest capability id")

    if set(represented_pack_capabilities) != set(expected_pack_capabilities):
        missing = sorted(set(expected_pack_capabilities) - set(represented_pack_capabilities))
        extra = sorted(set(represented_pack_capabilities) - set(expected_pack_capabilities))
        errors.append(f"Pack capability coverage mismatch missing={missing} extra={extra}")

    coverage = registry["coverage"]
    non_pack_count = sum(row["pack_binding"] is None for row in operations)
    if coverage["pack_capability_count"] != len(expected_pack_capabilities):
        errors.append("declared Pack capability count differs from manifests")
    if coverage["represented_pack_capability_count"] != len(represented_pack_capabilities):
        errors.append("represented Pack capability count is stale")
    if coverage["non_pack_operation_count"] != non_pack_count:
        errors.append("non-Pack operation count is stale")
    if coverage["operation_count"] != len(operations):
        errors.append("operation count is stale")
    current_pack_facts = load_json(CURRENT_FACTS_PATH)["facts"]["packs"]
    if current_pack_facts["count"] != len(manifest_paths):
        errors.append("Pack manifest count differs from deterministic Current facts")
    if current_pack_facts["capability_route_count"] != len(expected_pack_capabilities):
        errors.append("Pack capability count differs from deterministic Current facts")
    execution_baseline = load_json(EXECUTION_CONTRACT_PATH)["formal_baseline"]["sha"]
    if coverage["formal_main_baseline"] != registry["registry_lifecycle"]["baseline_sha"]:
        errors.append("coverage baseline differs from registry lifecycle baseline")
    if coverage["formal_main_baseline"] != execution_baseline:
        errors.append("registry baseline differs from the Task148 execution contract")

    operation_map = _operation_map(registry)
    live = operation_map.get("external.live_invocation")
    obligation = next(
        row for row in load_json(OPEN_OBLIGATION_PATH)["obligations"]
        if row["obligation_id"] == "LIVE_EXTERNAL_INVOCATION"
    )
    if live is None or live["current_status"] != "OWNER_DEFERRED":
        errors.append("external.live_invocation must remain OWNER_DEFERRED")
    elif obligation["current_status"] != "OPEN" or obligation["operational_state"] != "OWNER_DEFERRED":
        errors.append("external.live_invocation differs from the open-obligation authority")

    reference = operation_map.get("executor.reference_conformance")
    identity = load_json(SYSTEM_IDENTITY_PATH)["current_architecture_identity"]["reference_executor_role"]
    if reference is None or reference["current_status"] != "REFERENCE_ONLY":
        errors.append("executor.reference_conformance must remain REFERENCE_ONLY")
    if identity != "REFERENCE_EXECUTOR / CONFORMANCE_EXECUTOR / FALLBACK_MINIMAL":
        errors.append("Reference Executor identity authority changed unexpectedly")

    if operation_map.get("research.reos_full", {}).get("current_status") != "UNSUPPORTED":
        errors.append("research.reos_full must remain UNSUPPORTED")
    if operation_map.get("repository.apply_iteration_method_1_3", {}).get("current_status") != "HISTORICAL":
        errors.append("Iteration Method 1.3.0 boundary must remain HISTORICAL")
    if operation_map.get("repository.apply_iteration_method", {}).get("current_status") != "CURRENT":
        errors.append("Current Iteration Method operation is missing")

    tick = chr(96)
    required_markers = {
        ROOT / "ITERATION.md": [f"Current: {tick}1.4.0{tick}", "governs how 点火 changes itself"],
        ROOT / "docs/architecture/reos-vnext-light.md": ["OWNER_ACCEPTED_WITH_EXPLICIT_RESIDUALS", "KEEP_LIGHT_ONLY", f"There is no available {tick}REOS_FULL{tick} runtime"],
        ROOT / "docs/publication/zhiyuan-writing-method.md": [f"Version: {tick}0.5.0{tick} current", "CURRENT_MERGED_L6_CAPABILITY"],
        ROOT / "docs/architecture/language-thought-logic-plane.md": ["CURRENT_CROSS_LAYER_CONTROL_PLANE"],
        ROOT / "agent_kernel/README.md": ["CURRENT_BOUNDED_R0"],
    }
    for path, markers in required_markers.items():
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(f"Current source marker missing: {path.relative_to(REPO_ROOT)} :: {marker}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("IGNITION_OPERATION_CAPABILITY_REGISTRY_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    registry = load_json(REGISTRY_PATH)
    print(
        "IGNITION_OPERATION_CAPABILITY_REGISTRY_OK "
        f"operations={len(registry['operations'])} "
        f"pack_capabilities={registry['coverage']['represented_pack_capability_count']} "
        f"statuses={len(set(row['current_status'] for row in registry['operations']))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
