#!/usr/bin/env python3
"""Fail-closed validation for Task149 Step14 authenticated fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/step14-authenticated-channel-fail-closed-r0.json"
SCHEMA_PATH = ROOT / "schemas/operations/task149-step14-authenticated-channel-fail-closed-r0.schema.json"
EXPECTED_PREVIOUS_COMMIT = "f565feb7838247e12a088762434c0ce7aaa5fcee"
EXPECTED_CHANNELS = {"twitter", "reddit", "xiaohongshu", "instagram", "facebook"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    if document.get("formal_previous_commit") != EXPECTED_PREVIOUS_COMMIT:
        errors.append("Step14 must bind the published Step13 formal commit")
    if document.get("real_authenticated_calls") != 0 or document.get("current_explicit_credential_admission") is not False:
        errors.append("real authenticated access or explicit admission was introduced")
    fixtures = {entry.get("channel"): entry for entry in document.get("fixtures", [])}
    if set(fixtures) != EXPECTED_CHANNELS:
        errors.append("authenticated fixture channel set drifted")
    for channel, fixture in fixtures.items():
        if fixture.get("expected_status") != "AUTH_REQUIRED":
            errors.append(f"fixture did not fail closed as AUTH_REQUIRED: {channel}")
        if fixture.get("actual_action") != "REJECT_WITHOUT_CALL":
            errors.append(f"fixture admitted a call: {channel}")
        for key in ("provider_local_policy_accepted", "existing_login_state_used", "browser_login_invoked", "cookie_read", "cookie_imported", "authenticated_mcp_started"):
            if fixture.get(key) is not False:
                errors.append(f"implicit authority boundary widened: {channel}:{key}")
    forbidden = document.get("forbidden_implicit_authority", {})
    for key in ("automatic_browser_login", "automatic_chrome_cookie_read", "automatic_cookie_import", "automatic_authenticated_mcp_start", "existing_login_state_is_implicit_authorization"):
        if forbidden.get(key) is not False:
            errors.append(f"forbidden implicit authority widened: {key}")
    if document.get("automated_regression", {}).get("all_cases_fail_closed") is not True:
        errors.append("automated regression is not fail-closed")
    boundaries = document.get("boundaries", {})
    if boundaries.get("authenticated_channel_admission") != "NO_AUTHENTICATED_CHANNEL_ADMISSION" or boundaries.get("current_integration") != "NOT_CURRENT_INTEGRATION" or boundaries.get("production_readiness") != "NOT_PRODUCTION_READY":
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
        print("TASK149_STEP14_AUTH_FAIL_CLOSED_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK149_STEP14_AUTH_FAIL_CLOSED_OK fixtures=5 calls=0 implicit_authority=closed auth_admission=closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
