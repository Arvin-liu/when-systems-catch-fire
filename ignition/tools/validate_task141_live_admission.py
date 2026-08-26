#!/usr/bin/env python3
"""Validate that Task141 live admission closed without an authorized family."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/operations/iterations/141/step10-live-admission.json"


class Task141LiveAdmissionError(RuntimeError):
    """Raised when live admission claims a probe without policy authority."""


def run_validation() -> dict[str, Any]:
    document = json.loads(PATH.read_text(encoding="utf-8"))
    if document.get("task_id") != "IGNITION-20260826-141" or document.get("step") != "10":
        raise Task141LiveAdmissionError("Step10 binding changed")
    if document.get("status") != "SKIPPED_UNSAFE_OR_UNAVAILABLE":
        raise Task141LiveAdmissionError("Step10 must record unavailable safe admission")
    admission = document["admission"]
    if admission["status"] != "NO_AUTHORIZED_FAMILY" or admission["selected_executor_id"] is not None or admission["live_dispatch_authorized"] or admission["live_inference_authorized"]:
        raise Task141LiveAdmissionError("Step10 widened live authority")
    preflight = document["preflight"]
    if any(preflight[field] != expected for field, expected in (("disposable_workspace", "NOT_CREATED"), ("runtime_scratch", "NOT_CREATED"), ("capability_lease", "NOT_ISSUED"), ("durable_capture", "NOT_INITIALIZED"), ("independent_validator", "NOT_STARTED"))):
        raise Task141LiveAdmissionError("Step10 created live resources without admission")
    safety = document["safety"]
    if safety["live_dispatch_calls"] != 0 or any(safety[field] is not False for field in ("live_process_started", "live_inference_started", "configuration_changed", "billing_changed", "secret_content_read")):
        raise Task141LiveAdmissionError("Step10 safety evidence is inconsistent")
    return {"status": "PASS", "admission_status": admission["status"], "live_dispatch_calls": safety["live_dispatch_calls"], "live_inference_started": safety["live_inference_started"], "claim_ceiling": document["claim_ceiling"]}


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
