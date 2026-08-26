#!/usr/bin/env python3
"""Validate and record Task141 Step14 Current/architecture synchronization."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from agent_federation.live_current_projection import validate_projection
from tools import build_current_snapshot
from tools import generate_current_facts
from tools import validate_current_release_lifecycle
from tools import validate_current_state_sync
from tools import validate_current_task_lineage
from tools import validate_current_volatile_fact_registry


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
TASK_ID = "IGNITION-20260826-141"
IDENTITY_PATH = ROOT / "data/architecture/current-system-identity.json"
LINEAGE_PATH = ROOT / "data/operations/current-task-lineage-status.json"
LIFECYCLE_PATH = ROOT / "data/operations/current-release-lifecycle-r1.json"
FACTS_PATH = ROOT / "data/architecture/current-facts.json"
SNAPSHOT_PATH = ROOT / "data/operations/current-snapshot-r1.json"
MAP_LAYOUT_PATH = ROOT / "data/architecture/interactive-system-map-layout.json"
MAP_PATH = ROOT / "data/architecture/interactive-system-map.json"
PROJECTION_PATH = ROOT / "data/operations/iterations/141/live-current-projection-r3.json"
RECEIPT_PATH = ROOT / "data/operations/iterations/141/current-state-sync-receipt.json"
OUTPUT_PATH = ROOT / "data/operations/iterations/141/step14-current-state-sync.json"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def compiler_errors() -> list[str]:
    contract = load(ROOT / "data/operations/current-surface-block-contract-r1.json")
    errors: list[str] = []
    snapshot = build_current_snapshot.build_snapshot()
    for surface in contract["surfaces"]:
        path = REPO_ROOT / surface["path"]
        from tools import current_surface_compiler

        if path.read_text(encoding="utf-8") != current_surface_compiler.compile_surface(path.read_text(encoding="utf-8"), surface, snapshot):
            errors.append(f"stale current surface: {surface['surface_id']}")
    return errors


def build_report() -> dict[str, Any]:
    identity = load(IDENTITY_PATH)
    lineage = load(LINEAGE_PATH)
    lifecycle = load(LIFECYCLE_PATH)
    facts = load(FACTS_PATH)
    snapshot = load(SNAPSHOT_PATH)
    layout = load(MAP_LAYOUT_PATH)
    materialized_map = load(MAP_PATH)
    projection = validate_projection(load(PROJECTION_PATH))
    receipt = load(RECEIPT_PATH)
    errors: list[str] = []

    errors.extend(validate_current_state_sync.run_check(receipt_path=RECEIPT_PATH, check_fixtures=True))
    errors.extend(validate_current_task_lineage.validate())
    errors.extend(validate_current_release_lifecycle.validate())
    errors.extend(validate_current_volatile_fact_registry.validate())
    errors.extend(generate_current_facts.check())
    errors.extend(build_current_snapshot.check())
    errors.extend(compiler_errors())

    expected_identity = {
        "identity_epoch": "os-control-plane-r7-live-state-semantics-structured-result-reliability-r1",
        "current_formal_task_id": TASK_ID,
        "current_formal_task_ordinal": 141,
        "latest_architecture_changing_task_id": TASK_ID,
        "latest_architecture_task_ordinal": 141,
        "current_iteration_boundary": 141,
        "current_map_version": "0.15.0",
        "historical_map_version": "0.14.0",
    }
    for key, value in expected_identity.items():
        observed = identity.get(key)
        if key == "current_map_version":
            observed = layout.get("current_map_version")
        elif key == "historical_map_version":
            observed = layout.get("historical_map_version")
        if observed != value:
            errors.append(f"identity mismatch {key}: {observed!r} != {value!r}")
    if materialized_map.get("map_version") != layout.get("current_map_version") or materialized_map.get("historical_map_version") != layout.get("historical_map_version"):
        errors.append("materialized map is not bound to layout identity")
    if lineage["current_task"]["task_id"] != TASK_ID or lineage["current_task"]["execution_status"] != "IN_PROGRESS" or lineage["current_task"]["terminal"] is not False:
        errors.append("current task must be Task141 IN_PROGRESS and non-terminal at Step14")
    if lifecycle["task_id"] != TASK_ID or lifecycle["content_phase"] != "RUNNING" or lifecycle["current_task_terminal"] is not False:
        errors.append("current lifecycle must be Task141 RUNNING and non-terminal at Step14")
    expected_dimensions = {
        "live_dispatch_observation_status": "OBSERVED",
        "live_process_observation_status": "OBSERVED",
        "inference_observation_status": "NOT_OBSERVED",
        "validated_completion_status": "NOT_VALIDATED",
        "reconciliation_blocker_status": "NONE",
        "next_eligible_action": "RUN_DYNAMIC_EXECUTOR_ADMISSION",
    }
    for key, value in expected_dimensions.items():
        if projection["live_state_dimensions"].get(key) != value:
            errors.append(f"live dimension mismatch {key}")
    if projection["current_live_ceiling"] != "LIVE_EXTERNAL_PROCESS_OBSERVED_NO_VALIDATED_COMPLETION":
        errors.append("R3 compatibility ceiling does not acknowledge observed process")
    if projection["counts"] != {
        "complete_evidence_count": 4,
        "incomplete_evidence_count": 2,
        "observation_incomplete_count": 2,
        "total_attempts": 6,
        "unreconciled_count": 0,
        "validated_completion_count": 0,
    }:
        errors.append("Task141 projection counts drifted")
    if receipt.get("architecture_identity_impact") != "ARCHITECTURE_CHANGED" or len(receipt.get("surface_decisions", [])) != 11:
        errors.append("Step14 receipt does not close the architecture surface set")

    validator_status = {
        "current_state_sync": "PASS" if not validate_current_state_sync.run_check(receipt_path=RECEIPT_PATH, check_fixtures=True) else "FAIL",
        "current_task_lineage": "PASS" if not validate_current_task_lineage.validate() else "FAIL",
        "current_release_lifecycle": "PASS" if not validate_current_release_lifecycle.validate() else "FAIL",
        "current_volatile_fact_registry": "PASS" if not validate_current_volatile_fact_registry.validate() else "FAIL",
        "current_facts_determinism": "PASS" if not generate_current_facts.check() else "FAIL",
        "current_snapshot_determinism": "PASS" if not build_current_snapshot.check() else "FAIL",
        "current_surface_compiler": "PASS" if not compiler_errors() else "FAIL",
    }
    return {
        "schema_version": "ignition-141-step14-current-state-sync-r1",
        "task_id": TASK_ID,
        "step": "14",
        "status": "PASS" if not errors else "FAIL",
        "architecture_identity_impact": receipt["architecture_identity_impact"],
        "current_identity": {key: identity[key] for key in ("identity_epoch", "current_formal_task_id", "current_formal_task_ordinal", "latest_architecture_changing_task_id", "latest_architecture_task_ordinal", "current_iteration_boundary")},
        "map_identity": {"current_map_version": layout["current_map_version"], "historical_map_version": layout["historical_map_version"], "materialized_map_version": materialized_map["map_version"]},
        "source_projections": {
            "live_projection_path": relative(PROJECTION_PATH),
            "live_projection_digest": projection["projection_digest"],
            "live_state_dimensions": projection["live_state_dimensions"],
            "current_facts_digest": sha256(FACTS_PATH),
            "current_snapshot_digest": sha256(SNAPSHOT_PATH),
            "current_snapshot_source_digest": snapshot["generated_from_source_digest"],
        },
        "live_projection_counts": projection["counts"],
        "surface_sync": {
            "receipt_path": relative(RECEIPT_PATH),
            "required_surface_count": len(identity["required_sync_surfaces"]),
            "changed_surface_count": sum(1 for item in receipt["surface_decisions"] if item["decision"] == "CHANGE"),
            "identity_contract_changed": receipt.get("identity_contract_changed"),
            "system_map_sync": receipt["system_map_sync"]["decision"],
            "state_changelog_delta": receipt["state_changelog_delta"]["decision"],
            "surface_sync_complete": receipt.get("surface_sync_complete"),
        },
        "validation": validator_status,
        "errors": errors,
        "claim_ceiling": "Task141 repository-local Current/architecture synchronization and live-state semantic projection evidence only; no validated live completion, external truth, production readiness, Owner acceptance, formal publication or epistemic acceptance is inferred.",
    }


def render(report: dict[str, Any]) -> bytes:
    return (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build_report()
    if args.write:
        OUTPUT_PATH.write_bytes(render(report))
        print(f"TASK141_STEP14_CURRENT_STATE_SYNC_WRITTEN status={report['status']} path={relative(OUTPUT_PATH)}")
        return 0 if report["status"] == "PASS" else 1
    if not OUTPUT_PATH.is_file():
        print("TASK141_STEP14_CURRENT_STATE_SYNC_INVALID\n- missing persisted artifact")
        return 1
    if OUTPUT_PATH.read_bytes() != render(report):
        print("TASK141_STEP14_CURRENT_STATE_SYNC_INVALID\n- persisted artifact is stale")
        return 1
    print(f"TASK141_STEP14_CURRENT_STATE_SYNC_OK status={report['status']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
