#!/usr/bin/env python3
"""Independently validate Task139's exact post-attempt binding and Current state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent_federation.live_attempt_ledger import LiveAttemptLedger
from agent_federation.live_current_projection import validate_projection


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
TASK_ID = "IGNITION-20260825-139"
DISPATCH_ID = "dispatch-139-live-02"
ATTEMPT_ID = "attempt-139-live-02"
EXECUTOR_ID = "external.codex"
LEDGER_PATH = ROOT / "data/operations/iterations/139/live-attempt-ledger.jsonl"
PROJECTION_PATH = ROOT / "data/operations/iterations/139/live-current-projection-r1.json"
ARTIFACT_PATH = ROOT / "data/operations/iterations/139/step11-live-attempt.json"


class Task139ValidationError(RuntimeError):
    """Raised when exact post-attempt binding or fail-closed Current diverges."""


def run_validation() -> dict[str, Any]:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    projection = validate_projection(json.loads(PROJECTION_PATH.read_text(encoding="utf-8")))
    records = LiveAttemptLedger(LEDGER_PATH).records()
    matches = [
        record for record in records
        if record["task_id"] == TASK_ID and record["dispatch_id"] == DISPATCH_ID and record["attempt_id"] == ATTEMPT_ID
    ]
    if len(matches) != 1:
        raise Task139ValidationError(f"expected exactly one Task139 live record, observed {len(matches)}")
    record = matches[0]
    expected_lease_digest = artifact["fresh_selection"]["lease_digest"]
    binding = {
        "task_id": record["task_id"],
        "dispatch_id": record["dispatch_id"],
        "attempt_id": record["attempt_id"],
        "executor_id": record["executor_id"],
        "capability_lease_digest": record["capability_lease_digest"],
    }
    expected_binding = {
        "task_id": TASK_ID,
        "dispatch_id": DISPATCH_ID,
        "attempt_id": ATTEMPT_ID,
        "executor_id": EXECUTOR_ID,
        "capability_lease_digest": expected_lease_digest,
    }
    if binding != expected_binding:
        raise Task139ValidationError("ledger record is not exactly bound to the Step11 task, dispatch, executor and lease")
    if record["process"]["state"] != "OBSERVATION_INCOMPLETE":
        raise Task139ValidationError("incomplete host observation was not retained as OBSERVATION_INCOMPLETE")
    if record["evidence_completeness"] != "INCOMPLETE" or record["public_events"]["capture_completeness"] != "INCOMPLETE":
        raise Task139ValidationError("incomplete host observation was projected as complete evidence")
    if record["structured_result"]["present"] or record["validator"]["status"] == "PASS":
        raise Task139ValidationError("incomplete host observation claims a structured result or validator PASS")
    if record["reconciliation_status"] not in {"OPEN", "REQUIRES_RECONCILIATION"}:
        raise Task139ValidationError("incomplete host observation does not retain reconciliation")
    if artifact["single_boundary"]["live_dispatch_calls"] != 0 or artifact["single_boundary"]["live_inference_started"]:
        raise Task139ValidationError("Step11 artifact claims an external live process despite zero live dispatch calls")
    if artifact["single_boundary"]["retry"] != "NOT_RUN_NO_BLIND_RETRY":
        raise Task139ValidationError("Step11 retry policy is not fail-closed")
    if projection["source_ledger"]["record_count"] != len(records) or projection["source_ledger"]["head_hash"] != records[-1]["record_hash"]:
        raise Task139ValidationError("Current projection is not derived from the current ledger head")
    latest = projection["latest_attempt_per_executor"][EXECUTOR_ID]
    if latest["attempt_id"] != ATTEMPT_ID or latest["state"] != "OBSERVATION_INCOMPLETE":
        raise Task139ValidationError("Current latest Codex attempt is not the exact incomplete Task139 observation")
    if projection["counts"]["validated_completion_count"] != 0 or projection["obligation"]["state"] != "OPEN":
        raise Task139ValidationError("Current closed the live obligation without an exact validated result")
    return {
        "schema_version": "ignition-139-step12-independent-validation-r1",
        "task_id": TASK_ID,
        "status": "PASS_FAIL_CLOSED",
        "exact_binding": binding,
        "record_sequence": record["sequence"],
        "record_hash": record["record_hash"],
        "projection_digest": projection["projection_digest"],
        "ledger_head_hash": projection["source_ledger"]["head_hash"],
        "counts": projection["counts"],
        "obligation": projection["obligation"],
        "next_eligible_action": projection["next_eligible_action"],
        "independent_executor_result_validator": "NOT_RUN_NO_EXACT_PUBLIC_RESULT",
        "completion_claim": False,
        "retry": "NOT_AUTHORIZED",
        "claim_ceiling": "Independent repository-local exact-binding and deterministic Current validation only; the admitted lease and dispatch preparation are not a live result or validated completion."
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    try:
        print(json.dumps(run_validation(), sort_keys=True, separators=(",", ":")))
    except (Task139ValidationError, OSError, ValueError, KeyError) as exc:
        print(f"TASK139_POST_ATTEMPT_INVALID\n- {type(exc).__name__}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
