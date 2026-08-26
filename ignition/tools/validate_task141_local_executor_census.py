#!/usr/bin/env python3
"""Validate the Task141 dynamic census and its policy freeze inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent_federation.local_executor_census import validate_path


ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "data/operations/iterations/141/local-executor-census-r1.json"
SELECTION = ROOT / "data/operations/iterations/141/step08-local-executor-census.json"


class Task141ExecutorCensusError(RuntimeError):
    """Raised when the fresh census is incomplete or policy is widened."""


def run_validation() -> dict[str, Any]:
    census_summary = validate_path(CENSUS, expected_task_id="IGNITION-20260826-141", expected_step="08")
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    if selection.get("status") != "PASS" or selection.get("task_id") != "IGNITION-20260826-141" or selection.get("step") != "08":
        raise Task141ExecutorCensusError("Step08 selection artifact is not PASS/bound")
    candidates = {item["executor_id"]: item for item in census["candidates"] if item["kind"] == "AGENTIC_EXECUTOR"}
    if set(candidates) != {"external.gemini", "external.codex", "external.hermes", "external.openclaw", "external.github-copilot-cli"}:
        raise Task141ExecutorCensusError("required Agentic Executor families are not all present")
    if candidates["external.codex"]["admission_status"] != "ADMITTED":
        raise Task141ExecutorCensusError("fresh Codex capability admission disappeared")
    if candidates["external.codex"]["policy_blockers"] != ["TASK140_ROOT_CAUSE_NOT_CONFIRMED_SAME_FAMILY_RETRY_FORBIDDEN"]:
        raise Task141ExecutorCensusError("Codex blind-retry policy blocker is missing")
    policy = selection["policy"]
    if policy["codex_same_family_retry"] != "FORBIDDEN_BLIND_RETRY":
        raise Task141ExecutorCensusError("Codex same-family retry is not frozen")
    if policy["live_selection_status"] != "NO_AUTHORIZED_FAMILY" or policy["policy_excluded_executor_ids"] != ["external.codex"]:
        raise Task141ExecutorCensusError("live policy selection widened beyond the fresh census")
    safety = selection["safety"]
    if any(value is not False for key, value in safety.items() if key in {"secret_content_read", "auth_content_copied", "configuration_changed", "billing_changed", "install_or_upgrade_performed", "live_inference_started", "workspace_modified"}):
        raise Task141ExecutorCensusError("census safety boundary is not closed")
    return {
        "status": "PASS",
        "candidate_count": census_summary["candidate_count"],
        "agentic_executor_count": census_summary["agentic_executor_count"],
        "admitted_executor_count": census_summary["admitted_executor_count"],
        "capability_selected_executor_id": census["selection"]["selected_executor_id"],
        "live_selection_status": policy["live_selection_status"],
        "codex_same_family_retry": policy["codex_same_family_retry"],
        "live_inference_started": safety["live_inference_started"],
        "claim_ceiling": selection["claim_ceiling"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    print(json.dumps(run_validation(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
