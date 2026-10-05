#!/usr/bin/env python3
"""Fail-closed consistency checks for the R2.2 local-only proof package."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
R = json.loads((ROOT / "proof-receipt.json").read_text(encoding="utf-8"))
FAIL = []
def require(condition, message):
    if not condition:
        FAIL.append(message)

require(R.get("marker") == "TASK229_R4_RUNTIME_PREREGISTRATION_R2_2_LOCAL_TOOL_PROOF_FROZEN_EXECUTION_NOT_STARTED", "success marker mismatch")
identity = R.get("codex_identity", {})
require(identity.get("version") == "codex-cli 0.159.2", "Codex version mismatch")
require(identity.get("identity_status") == "PASS_VERSION_PATH_SHA256", "Codex binary identity not pinned")
require(R.get("CODEX_HOME_config_assertion", {}).get("status") == "PASS", "CODEX_HOME config assertion failed")
require(R.get("effective_local_provider_config", {}).get("status") == "PASS_BEFORE_THREAD_START_IN_BOTH_COMPLETED_REPETITIONS", "effective provider gate not proven")
require(R.get("effective_local_provider_config", {}).get("provider_id") == "local_loopback", "local provider id mismatch")
require(R.get("egress_boundary", {}).get("external_provider_or_model_requests_transmitted") == 0, "external provider/model request count is nonzero")
require(R.get("egress_boundary", {}).get("non_loopback_attempts_observed_by_proxy") == 0, "non-loopback proxy attempts observed")
repetitions = R.get("repetitions", [])
require(len(repetitions) == 2, "expected exactly two complete repetitions")
for expected, run in enumerate(repetitions, 1):
    a = run.get("assertions", {})
    require(run.get("run") == expected and run.get("status") == "COMPLETE_PASS", f"run {expected} is not complete PASS")
    require(a.get("config_written_realpath_equals_CODEX_HOME_config_toml") is True, f"run {expected} config path mismatch")
    require(a.get("config_parsed_as_TOML") is True, f"run {expected} config TOML parse failed")
    require(a.get("effective_provider_id") == "local_loopback", f"run {expected} effective provider mismatch")
    require(a.get("effective_base_url_loopback") is True, f"run {expected} effective URL is not loopback")
    require(a.get("requires_openai_auth") is False, f"run {expected} local provider requires auth")
    require(a.get("request_max_retries") == 0 and a.get("stream_max_retries") == 0, f"run {expected} retries not zero")
    require(a.get("thread_start_ephemeral") is True, f"run {expected} thread is not ephemeral")
    require(a.get("thread_start_sandbox", {}).get("type") == "readOnly" and a.get("thread_start_sandbox", {}).get("networkAccess") is False, f"run {expected} thread sandbox mismatch")
    require(a.get("thread_start_runtime_workspace_roots") == [] and a.get("thread_start_environments") == [], f"run {expected} thread scope not empty")
    require(a.get("requested_dynamic_tools") == [] and a.get("requested_selected_capability_roots") == [], f"run {expected} requested dynamic/capability surfaces not empty")
    tools = a.get("tool_assertion", {})
    require(tools.get("pass") is True and tools.get("tools_field") == "empty_array", f"run {expected} model-facing tools field not empty")
    require(tools.get("nonempty_tool_namespace_keys") == [], f"run {expected} unexpected tool namespace present")
    require(a.get("loopback_mock_requests") == 1 and a.get("non_loopback_proxy_attempts") == 0, f"run {expected} request or egress count mismatch")
    require(a.get("process_cleanup", {}).get("clean_exit") is True and a.get("process_cleanup", {}).get("exit_code") == 0, f"run {expected} process cleanup failed")
    require(a.get("warnings") == ["Model metadata for `r2-2-local-synthetic` not found. Defaulting to fallback metadata; this can degrade performance and cause issues."], f"run {expected} warning set changed")
    for digest in [a.get("config_file_sha256"), a.get("request_body_sha256"), a.get("full_loopback_http_request_sha256"), a.get("assistant_payload_sha256"), a.get("normalized_model_request_sha256"), a.get("capture_manifest_sha256"), *a.get("capture_hashes", {}).values()]:
        require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None, f"run {expected} malformed SHA-256")
d = R.get("determinism", {})
require(d.get("status") == "PASS" and d.get("complete_fresh_repetitions") == 2, "two-run determinism not PASS")
require(d.get("same_model_facing_tool_inventory") is True and d.get("same_normalized_model_request") is True and d.get("same_thread_isolation") is True and d.get("same_assistant_payload") is True, "stable semantic proof fields differ")
require(R.get("counts", {}).get("live_canary_attempts") == 0 and R.get("counts", {}).get("R4_live_units_attempted") == 0 and R.get("counts", {}).get("evaluator_runs") == 0 and R.get("counts", {}).get("Task230_started") is False, "forbidden action count mismatch")
abort = R.get("preflight_and_aborted_attempts", {}).get("aborted_attempt", {})
require(abort.get("status") == "ABORTED_BEFORE_LOCAL_MODEL_REQUEST_NOT_A_TOOL_INVENTORY_RESULT" and abort.get("local_mock_model_requests") == 0, "preliminary aborted attempt was misclassified")
if FAIL:
    print("R2.2_LOCAL_PROOF_PACKAGE_INVALID")
    for item in FAIL:
        print("FAIL", item)
    sys.exit(1)
print("R2.2_LOCAL_PROOF_PACKAGE_VALID; two complete local tool-inventory runs; zero external/provider requests; no live canary/R4/evaluator/Task230")
