#!/usr/bin/env python3
"""Fail-closed validation for the Task150 Step11 registry-admission gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/150/step11-capability-registry-candidate-gate.json"
SCHEMA_PATH = ROOT / "schemas/operations/task150-step11-capability-registry-candidate-gate-r1.schema.json"


EXPECTED_RESULTS = {
    "no_current_provider_activation": "PASS",
    "no_draft_exception_survives_ready": "PASS",
    "experimental_contract_not_runtime_authority": "PASS",
    "no_authenticated_admission": "PASS",
    "no_provider_homepage_claim": "PASS",
    "live_external_invocation_unchanged": "PASS",
    "nonfunction_claim_materiality_clean": "PASS",
    "zero_background_current_claim": "PASS",
    "delta_viewport_containment_zero_failure": "FAIL",
    "owner_visual_acceptance": "PENDING",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [
        error.json_path + ": " + error.message
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)
    ]
    if errors:
        return errors

    candidate = document["candidate"]
    if candidate["registry_sha256_before"] != candidate["registry_sha256_after"]:
        errors.append("Capability Registry hash changed during a non-admission review")
    if candidate["operation_count_before"] != candidate["operation_count_after"]:
        errors.append("Capability Registry operation count changed during a non-admission review")
    if candidate["registry_write_performed"] is not False or candidate["operation_present_after"] is not False:
        errors.append("candidate registry write or operation presence was admitted")

    observed = {gate["id"]: gate["result"] for gate in document["gates"]}
    if observed != EXPECTED_RESULTS:
        errors.append(f"candidate gate results drifted: expected={EXPECTED_RESULTS!r} observed={observed!r}")

    decision = document["admission_decision"]
    if decision["decision"] != "NOT_REGISTERED" or decision["candidate_registry_write"] != "NOT_PERFORMED":
        errors.append("registry admission was not fail-closed")
    if decision["ready_or_merge_authorization"] != "NOT_GRANTED":
        errors.append("Ready or merge authorization was granted by a failed candidate gate")

    scope = document["scope_freeze"]
    if scope["current_admission"] != "NOT_ADMITTED" or scope["default_renderer"] != "NOT_SELECTED":
        errors.append("Current or default-renderer scope changed")
    if scope["authenticated_channels"] != "NO_AUTHENTICATED_ADMISSION":
        errors.append("authenticated channel admission changed")
    if scope["agent_reach"] != "NO_CHANGE" or scope["live_external_invocation"] != "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("Agent Reach or live invocation changed")
    if scope["provider_homepage"] != "NO_CLAIM" or scope["successor_task"] != "NOT_CREATED":
        errors.append("homepage or successor-task boundary changed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    _ = parser.parse_args()
    errors = validate()
    if errors:
        print("TASK150_STEP11_CAPABILITY_REGISTRY_GATE_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK150_STEP11_CAPABILITY_REGISTRY_GATE_OK decision=NOT_REGISTERED registry_write=false delta_viewport=FAIL owner_visual=PENDING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
