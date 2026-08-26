#!/usr/bin/env python3
"""Validate the Task141 no-live-probe and independent-validator closure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/operations/iterations/141/step11-live-probe-and-independent-validation.json"


class Task141LiveProbeError(RuntimeError):
    """Raised when Step11 records an attempt without admission authority."""


def run_validation() -> dict[str, Any]:
    document = json.loads(PATH.read_text(encoding="utf-8"))
    if document.get("task_id") != "IGNITION-20260826-141" or document.get("step") != "11":
        raise Task141LiveProbeError("Step11 binding changed")
    if document.get("status") != "SKIPPED_UNSAFE_OR_UNAVAILABLE":
        raise Task141LiveProbeError("Step11 must preserve unavailable live state")
    probe = document["probe"]
    if probe["attempts"] or probe["live_dispatch_calls"] != 0 or probe["live_process_observed"]:
        raise Task141LiveProbeError("Step11 contains an unauthorized live attempt")
    if probe["inference_observation_status"] != "NOT_APPLICABLE_PRE_PROCESS" or probe["validated_completion_status"] != "NOT_VALIDATED":
        raise Task141LiveProbeError("Step11 pre-process semantics are inconsistent")
    validator = document["independent_validator"]
    if validator["status"] != "NOT_STARTED_NO_LIVE_ATTEMPT" or validator["validated_completion_count"] != 0:
        raise Task141LiveProbeError("independent validator status is inconsistent")
    safety = document["safety"]
    if safety["blind_retry"] or safety["live_inference_started"] or safety["raw_spool_created"] or safety["configuration_changed"] or safety["billing_changed"] or safety["secret_content_read"]:
        raise Task141LiveProbeError("Step11 safety boundary is not closed")
    return {"status": "PASS", "attempt_count": len(probe["attempts"]), "live_dispatch_calls": probe["live_dispatch_calls"], "validator_status": validator["status"], "claim_ceiling": document["claim_ceiling"]}


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
