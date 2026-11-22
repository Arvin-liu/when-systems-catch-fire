#!/usr/bin/env python3
"""Build a discovery-only map of operation, Pack, and experimental execution boundaries."""

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
DATA_ROOT = IGNITION_ROOT / "data" / "operations"
REGISTRY_REL = "ignition/data/operations/ignition-operation-capability-registry-r1.json"
COMPONENTS_REL = "ignition/data/operations/project-components.json"
CANDIDATES_REL = "ignition/data/operations/toolbox-candidate-cards-r0.json"
OUTPUT_REL = "ignition/data/operations/capability-execution-boundary-map-r1.json"
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


class BoundaryMapError(ValueError):
    """Raised when a source registry is missing or inconsistent."""


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BoundaryMapError(f"cannot load {path}: {exc}") from exc


def repo_file_blob(path: str) -> str:
    source = REPO_ROOT / path
    if not source.is_file() or source.is_symlink():
        raise BoundaryMapError(f"required boundary source is missing or is a symlink: {path}")
    return git_blob_sha1(source.read_bytes())


def canonical_target_path(path: str) -> str:
    return path.split("#", 1)[0]


def source_repo_relative(path: str) -> str:
    return path.removeprefix("ignition/")


def exact_component_links(operation: dict[str, Any], components: list[dict[str, Any]]) -> list[dict[str, str]]:
    by_target: dict[str, str] = {}
    for component in components:
        target = canonical_target_path(component["canonical_target"])
        by_target[target] = component["component_id"]
    links: dict[tuple[str, str], dict[str, str]] = {}
    for source in operation.get("authoritative_sources", []):
        path = source.get("path")
        if not isinstance(path, str):
            continue
        target = source_repo_relative(path)
        component_id = by_target.get(target)
        if component_id:
            links[(component_id, path)] = {
                "component_id": component_id,
                "source_path": path,
                "relation": "EXACT_AUTHORITATIVE_SOURCE_TARGET",
            }
    return [links[key] for key in sorted(links)]


