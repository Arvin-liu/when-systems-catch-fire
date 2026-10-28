#!/usr/bin/env python3
"""Validate the Task141 bounded-family live policy freeze."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/operations/iterations/141/step09-live-policy-freeze.json"


class Task141LivePolicyError(RuntimeError):
    """Raised when the live family/attempt policy is widened or ambiguous."""


def run_validation() -> dict[str, Any]:
    document = json.loads(PATH.read_text(encoding="utf-8"))
    if document.get("task_id") != "IGNITION-20260826-141" or document.get("step") != "09" or document.get("status") != "PASS":
        raise Task141LivePolicyError("Task141 Step09 binding/status is invalid")
    policy = document["policy"]
    if policy["max_distinct_executor_families"] != 2 or policy["max_attempts_per_family"] != 1:
        raise Task141LivePolicyError("live family/attempt caps changed")
    if policy["stop_condition"] != "FIRST_EXACT_BOUND_LIVE_READONLY_VALIDATED_COMPLETION":
        raise Task141LivePolicyError("first exact-bound validated completion stop condition is missing")
    if policy["same_family_retry_rule"] != "NO_RETRY_WITHOUT_PUBLIC_ROOT_CAUSE_CONFIRMED_AND_FIXED":
        raise Task141LivePolicyError("same-family retry rule is not conservative")
    if policy["codex_family_status"] != "EXCLUDED_ROOT_CAUSE_NOT_CONFIRMED" or policy["authorized_families"]:
        raise Task141LivePolicyError("Codex or another family was authorized without a fresh safe admission")
    if policy["live_probe_authorization"] != "NO_AUTHORIZED_FAMILY" or policy["live_probe_count"] != 0:
        raise Task141LivePolicyError("live probing occurred despite no authorized family")
    if document["admission_decision"]["status"] != "NO_AUTHORIZED_FAMILY" or not document["admission_decision"]["stop_on_first_validated"]:
        raise Task141LivePolicyError("admission decision is not closed")
    if any(document["safety"][key] is not False for key in ("live_inference_started", "configuration_changed", "billing_changed", "secret_content_read", "workspace_modified")):
        raise Task141LivePolicyError("Step09 safety boundary is not closed")
    return {
        "status": "PASS",
        "live_probe_authorization": policy["live_probe_authorization"],
        "authorized_families": policy["authorized_families"],
        "max_distinct_executor_families": policy["max_distinct_executor_families"],
        "max_attempts_per_family": policy["max_attempts_per_family"],
        "validated_completion_count": policy["validated_completion_count"],
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
