#!/usr/bin/env python3
"""Record Task140 terminal-task / open-live-obligation semantics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent_federation.live_current_projection import validate_projection


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
TASK_ID = "IGNITION-20260826-140"
LINEAGE_PATH = ROOT / "data/operations/current-task-lineage-status.json"
LIFECYCLE_PATH = ROOT / "data/operations/current-release-lifecycle-r1.json"
PROJECTION_PATH = ROOT / "data/operations/iterations/140/live-current-projection-r2.json"
OUTPUT_PATH = ROOT / "data/operations/iterations/140/step14-current-terminal-semantics.json"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build() -> dict[str, Any]:
    lineage = load(LINEAGE_PATH)
    lifecycle = load(LIFECYCLE_PATH)
    projection = validate_projection(load(PROJECTION_PATH))
    task = lineage["current_task"]
    if task["task_id"] != TASK_ID or task["execution_status"] != "COMPLETED_WITH_CLASSIFIED_RESIDUALS" or task["terminal"] is not True:
        raise ValueError("Task140 current task is not terminal classified-residual state")
    if lifecycle["task_id"] != TASK_ID or lifecycle["content_phase"] != "RELEASE_READY" or lifecycle["current_task_terminal"] is not True:
        raise ValueError("Task140 lifecycle is not RELEASE_READY terminal state")
    if projection["counts"]["validated_completion_count"] != 0 or projection["counts"]["unreconciled_count"] != 0:
        raise ValueError("terminal semantics require zero validated completions and zero unreconciled attempts")
    if projection["obligation"]["state"] != "OPEN":
        raise ValueError("live obligation must remain OPEN without validated completion")
    if projection["next_eligible_action"]["action"] != "RUN_DYNAMIC_EXECUTOR_ADMISSION":
        raise ValueError("next live action must remain projection-derived dynamic admission")
    return {
        "schema_version": "ignition-140-step14-current-terminal-semantics-r1",
        "task_id": TASK_ID,
        "status": "PASS",
        "task_terminal": {
            "execution_status": task["execution_status"],
            "terminal": task["terminal"],
            "content_phase": lifecycle["content_phase"],
            "current_task_terminal": lifecycle["current_task_terminal"],
        },
        "current_state_ceiling": {
            "current_state_status": lineage["current_state"]["current_state_status"],
            "epistemically_accepted": lineage["current_state"]["epistemically_accepted"],
        },
        "live_obligation_transition": {
            "task_terminalization": "COMPLETED_WITH_CLASSIFIED_RESIDUALS",
            "live_obligation_state": projection["obligation"]["state"],
            "validated_completion_count": projection["counts"]["validated_completion_count"],
            "unreconciled_count": projection["counts"]["unreconciled_count"],
            "observation_incomplete_count": projection["counts"]["observation_incomplete_count"],
            "next_action": projection["next_eligible_action"]["action"],
            "reason_source": "ignition/data/operations/iterations/140/live-current-projection-r2.json",
        },
        "projection_digest": projection["projection_digest"],
        "identity": {
            "current_formal_task": lineage["task_identity"]["current_formal_task"],
            "latest_architecture_changing_task": lineage["task_identity"]["latest_architecture_changing_task"],
            "current_formal_task_ordinal": 140,
        },
        "historical_lineage_guard": {
            "task125_file_status": lineage["lineages"][0]["predecessor"]["task_file_status"],
            "task125_requirement_lineage_status": lineage["lineages"][0]["predecessor"]["requirement_lineage_status"],
        },
        "claim_ceiling": "Task140 repository-local terminal task and open live-obligation transition only; no validated live completion, external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        result = build()
        if args.write:
            OUTPUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(f"TASK140_TERMINAL_SEMANTICS_INVALID\n- {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
