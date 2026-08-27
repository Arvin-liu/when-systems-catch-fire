#!/usr/bin/env python3
"""Validate the task-local phase parking record for IGNITION-143."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from agent_federation.live_current_projection import validate_projection
except ImportError:
    from ignition.agent_federation.live_current_projection import validate_projection


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
PHASE_PATH = ROOT / "data/operations/iterations/143/phase-closure-state-r1.json"
STEP_PATH = ROOT / "data/operations/iterations/143/step01-phase-closure.json"
REGISTRY_PATH = ROOT / "data/operations/open-obligation-registry-r1.json"
LINEAGE_PATH = ROOT / "data/operations/current-task-lineage-status.json"
LIFECYCLE_PATH = ROOT / "data/operations/formal-task-lifecycle-r1.json"
RELEASE_PATH = ROOT / "data/operations/current-release-lifecycle-r1.json"
PROJECTION_PATH = ROOT / "data/operations/iterations/141/live-current-projection-r3.json"
CENSUS_PATH = ROOT / "data/operations/iterations/142/local-executor-census-r2.json"
CONTRACT_PATH = ROOT / "data/operations/iterations/143/execution-contract-r1.json"

CURRENT_ACTION = "OWNER_DEFERRED_REQUIRES_EXPLICIT_REOPEN_AND_LOCAL_ENVIRONMENT_PREPARATION"
BASELINE_SHA = "b359580fe31866bc04eeb24911011e0baba9b66d"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate() -> list[str]:
    errors: list[str] = []
    paths = (PHASE_PATH, STEP_PATH, REGISTRY_PATH, LINEAGE_PATH, LIFECYCLE_PATH, RELEASE_PATH, PROJECTION_PATH, CENSUS_PATH, CONTRACT_PATH)
    for path in paths:
        if not path.is_file():
            errors.append(f"missing required phase-closure source: {path.relative_to(ROOT.parent)}")
    if errors:
        return errors

    phase = load(PHASE_PATH)
    step = load(STEP_PATH)
    registry = load(REGISTRY_PATH)
    lineage = load(LINEAGE_PATH)
    lifecycle = load(LIFECYCLE_PATH)
    release = load(RELEASE_PATH)
    projection = validate_projection(load(PROJECTION_PATH))
    census = load(CENSUS_PATH)
    contract = load(CONTRACT_PATH)

    if phase.get("schema_version") != "phase-closure-state-r1" or phase.get("task_id") != "IGNITION-20260827-143":
        errors.append("phase closure state identity is invalid")
    if phase.get("formal_baseline", {}).get("sha") != BASELINE_SHA:
        errors.append("phase closure baseline is not Task142 final main")
    architecture = phase.get("architecture", {})
    if architecture.get("phase") != "CLOSED" or architecture.get("mode") != "FROZEN_TASK142_BASELINE":
        errors.append("architecture phase is not closed on the frozen Task142 baseline")
    if architecture.get("latest_architecture_task") != "IGNITION-20260827-142" or architecture.get("current_map_version") != "0.16.0":
        errors.append("architecture resume identity is not the frozen Task142 identity")

    executor = phase.get("executor_qualification", {})
    if executor.get("phase") != "OWNER_DEFERRED" or executor.get("status") != "DEFERRED_NOT_FAILED":
        errors.append("executor qualification is not explicitly Owner-deferred")
    if executor.get("no_live_process_started") is not True or executor.get("no_automatic_resume") is not True:
        errors.append("phase closure does not enforce the no-live/no-automatic-resume boundary")
    if set(executor.get("resume_prerequisites", [])) != {"OWNER_EXPLICIT_REOPEN", "LOCAL_ENVIRONMENT_PREPARED_INSTALLED_AND_ATTESTED"}:
        errors.append("future executor resume prerequisites are incomplete")
    if executor.get("historical_census") != "ignition/data/operations/iterations/142/local-executor-census-r2.json":
        errors.append("executor census provenance is not preserved")
    blockers = "\n".join(executor.get("known_blocker_families", []))
    for family in ("Gemini", "Hermes", "Openclaw", "Codex"):
        if family not in blockers:
            errors.append(f"known blocker summary is missing {family}")

    publication = phase.get("publication_production", {})
    if publication.get("phase") != "ACTIVE" or publication.get("canonical_entrypoint") != "ignition/PUBLICATIONS/pointfire-results-book/README.md":
        errors.append("publication production is not active at the canonical entrypoint")

    live = next((row for row in registry.get("obligations", []) if row.get("obligation_id") == "LIVE_EXTERNAL_INVOCATION"), None)
    if registry.get("current_task_id") != "IGNITION-20260827-143" or live is None:
        errors.append("open-obligation registry is not carried to Task143")
    else:
        if live.get("current_status") != "OPEN" or live.get("operational_state") != "OWNER_DEFERRED":
            errors.append("live obligation is not OPEN/OWNER_DEFERRED")
        if live.get("next_eligible_action") != CURRENT_ACTION:
            errors.append("live obligation exposes a non-deferred current action")
        if live.get("owner_deferral", {}).get("historical_next_action") != projection["next_eligible_action"]["action"]:
            errors.append("live obligation does not preserve the historical projection action")
        if live.get("inherited_by_task") != "IGNITION-20260827-143":
            errors.append("live obligation is not inherited by Task143")

    expected_counts = {"total_attempts": 6, "validated_completion_count": 0, "unreconciled_count": 0, "observation_incomplete_count": 2}
    if any(projection["counts"].get(key) != value for key, value in expected_counts.items()):
        errors.append("historical live-attempt counts changed unexpectedly")
    if census.get("candidates") is None or len(census["candidates"]) != 14:
        errors.append("historical executor census is not preserved")
    if lineage.get("current_task", {}).get("task_id") != "IGNITION-20260827-143" or lineage.get("current_task", {}).get("execution_status") != "IN_PROGRESS":
        errors.append("current lineage is not the active Task143 publication task")
    if lineage.get("task_identity", {}).get("latest_architecture_changing_task") != "IGNITION-20260827-142":
        errors.append("Task143 incorrectly changes the latest architecture identity")
    if release.get("task_id") != "IGNITION-20260827-143" or release.get("content_phase") != "RUNNING" or release.get("current_task_terminal") is not False:
        errors.append("release lifecycle is not active for Task143")
    if contract.get("identity_impact") != "PRESENTATION_ONLY":
        errors.append("Task143 phase closure must remain presentation-only")
    task143 = step.get("task143_live_boundary", {})
    if step.get("result") != "PASS" or task143.get("external_agent_live_process_started") is not False or task143.get("external_agent_live_inference_started") is not False or task143.get("qualification_attempt_count") != 0:
        errors.append("Step01 records an impermissible Task143 external live activity")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    errors = validate()
    if errors:
        print("TASK143_PHASE_CLOSURE_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK143_PHASE_CLOSURE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
