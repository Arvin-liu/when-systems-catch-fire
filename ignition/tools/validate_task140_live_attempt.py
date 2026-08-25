#!/usr/bin/env python3
"""Independently validate Task140's exact live-attempt binding and fail-closed result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent_federation.live_attempt_ledger import LiveAttemptLedger
from agent_federation.live_current_projection import validate_projection


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
TASK_ID = "IGNITION-20260826-140"
DISPATCH_ID = "dispatch-140-live-01"
ATTEMPT_ID = "attempt-140-live-01"
EXECUTOR_ID = "external.codex"
LEDGER_PATH = ROOT / "data/operations/iterations/139/live-attempt-ledger.jsonl"
PROJECTION_PATH = ROOT / "data/operations/iterations/140/live-current-projection-r2.json"
ARTIFACT_PATH = ROOT / "data/operations/iterations/140/step11-live-attempt.json"
OBSERVATION_EVENTS_PATH = ROOT / "data/operations/iterations/140/live-observation-events-r1.jsonl"
STEP09_PATH = ROOT / "data/operations/iterations/140/step09-local-executor-census-and-selection.json"


class Task140ValidationError(RuntimeError):
    """Raised when exact post-attempt binding or fail-closed Current diverges."""


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_validation() -> dict[str, Any]:
    artifact = _load(ARTIFACT_PATH)
    projection = validate_projection(_load(PROJECTION_PATH))
    census = _load(STEP09_PATH)
    records = LiveAttemptLedger(LEDGER_PATH).records()
    matches = [
        record for record in records
        if record["task_id"] == TASK_ID
        and record["dispatch_id"] == DISPATCH_ID
        and record["attempt_id"] == ATTEMPT_ID
    ]
    if len(matches) != 1:
        raise Task140ValidationError(f"expected exactly one Task140 live record, observed {len(matches)}")
    record = matches[0]
    expected_lease_digest = artifact["result"]["lease_digest"]
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
        raise Task140ValidationError("ledger record is not exactly bound to the Step11 task, dispatch, executor and lease")

    process = record["process"]
    events = record["public_events"]
    structured = record["structured_result"]
    validator = record["validator"]
    if process != {
        "cleanup_status": "CLEANED",
        "process_group_status": "CONFIRMED_GONE",
        "return_code": 1,
        "signal": None,
        "state": "MALFORMED_RESULT",
        "timed_out": False,
    }:
        raise Task140ValidationError("live process result or cleanup evidence is not the recorded bounded result")
    if record["evidence_completeness"] != "COMPLETE" or events["capture_completeness"] != "COMPLETE":
        raise Task140ValidationError("durable capture is not complete")
    if structured != {"digest": "NOT_APPLICABLE", "present": False, "ref": None}:
        raise Task140ValidationError("malformed live result unexpectedly contains a structured result")
    if validator["status"] != "NOT_RUN":
        raise Task140ValidationError("validator status is not the expected no-result boundary")
    if record["reconciliation_status"] != "NOT_REQUIRED":
        raise Task140ValidationError("complete malformed result was incorrectly left in reconciliation")
    if record["workspace_digest_before"] != record["workspace_digest_after"]:
        raise Task140ValidationError("read-only fixture changed across the live attempt")

    result = artifact["result"]
    if result["live_dispatch_calls"] != 1 or result["live_inference_started"] is not True:
        raise Task140ValidationError("Step11 does not prove that exactly one live process crossed the dispatch boundary")
    if result["process"] != {
        "elapsed_seconds": result["process"]["elapsed_seconds"],
        "output_truncated": False,
        "process_group_status": "CONFIRMED_GONE",
        "return_code": 1,
        "timed_out": False,
    }:
        raise Task140ValidationError("Step11 process observation disagrees with the canonical ledger")
    if result["capture_completeness"] != "COMPLETE" or result["structured_result"] is not None:
        raise Task140ValidationError("Step11 capture/result boundary is not fail-closed")
    policy = artifact["bounded_attempt_policy"]
    if policy["blind_retry"] != "FORBIDDEN" or policy["max_attempts_per_executor_family"] != 1:
        raise Task140ValidationError("bounded attempt policy does not forbid same-family blind retry")

    source = projection["source_ledger"]
    if source["record_count"] != len(records) or source["head_hash"] != records[-1]["record_hash"]:
        raise Task140ValidationError("Current projection is not derived from the current ledger head")
    if source["observation_events"]["path"] != "ignition/data/operations/iterations/140/live-observation-events-r1.jsonl":
        raise Task140ValidationError("typed observation overlay is not the bound source")
    latest = projection["latest_attempt_per_executor"][EXECUTOR_ID]
    expected_typed = {
        "attempt_id": ATTEMPT_ID,
        "state": "MALFORMED_RESULT",
        "probe_return_code": 0,
        "transport_return_code": 0,
        "public_probe_calls": 2,
        "live_dispatch_calls": 1,
        "live_dispatch_started": True,
        "live_process_started": True,
        "live_process_return_code": 1,
        "capture_initialized": True,
        "structured_result_present": False,
        "validator_status": "NOT_RUN",
        "legacy_record_return_code_preserved": 1,
        "legacy_return_code_scope": "LIVE_PROCESS_RETURN_CODE_OBSERVED",
    }
    for key, expected in expected_typed.items():
        if latest.get(key) != expected:
            raise Task140ValidationError(f"typed projection field {key!r} is not exactly {expected!r}")
    counts = projection["counts"]
    if counts["total_attempts"] != 6 or counts["validated_completion_count"] != 0 or counts["unreconciled_count"] != 0:
        raise Task140ValidationError("Current counts do not preserve six attempts, zero validated completions and zero unreconciled attempts")
    if projection["obligation"]["state"] != "OPEN":
        raise Task140ValidationError("Current closed the live obligation without a validated completion")
    if census["selection"]["selection_status"] != "SELECTED" or census["selection"]["selected_executor_id"] != EXECUTOR_ID:
        raise Task140ValidationError("Step09 census does not prove the selected executor family")

    return {
        "schema_version": "ignition-140-step12-independent-validation-r1",
        "task_id": TASK_ID,
        "status": "PASS_FAIL_CLOSED",
        "exact_binding": binding,
        "record_sequence": record["sequence"],
        "record_hash": record["record_hash"],
        "projection_digest": projection["projection_digest"],
        "ledger_head_hash": source["head_hash"],
        "observation_event_head_hash": source["observation_events"]["head_hash"],
        "counts": counts,
        "obligation": projection["obligation"],
        "next_eligible_action": projection["next_eligible_action"],
        "live_process_boundary": {
            "probe_return_code": latest["probe_return_code"],
            "transport_return_code": latest["transport_return_code"],
            "live_process_return_code": latest["live_process_return_code"],
            "capture_completeness": latest["capture_completeness"],
            "structured_result_present": latest["structured_result_present"],
            "validator_status": latest["validator_status"],
        },
        "independent_executor_result_validator": "NOT_RUN_NO_EXACT_PUBLIC_RESULT",
        "completion_claim": False,
        "retry": "NOT_AUTHORIZED_SAME_FAMILY",
        "second_family_admission": "NO_SAFE_CANDIDATE_IN_FRESH_CENSUS",
        "claim_ceiling": "Independent repository-local exact-binding and typed live-process validation only; the malformed process result is not a validated completion, and no external effect, production readiness, Owner acceptance or epistemic upgrade is inferred.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if not args.check and not args.write:
        parser.error("--check or --write is required")
    try:
        value = run_validation()
        if args.write:
            output = ROOT / "data/operations/iterations/140/step12-independent-validation.json"
            output.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    except (Task140ValidationError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"TASK140_POST_ATTEMPT_INVALID\n- {type(exc).__name__}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
