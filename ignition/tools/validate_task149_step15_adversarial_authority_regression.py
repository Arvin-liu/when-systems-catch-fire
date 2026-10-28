#!/usr/bin/env python3
"""Fail-closed validation for Task149 Step15 provider-authority fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/step15-adversarial-authority-regression-r0.json"
SCHEMA_PATH = ROOT / "schemas/operations/task149-step15-adversarial-authority-regression-r0.schema.json"
EXPECTED_PREVIOUS_COMMIT = "11b7828db702afdce55b77481652ced49f75f918"
EXPECTED_DECISIONS = {
    "third-party-skill-global-internet-directive": "PROVIDER_LOCAL_POLICY",
    "provider-verified-output": "REJECT_UNPROVEN_EXTERNAL_TRUTH",
    "provider-health-green": "REJECT_HEALTH_AS_SUCCESS",
    "archify-node-without-canonical-provenance": "REJECT_MISSING_CANONICAL_PROVENANCE",
    "agent-reach-backend-exists": "AUTH_REQUIRED",
    "third-party-readme-production-ready": "REJECT_CLAIM_CEILING",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    if document.get("formal_previous_commit") != EXPECTED_PREVIOUS_COMMIT:
        errors.append("Step15 must bind the published Step14 formal commit")
    if document.get("external_calls") != 0 or document.get("fixture_only") is not True:
        errors.append("Step15 must remain fixture-only with zero external calls")
    fixtures = {fixture.get("fixture_id"): fixture for fixture in document.get("fixtures", [])}
    if set(fixtures) != set(EXPECTED_DECISIONS):
        errors.append("adversarial fixture set drifted")
    for fixture_id, expected in EXPECTED_DECISIONS.items():
        fixture = fixtures.get(fixture_id, {})
        if fixture.get("expected_decision") != expected:
            errors.append(f"expected authority decision drifted: {fixture_id}")
        for key in ("escalation_blocked", "external_truth_claimed", "current_capability_promoted"):
            required = True if key == "escalation_blocked" else False
            if fixture.get(key) is not required:
                errors.append(f"authority escalation widened: {fixture_id}:{key}")
    invariants = document.get("regression_invariants", {})
    for key in ("provider_local_policy_is_ignition_global_policy", "provider_output_is_external_truth", "provider_health_is_user_task_success", "derived_artifact_is_canonical_architecture", "backend_presence_is_credential_authorization", "provider_readme_is_ignition_current"):
        if invariants.get(key) is not False:
            errors.append(f"global authority invariant widened: {key}")
    if invariants.get("all_escalations_blocked") is not True:
        errors.append("not all adversarial escalations were blocked")
    if invariants.get("authenticated_channel_admission") != "NO_AUTHENTICATED_CHANNEL_ADMISSION" or invariants.get("current_integration") != "NOT_CURRENT_INTEGRATION" or invariants.get("production_readiness") != "NOT_PRODUCTION_READY":
        errors.append("authenticated/Current/production boundary widened")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_STEP15_AUTHORITY_REGRESSION_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK149_STEP15_AUTHORITY_REGRESSION_OK fixtures=6 escalations_blocked=6 external_calls=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
