#!/usr/bin/env python3
"""Validate the persisted Task141 22-case adversarial matrix receipt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.validate_task141_adversarial_matrix import run_matrix


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/operations/iterations/141/step13-adversarial-matrix.json"


class Task141AdversarialReceiptError(RuntimeError):
    """Raised when the persisted matrix is stale or incomplete."""


def run_validation() -> dict[str, Any]:
    persisted = json.loads(PATH.read_text(encoding="utf-8"))
    fresh = run_matrix()
    if persisted != fresh:
        raise Task141AdversarialReceiptError("persisted adversarial matrix is not the fresh deterministic matrix")
    if persisted["task_id"] != "IGNITION-20260826-141" or persisted["status"] != "PASS" or persisted["case_count"] != 22:
        raise Task141AdversarialReceiptError("matrix task/status/count is invalid")
    if persisted["negative_case_count"] != 17 or persisted["positive_case_count"] != 5 or persisted["live_processes_started"] != 0:
        raise Task141AdversarialReceiptError("matrix counts or live-process safety claim is invalid")
    if any(case["status"] != "PASS" for case in persisted["cases"]):
        raise Task141AdversarialReceiptError("matrix contains a failed case")
    return {"status": "PASS", "case_count": persisted["case_count"], "negative_case_count": persisted["negative_case_count"], "positive_case_count": persisted["positive_case_count"], "live_processes_started": persisted["live_processes_started"], "claim_ceiling": persisted["claim_ceiling"]}


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
