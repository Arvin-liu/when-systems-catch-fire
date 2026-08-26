#!/usr/bin/env python3
"""Validate the bounded public archaeology and no-blind-retry decision for Task141."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/operations/iterations/141/step06-malformed-root-cause-archaeology.json"


class Task141RootCauseArchaeologyError(RuntimeError):
    """Raised when the public root-cause audit is incomplete or overclaims."""


def run_validation() -> dict[str, Any]:
    document = json.loads(PATH.read_text(encoding="utf-8"))
    if document.get("task_id") != "IGNITION-20260826-141" or document.get("step") != "06":
        raise Task141RootCauseArchaeologyError("Task141 Step06 binding changed")
    if document.get("status") != "PASS":
        raise Task141RootCauseArchaeologyError("Step06 is not PASS")
    probe = document["public_probe"]
    if probe["version_exit_code"] != 0 or probe["exec_help_exit_code"] != 0:
        raise Task141RootCauseArchaeologyError("public Codex version/help probe failed")
    if not probe["required_public_flags_present"] or probe["live_inference_started"]:
        raise Task141RootCauseArchaeologyError("public probe is incomplete or started inference")
    evidence = document["task140_static_evidence"]
    if evidence["historical_exit_code"] != 1 or evidence["historical_stdout_bytes"] != 0:
        raise Task141RootCauseArchaeologyError("Task140 malformed evidence changed")
    root_cause = document["root_cause"]
    if root_cause["status"] != "ROOT_CAUSE_NARROWED_NOT_CONFIRMED":
        raise Task141RootCauseArchaeologyError("Step06 must not promote an unconfirmed root cause")
    if root_cause["root_cause_confirmed"] or root_cause["repair_applied"]:
        raise Task141RootCauseArchaeologyError("unconfirmed root cause was promoted")
    if root_cause["same_family_retry"] != "FORBIDDEN_BLIND_RETRY":
        raise Task141RootCauseArchaeologyError("Codex same-family retry was not blocked")
    return {
        "status": "PASS",
        "root_cause_status": root_cause["status"],
        "codex_same_family_retry": root_cause["same_family_retry"],
        "public_flags_present": probe["required_public_flags_present"],
        "live_inference_started": probe["live_inference_started"],
        "claim_ceiling": document["claim_ceiling"],
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
