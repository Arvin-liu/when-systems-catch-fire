#!/usr/bin/env python3
"""Fail-closed validation for Task149 Step12 zero-auth acquisition receipts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/step12-zero-auth-acquisition-smoke-r0.json"
SCHEMA_PATH = ROOT / "schemas/operations/task149-step12-zero-auth-acquisition-smoke-r0.schema.json"
EXPECTED_PREVIOUS_COMMIT = "497a5cdc90afa509a603bc1ae21fc2bf833abc20"
EXPECTED_DOCTOR_SHA = "3d89f4e661f00f41b1377b765bd0d3e8e0706f3fa57441e16c6356040d560333"
EXPECTED_UPDATE_SHA = "a38043ddf8ca4adb7c33a1d696f44e802782eadc226b1e3f029c6af0ffb4209a"
EXPECTED_REVISION = "06c202b03400a7d31886bf4399213706da1a0324"
EXPECTED_STATUSES = {
    "web_public_page_read": ("PASS", 0, 1),
    "github_public_repository_read": ("AUTH_REQUIRED", 4, 0),
    "github_public_repository_search": ("AUTH_REQUIRED", 4, 0),
    "rss_public_feed_read": ("PASS", 0, 20),
    "youtube_public_metadata_read": ("PASS_WITH_LIMITS", 0, 1),
    "public_semantic_search": ("ENVIRONMENT_MISSING", 1, 0),
    "bilibili_public_search": ("PASS", 0, 12),
    "v2ex_public_hot_topics_read": ("PASS", 0, 9),
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    if document.get("formal_previous_commit") != EXPECTED_PREVIOUS_COMMIT:
        errors.append("Step12 must bind the published Step11 formal commit")
    if document.get("provider_revision") != EXPECTED_REVISION:
        errors.append("Step12 provider revision drifted")
    doctor = document.get("doctor_evidence", {})
    if doctor.get("source_step11_doctor_sha256") != EXPECTED_DOCTOR_SHA:
        errors.append("Step12 must bind Step11 doctor evidence")
    if doctor.get("check_update_result_sha256") != EXPECTED_UPDATE_SHA:
        errors.append("Step12 check-update evidence hash drifted")
    if document.get("authenticated_calls_attempted") is not False:
        errors.append("authenticated calls were attempted")
    operations = {entry.get("operation_id"): entry for entry in document.get("operations", [])}
    if set(operations) != set(EXPECTED_STATUSES):
        errors.append("zero-auth smoke operation set drifted")
    for operation_id, (status, exit_code, count) in EXPECTED_STATUSES.items():
        entry = operations.get(operation_id, {})
        if (entry.get("status"), entry.get("exit_code"), entry.get("returned_result_count")) != (status, exit_code, count):
            errors.append(f"smoke outcome drifted: {operation_id}")
        if entry.get("selected_provider") != "agent-reach":
            errors.append(f"provider drifted: {operation_id}")
        if entry.get("authenticated_call") is not False:
            errors.append(f"authenticated call marker widened: {operation_id}")
        effects = entry.get("side_effects", {})
        for key in ("system_install", "configuration_write", "credential_or_cookie_access", "external_write"):
            if effects.get(key) is not False:
                errors.append(f"side effect boundary widened: {operation_id}:{key}")
        if effects.get("read_only") is not True:
            errors.append(f"operation was not read-only: {operation_id}")
        if entry.get("provenance", {}).get("external_truth_claimed") is not False:
            errors.append(f"external truth claim widened: {operation_id}")
    if operations.get("github_public_repository_read", {}).get("status") != "AUTH_REQUIRED" or operations.get("github_public_repository_search", {}).get("status") != "AUTH_REQUIRED":
        errors.append("GitHub zero-auth route must remain auth-gated")
    if operations.get("public_semantic_search", {}).get("status") != "ENVIRONMENT_MISSING":
        errors.append("Exa absence must remain ENVIRONMENT_MISSING")
    if operations.get("youtube_public_metadata_read", {}).get("status") != "PASS_WITH_LIMITS":
        errors.append("YouTube smoke must remain metadata-only bounded")
    if document.get("summary", {}).get("environment_missing_is_valid_result") is not True:
        errors.append("environment-missing result was not retained as valid evidence")
    boundaries = document.get("boundaries", {})
    if boundaries.get("authenticated_channel_admission") != "NO_AUTHENTICATED_CHANNEL_ADMISSION":
        errors.append("authenticated channel admission must remain closed")
    if boundaries.get("current_integration") != "NOT_CURRENT_INTEGRATION" or boundaries.get("production_readiness") != "NOT_PRODUCTION_READY":
        errors.append("Current/production boundary widened")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_STEP12_ZERO_AUTH_SMOKE_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK149_STEP12_ZERO_AUTH_SMOKE_OK operations=8 pass=4 limited=1 auth_required=2 environment_missing=1 authenticated_calls=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
