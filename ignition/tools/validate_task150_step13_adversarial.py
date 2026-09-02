#!/usr/bin/env python3
"""Fail-closed validation for Task150 Step13 adversarial fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/fixtures/task150-step13-adversarial.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step13-adversarial-r1.schema.json"


EXPECTED_CASES = {
    "promote_current_provider": ("current_admission", "CURRENT_BOUNDED"),
    "provider_becomes_ignition_authority": ("provider_is_ignition_authority", True),
    "provider_capability_becomes_permission": ("provider_capability_is_permission", True),
    "provider_output_becomes_external_truth": ("provider_output_is_external_truth", True),
    "provider_policy_becomes_global_policy": ("provider_local_policy_is_ignition_global_policy", True),
    "adapter_pass_becomes_current_capability": ("adapter_spike_pass_is_current_capability", True),
    "authenticated_channel_admission": ("authenticated_channel_admission", "ADMITTED"),
    "live_external_invocation_change": ("live_external_invocation", "RUN"),
    "provider_homepage_claim": ("provider_homepage_claim", True),
    "topology_mutation": ("topology_mutation", True),
}

SAFE_VALUES = {
    "current_admission": "NOT_ADMITTED",
    "default_renderer": "NOT_SELECTED",
    "provider_is_ignition_authority": False,
    "provider_capability_is_permission": False,
    "provider_output_is_external_truth": False,
    "provider_local_policy_is_ignition_global_policy": False,
    "adapter_spike_pass_is_current_capability": False,
    "authenticated_channel_admission": "NO_AUTHENTICATED_ADMISSION",
    "live_external_invocation": "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN",
    "provider_homepage_claim": False,
    "topology_mutation": False,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_mutation(mutation: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    unknown = sorted(set(mutation) - set(SAFE_VALUES))
    if unknown:
        errors.append(f"unknown admission mutation fields: {unknown}")
    for key, value in mutation.items():
        if key in SAFE_VALUES and value != SAFE_VALUES[key]:
            errors.append(f"{key} escalates from {SAFE_VALUES[key]!r} to {value!r}")
    return errors


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)
    ]
    if errors:
        return errors

    if document["fixture_execution"]["provider_process_started"] is not False or document["fixture_execution"]["credentials_or_sessions_accessed"] is not False or document["fixture_execution"]["system_or_repository_mutation"] is not False:
        errors.append("adversarial fixture execution crossed a side-effect boundary")
    if document["safe_baseline"] != SAFE_VALUES:
        errors.append("safe baseline drifted")

    observed_ids = [case["id"] for case in document["cases"]]
    if set(observed_ids) != set(EXPECTED_CASES) or len(observed_ids) != len(set(observed_ids)):
        errors.append(f"adversarial case census drifted: {observed_ids!r}")
    for case in document["cases"]:
        expected = EXPECTED_CASES.get(case["id"])
        if expected is None:
            continue
        key, value = expected
        if case["mutation"] != {key: value}:
            errors.append(f"{case['id']} mutation drifted")
        if not evaluate_mutation(case["mutation"]):
            errors.append(f"{case['id']} was not rejected by the fail-closed evaluator")
        if case["expected_outcome"] != "FAIL_CLOSED_REJECT" or case["observed_result"] != "REJECTED":
            errors.append(f"{case['id']} outcome was not rejection")

    scope = document["scope_freeze"]
    if scope["current_admission"] != "NOT_ADMITTED" or scope["default_renderer"] != "NOT_SELECTED" or scope["provider_homepage"] != "NO_CLAIM":
        errors.append("Current, renderer or homepage boundary changed")
    if scope["authenticated_channels"] != "NO_AUTHENTICATED_ADMISSION" or scope["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("authentication or live invocation boundary changed")
    if scope["agent_reach"] != "NO_CHANGE" or scope["task151"] != "FORBIDDEN":
        errors.append("Agent Reach or successor-task boundary changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP13_ADVERSARIAL_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK150_STEP13_ADVERSARIAL_OK cases=10 rejected=10 side_effects=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
