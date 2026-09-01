#!/usr/bin/env python3
"""Fail-closed validation for Task149 Step09 Agent Reach channel matrix."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/step09-agent-reach-channel-capability-matrix-r0.json"
SCHEMA_PATH = ROOT / "schemas/operations/task149-step09-agent-reach-channel-capability-matrix-r0.schema.json"
EXPECTED_PREVIOUS_COMMIT = "e27aff553ad8512b78cd2fdb8d7cb8b48889f7ee"
EXPECTED_DOCTOR_SHA = "1bd983b684c4c567958278ff218321274c91bc437a6ec9ce4eb354da5861b6f3"
PUBLIC = {
    "read_public_github_repository", "search_public_github_repositories", "read_public_web_page", "search_public_web",
    "read_rss_atom", "read_public_youtube_metadata_or_transcript", "search_public_bilibili", "read_public_bilibili",
    "read_public_v2ex", "read_public_xiaoyuzhou_transcript",
}
AUTH = {"read_twitter_x", "read_reddit", "read_xiaohongshu", "read_instagram", "read_facebook", "read_authenticated_linkedin", "read_authenticated_xueqiu"}
DOCTOR_CHANNELS = {"github", "twitter", "youtube", "reddit", "facebook", "instagram", "bilibili", "xiaohongshu", "linkedin", "xiaoyuzhou", "v2ex", "xueqiu", "rss", "exa_search", "web"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    if document.get("formal_previous_commit") != EXPECTED_PREVIOUS_COMMIT:
        errors.append("Step09 must bind the published Step08 formal commit")
    if document.get("doctor_evidence", {}).get("result_sha256") != EXPECTED_DOCTOR_SHA:
        errors.append("Step09 must bind the isolated Agent Reach doctor evidence")
    capabilities = {entry.get("capability_id"): entry for entry in document.get("capabilities", [])}
    if set(document.get("public_no_auth_candidate_capabilities", [])) != PUBLIC - {"read_public_xiaoyuzhou_transcript"}:
        errors.append("public capability inventory is incomplete or drifted")
    if set(document.get("authenticated_session_bearing_capabilities", [])) != AUTH:
        errors.append("authenticated capability inventory is incomplete or drifted")
    if not PUBLIC.issubset(capabilities) or not AUTH.issubset(capabilities):
        errors.append("public/authenticated capability records are incomplete")
    if set(entry.get("channel") for entry in document.get("observed_doctor_channels", [])) != DOCTOR_CHANNELS:
        errors.append("doctor channel set drifted")
    for capability_id, entry in capabilities.items():
        if entry.get("provider_local_policy_inherited") is not False:
            errors.append(f"provider-local policy inherited for {capability_id}")
        if entry.get("scope") == "AUTHENTICATED_SESSION_BEARING" and entry.get("status") not in {"AUTH_REQUIRED", "OWNER_APPROVAL_REQUIRED"}:
            errors.append(f"authenticated capability was not fail-closed: {capability_id}")
    for capability_id in ("read_public_github_repository", "search_public_github_repositories"):
        if capabilities.get(capability_id, {}).get("status") != "AUTH_REQUIRED":
            errors.append(f"GitHub capability status drifted: {capability_id}")
    for capability_id in ("read_public_web_page", "read_rss_atom", "search_public_bilibili", "read_public_bilibili", "read_public_v2ex"):
        if capabilities.get(capability_id, {}).get("status") != "AVAILABLE_READ_ONLY":
            errors.append(f"zero-auth available channel status drifted: {capability_id}")
    if capabilities.get("search_public_web", {}).get("status") != "ENVIRONMENT_MISSING":
        errors.append("public web search must remain environment-missing without Exa configuration")
    if document.get("isolation_evidence", {}).get("cookie_or_session_read") is not False or document.get("isolation_evidence", {}).get("system_install") is not False:
        errors.append("Step09 isolation boundary widened")
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
        print("TASK149_STEP09_AGENT_REACH_CHANNEL_MATRIX_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    capabilities = load_json(ARTIFACT_PATH)["capabilities"]
    print(f"TASK149_STEP09_AGENT_REACH_CHANNEL_MATRIX_OK capabilities={len(capabilities)} doctor_channels=15 auth_admission=closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