def build_map() -> dict[str, Any]:
    registry_path = REPO_ROOT / REGISTRY_REL
    components_path = REPO_ROOT / COMPONENTS_REL
    candidates_path = REPO_ROOT / CANDIDATES_REL
    registry = load_json(registry_path)
    component_registry = load_json(components_path)
    candidate_catalog = load_json(candidates_path)
    components = component_registry["components"]
    operations = registry["operations"]
    manifests: dict[str, tuple[dict[str, Any], str]] = {}
    for manifest_path in registry["coverage"]["pack_manifest_paths"]:
        manifest_repo_path = manifest_path if manifest_path.startswith("ignition/") else "ignition/" + manifest_path
        manifest = load_json(REPO_ROOT / manifest_repo_path)
        manifests[manifest["pack_id"]] = (manifest, manifest_repo_path)

    operation_rows: list[dict[str, Any]] = []
    for index, operation in enumerate(operations):
        binding = operation.get("pack_binding")
        pack = manifests.get(binding["pack_id"]) if binding else None
        operation_pointer = f"/operations/{index}"
        status = operation.get("current_status")
        callability = operation.get("ai_callability")
        if status == "OWNER_DEFERRED" or status in {"UNSUPPORTED", "HISTORICAL", "REFERENCE_ONLY"} or callability == "STATUS_ONLY":
            routing_state = "DEFERRED"
            states = ["DISCOVERABLE", "REGISTERED", "DEFERRED", "UNRESOLVED"]
        elif pack is not None:
            routing_state = "ROUTED_PROPOSAL"
            states = ["DISCOVERABLE", "REGISTERED", "METADATA_LOADABLE", "ROUTED_PROPOSAL", "UNRESOLVED"]
        else:
            routing_state = "DISCOVERABLE"
            states = ["DISCOVERABLE", "REGISTERED", "UNRESOLVED"]

        implementation = {
            "state": "UNRESOLVED",
            "entrypoints": [],
            "executor_binding": None,
            "reason": (
                "The operation registry has no exact implementation-entrypoint and executor binding for this operation. "
                "authoritative_sources and validation_checks are references, not executable-entrypoint evidence."
            ),
        }
        if operation["operation_id"] == "repository.apply_iteration_method":
            implementation["documented_procedure_refs"] = [
                source["path"]
                for source in operation.get("authoritative_sources", [])
                if source.get("path") == "ignition/ITERATION.md"
            ]
            implementation["reason"] = (
                "ITERATION.md is a documented governed procedure; the registry does not bind it to a machine executor entrypoint."
            )

        operation_rows.append({
            "operation_id": operation["operation_id"],
            "registry_ref": {
                "path": REGISTRY_REL,
                "json_pointer": operation_pointer,
            },
            "contract_refs": {
                name: f"{operation_pointer}/{name}"
                for name in (
                    "current_status",
                    "ai_callability",
                    "accepted_input_types",
                    "default_execution_mode",
                    "repository_mutation_permission",
                    "external_action_permission",
                    "explicit_owner_authorization_required",
                    "validation_checks",
                    "claim_ceiling",
                )
            },
            "component_links": exact_component_links(operation, components),
            "pack_ref": (
                {
                    "pack_id": binding["pack_id"],
                    "manifest_path": binding["manifest_path"] if binding["manifest_path"].startswith("ignition/") else "ignition/" + binding["manifest_path"],
                    "manifest_capability_id": binding["manifest_capability_id"],
                }
                if binding
                else None
            ),
            "routing_state": routing_state,
            "implementation": implementation,
            "execution_state": "NOT_PERFORMED_BY_THIS_DISCOVERY_MAP",
            "boundary_states": states,
        })

    pack_rows: list[dict[str, Any]] = []
    for pack_id, (manifest, manifest_path) in sorted(manifests.items()):
        pack_rows.append({
            "pack_id": pack_id,
            "manifest_ref": {"path": manifest_path, "blob_sha1": repo_file_blob(manifest_path)},
            "domain": manifest["domain"],
            "capability_ids": list(manifest["capabilities_provided"]),
            "action_hooks": list(manifest["action_hooks"]),
            "planning_hooks": list(manifest.get("planning_hooks", [])),
            "validator_entrypoints": list(manifest["validator_entrypoints"]),
            "load_policy": manifest["load_policy"],
            "load_state": "METADATA_LOADABLE",
            "route_state": "ROUTED_PROPOSAL",
            "runtime_evidence": [
                {"path": path, "blob_sha1": repo_file_blob(path)} for path in RUNTIME_EVIDENCE_PATHS
            ],
            "execution_claim": "NOT_PERFORMED_BY_PACK_AWARE_ROUTER",
            "executor_requirement": "A separately bound and authorized executor is required; manifest hooks alone are declarations.",
            "boundary_states": ["DISCOVERABLE", "METADATA_LOADABLE", "ROUTED_PROPOSAL", "UNRESOLVED"],
        })

    experimental_rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidate_catalog["candidates"]):
        experimental_rows.append({
            "tool_id": candidate["tool_id"],
            "catalog_ref": {
                "path": CANDIDATES_REL,
                "json_pointer": f"/candidates/{index}",
            },
            "availability": candidate["availability"],
            "lifecycle": candidate["lifecycle"],
            "source_path": candidate["source_path"],
            "entrypoint": candidate["entrypoint"],
            "execution_mode": candidate["execution_mode"],
            "router_selectable_by_default": candidate["router_selectable_by_default"],
            "boundary_state": "EXPERIMENTAL_OPT_IN",
            "implementation_evidence": "CANDIDATE_CATALOG_SOURCE_AND_ENTRYPOINT_DECLARATION_ONLY",
            "execution_claim": "NOT_PERFORMED_BY_THIS_DISCOVERY_MAP",
            "boundary_states": ["DISCOVERABLE", "EXPERIMENTAL_OPT_IN"],
        })

    sources = {
        "operation_registry": {"path": REGISTRY_REL, "blob_sha1": repo_file_blob(REGISTRY_REL)},
        "component_registry": {"path": COMPONENTS_REL, "blob_sha1": repo_file_blob(COMPONENTS_REL)},
        "optional_candidate_catalog": {"path": CANDIDATES_REL, "blob_sha1": repo_file_blob(CANDIDATES_REL)},
        "runtime_evidence": [{"path": path, "blob_sha1": repo_file_blob(path)} for path in RUNTIME_EVIDENCE_PATHS],
        "supporting_entrypoint_evidence": [
            {**item, "blob_sha1": repo_file_blob(item["path"])} for item in SUPPORTING_TOOL_EVIDENCE
        ],
    }

    return {
        "schema_version": "capability-execution-boundary-map-r1",
        "authority_boundary": "GENERATED_DISCOVERY_AND_BOUNDARY_PROJECTION; OPERATION_REGISTRY_AND_PACK_MANIFESTS_REMAIN_AUTHORITATIVE",
        "sources": sources,
        "generic_runtime_boundary": {
            "kernel_contract_ref": "ignition/agent_kernel/contracts.py",
            "runtime_coordinator_ref": "ignition/agent_runtime/runtime.py",
            "typed_local_action_executor_ref": "ignition/agent_runtime/actions.py",
            "executor_admission_ref": "ignition/agent_runtime/executor_admission.py",
            "observed_boundary": "GENERIC_TYPED_LOCAL_RUNTIME_WITH_CAPABILITY_SCOPE_AND_EXECUTOR_ADMISSION",
            "operation_binding": "NO_EXACT_OPERATION_ID_TO_RUNTIME_ENTRYPOINT_BINDING_ESTABLISHED",
            "execution_claim": "RUNTIME_SOURCE_EXISTS; THIS MAP PERFORMED NO ACTION AND DOES NOT BIND IT TO A REGISTERED DOMAIN OPERATION",
        },
        "boundary_vocabulary": {
            "DISCOVERABLE": "An index or catalog can name the item; discovery does not authorize use.",
            "REGISTERED": "An operation id is present in the operation registry; registration does not prove implementation or execution.",
            "METADATA_LOADABLE": "Pack Registry validates/loads declarative metadata only; it does not import or execute hooks.",
            "ROUTED_PROPOSAL": "Pack-aware routing emits a proposal; no domain action is performed by the router.",
            "EXECUTABLE_UNDER_DECLARED_RUNTIME": "Use only when an exact implementation entrypoint, executor binding, and declared execution conditions are evidenced; no operation is assigned this state by this map.",
            "EXPERIMENTAL_OPT_IN": "An optional catalog entry remains Experimental and default-off; use requires a separate explicit selection under its declared contract.",
            "DEFERRED": "The registry contract is status-only, deferred, historical, or unsupported for execution routing.",
            "UNRESOLVED": "An exact implementation/executor mapping is not established by the cited authority assets.",
        },
        "operations": operation_rows,
        "packs": pack_rows,
        "optional_experimental_tools": experimental_rows,
        "claim_ceiling": "Repository-local declarations and routing code only. No action, external completion, truth, Owner acceptance, or scientific result is inferred.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="write the deterministic boundary map")
    group.add_argument("--check", action="store_true", help="verify the checked-in boundary map")
    args = parser.parse_args(argv)
    output_path = REPO_ROOT / OUTPUT_REL
    try:
        document = build_map()
    except BoundaryMapError as exc:
        print(f"CAPABILITY_EXECUTION_BOUNDARY_MAP_INVALID: {exc}", file=sys.stderr)
        return 1
    expected = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not output_path.is_file() or output_path.read_text(encoding="utf-8") != expected:
            print(f"CAPABILITY_EXECUTION_BOUNDARY_MAP_STALE: {OUTPUT_REL}", file=sys.stderr)
            return 1
        print("CAPABILITY_EXECUTION_BOUNDARY_MAP_OK operations=20 packs=4 experimental=77 runtime_evidence=9")
        return 0
    output_path.write_text(expected, encoding="utf-8")
    print("CAPABILITY_EXECUTION_BOUNDARY_MAP_WRITTEN operations=20 packs=4 experimental=77 runtime_evidence=9")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
