#!/usr/bin/env python3
"""Build/check the deterministic Current Surface Compiler snapshot input."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    from tools import iteration_boundary, task_identity
except ImportError:
    import iteration_boundary
    import task_identity


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
REGISTRY_PATH = ROOT / "data/operations/current-volatile-fact-registry-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/current-snapshot-r1.schema.json"
SNAPSHOT_PATH = ROOT / "data/operations/current-snapshot-r1.json"
CURRENT_FACTS_PATH = ROOT / "data/architecture/current-facts.json"
LIFECYCLE_PATH = ROOT / "data/operations/current-release-lifecycle-r1.json"
SEMANTICS_PATH = ROOT / "data/operations/iteration-boundary-semantics-r1.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def pointer_get(value: Any, pointer: str) -> Any:
    if pointer == "":
        return value
    current = value
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


def resolve(path: str) -> Path:
    candidate = (REPO_ROOT / path).resolve()
    candidate.relative_to(REPO_ROOT.resolve())
    return candidate


def registry_values(registry: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    values: dict[str, Any] = {}
    sources: dict[str, Any] = {}
    for fact in registry["facts"]:
        source = fact["canonical_source"]
        path = resolve(source["path"])
        value = pointer_get(load_json(path), source["json_pointer"])
        if fact.get("extractor") == "task_identity_ordinal":
            try:
                value = task_identity.parse_task_id(value)["ordinal"]
            except task_identity.TaskIdentityError as exc:
                raise ValueError(f"cannot derive ordinal for {fact['fact_id']}: {exc}") from exc
        if value is None and fact["null_behavior"] == "FAIL":
            raise ValueError(f"canonical fact is null: {fact['fact_id']}")
        values[fact["fact_id"]] = value
        sources[fact["fact_id"]] = source
    return values, sources


def source_paths(registry: dict[str, Any]) -> list[Path]:
    paths = {REGISTRY_PATH, SCHEMA_PATH, HERE, CURRENT_FACTS_PATH, LIFECYCLE_PATH, SEMANTICS_PATH, iteration_boundary.HERE, Path(task_identity.__file__).resolve()}
    paths.update(resolve(fact["canonical_source"]["path"]) for fact in registry["facts"])
    return sorted(paths, key=relative)


def source_digest(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(relative(path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        digest.update(b"\0")
    return digest.hexdigest()


def build_snapshot() -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH)
    values, _sources = registry_values(registry)
    identity = load_json(resolve("ignition/data/architecture/current-system-identity.json"))
    lineage = load_json(resolve("ignition/data/operations/current-task-lineage-status.json"))
    facts = load_json(CURRENT_FACTS_PATH)
    map_layout = load_json(resolve("ignition/data/architecture/interactive-system-map-layout.json"))
    lifecycle = load_json(LIFECYCLE_PATH)
    iteration = iteration_boundary.derive()
    if facts.get("schema_version") != "current-facts-r1":
        raise ValueError("current-facts projection schema is not current-facts-r1")
    current_task = lineage["current_task"]
    task_identity = lineage.get("task_identity")
    if not task_identity:
        raise ValueError("canonical task identity state is missing")
    if values["current_task_id"] != current_task["task_id"]:
        raise ValueError("registry current_task_id does not match task lineage source")
    if values["current_formal_task"] != task_identity["current_formal_task"]:
        raise ValueError("registry current_formal_task does not match task identity state")
    if values["latest_architecture_changing_task"] != task_identity["latest_architecture_changing_task"]:
        raise ValueError("registry architecture task does not match task identity state")
    if values["release_candidate_task"] != lifecycle["task_id"]:
        raise ValueError("registry release_candidate_task does not match lifecycle task")
    if values["publication_witness_task"] != task_identity["publication_witness_task"]:
        raise ValueError("registry publication_witness_task does not match task identity state")
    if values["current_map_version"] != map_layout["current_map_version"]:
        raise ValueError("registry current_map_version does not match map layout")
    if lifecycle["task_id"] != current_task["task_id"]:
        raise ValueError("release lifecycle task_id does not match current task")
    for key, expected in iteration.items():
        if key == "current_iteration_boundary_semantics":
            continue
        if values.get(key) != expected and key in values:
            raise ValueError(f"registry {key} does not match canonical derivation")
    if values.get("current_iteration_boundary") != iteration["current_iteration_boundary"]:
        raise ValueError("registry current_iteration_boundary is not the formal ordinal alias")
    if values.get("current_formal_task") != iteration["current_formal_task_id"]:
        raise ValueError("registry current_formal_task does not match iteration identity")
    if values.get("latest_architecture_changing_task") != iteration["latest_architecture_changing_task_id"]:
        raise ValueError("registry architecture task does not match iteration identity")

    spine = identity["current_architecture_identity"]["internal_control_spine"]
    control_text = identity["current_architecture_identity"]["control_plane_role"]
    overlay_specs = [
        {
            "overlay_id": "durability-lifecycle",
            "label": "Durability / Lifecycle",
            "marker": "Durability / Lifecycle",
            "source_paths": ["ignition/data/operations/durability", "ignition/docs/architecture/os-control-plane-r2.md"],
            "authority": "repository-local continuity and recovery projection",
            "status": "ACTIVE_BOUNDED_OVERLAY"
        },
        {
            "overlay_id": "steering-intent",
            "label": "Steering / Intent / Goal / Obligation",
            "marker": "Steering / Intent / Goal / Obligation",
            "source_paths": ["ignition/data/operations/steering/current-state-r1.json", "ignition/docs/architecture/os-steering-intent-r1.md"],
            "authority": "repository-local steering and explainability projection",
            "status": "ACTIVE_BOUNDED_OVERLAY"
        },
        {
            "overlay_id": "structural-governance",
            "label": "Structural Governance Surface",
            "marker": "Structural Governance Surface",
            "source_paths": ["ignition/data/epistemic-governance/soft-governance-non-authority-invariant-r0.json", "ignition/docs/architecture/esi-human-surface-r0.md"],
            "authority": "advisory-only reading and experiment context",
            "status": "ACTIVE_ADVISORY_ONLY"
        }
    ]
    overlays = [
        {key: spec[key] for key in ("overlay_id", "label", "source_paths", "authority", "status")}
        for spec in overlay_specs
        if spec["marker"] in spine or spec["marker"] in control_text
    ]
    lineages = lineage.get("lineages", [])
    predecessor = lineages[0]["predecessor"] if lineages else {}
    successor = lineages[0]["successor"] if lineages else {}
    snapshot = {
        "schema_version": "current-snapshot-r1",
        "contract_id": "CURRENT_SURFACE_NO_SPLIT_BRAIN_INVARIANT",
        "source_policy": {
            "kind": "DETERMINISTIC_CANONICAL_SOURCE_PROJECTION",
            "commit_sha_policy": "Exact Git SHA is intentionally omitted; source digest is deterministic and release SHA belongs to the receipt.",
            "registry_path": relative(REGISTRY_PATH)
        },
        "generated_from_source_digest": source_digest(source_paths(registry)),
        "identity": {
            "epoch": values["current_identity_epoch"],
            "system_role": values["current_system_role"],
            "driver_role": identity["current_architecture_identity"]["driver_role"],
            "external_executor_role": identity["current_architecture_identity"]["external_executor_role"],
            "reference_executor_role": identity["current_architecture_identity"]["reference_executor_role"]
        },
        "current_method_version": values["current_method_version"],
        "current_task": dict(current_task),
        "iteration_identity": dict(iteration),
        "task_identity": {
            "current_formal_task": values["current_formal_task"],
            "latest_architecture_changing_task": values["latest_architecture_changing_task"],
            "release_candidate_task": values["release_candidate_task"],
            "publication_witness_task": values["publication_witness_task"],
            "previous_canonical_current_task": task_identity["previous_canonical_current_task"],
            "previous_formal_task": task_identity["previous_formal_task"]
        },
        "latest_architecture_changing_task": values["latest_architecture_changing_task"],
        "map": {
            "current_version": values["current_map_version"],
            "historical_versions": [values["historical_map_version"]],
            "source_path": "ignition/data/architecture/interactive-system-map-layout.json",
            "projection_status": "CURRENT_DERIVED_PROJECTION"
        },
        "engineering_status": {
            "current_state_status": values["current_state_status"],
            "epistemically_accepted": values["epistemic_acceptance"]
        },
        "task_lineage": {
            "current_task_id": current_task["task_id"],
            "current_task_status": current_task["execution_status"],
            "predecessor_status": predecessor.get("canonical_status", "UNKNOWN"),
            "predecessor_requirement_lineage": predecessor.get("requirement_lineage_status", "UNKNOWN"),
            "successor_status": successor.get("execution_status", "UNKNOWN"),
            "claim_ceiling": lineage["claim_ceiling"]
        },
        "release_lifecycle": {
            "task_id": lifecycle["task_id"],
            "content_phase": lifecycle["content_phase"],
            "required_publication_ref": lifecycle["required_publication_ref"],
            "publication_authority": lifecycle["publication_authority"],
            "embedded_publication_assertion": lifecycle["embedded_publication_assertion"],
            "post_publication_check_required": lifecycle["post_publication_remote_check_required"]
        },
        "active_architecture_overlays": overlays,
        "live_external_ceiling": facts["facts"]["federation"]["live_invocation_ceiling"],
        "live_state_dimensions": facts["facts"]["federation"]["live_state_dimensions"],
        "live_attempt_projection": facts["facts"]["federation"]["live_attempt_projection"],
        "architecture_counts": dict(facts["facts"]["architecture"]),
        "claim_ceiling": "Deterministic repository-local Current projection only; no Owner authority, external truth, production readiness or epistemic upgrade."
    }
    return snapshot


def render(snapshot: dict[str, Any]) -> bytes:
    return (json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def check() -> list[str]:
    expected = render(build_snapshot())
    if not SNAPSHOT_PATH.is_file():
        return [f"missing snapshot: {relative(SNAPSHOT_PATH)}"]
    return [] if SNAPSHOT_PATH.read_bytes() == expected else [f"stale snapshot: {relative(SNAPSHOT_PATH)}"]


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write:
        SNAPSHOT_PATH.write_bytes(render(build_snapshot()))
        print(f"CURRENT_SNAPSHOT_WRITTEN path={relative(SNAPSHOT_PATH)}")
        return 0
    errors = check()
    if errors:
        print("CURRENT_SNAPSHOT_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("CURRENT_SNAPSHOT_DETERMINISTIC_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
