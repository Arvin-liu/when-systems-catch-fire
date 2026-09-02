#!/usr/bin/env python3
"""Fail-closed validation for the Task149 Owner adjudication record."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/task149-owner-adjudication-r1.json"
SCHEMA_PATH = ROOT / "schemas/operations/task149-owner-adjudication-r1.schema.json"
FINAL_REPORT_PATH = ROOT / "data/operations/iterations/149/final-report-external-capability-provider-adapter-spikes-r0.json"
CONTRACT_PATH = ROOT / "data/operations/iterations/149/provider-adapter-contract-r0.json"
CURRENT_FACTS_PATH = ROOT / "data/architecture/current-facts.json"
REGISTRY_PATH = ROOT / "data/operations/ignition-operation-capability-registry-r1.json"
CLAIM_REGISTRY_PATH = ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl"

EXPECTED_HEAD = "04cba7fe60ac73a13116b5b2acec5251c03cb308"
# The Owner record was reviewed before the final Task149 refresh, but its
# Current-state assertions describe the merged-main projection.  Keep that
# historical projection pinned so later Task150 Current changes do not rewrite
# the meaning of this record.
TASK149_CURRENT_MAIN = "d7372c27abe456b5b8c058675630d8038f91b448"
EXPECTED_CONTRACT_SHA = "9abb57273e34f98271394099a6ecefa250def26992e1f31d83b8824857ca4649"
EXPECTED_FINAL_REPORT_SHA = "921b9c53068825d0e212e1c522ec89a0bd74a44e2f7327e573cc7347439ee0ff"
EXPECTED_HUMAN_REPORT_SHA = "d22fbb9ae30003ac68a15f5a83e6b0bfa082411a3cc37296fe9965eff9f86bae"
EXPECTED_KNOWLEDGE_SEARCH_RECORDS = 24422
EXPIRED_EXCEPTION = "IGNITION-149-PROVIDER-ADAPTER-SPIKE"
REPLACEMENT_EXCEPTION = "HISTORICAL_OR_EXPERIMENTAL_PROVIDER_EVIDENCE_NO_RUNTIME_AUTHORITY"
TASK149_NONFUNCTION_IDS = {
    "NFC-98a78fb43c197995",
    "NFC-b69088986bec56f3",
    "NFC-3c5227edb0c17073",
    "NFC-b3c5c7948b976bda",
    "NFC-539e81e21c559678",
    "NFC-0e22bc9d70db50fa",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_bytes(commit: str, relative_path: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=REPO_ROOT,
        stderr=subprocess.DEVNULL,
    )


def git_json(commit: str, relative_path: str) -> Any:
    return json.loads(git_bytes(commit, relative_path).decode("utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]

    formal = document.get("formal_observation", {})
    if formal.get("reviewed_formal_head_before_record") != EXPECTED_HEAD:
        errors.append("Owner adjudication must bind the corrected A4 formal head")

    contract = load_json(CONTRACT_PATH)
    if sha256(CONTRACT_PATH) != EXPECTED_CONTRACT_SHA:
        errors.append("provider-neutral contract hash drifted")
    if contract.get("research_scope") != "EXPERIMENTAL_PROVIDER_ADMISSION_RESEARCH_ONLY":
        errors.append("contract research scope is not experimental-only")
    if contract.get("runtime_interface_status") != "NOT_A_CURRENT_RUNTIME_PROVIDER_INTERFACE":
        errors.append("contract runtime interface boundary widened")

    final_report = load_json(FINAL_REPORT_PATH)
    if sha256(FINAL_REPORT_PATH) != EXPECTED_FINAL_REPORT_SHA:
        errors.append("historical Step16 machine report hash drifted")
    human_path = REPO_ROOT / final_report.get("human_report_path", "")
    if not human_path.is_file() or hashlib.sha256(human_path.read_bytes()).hexdigest() != EXPECTED_HUMAN_REPORT_SHA:
        errors.append("historical Step16 human report hash drifted")
    recommendations = final_report.get("recommendations", {})
    if recommendations.get("archify", {}).get("recommendation") != "CONTINUE_EXPERIMENT":
        errors.append("Archify decision is not CONTINUE_EXPERIMENT")
    if recommendations.get("agent_reach_public", {}).get("recommendation") != "CONTINUE_EXPERIMENT":
        errors.append("public Agent Reach decision is not CONTINUE_EXPERIMENT")
    authenticated = recommendations.get("agent_reach_authenticated", {})
    if authenticated.get("recommendation") != "DEFER" or authenticated.get("authenticated_calls") != 0:
        errors.append("authenticated Agent Reach decision/call boundary widened")
    if final_report.get("overall_status") != "PROVIDER_ADMISSION_CANDIDATE":
        errors.append("historical overall status drifted")
    if final_report.get("exact_next_action") != "AWAIT_OWNER_PROVIDER_ADAPTER_REVIEW":
        errors.append("historical Step16 next action was rewritten")

    facts = git_json(TASK149_CURRENT_MAIN, "ignition/data/architecture/current-facts.json")
    if facts.get("current_formal_task_id") != "IGNITION-20260829-148":
        errors.append("Current facts no longer identify Task148")
    if facts.get("facts", {}).get("foundation", {}).get("nonfunction_claims") != 17859:
        errors.append("Current facts nonfunction count drifted")
    if facts.get("facts", {}).get("knowledge_experience", {}).get("search_records") != EXPECTED_KNOWLEDGE_SEARCH_RECORDS:
        errors.append("Current facts Knowledge search count drifted")

    registry = git_json(TASK149_CURRENT_MAIN, "ignition/data/operations/ignition-operation-capability-registry-r1.json")
    if len(registry.get("operations", [])) != 19:
        errors.append("Current operation registry count changed")
    provider_like = [value for value in registry.values() if isinstance(value, str) and any(token in value.lower() for token in ("archify", "agent reach", "provider"))]
    if provider_like:
        errors.append("Current operation registry contains a provider-like string")

    policy_text = git_bytes(
        TASK149_CURRENT_MAIN,
        "ignition/data/agent-federation/build-vs-integrate-policy-r1.json",
    ).decode("utf-8")
    if EXPIRED_EXCEPTION in policy_text:
        errors.append("expired Task149 draft exception survived")
    if REPLACEMENT_EXCEPTION not in policy_text:
        errors.append("replacement evidence-only exception is missing")

    canonical_ids = {
        json.loads(line)["canonical_id"]
        for line in git_bytes(
            TASK149_CURRENT_MAIN,
            "ignition/data/foundation/nonfunction-claims/claim-registry.jsonl",
        ).decode("utf-8").splitlines()
        if line.strip()
    }
    if canonical_ids & TASK149_NONFUNCTION_IDS:
        errors.append("Task149 operational record IDs remain canonical nonfunction claims")

    boundary = document.get("authority_boundary", {})
    if boundary.get("current_provider_capability_added") is not False or boundary.get("current_operation_registry_changed") is not False:
        errors.append("Owner adjudication boundary allows Current capability or operation change")
    if boundary.get("authenticated_channel_admission") != "NO_AUTHENTICATED_CHANNEL_ADMISSION" or boundary.get("authenticated_calls") != 0:
        errors.append("Owner adjudication authenticated boundary widened")
    if boundary.get("live_external_invocation") != "OPEN_OWNER_DEFERRED_NOT_RUN":
        errors.append("live external invocation boundary changed")

    lifecycle = document.get("lifecycle_boundary", {})
    if lifecycle.get("ready_authorized_by_this_record") is not False or lifecycle.get("merge_executed_by_this_record") is not False:
        errors.append("Owner adjudication performed a lifecycle transition")
    if lifecycle.get("task150_creation") != "BLOCKED_UNTIL_A8_FRESH_MAIN_CLOSEOUT" or lifecycle.get("task150_scope_if_a8_passes") != "ARCHIFY_ONLY":
        errors.append("Task150 lifecycle boundary widened")

    evidence = document.get("retained_evidence_and_residuals", {})
    if evidence.get("archify", {}).get("validation") != "PASS 9/9":
        errors.append("Archify PASS 9/9 evidence was not retained")
    if len(evidence.get("archify", {}).get("residuals", [])) != 4:
        errors.append("Archify residual set was not retained")
    if len(evidence.get("agent_reach_public", {}).get("residuals", [])) != 6:
        errors.append("public Agent Reach residual set was not retained")
    if evidence.get("agent_reach_authenticated", {}).get("residuals") != [
        "authenticated/session-bearing channels remain deferred and no admission queue exists"
    ]:
        errors.append("authenticated residual boundary was not retained")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_OWNER_ADJUDICATION_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK149_OWNER_ADJUDICATION_OK archify=FIT_WITH_LIMITS/CONTINUE_EXPERIMENT agent_reach_public=FIT_WITH_LIMITS/CONTINUE_EXPERIMENT authenticated=DEFER ready=CONDITIONAL_ON_A6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
