#!/usr/bin/env python3
"""Fail-closed validation for Task149 Step10 safety isolation evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/step10-agent-reach-safety-isolation-r0.json"
SCHEMA_PATH = ROOT / "schemas/operations/task149-step10-agent-reach-safety-isolation-r0.schema.json"
EXPECTED_PREVIOUS_COMMIT = "77b782a43da046ccae20446b0badd0160ad7a239"
EXPECTED_DOCTOR_SHA = "e3121078405d05d8ad573c40bfaf463ea4adf55f3615ca50a505f242f0d8ecc2"
EXPECTED_DRY_RUN_SHA = "e4dec3782f0fd89798a1c0277b343a1d84a0ca6060a30e30a4043a3e6f11e76b"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    if document.get("formal_previous_commit") != EXPECTED_PREVIOUS_COMMIT:
        errors.append("Step10 must bind the published Step09 formal commit")
    environment = document.get("ephemeral_environment", {})
    if environment.get("before_file_count") != 0 or environment.get("after_file_count") != 0:
        errors.append("isolated HOME/XDG paths must be empty before and after the dry-run")
    if document.get("commands", {}).get("doctor", {}).get("result_sha256") != EXPECTED_DOCTOR_SHA:
        errors.append("doctor evidence hash drifted")
    if document.get("commands", {}).get("install_dry_run", {}).get("result_sha256") != EXPECTED_DRY_RUN_SHA:
        errors.append("dry-run evidence hash drifted")
    mutation = document.get("mutation_audit", {})
    for key in ("sudo_invoked", "system_flag_invoked", "system_install_performed", "system_config_written", "firewall_or_security_changed", "browser_login_invoked", "cookie_or_session_read", "private_credential_read", "external_write_invoked", "private_repository_write_invoked", "upstream_repository_modified", "formal_worktree_modified_during_isolation_check", "control_worktree_modified_during_isolation_check"):
        if mutation.get(key) is not False:
            errors.append(f"safety mutation audit widened: {key}")
    if mutation.get("command_argv_forbidden_tokens_absent") is not True:
        errors.append("forbidden command tokens were not proven absent")
    if document.get("ephemeral_environment", {}).get("credential_or_cookie_content_access") != "NONE":
        errors.append("credential/cookie access must remain NONE")
    if document.get("boundaries", {}).get("authenticated_channel_admission") != "NO_AUTHENTICATED_CHANNEL_ADMISSION":
        errors.append("authenticated channel admission must remain closed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_STEP10_AGENT_REACH_SAFETY_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK149_STEP10_AGENT_REACH_SAFETY_OK isolated=true system_install=false credential_access=none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
