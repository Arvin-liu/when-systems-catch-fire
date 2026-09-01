#!/usr/bin/env python3
"""Fail-closed validation for Task149 Step11 Agent Reach health evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/step11-agent-reach-health-capability-probe-r0.json"
SCHEMA_PATH = ROOT / "schemas/operations/task149-step11-agent-reach-health-capability-probe-r0.schema.json"
EXPECTED_PREVIOUS_COMMIT = "a1627e94514cdb415241f5adba7cceb41509b2c2"
EXPECTED_SOURCE_MATRIX_SHA = "e7aa7c20bd679e8d6a4603cfc97b105ca5051e4ce281f385be31687c3e4cb7fa"
EXPECTED_DOCTOR_SHA = "3d89f4e661f00f41b1377b765bd0d3e8e0706f3fa57441e16c6356040d560333"
CHANNELS = {"github", "twitter", "youtube", "reddit", "facebook", "instagram", "bilibili", "xiaohongshu", "linkedin", "xiaoyuzhou", "v2ex", "xueqiu", "rss", "exa_search", "web"}
CAPABILITIES = {
    "read_public_github_repository", "search_public_github_repositories", "read_public_web_page", "search_public_web", "read_rss_atom",
    "read_public_youtube_metadata_or_transcript", "search_public_bilibili", "read_public_bilibili", "read_public_v2ex", "read_public_xiaoyuzhou_transcript",
    "read_twitter_x", "read_reddit", "read_xiaohongshu", "read_instagram", "read_facebook", "read_authenticated_linkedin", "read_authenticated_xueqiu",
}
EXPECTED_CHANNEL_STATUS = {
    "github": ("warn", None, "AUTH_REQUIRED"), "twitter": ("warn", None, "AUTH_REQUIRED"), "youtube": ("warn", "yt-dlp", "ENVIRONMENT_MISSING"),
    "reddit": ("off", None, "AUTH_REQUIRED"), "facebook": ("off", None, "AUTH_REQUIRED"), "instagram": ("off", None, "AUTH_REQUIRED"),
    "bilibili": ("ok", "B站搜索 API", "AVAILABLE_READ_ONLY"), "xiaohongshu": ("off", None, "AUTH_REQUIRED"),
    "linkedin": ("off", None, "OWNER_APPROVAL_REQUIRED"), "xiaoyuzhou": ("off", None, "ENVIRONMENT_MISSING"),
    "v2ex": ("ok", "V2EX API (public)", "AVAILABLE_READ_ONLY"), "xueqiu": ("warn", None, "AUTH_REQUIRED"),
    "rss": ("ok", "feedparser", "AVAILABLE_READ_ONLY"), "exa_search": ("off", None, "ENVIRONMENT_MISSING"), "web": ("ok", "Jina Reader", "AVAILABLE_READ_ONLY"),
}
AUTHENTICATED = {"read_twitter_x", "read_reddit", "read_xiaohongshu", "read_instagram", "read_facebook", "read_authenticated_linkedin", "read_authenticated_xueqiu"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    if document.get("formal_previous_commit") != EXPECTED_PREVIOUS_COMMIT:
        errors.append("Step11 must bind the published Step10 formal commit")
    if document.get("source_matrix_sha256") != EXPECTED_SOURCE_MATRIX_SHA:
        errors.append("Step11 must bind the published Step09 capability matrix")
    doctor = document.get("doctor_evidence", {})
    if doctor.get("result_sha256") != EXPECTED_DOCTOR_SHA:
        errors.append("Step11 doctor evidence hash drifted")
    if doctor.get("observed_channel_count") != 15 or doctor.get("doctor_success_is_not_acquisition_success") is not True:
        errors.append("doctor evidence must retain the 15-channel and non-success semantics")
    channels = {entry.get("channel"): entry for entry in document.get("channel_health", [])}
    if set(channels) != CHANNELS:
        errors.append("channel health set drifted")
    for channel, (doctor_status, active_backend, status) in EXPECTED_CHANNEL_STATUS.items():
        entry = channels.get(channel, {})
        if (entry.get("doctor_status"), entry.get("active_backend"), entry.get("acquisition_status")) != (doctor_status, active_backend, status):
            errors.append(f"channel health drifted: {channel}")
        if entry.get("environment_availability") != status:
            errors.append(f"channel environment status drifted: {channel}")
        if entry.get("provider_local_policy_inherited") is not False:
            errors.append(f"provider-local policy inherited for {channel}")
    capabilities = {entry.get("capability_id"): entry for entry in document.get("capability_detection", [])}
    if set(capabilities) != CAPABILITIES:
        errors.append("capability detection set drifted")
    for capability_id in AUTHENTICATED:
        if capabilities.get(capability_id, {}).get("status") not in {"AUTH_REQUIRED", "OWNER_APPROVAL_REQUIRED"}:
            errors.append(f"authenticated capability was not fail-closed: {capability_id}")
    if document.get("health_semantics", {}).get("active_backend_is_not_permission") is not True:
        errors.append("active backend was promoted to permission")
    if document.get("health_semantics", {}).get("detected_backend_is_not_invocation_success") is not True:
        errors.append("detected backend was promoted to invocation success")
    safety = document.get("safety_evidence", {})
    for key in ("cookie_or_session_access", "system_install", "system_configuration_change", "persistent_provider_config_written", "external_write"):
        if safety.get(key) is not False:
            errors.append(f"safety boundary widened: {key}")
    if safety.get("credential_content_access") != "NONE" or safety.get("home_xdg_file_count_after") != 0:
        errors.append("credential or isolated-runtime cleanup boundary widened")
    boundaries = document.get("boundaries", {})
    if boundaries.get("authenticated_channel_admission") != "NO_AUTHENTICATED_CHANNEL_ADMISSION":
        errors.append("authenticated channel admission must remain closed")
    if boundaries.get("current_integration") != "NOT_CURRENT_INTEGRATION" or boundaries.get("production_readiness") != "NOT_PRODUCTION_READY":
        errors.append("Current or production boundary widened")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_STEP11_AGENT_REACH_HEALTH_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK149_STEP11_AGENT_REACH_HEALTH_OK channels=15 capabilities=17 doctor_success_not_acquisition=true auth_admission=closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
