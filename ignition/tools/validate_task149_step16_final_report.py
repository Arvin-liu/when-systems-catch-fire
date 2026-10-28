#!/usr/bin/env python3
"""Fail-closed validation for Task149 Step16 unified provider report."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/final-report-external-capability-provider-adapter-spikes-r0.json"
SCHEMA_PATH = ROOT / "schemas/operations/task149-final-report-external-capability-provider-adapter-spikes-r0.schema.json"
EXPECTED_PREVIOUS_COMMIT = "c7ba9f9141469dbaf03cc42f7079f22a5b2fa145"
EXPECTED_HUMAN_REPORT_SHA = "d22fbb9ae30003ac68a15f5a83e6b0bfa082411a3cc37296fe9965eff9f86bae"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    if document.get("formal_previous_commit") != EXPECTED_PREVIOUS_COMMIT:
        errors.append("Step16 must bind the published Step15 formal commit")
    if document.get("human_report_sha256") != EXPECTED_HUMAN_REPORT_SHA:
        errors.append("human-readable report hash drifted")
    human_path = REPO_ROOT / document.get("human_report_path", "")
    if not human_path.is_file() or hashlib.sha256(human_path.read_bytes()).hexdigest() != EXPECTED_HUMAN_REPORT_SHA:
        errors.append("human-readable report is missing or not bound by hash")
    recommendations = document.get("recommendations", {})
    if recommendations.get("archify", {}).get("recommendation") != "CONTINUE_EXPERIMENT":
        errors.append("Archify recommendation must remain CONTINUE_EXPERIMENT")
    if recommendations.get("archify", {}).get("future_role") != "derived visualization provider":
        errors.append("Archify future role drifted")
    if recommendations.get("agent_reach_public", {}).get("recommendation") != "CONTINUE_EXPERIMENT":
        errors.append("public Agent Reach recommendation must remain CONTINUE_EXPERIMENT")
    if recommendations.get("agent_reach_authenticated", {}).get("recommendation") != "DEFER":
        errors.append("authenticated Agent Reach recommendation must remain DEFER")
    if recommendations.get("agent_reach_authenticated", {}).get("authenticated_calls") != 0:
        errors.append("authenticated Agent Reach calls must remain zero")
    for name, recommendation in recommendations.items():
        if recommendation.get("current_integration") != "NOT_CURRENT_INTEGRATION" or recommendation.get("production_readiness") != "NOT_PRODUCTION_READY":
            errors.append(f"provider recommendation boundary widened: {name}")
    if document.get("overall_status") != "PROVIDER_ADMISSION_CANDIDATE":
        errors.append("overall status drifted")
    if document.get("exact_next_action") != "AWAIT_OWNER_PROVIDER_ADAPTER_REVIEW":
        errors.append("exact next action drifted")
    if document.get("test_summary", {}).get("local_formal_task_tests") != "ALL_TASK149_SPIKE_TESTS_PASS_WITH_RETAINED_RESIDUALS":
        errors.append("test summary is not complete")
    if document.get("test_summary", {}).get("external_live_invocation") != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("live invocation boundary drifted")
    boundaries = document.get("boundaries", {})
    for key in ("external_provider_is_ignition_authority", "provider_capability_is_permission", "provider_output_is_external_truth", "provider_local_policy_is_ignition_global_policy", "adapter_spike_pass_is_current_capability"):
        if boundaries.get(key) is not False:
            errors.append(f"global boundary widened: {key}")
    if boundaries.get("current_integration") != "NOT_CURRENT_INTEGRATION" or boundaries.get("production_readiness") != "NOT_PRODUCTION_READY" or boundaries.get("authenticated_channel_admission") != "NO_AUTHENTICATED_CHANNEL_ADMISSION":
        errors.append("Current/production/authenticated boundary widened")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_STEP16_FINAL_REPORT_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK149_STEP16_FINAL_REPORT_OK archify=CONTINUE_EXPERIMENT agent_reach_public=CONTINUE_EXPERIMENT authenticated=DEFER status=PROVIDER_ADMISSION_CANDIDATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
