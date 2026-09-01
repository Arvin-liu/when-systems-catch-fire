#!/usr/bin/env python3
"""Fail-closed validation for Task149 Step08 provider adjudication."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/step08-provider-adjudication-r0.json"
SCHEMA_PATH = ROOT / "schemas/operations/task149-step08-provider-adjudication-r0.schema.json"
EXPECTED_PREVIOUS_COMMIT = "e9194e9bfe858712a8b07620604684e4b98eca2b"
EXPECTED_DOCTOR_SHA = "1bd983b684c4c567958278ff218321274c91bc437a6ec9ce4eb354da5861b6f3"
EXPECTED_UPDATE_SHA = "a38043ddf8ca4adb7c33a1d696f44e802782eadc226b1e3f029c6af0ffb4209a"
FORBIDDEN_BOUNDARY_KEYS = {
    "external_provider_is_ignition_authority",
    "provider_capability_is_permission",
    "provider_output_is_external_truth",
    "provider_local_policy_is_ignition_global_policy",
    "adapter_spike_pass_is_current_capability",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    if document.get("formal_previous_commit") != EXPECTED_PREVIOUS_COMMIT:
        errors.append("Step08 must bind the published Step07 formal commit")
    runtime = document.get("agent_reach_runtime", {})
    if runtime.get("doctor_result_sha256") != EXPECTED_DOCTOR_SHA:
        errors.append("Agent Reach doctor result hash drifted")
    if runtime.get("check_update_result_sha256") != EXPECTED_UPDATE_SHA:
        errors.append("Agent Reach check-update result hash drifted")
    if runtime.get("isolated_runtime", {}).get("system_install") is not False or runtime.get("isolated_runtime", {}).get("persistent_agent_reach_config_written") is not False:
        errors.append("Agent Reach runtime must remain isolated and non-persistent")
    comparisons = document.get("provider_comparisons", [])
    operations = {entry.get("abstract_operation") for entry in comparisons}
    if not {"read_public_github_repository", "search_public_github_repositories", "read_public_web_page"}.issubset(operations):
        errors.append("Step08 must retain GitHub read/search and generic web read comparisons")
    for entry in comparisons:
        native = entry.get("native_provider", {})
        routed = entry.get("agent_reach_routed_provider", {})
        if native.get("exit_code") != 0 or native.get("http_status") != 200:
            errors.append(f"native comparison did not remain HTTP 200: {entry.get('abstract_operation')}")
        if routed.get("channel") == "github":
            if routed.get("status") != "AUTH_REQUIRED" or routed.get("exit_code") != 4:
                errors.append(f"Agent Reach GitHub auth failure semantics drifted: {entry.get('abstract_operation')}")
        if routed.get("channel") == "web":
            if routed.get("status") != "AVAILABLE_READ_ONLY" or routed.get("exit_code") != 0 or routed.get("http_status") != 200:
                errors.append("Agent Reach web route must remain a bounded read-only success")
        for provider in (native, routed):
            provenance = provider.get("provenance", {})
            if provenance.get("raw_output_bound") is not True:
                errors.append(f"raw output provenance is not bound: {entry.get('abstract_operation')}")
        if entry.get("normalization", {}).get("schema") != "PROVIDER_NEUTRAL_SOURCE_RESULT_R0":
            errors.append("provider-neutral normalization schema missing")
    experiment = document.get("provider_switching_experiment", {})
    if experiment.get("same_abstract_operations") is not True or experiment.get("upper_workflow_change") is not False:
        errors.append("provider switching must use the same abstract operation without upper-workflow change")
    if experiment.get("provider_swap_result") != "PARTIAL":
        errors.append("provider switching result must remain PARTIAL")
    for key in ("output_normalization_required", "provenance_required", "failure_semantics_preserved", "health_state_preserved", "permission_difference_observed", "dependency_difference_observed"):
        if experiment.get(key) is not True:
            errors.append(f"provider switching evidence missing: {key}")
    if experiment.get("provider_switching_leaks_implementation_details_upward") is not False:
        errors.append("provider implementation details must not leak upward")
    decisions = {entry.get("provider_id"): entry.get("decision") for entry in document.get("adjudications", [])}
    if decisions.get("archify") != "FIT_WITH_LIMITS":
        errors.append("Archify adjudication must remain FIT_WITH_LIMITS")
    if decisions.get("agent-reach-public") != "FIT_WITH_LIMITS":
        errors.append("public Agent Reach adjudication must remain FIT_WITH_LIMITS")
    if decisions.get("agent-reach-authenticated") != "DEFER":
        errors.append("authenticated Agent Reach adjudication must remain DEFER")
    recommendation = document.get("admission_recommendation", {})
    if recommendation.get("future_candidate_only") is not True or recommendation.get("not_current_integration") is not True or recommendation.get("not_production_ready") is not True:
        errors.append("provider recommendations must remain future candidates only")
    if document.get("side_effect_boundary", {}).get("cookie_or_session_read") is not False:
        errors.append("cookie/session reads must remain false")
    if document.get("side_effect_boundary", {}).get("browser_login") is not False:
        errors.append("browser login must remain false")
    if document.get("boundaries", {}).get("authenticated_channel_admission") != "NO_AUTHENTICATED_CHANNEL_ADMISSION":
        errors.append("authenticated channel admission must remain closed")
    if any(key in document.get("boundaries", {}) and document["boundaries"].get(key) is not False for key in FORBIDDEN_BOUNDARY_KEYS):
        errors.append("provider authority boundary widened")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_STEP08_PROVIDER_ADJUDICATION_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK149_STEP08_PROVIDER_ADJUDICATION_OK archify=FIT_WITH_LIMITS agent_reach_public=FIT_WITH_LIMITS authenticated=DEFER")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
