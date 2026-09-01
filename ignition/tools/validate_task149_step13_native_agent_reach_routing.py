#!/usr/bin/env python3
"""Fail-closed validation for Task149 Step13 provider routing evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/step13-native-agent-reach-routing-r0.json"
SCHEMA_PATH = ROOT / "schemas/operations/task149-step13-native-agent-reach-routing-r0.schema.json"
EXPECTED_PREVIOUS_COMMIT = "79d56bd74e8395541531bded69caec8d45a8f061"
EXPECTED_STEP08_SHA = "d24903133a666f67bb6f97a22a1a382ff2a54ed684a998fe19aefe94c8eb7208"
EXPECTED_STEP12_SHA = "5709944e678e7ecbc07fff3473a963cd59c7e99b0957696ed83df41c9355dc52"
EXPECTED_REVISION = "06c202b03400a7d31886bf4399213706da1a0324"
EXPECTED_OPERATIONS = {"read_public_github_repository", "search_public_github_repositories", "read_public_web_page"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    if document.get("formal_previous_commit") != EXPECTED_PREVIOUS_COMMIT:
        errors.append("Step13 must bind the published Step12 formal commit")
    if document.get("source_step08_receipt_sha256") != EXPECTED_STEP08_SHA or document.get("source_step12_receipt_sha256") != EXPECTED_STEP12_SHA:
        errors.append("Step13 source receipts drifted")
    if document.get("agent_reach_revision") != EXPECTED_REVISION:
        errors.append("Agent Reach revision drifted")
    comparisons = {entry.get("abstract_operation"): entry for entry in document.get("provider_comparisons", [])}
    if set(comparisons) != EXPECTED_OPERATIONS:
        errors.append("Step13 comparison operation set drifted")
    for operation, entry in comparisons.items():
        native = entry.get("native_provider", {})
        routed = entry.get("agent_reach_routed_provider", {})
        if native.get("status") != "PASS" or native.get("exit_code") != 0 or native.get("result_count", 0) < 1:
            errors.append(f"native path did not pass: {operation}")
        if entry.get("provider_switching_leaks_implementation_details_upward") is not False:
            errors.append(f"implementation detail leaked upward: {operation}")
        if entry.get("normalization", {}).get("implementation_detail_leaks_upward") is not False:
            errors.append(f"normalization leaked implementation details: {operation}")
        for result_name, result in (("native", native), ("agent_reach", routed)):
            if result.get("provenance", {}).get("raw_output_bound") is not True or result.get("provenance", {}).get("external_truth_claimed") is not False:
                errors.append(f"provenance boundary drifted: {operation}:{result_name}")
        if operation.startswith("read_public_github") or operation.startswith("search_public_github"):
            if routed.get("status") != "AUTH_REQUIRED" or routed.get("exit_code") != 4 or routed.get("result_count") != 0:
                errors.append(f"Agent Reach GitHub auth gate drifted: {operation}")
            if entry.get("health_state", {}).get("agent_reach") != "AUTH_REQUIRED":
                errors.append(f"Agent Reach GitHub health drifted: {operation}")
        if operation == "read_public_web_page":
            if routed.get("status") != "PASS" or routed.get("exit_code") != 0 or routed.get("result_count") != 1:
                errors.append("Agent Reach web route did not pass")
    experiment = document.get("provider_switching_experiment", {})
    for key in ("output_normalization_required", "provenance_required", "failure_semantics_preserved", "health_state_preserved", "permission_difference_observed", "dependency_difference_observed"):
        if experiment.get(key) is not True:
            errors.append(f"routing dimension not retained: {key}")
    if experiment.get("provider_swap_result") != "PARTIAL" or experiment.get("upper_workflow_change") is not False or experiment.get("glue_code_used_to_hide_failure") is not False:
        errors.append("provider switching result was widened or hidden")
    boundary = document.get("boundaries", {})
    if boundary.get("authenticated_channel_admission") != "NO_AUTHENTICATED_CHANNEL_ADMISSION" or boundary.get("current_integration") != "NOT_CURRENT_INTEGRATION" or boundary.get("production_readiness") != "NOT_PRODUCTION_READY":
        errors.append("Current/authenticated/production boundary widened")
    side_effects = document.get("side_effect_boundary", {})
    for key in ("system_install", "system_configuration", "browser_login", "cookie_or_session_read", "credential_content_access", "external_write", "private_repository_write"):
        if side_effects.get(key) is not False:
            errors.append(f"side effect boundary widened: {key}")
    if side_effects.get("persistent_files_after_cleanup") != 0 or side_effects.get("gh_telemetry_files_observed") != side_effects.get("gh_telemetry_files_quarantined"):
        errors.append("isolated telemetry cleanup is incomplete")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_STEP13_ROUTING_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK149_STEP13_ROUTING_OK comparisons=3 swap=PARTIAL upper_workflow_change=false auth_admission=closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
