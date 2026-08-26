#!/usr/bin/env python3
"""Validate Task140 historical preservation and the additive Task141 correction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent_federation.live_attempt_ledger import LiveAttemptLedger
from agent_federation.live_current_projection import validate_projection
from agent_federation.live_inference_observation_events import LiveInferenceObservationEventLedger


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "data/operations/iterations/139/live-attempt-ledger.jsonl"
OLD_PROJECTION_PATH = ROOT / "data/operations/iterations/140/live-current-projection-r2.json"
OLD_ATTEMPT_PATH = ROOT / "data/operations/iterations/140/step11-live-attempt.json"
CORRECTION_PATH = ROOT / "data/operations/iterations/141/live-inference-observation-events-r1.jsonl"


class Task140HistoricalCorrectionError(RuntimeError):
    """Raised when the additive correction or historical evidence diverges."""


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_validation() -> dict[str, Any]:
    records = LiveAttemptLedger(LEDGER_PATH).records()
    matches = [record for record in records if record["attempt_id"] == "attempt-140-live-01"]
    if len(matches) != 1:
        raise Task140HistoricalCorrectionError(f"expected one Task140 attempt, found {len(matches)}")
    record = matches[0]
    if record["task_id"] != "IGNITION-20260826-140" or record["dispatch_id"] != "dispatch-140-live-01":
        raise Task140HistoricalCorrectionError("Task140 binding changed")
    expected_process = {
        "cleanup_status": "CLEANED",
        "process_group_status": "CONFIRMED_GONE",
        "return_code": 1,
        "signal": None,
        "state": "MALFORMED_RESULT",
        "timed_out": False,
    }
    if record["process"] != expected_process:
        raise Task140HistoricalCorrectionError("Task140 process evidence changed")
    if record["evidence_completeness"] != "COMPLETE" or record["public_events"]["capture_completeness"] != "COMPLETE":
        raise Task140HistoricalCorrectionError("Task140 capture completeness changed")
    if record["structured_result"] != {"digest": "NOT_APPLICABLE", "present": False, "ref": None}:
        raise Task140HistoricalCorrectionError("Task140 structured-result absence changed")
    projection = validate_projection(_load(OLD_PROJECTION_PATH))
    if projection["schema_version"] != "live-current-projection-r2" or projection["projection_digest"] != "b1f2802cb6bf17d73e6f775f1bc544c10f4311c9a431af60945109c77b49c1f3":
        raise Task140HistoricalCorrectionError("Task140 R2 projection was rewritten")
    old_attempt = _load(OLD_ATTEMPT_PATH)
    if old_attempt["result"]["live_inference_started"] is not True:
        raise Task140HistoricalCorrectionError("Task140 raw receipt provenance was rewritten")
    events = LiveInferenceObservationEventLedger(CORRECTION_PATH).records()
    correction = [event for event in events if event["attempt_id"] == "attempt-140-live-01"]
    if len(correction) != 1 or correction[0]["prior_record_hash"] != record["record_hash"]:
        raise Task140HistoricalCorrectionError("Task141 correction does not bind to the unchanged Task140 record")
    if correction[0]["inference_observation_status"] != "NOT_OBSERVED" or correction[0]["marker_observed"] is not False:
        raise Task140HistoricalCorrectionError("Task141 inference correction is not conservative")
    return {
        "status": "PASS",
        "task140_record_hash": record["record_hash"],
        "task140_process_observed": True,
        "task140_return_code": 1,
        "task140_capture_completeness": "COMPLETE",
        "task140_structured_result_present": False,
        "task140_raw_spool_status": "CLEANED",
        "task140_forensics_capsule_status": "NOT_AVAILABLE_HISTORICAL_RAW_SPOOL_CLEANED",
        "root_cause_status": "ROOT_CAUSE_NOT_RECOVERABLE_FROM_TASK140_FORMAL_EVIDENCE",
        "inference_correction_status": correction[0]["inference_observation_status"],
        "history_rewritten": False,
        "claim_ceiling": "Task140 historical repository evidence and additive Task141 provenance correction only; no inference, validated completion, external truth, production readiness, Owner acceptance or epistemic upgrade is inferred.",
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
