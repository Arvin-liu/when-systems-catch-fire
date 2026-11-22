#!/usr/bin/env python3
"""Validate the task-intent index, R/O/G responsibility matrix, and execution-boundary map."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


HERE = Path(__file__).resolve()
IGNITION_ROOT = HERE.parents[2]
REPO_ROOT = IGNITION_ROOT.parent
DATA = IGNITION_ROOT / "data" / "operations"
REGISTRY_PATH = DATA / "ignition-operation-capability-registry-r1.json"
COMPONENTS_PATH = DATA / "project-components.json"
VALIDATION_MAP_PATH = DATA / "component-validation-map-r1.json"
CANDIDATES_PATH = DATA / "toolbox-candidate-cards-r0.json"
INTENT_PATH = DATA / "task-intent-index-r1.json"
MATRIX_PATH = DATA / "component-domain-responsibilities-r1.json"
BOUNDARY_PATH = DATA / "capability-execution-boundary-map-r1.json"
CALLABLE_STATUSES = {"CURRENT", "CURRENT_BOUNDED"}
CALLABILITIES = {"PUBLIC", "PUBLIC_BOUNDED"}
DOMAINS = {"R", "O", "G"}
RUNTIME_EVIDENCE_PATHS = (
    "ignition/agent_runtime/pack_registry.py",
    "ignition/agent_runtime/routing.py",
    "ignition/agent_runtime/README.md",
    "ignition/tests/test_pack_registry.py",
    "ignition/tests/test_pack_aware_routing.py",
    "ignition/agent_kernel/contracts.py",
    "ignition/agent_runtime/actions.py",
    "ignition/agent_runtime/executor_admission.py",
    "ignition/agent_runtime/runtime.py",
)
SUPPORTING_TOOL_EVIDENCE = (
    {
        "operation_ids": ["foundation.resolve_current_asset"],
        "path": "ignition/tools/foundation/resolve_current_canonical_asset.py",
        "role": "RELATED_CURRENT_IDENTITY_RESOLVER_NOT_EXACT_OPERATION_REGISTRY_BINDING",
        "execution_relation": "READ_ONLY_RESOLVER_SOURCE; THIS MAP DID NOT INVOKE IT",
    },
    {
        "operation_ids": ["knowledge.collide_object"],
        "path": "ignition/tools/operations/evaluate_object_collision_run.py",
        "role": "REGISTRY_DECLARED_VALIDATION_CHECK_AND_RESULT_RENDERER_NOT_ACTION_EXECUTOR",
        "execution_relation": "CHECKS_AND_RENDERS_A_TYPED_RUN; THIS MAP DID NOT INVOKE IT",
    },
    {
        "operation_ids": ["*"],
        "path": "ignition/tools/operations/plan_ignition_operation_run.py",
        "role": "REGISTERED_OPERATION_READ_PLAN_GENERATOR_NOT_INVOKER",
        "execution_relation": "RETURNS_execution_authorized_FALSE; THIS MAP DID NOT INVOKE IT",
    },
)


class AssetValidationError(ValueError):
    """Raised when an asset is stale, incomplete, or promotes its evidence."""


def _fail(message: str) -> None:
    raise AssetValidationError(message)


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"cannot load {path.relative_to(REPO_ROOT)}: {exc}")


def _blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _repo_blob(path: str) -> str:
    source = REPO_ROOT / path
    if not source.is_file() or source.is_symlink():
        _fail(f"source citation is missing or is a symlink: {path}")
    return _blob_sha1(source.read_bytes())


def _check_source_ref(ref: dict[str, Any], expected_path: str | None = None) -> None:
    path = ref.get("path")
    if not isinstance(path, str) or (expected_path is not None and path != expected_path):
        _fail(f"invalid source path reference: {ref}")
    if ref.get("blob_sha1") != _repo_blob(path):
        _fail(f"stale source citation: {path}")


def _canonical_target(path: str) -> str:
    return path.split("#", 1)[0]


def _source_repo_path(path: str) -> str:
    return path.removeprefix("ignition/")


def validate_task_intent_index(
    index: dict[str, Any], registry: dict[str, Any], component_registry: dict[str, Any]
) -> None:
    if index.get("schema_version") != "task-intent-index-r1":
        _fail("task-intent index schema_version is not r1")
    sources = index.get("sources", {})
    _check_source_ref(sources.get("operation_registry", {}), "ignition/data/operations/ignition-operation-capability-registry-r1.json")
    _check_source_ref(sources.get("component_registry", {}), "ignition/data/operations/project-components.json")

    operations = registry.get("operations", [])
    operations_by_id = {item["operation_id"]: (position, item) for position, item in enumerate(operations)}
    components = {item["component_id"]: item for item in component_registry.get("components", [])}
    entries = index.get("entries")
    if not isinstance(entries, list):
        _fail("task-intent entries must be an array")
    ids = [entry.get("operation_id") for entry in entries]
    if len(ids) != len(set(ids)):
        _fail("task-intent index contains duplicate operation ids")
    eligible = {
        operation_id
        for operation_id, (_, operation) in operations_by_id.items()
        if operation.get("current_status") in CALLABLE_STATUSES
        and operation.get("ai_callability") in CALLABILITIES
    }
    if set(ids) != eligible:
        _fail(f"task-intent coverage mismatch: expected {len(eligible)} routable Current operations, got {len(ids)}")

    for entry in entries:
        operation_id = entry.get("operation_id")
        position, operation = operations_by_id[operation_id]
        ref = entry.get("input_type_source_ref", {})
        expected_pointer = f"/operations/{position}/accepted_input_types"
        if ref != {
            "path": "ignition/data/operations/ignition-operation-capability-registry-r1.json",
            "operation_id": operation_id,
            "json_pointer": expected_pointer,
        }:
            _fail(f"input types are not bound to the exact registry contract for {operation_id}")
        if not isinstance(entry.get("aliases_zh"), list) or not entry["aliases_zh"]:
            _fail(f"Chinese aliases are required for {operation_id}")
        if not isinstance(entry.get("aliases_en"), list) or not entry["aliases_en"]:
            _fail(f"English aliases are required for {operation_id}")
        if not entry.get("keywords_zh") or not entry.get("keywords_en"):
            _fail(f"Chinese and English keywords are required for {operation_id}")
        for field in ("aliases_zh", "aliases_en", "keywords_zh", "keywords_en"):
            values = entry[field]
            if any(not isinstance(value, str) or not value.strip() for value in values):
                _fail(f"invalid phrase in {field} for {operation_id}")
        if entry.get("component_resolution") not in {"RESOLVED", "UNRESOLVED"}:
            _fail(f"invalid component resolution state for {operation_id}")
        links = entry.get("component_links", [])
        expected_links = []
        by_target = {_canonical_target(item["canonical_target"]): item["component_id"] for item in components.values()}
        for source in operation.get("authoritative_sources", []):
            path = source.get("path")
            if isinstance(path, str):
                component_id = by_target.get(_source_repo_path(path))
                if component_id:
                    expected_links.append({
                        "component_id": component_id,
                        "source_path": path,
                        "relation": "EXACT_AUTHORITATIVE_SOURCE_TARGET",
                    })
        expected_links = sorted(expected_links, key=lambda item: (item["component_id"], item["source_path"]))
        if links != expected_links:
            _fail(f"component links are not exact canonical-source matches for {operation_id}")
        if entry.get("component_ids") != sorted({item["component_id"] for item in expected_links}):
            _fail(f"component_ids do not match exact source links for {operation_id}")
        if bool(expected_links) != (entry["component_resolution"] == "RESOLVED"):
            _fail(f"component resolution state disagrees with exact links for {operation_id}")
        if not expected_links and not entry.get("component_resolution_reason"):
            _fail(f"unresolved component association needs a concrete reason for {operation_id}")


def _matrix_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    single = {domain: 0 for domain in sorted(DOMAINS)}
    shared = 0
    unresolved = 0
    for row in rows:
        status = row["classification_status"]
        if status == "SINGLE_DOMAIN_PRIMARY":
            single[row["primary_responsibility_domain"]] += 1
        elif status == "SHARED_CROSS_DOMAIN":
            shared += 1
        elif status == "UNRESOLVED":
            unresolved += 1
    return {"single_domain_primary": single, "shared_cross_domain": shared, "unresolved": unresolved}


def validate_component_matrix(
    matrix: dict[str, Any], component_registry: dict[str, Any], validation_map: dict[str, Any], registry: dict[str, Any]
) -> None:
    if matrix.get("schema_version") != "component-domain-responsibilities-r1":
        _fail("component responsibility matrix schema_version is not r1")
    source_refs = matrix.get("sources", {})
    _check_source_ref(source_refs.get("component_registry", {}), "ignition/data/operations/project-components.json")
    _check_source_ref(source_refs.get("validation_map", {}), "ignition/data/operations/component-validation-map-r1.json")

    components = component_registry.get("components", [])
    component_by_id = {item["component_id"]: item for item in components}
    mapped = {item["component_id"]: item for item in validation_map.get("components", [])}
    rows = matrix.get("components", [])
    row_ids = [row.get("component_id") for row in rows]
    if len(rows) != 106 or len(row_ids) != len(set(row_ids)) or set(row_ids) != set(component_by_id):
        _fail("component responsibility matrix must cover each of the 106 registry ids exactly once")

    for row in rows:
        component_id = row["component_id"]
        source = component_by_id[component_id]
        if row.get("canonical_target") != source["canonical_target"]:
            _fail(f"canonical target drift for component {component_id}")
        map_row = mapped.get(component_id)
        projection = row.get("validation_map_projection")
        if map_row is None:
            if projection is not None:
                _fail(f"unmapped component {component_id} has a validation-map projection")
        else:
            expected_projection = {
                "component_id": component_id,
                "declared_validation_domain_associations": map_row["domains"],
                "validation_consumers": map_row["validation_targets"],
                "change_classifications": map_row["change_classifications"],
                "evidence_ref": {
                    "path": "ignition/data/operations/component-validation-map-r1.json",
                    "json_pointer": f"/components/{next(i for i, item in enumerate(validation_map['components']) if item['component_id'] == component_id)}/evidence",
                    "relation": "DECLARED_VALIDATION_ASSOCIATION_ONLY_NOT_OWNERSHIP",
                },
            }
            if projection != expected_projection:
                _fail(f"validation-map semantics were not preserved separately for {component_id}")

        status = row.get("classification_status")
        primary = row.get("primary_responsibility_domain")
        evidence_refs = row.get("responsibility_evidence", [])
        interfaces = row.get("cross_domain_interfaces", [])
        participants = row.get("participating_domains", [])
        if status == "UNRESOLVED":
            if primary is not None or not row.get("unresolved_reason"):
                _fail(f"unresolved component needs a concrete reason and no primary domain: {component_id}")
        elif status == "SINGLE_DOMAIN_PRIMARY":
            if primary not in DOMAINS or not evidence_refs:
                _fail(f"single-domain assignment lacks a valid domain or direct evidence: {component_id}")
        elif status == "SHARED_CROSS_DOMAIN":
            if primary not in DOMAINS or len(set(participants)) < 2 or not interfaces or not evidence_refs:
                _fail(f"shared component lacks a primary, participants, interface, or direct evidence: {component_id}")
        else:
            _fail(f"unknown responsibility classification for {component_id}: {status}")
        for participant in participants:
            if participant not in DOMAINS:
                _fail(f"invalid participating domain {participant} on {component_id}")
        for ref in evidence_refs:
            _check_source_ref(ref)
            if ref["path"] in {
                "ignition/data/operations/project-components.json",
                "ignition/data/operations/component-validation-map-r1.json",
            }:
                _fail(f"identity/validation map alone cannot prove responsibility for {component_id}")

    counts = _matrix_counts(rows)
    if matrix.get("classification_counts") != counts:
        _fail(f"matrix classification counts are stale: expected {counts}")
    expected_unmapped = sorted(set(component_by_id) - set(mapped))
    previous = matrix.get("previously_unmapped_review", [])
    if [item.get("component_id") for item in previous] != expected_unmapped:
        _fail("previously unmapped component review must cover the exact 46 ids in component_id order")
    for item in previous:
        component = component_by_id[item["component_id"]]
        if item.get("canonical_target") != component["canonical_target"]:
            _fail(f"previously-unmapped target drift for {item['component_id']}")
        if item.get("disposition") != next(row["classification_status"] for row in rows if row["component_id"] == item["component_id"]):
            _fail(f"previously-unmapped disposition drift for {item['component_id']}")
        if not item.get("disposition_reason"):
            _fail(f"previously-unmapped component requires a specific disposition reason: {item['component_id']}")

    operations = {item["operation_id"]: item for item in registry.get("operations", [])}
    expected_consumers: dict[str, list[dict[str, str]]] = {component_id: [] for component_id in component_by_id}
    by_target = {_canonical_target(item["canonical_target"]): item["component_id"] for item in components}
    for operation in operations.values():
        for source in operation.get("authoritative_sources", []):
            path = source.get("path")
            if isinstance(path, str):
                component_id = by_target.get(_source_repo_path(path))
                if component_id:
                    expected_consumers[component_id].append({"operation_id": operation["operation_id"], "source_path": path})
    for row in rows:
        expected = sorted(expected_consumers[row["component_id"]], key=lambda item: (item["operation_id"], item["source_path"]))
        if row.get("operation_source_consumers") != expected:
            _fail(f"operation source-consumer links are stale for {row['component_id']}")


def validate_execution_boundary_map(
    boundary: dict[str, Any], registry: dict[str, Any], component_registry: dict[str, Any], candidates: dict[str, Any]
) -> None:
    if boundary.get("schema_version") != "capability-execution-boundary-map-r1":
        _fail("capability boundary map schema_version is not r1")
    sources = boundary.get("sources", {})
    _check_source_ref(sources.get("operation_registry", {}), "ignition/data/operations/ignition-operation-capability-registry-r1.json")
    _check_source_ref(sources.get("component_registry", {}), "ignition/data/operations/project-components.json")
    _check_source_ref(sources.get("optional_candidate_catalog", {}), "ignition/data/operations/toolbox-candidate-cards-r0.json")
    runtime_refs = sources.get("runtime_evidence", [])
    if [item.get("path") for item in runtime_refs] != list(RUNTIME_EVIDENCE_PATHS):
        _fail("runtime evidence must cover the exact Pack routing, Kernel, Action Executor, and admission sources")
    for item in runtime_refs:
        _check_source_ref(item)
    expected_supporting_tools = [
        {**item, "blob_sha1": _repo_blob(item["path"])} for item in SUPPORTING_TOOL_EVIDENCE
    ]
    if sources.get("supporting_entrypoint_evidence") != expected_supporting_tools:
        _fail("supporting resolver/planner/validator evidence is missing, stale, or promoted to operation execution")
    expected_runtime_boundary = {
        "kernel_contract_ref": "ignition/agent_kernel/contracts.py",
        "runtime_coordinator_ref": "ignition/agent_runtime/runtime.py",
        "typed_local_action_executor_ref": "ignition/agent_runtime/actions.py",
        "executor_admission_ref": "ignition/agent_runtime/executor_admission.py",
        "observed_boundary": "GENERIC_TYPED_LOCAL_RUNTIME_WITH_CAPABILITY_SCOPE_AND_EXECUTOR_ADMISSION",
        "operation_binding": "NO_EXACT_OPERATION_ID_TO_RUNTIME_ENTRYPOINT_BINDING_ESTABLISHED",
        "execution_claim": "RUNTIME_SOURCE_EXISTS; THIS MAP PERFORMED NO ACTION AND DOES NOT BIND IT TO A REGISTERED DOMAIN OPERATION",
    }
    if boundary.get("generic_runtime_boundary") != expected_runtime_boundary:
        _fail("generic runtime evidence must remain separate from operation implementation bindings")

    operations = registry.get("operations", [])
    rows = boundary.get("operations", [])
    if len(operations) != 20 or {row.get("operation_id") for row in rows} != {item["operation_id"] for item in operations} or len(rows) != 20:
        _fail("boundary map must cover all 20 registered operations exactly once")
    by_id = {item["operation_id"]: (i, item) for i, item in enumerate(operations)}
    components = component_registry.get("components", [])
    by_target = {_canonical_target(item["canonical_target"]): item["component_id"] for item in components}
    packs = {item["pack_id"]: item for item in boundary.get("packs", [])}
    if len(packs) != 4:
        _fail("boundary map must cover the four Pack manifests")
    for row in rows:
        position, operation = by_id[row["operation_id"]]
        root = f"/operations/{position}"
        if row.get("registry_ref") != {"path": "ignition/data/operations/ignition-operation-capability-registry-r1.json", "json_pointer": root}:
            _fail(f"stale registry pointer for {row['operation_id']}")
        expected_contract_refs = {
            name: f"{root}/{name}"
            for name in (
                "current_status", "ai_callability", "accepted_input_types", "default_execution_mode",
                "repository_mutation_permission", "external_action_permission",
                "explicit_owner_authorization_required", "validation_checks", "claim_ceiling",
            )
        }
        if row.get("contract_refs") != expected_contract_refs:
            _fail(f"operation contract references are incomplete for {row['operation_id']}")
        expected_links = []
        for source in operation.get("authoritative_sources", []):
            path = source.get("path")
            if isinstance(path, str):
                component_id = by_target.get(_source_repo_path(path))
                if component_id:
                    expected_links.append({"component_id": component_id, "source_path": path, "relation": "EXACT_AUTHORITATIVE_SOURCE_TARGET"})
        expected_links.sort(key=lambda item: (item["component_id"], item["source_path"]))
        if row.get("component_links") != expected_links:
            _fail(f"stale component source links for {row['operation_id']}")
        binding = operation.get("pack_binding")
        pack_ref = row.get("pack_ref")
        if binding is None:
            if pack_ref is not None:
                _fail(f"unexpected Pack binding for {row['operation_id']}")
        else:
            expected_pack_ref = {
                "pack_id": binding["pack_id"],
                "manifest_path": binding["manifest_path"] if binding["manifest_path"].startswith("ignition/") else "ignition/" + binding["manifest_path"],
                "manifest_capability_id": binding["manifest_capability_id"],
            }
            if pack_ref != expected_pack_ref or binding["pack_id"] not in packs:
                _fail(f"operation/Pack manifest binding drift for {row['operation_id']}")
            pack = packs[binding["pack_id"]]
            if binding["manifest_capability_id"] not in pack["capability_ids"]:
                _fail(f"manifest does not declare bound capability for {row['operation_id']}")
        implementation = row.get("implementation", {})
        if implementation.get("state") == "EXECUTABLE_UNDER_DECLARED_RUNTIME":
            if not implementation.get("entrypoints") or not implementation.get("executor_binding"):
                _fail(f"executable state lacks an exact entrypoint and executor for {row['operation_id']}")
        if row.get("execution_state") != "NOT_PERFORMED_BY_THIS_DISCOVERY_MAP":
            _fail(f"operation execution was falsely promoted for {row['operation_id']}")

    manifests_by_id = {}
    for row in boundary["packs"]:
        _check_source_ref(row.get("manifest_ref", {}))
        for ref in row.get("runtime_evidence", []):
            _check_source_ref(ref)
        if row.get("runtime_evidence") != runtime_refs:
            _fail(f"Pack runtime evidence differs from the top-level runtime boundary sources: {row.get('pack_id')}")
        manifest = _load(REPO_ROOT / row["manifest_ref"]["path"])
        manifests_by_id[manifest["pack_id"]] = manifest
        for field, key in (("capability_ids", "capabilities_provided"), ("action_hooks", "action_hooks"), ("planning_hooks", "planning_hooks"), ("validator_entrypoints", "validator_entrypoints")):
            if row.get(field) != manifest.get(key, []):
                _fail(f"Pack manifest projection drift: {manifest['pack_id']} {field}")
        if row.get("load_state") != "METADATA_LOADABLE" or row.get("route_state") != "ROUTED_PROPOSAL":
            _fail(f"Pack state must remain metadata-loadable and proposal-only: {manifest['pack_id']}")
        if row.get("execution_claim") != "NOT_PERFORMED_BY_PACK_AWARE_ROUTER":
            _fail(f"Pack hook execution was falsely promoted: {manifest['pack_id']}")

    candidate_rows = boundary.get("optional_experimental_tools", [])
    candidate_cards = candidates.get("candidates", [])
    if len(candidate_rows) != 77 or len(candidate_cards) != 77:
        _fail("boundary map must cover all 77 optional experimental entries")
    candidate_by_id = {item["tool_id"]: item for item in candidate_cards}
    if len(candidate_by_id) != 77 or {item.get("tool_id") for item in candidate_rows} != set(candidate_by_id):
        _fail("optional experimental tool ids are missing or duplicated")
    for row in candidate_rows:
        card = candidate_by_id[row["tool_id"]]
        pointer_index = candidate_cards.index(card)
        expected_ref = {"path": "ignition/data/operations/toolbox-candidate-cards-r0.json", "json_pointer": f"/candidates/{pointer_index}"}
        if row.get("catalog_ref") != expected_ref:
            _fail(f"stale candidate catalog pointer for {row['tool_id']}")
        for field in ("availability", "lifecycle", "source_path", "entrypoint", "execution_mode", "router_selectable_by_default"):
            if row.get(field) != card.get(field):
                _fail(f"candidate source projection drift for {row['tool_id']} {field}")
        if card.get("availability") != "EXPERIMENTAL_AVAILABLE" or card.get("lifecycle") != "EXPERIMENTAL" or card.get("router_selectable_by_default") is not False:
            _fail(f"candidate is no longer Experimental/default-off: {row['tool_id']}")
        if row.get("boundary_state") != "EXPERIMENTAL_OPT_IN" or row.get("execution_claim") != "NOT_PERFORMED_BY_THIS_DISCOVERY_MAP":
            _fail(f"candidate was falsely promoted beyond opt-in discovery: {row['tool_id']}")

    vocabulary = boundary.get("boundary_vocabulary", {})
    required = {"DISCOVERABLE", "REGISTERED", "METADATA_LOADABLE", "ROUTED_PROPOSAL", "EXECUTABLE_UNDER_DECLARED_RUNTIME", "EXPERIMENTAL_OPT_IN", "DEFERRED", "UNRESOLVED"}
    if set(vocabulary) != required:
        _fail("boundary vocabulary must define the eight required states exactly")
    if any(row.get("implementation", {}).get("state") == "EXECUTABLE_UNDER_DECLARED_RUNTIME" for row in rows):
        _fail("no registered operation has exact implementation and executor evidence in this mapping")


def validate_all() -> dict[str, Any]:
    registry = _load(REGISTRY_PATH)
    components = _load(COMPONENTS_PATH)
    validation_map = _load(VALIDATION_MAP_PATH)
    candidates = _load(CANDIDATES_PATH)
    index = _load(INTENT_PATH)
    matrix = _load(MATRIX_PATH)
    boundary = _load(BOUNDARY_PATH)
    validate_task_intent_index(index, registry, components)
    validate_component_matrix(matrix, components, validation_map, registry)
    validate_execution_boundary_map(boundary, registry, components, candidates)
    return {
        "task_intent_entries": len(index["entries"]),
        "components": len(matrix["components"]),
        "classification_counts": matrix["classification_counts"],
        "previously_unmapped": len(matrix["previously_unmapped_review"]),
        "operations": len(boundary["operations"]),
        "packs": len(boundary["packs"]),
        "optional_experimental_tools": len(boundary["optional_experimental_tools"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate source linkage and all generated boundaries")
    parser.parse_args(argv)
    try:
        report = validate_all()
    except AssetValidationError as exc:
        print(f"DISCOVERY_DOMAIN_ASSETS_INVALID: {exc}", file=sys.stderr)
        return 1
    print("DISCOVERY_DOMAIN_ASSETS_OK " + json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
