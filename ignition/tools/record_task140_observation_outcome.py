#!/usr/bin/env python3
"""Record the typed observation outcome for the one Task140 live attempt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_federation.live_attempt_ledger import LiveAttemptLedger
from agent_federation.live_observation_events import LiveObservationEventLedger


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
TASK_ID = "IGNITION-20260826-140"
ATTEMPT_ID = "attempt-140-live-01"
DISPATCH_ID = "dispatch-140-live-01"
LEDGER_PATH = ROOT / "data/operations/iterations/139/live-attempt-ledger.jsonl"
EVENT_PATH = ROOT / "data/operations/iterations/140/live-observation-events-r1.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if not args.write:
        parser.error("--write is required")
    records = LiveAttemptLedger(LEDGER_PATH).records()
    matches = [record for record in records if record["task_id"] == TASK_ID and record["attempt_id"] == ATTEMPT_ID and record["dispatch_id"] == DISPATCH_ID]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one Task140 attempt, observed {len(matches)}")
    record = matches[0]
    if record["process"]["state"] != "MALFORMED_RESULT" or record["process"]["return_code"] != 1:
        raise SystemExit("Task140 attempt is not the observed malformed-result exit-1 boundary")
    if record["public_events"]["capture_completeness"] != "COMPLETE":
        raise SystemExit("Task140 attempt capture is not complete")
    outcome = {
        "schema_version": "live-observation-outcome-r1",
        "observation_outcome_type": "LIVE_PROCESS_OBSERVED",
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
    event = {
        "task_id": TASK_ID,
        "dispatch_id": DISPATCH_ID,
        "attempt_id": ATTEMPT_ID,
        "prior_record_hash": record["record_hash"],
        "observation_outcome": outcome,
        "claim_ceiling": "Typed Task140 process observation only; the observed nonzero process result has no structured result or validator PASS and is not a validated completion or external-effect claim.",
    }
    normalized = LiveObservationEventLedger(EVENT_PATH).append(event, expected_task_id=TASK_ID, expected_attempt_id=ATTEMPT_ID)
    print(json.dumps({"path": str(EVENT_PATH.relative_to(ROOT.parent)), "event_hash": normalized["event_hash"], "prior_record_hash": record["record_hash"], "observation_outcome": outcome}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
