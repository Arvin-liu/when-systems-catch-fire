#!/usr/bin/env python3
"""Validate the R3 candidate contract and exact protected-PR evidence.

R3 remains a candidate until an independent Owner-approved 1111 witness binds
the actual final main SHA. Without that witness, R2 remains effective.
"""

from __future__ import annotations

import argparse
import base64
import copy
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote, urlparse

from jsonschema import Draft202012Validator, FormatChecker


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
PROTOCOL_PATH = ROOT / "data/operations/release-transaction-protocol-r3.json"
SCHEMA_PATH = ROOT / "schemas/operations/release-transaction-protocol-r3.schema.json"
R2_PROTOCOL_PATH = ROOT / "data/operations/release-transaction-protocol-r2.json"
RECOVERY_STATE_PATH = ROOT / "data/operations/release-transaction-recovery-state-r1.json"
CURRENT_TASK_PATH = ROOT / "data/operations/current-task-lineage-status.json"
TASK_IDENTITY_MODEL_PATH = ROOT / "data/operations/task-identity-model-r1.json"
OWNER_AUTHORIZATION_REPOSITORY = "Arvin-liu/1111"
OWNER_AUTHORIZATION_PATH = "instructions/goal-mode/IGNITION-2026-10-24-R3-ONE-TIME-TRANSITION-AUTHORIZATION-R1.json"
SUCCESSOR_REGISTRATION_PATH = "instructions/goal-mode/IGNITION-R3-ADMISSION-SUCCESSOR-REGISTRATION-R3.json"
R2_RESTORE_AUTHORIZATION_PATH = "instructions/goal-mode/IGNITION-R3-TO-R2-RESTORE-AUTHORIZATION-R1.json"
TRANSITION_WITNESS_PATH = "reports/operations/IGNITION-2026-10-18-R3-PUBLISHED-AND-VERIFIED-R0.json"
R2_RESTORATION_WITNESS_PATH = "reports/operations/IGNITION-R3-TO-R2-RESTORED-AND-VERIFIED-R1.json"
SUCCESSOR_PROTOCOL_PATH = ROOT / "data/operations/release-transaction-protocol-r3-successor-r1.json"
SUCCESSOR_SCHEMA_PATH = ROOT / "schemas/operations/release-transaction-protocol-r3-successor-r1.schema.json"
SUCCESSOR_REGISTRATION_PREFIX = "instructions/goal-mode/r3-successors/registrations/"
SUCCESSOR_AUTHORIZATION_PREFIX = "instructions/goal-mode/r3-successors/authorizations/"
SUCCESSOR_REVOCATION_PREFIX = "instructions/goal-mode/r3-successors/revocations/"
SUCCESSOR_SUPERSESSION_PREFIX = "instructions/goal-mode/r3-successors/supersessions/"
SUCCESSOR_REVIEW_PREFIX = "instructions/goal-mode/r3-successors/reviews/"
SUCCESSOR_PUBLICATION_PREFIX = "reports/operations/r3-successors/publications/"
SUCCESSOR_MIGRATION_PREFIX = "reports/operations/r3-successors/migrations/"
SUCCESSOR_LEDGER_PREFIXES = (
    SUCCESSOR_REGISTRATION_PREFIX,
    SUCCESSOR_AUTHORIZATION_PREFIX,
    SUCCESSOR_REVOCATION_PREFIX,
    SUCCESSOR_SUPERSESSION_PREFIX,
    SUCCESSOR_REVIEW_PREFIX,
    SUCCESSOR_PUBLICATION_PREFIX,
    SUCCESSOR_MIGRATION_PREFIX,
)
SUCCESSOR_PROTOCOL_ID = "RELEASE_TRANSACTION_PROTOCOL_R3_SUCCESSOR_R1"
SUCCESSOR_ROOT_PR_NUMBER = 163
SUCCESSOR_ROOT_MERGE_SHA = "5f5af13ba5cd32b9e8a363ff8672f01f65d375c6"
SUCCESSOR_ROOT_HEAD_SHA = "9742a6c229bfbc9d403124e8f78b7613ea05b2c8"
SUCCESSOR_ROOT_BASE_SHA = "dda58027561c1c8fc99e3fa22e2e3eab6e20b69d"
SUCCESSOR_ROOT_TREE_SHA = "1eac0c48bae58e7df78f764cff516ec2436e342b"
SUCCESSOR_ROOT_PARENTS = [SUCCESSOR_ROOT_BASE_SHA, SUCCESSOR_ROOT_HEAD_SHA]
SUCCESSOR_ROOT_AUTHORITY_PATH = "instructions/goal-mode/IGNITION-2026-11-04-OWNER-ROOT-GOVERNANCE-AUTHORITY-R0.json"
SUCCESSOR_ROOT_AUTHORITY_BLOB = "dc63d9a94c1edb9f633a15918def762c17eafe1d"
SUCCESSOR_ROOT_AUTHORITY_SHA256 = "995b12e2c86d9af6788c92b6a04780dbb513af4b92aefe2bf194838549c751bc"
SUCCESSOR_ROOT_INSTRUCTION_PATH = "instructions/IGNITION-2026-11-04-R3-SUCCESSOR-PROTOCOL-AMENDMENT-INSTRUCTION-R0.md"
SUCCESSOR_ROOT_INSTRUCTION_BLOB = "cdf9f4783eae4f509d2a44f4bcacbaf4eb97a687"
SUCCESSOR_ROOT_INSTRUCTION_SHA256 = "e6ae8406ddf68904e4d85f1aff3f823686e0e0a6b7a4f428e8eaca19e887dea9"
TASK22_IDENTITY_PR_NUMBER = 165
TASK22_IDENTITY_BASE_SHA = "5f5af13ba5cd32b9e8a363ff8672f01f65d375c6"
TASK22_IDENTITY_HEAD_SHA = "17ed13c274630269062e84834d52b49f34236931"
TASK22_IDENTITY_MERGE_SHA = "5449650811882f0c107e58680ee43d92577f7288"
TASK22_IDENTITY_TREE_BLOB = "146df919b91ddf2bf189a106441abee80486056d"
TASK22_IDENTITY_FILE_SHA256 = "f4300d22378458b1ed36ccb168cbe67be71c8056706005af331e3bd93c6ccc05"
TASK22_IDENTITY_PATH = "instructions/goal-mode/IGNITION-2026-11-05-TASK22-OWNER-IDENTITY-ASSIGNMENT-R0.json"
HISTORICAL_ADJUDICATION_PR_NUMBER = 162
HISTORICAL_ADJUDICATION_MERGE_SHA = "dda58027561c1c8fc99e3fa22e2e3eab6e20b69d"
HISTORICAL_AUDIT_PATH = "reports/operations/IGNITION-2026-11-04-TASK21-PR267-POSTMERGE-INDEPENDENT-AUDIT-R0.md"
HISTORICAL_AUDIT_BLOB = "d8ca4bd6a3d40af88655b3c8e13917810ff99998"
HISTORICAL_R3_BLOCKER_PATH = "reports/operations/IGNITION-2026-11-04-TASK21-NEW-MAIN-R3-WITNESS-BLOCKER-R0.md"
HISTORICAL_R3_BLOCKER_BLOB = "d335fb700e6ce50fcb75195fe09d8919b7d833d8"
HISTORICAL_OWNER_DECISION_PATH = "reports/operations/IGNITION-2026-11-04-TASK21-OWNER-FINAL-ADJUDICATION-CANDIDATE-R0.md"
HISTORICAL_OWNER_DECISION_BLOB = "3744b481d6a2688c15022bbd9dbee0c004a979e9"
PUBLIC_REPOSITORY = "Arvin-liu/when-systems-catch-fire"
R2_CANONICAL_SUITE_MINIMUM_SECONDS = 14400
GITHUB_WEB_FLOW_ACCOUNT_ID = 19864447
MAX_FIRST_PARENT_CONTROL_PATH_SCAN = 10000


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def _schema_errors(document: Any, schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
    return [f"{error.json_path}: {error.message}" for error in errors]


def validate_contract(document: dict[str, Any] | None = None) -> list[str]:
    protocol = document if document is not None else load_json(PROTOCOL_PATH)
    schema = load_json(SCHEMA_PATH)
    errors = _schema_errors(protocol, schema)
    if errors:
        return errors

    r2 = load_json(R2_PROTOCOL_PATH)
    r2_gates = r2["pre_publication_hard_gates"]
    preserved = protocol["preserved_hard_gates"]
    if preserved["required_gate_ids"] != r2_gates["required_gate_ids"]:
        errors.append("R3 must preserve the exact R2 required-gate set and order")
    preserved_suite = preserved["canonical_full_suite"]
    r2_suite = r2_gates["canonical_full_suite"]
    for field in ("zero_failures_errors_skips", "clean_before_after", "exact_candidate_sha", "no_watchdog"):
        if preserved_suite.get(field) != r2_suite.get(field):
            errors.append(f"R3 must preserve the R2 canonical full-suite gate value for {field}")
            break
    count_exception = protocol["r2_full_suite_count_exception"]
    if count_exception["r2_required_runs"] != r2_suite["required_runs"]:
        errors.append("R3 must identify the unchanged R2 canonical full-suite run-count clause being explicitly excepted")
    if count_exception["r2_required_runs"] != 2:
        errors.append("R2 historical canonical full-suite run count must remain two")
    if count_exception["r3_run_count_policy"] != preserved_suite["run_count_policy"]:
        errors.append("R3 run-count exception and canonical suite evidence policy disagree")
    if not count_exception["explicit_owner_approval_required"] or not count_exception["r3_requires_complete_evidence_and_independent_revalidation"]:
        errors.append("R3 run-count exception must require complete evidence, independent revalidation and explicit Owner approval")
    publication_exception = protocol["r2_publication_method_exception"]
    r2_publication_method = r2.get("main_mutation_policy", {}).get("mode")
    if publication_exception["r2_publication_method"] != r2_publication_method:
        errors.append("R3 must identify the unchanged R2 fast-forward publication method being explicitly excepted")
    if publication_exception["r2_publication_method"] != "ORDINARY_FAST_FORWARD_ONLY":
        errors.append("R2 historical publication method must remain ordinary fast-forward only")
    if publication_exception["r3_publication_method"] != "PROTECTED_GITHUB_PR_MERGE_COMMIT" or protocol["prepublication"]["required_merge_method"] != "MERGE_COMMIT":
        errors.append("R3 publication exception must specify the protected PR merge-commit path")
    if not publication_exception["explicit_owner_approval_required"]:
        errors.append("R3 publication-method exception must require explicit Owner approval")
    duration_policy = protocol["canonical_suite_duration_policy"]
    exception = duration_policy["r2_duration_exception"]
    if exception["r2_minimum_natural_window_seconds"] != r2_suite["minimum_natural_window_seconds"]:
        errors.append("R3 must identify the unchanged R2 duration clause being explicitly excepted")
    if exception["r2_minimum_natural_window_seconds"] != R2_CANONICAL_SUITE_MINIMUM_SECONDS:
        errors.append("R2 historical minimum natural window must remain 14,400 seconds")
    if exception["r3_candidate_duration_threshold"] != "NONE" or not exception["explicit_owner_approval_required"]:
        errors.append("R3 duration exception must have no elapsed-time threshold and require explicit Owner approval")
    if duration_policy["elapsed_duration_semantics"] != "OBSERVED_NATURAL_ELAPSED_SECONDS_ONLY":
        errors.append("R3 must record natural elapsed duration as an observed value only")
    if not duration_policy["natural_process_exit_required"] or not duration_policy["watchdog_termination_fails"]:
        errors.append("R3 must require successful natural process exit and fail watchdog termination")
    if protocol["effective_policy_before_activation"] != r2["contract_id"]:
        errors.append("R2 remains current until a matching independent transition receipt is verified")
    if protocol["status"] != "CANDIDATE_NOT_EFFECTIVE":
        errors.append("an unmerged R3 candidate cannot declare itself effective")
    required_contexts = protocol["prepublication"]["required_status_check_contexts"]
    branch_policy = protocol["branch_protection_requirements"]
    if required_contexts != branch_policy["required_status_check_contexts"]:
        errors.append("prepublication and branch-protection required contexts must match exactly")
    if sorted(item["context"] for item in required_contexts) != sorted(protocol["prepublication"]["required_workflow_names"]):
        errors.append("required workflow names must exactly equal the unique required status contexts")
    if protocol["prepublication"]["minimum_approving_reviews"] != 0 or protocol["prepublication"]["self_approval_is_not_required"] is not True:
        errors.append("single-Owner admission must not require an impossible self-approval")
    if any(
        branch_policy.get(field) is not True
        for field in (
            "require_code_owner_review_disabled",
            "require_last_push_approval_disabled",
            "require_linear_history_disabled",
        )
    ):
        errors.append("single-Owner merge-commit policy must explicitly disable code-owner/last-push reviews and linear history")
    if protocol["postactivation_recovery"]["target_r2_protocol_blob_sha"] != git_blob_sha(R2_PROTOCOL_PATH):
        errors.append("R3 recovery must target the exact preserved R2 protocol blob")
    try:
        recovery_state = load_json(RECOVERY_STATE_PATH)
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"R3 recovery state is missing or unreadable: {error}")
    else:
        recovery_errors = _schema_errors(
            recovery_state, {"$ref": "#/$defs/recoveryState", "$defs": schema["$defs"]}
        )
        errors.extend(f"R3 recovery state: {item}" for item in recovery_errors)
        if recovery_state.get("source_r3_protocol_blob_sha") != git_blob_sha(PROTOCOL_PATH):
            errors.append("R3 recovery state must bind the exact candidate protocol blob")
        if recovery_state.get("target_r2_protocol_blob_sha") != git_blob_sha(R2_PROTOCOL_PATH):
            errors.append("R3 recovery state must bind the exact preserved R2 protocol blob")
    return errors


def git_blob_sha(path: Path = PROTOCOL_PATH) -> str:
    content = path.read_bytes()
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def validate_successor_protocol_contract(
    document: dict[str, Any] | None = None,
) -> list[str]:
    """Validate the forward-only successor profile without changing effective R3.

    R3's signed bootstrap protocol and #266 receipt remain byte-for-byte fixed.
    This profile is inert until the later, exact Formal-merge migration witness
    has itself been verified on 1111/main.
    """
    try:
        successor = document if document is not None else load_json(SUCCESSOR_PROTOCOL_PATH)
        schema = load_json(SUCCESSOR_SCHEMA_PATH)
        legacy = load_json(PROTOCOL_PATH)
    except (OSError, json.JSONDecodeError) as error:
        return [f"R3 successor protocol or schema is unreadable: {error}"]
    errors = _schema_errors(successor, schema)
    if errors:
        return errors
    if git_blob_sha(PROTOCOL_PATH) != successor["inherits_from"]["bootstrap_protocol_blob_sha"]:
        errors.append("successor profile must inherit the byte-exact R3 bootstrap protocol blob")
    if legacy["owner_authorization_integrity"]["record_path"] != successor["inherits_from"]["legacy_bootstrap_authorization_path"]:
        errors.append("successor profile changed the historical R3 bootstrap authorization path")
    if legacy["identity_binding"]["successor_registration"]["authority_path"] != successor["inherits_from"]["legacy_successor_registration_path"]:
        errors.append("successor profile changed the historical R3 successor registration path")
    if legacy["independent_witness"]["path"] != successor["inherits_from"]["legacy_publication_witness_path"]:
        errors.append("successor profile changed the historical #266 publication witness path")
    if successor["status"] != "CANDIDATE_NOT_EFFECTIVE":
        errors.append("successor profile cannot activate itself from repository content")
    return errors


def authoritative_task_context() -> tuple[dict[str, Any], list[str]]:
    """Load formal identity from the checked-out canonical sources; never infer it."""
    errors: list[str] = []
    try:
        lineage = load_json(CURRENT_TASK_PATH)
        identity_model = load_json(TASK_IDENTITY_MODEL_PATH)
        candidate_binding = identity_model["role_bindings"]["release_candidate_task"]
        execution_path = ROOT.parent / candidate_binding["source_path"]
        execution = load_json(execution_path)
    except (KeyError, OSError, json.JSONDecodeError) as error:
        return {}, [f"canonical task identity sources are incomplete: {error}"]

    task_id = lineage.get("current_task", {}).get("task_id")
    binding = identity_model.get("role_bindings", {}).get("current_formal_task", {})
    if binding.get("source_path") != "ignition/data/operations/current-task-lineage-status.json" or binding.get("json_pointer") != "/current_task/task_id":
        errors.append("task identity model does not bind the canonical current-task source")
    release_binding = identity_model.get("role_bindings", {}).get("release_candidate_task", {})
    if release_binding.get("json_pointer") != "/identity_expectations/release_candidate_task":
        errors.append("task identity model does not bind the release-candidate execution contract")
    if not task_id or execution.get("task_id") != task_id:
        errors.append("lineage, identity model and authorized execution contract task IDs disagree")
    task_match = (
        re.fullmatch(r"IGNITION-[0-9]{8}-(?P<ordinal>[0-9]{3})", task_id)
        if isinstance(task_id, str) else None
    )
    if execution.get("identity_expectations", {}).get("current_formal_task") != task_id or execution.get("identity_expectations", {}).get("release_candidate_task") != task_id:
        errors.append("lineage, identity model and authorized execution contract task IDs disagree")

    ordinal = next((execution.get(key) for key in ("formal_ordinal", "task_ordinal", "ordinal") if type(execution.get(key)) is int), None)
    branch = execution.get("expected_task_branch")
    receipt_branch = execution.get("expected_receipt_branch")
    formal_base_main_sha = execution.get("formal_baseline", {}).get("sha")
    if ordinal is None:
        errors.append("canonical execution contract does not bind a formal task ordinal")
    elif task_match is None or int(task_match.group("ordinal")) != ordinal:
        errors.append("canonical execution-contract ordinal differs from its canonical task ID")
    if not isinstance(branch, str) or not branch:
        errors.append("canonical execution contract does not bind an expected task branch")
    if not isinstance(receipt_branch, str) or not receipt_branch:
        errors.append("canonical execution contract does not bind an expected 1111 receipt branch")
    if not isinstance(formal_base_main_sha, str) or len(formal_base_main_sha) != 40:
        errors.append("canonical execution contract does not bind the exact formal main base SHA")
    registration = execution.get("successor_registration")
    if not isinstance(registration, dict):
        errors.append("canonical execution contract does not bind a signed 1111 successor registration")
        registration = {}
    registration_profile = registration.get("protocol_id", "R3_BOOTSTRAP_FIXED_PATH")
    successor_registration_path = registration.get("path")
    successor_registration_id = registration.get("registration_id")
    successor_protocol_blob_sha = registration.get("protocol_blob_sha")
    successor_protocol_file_sha256 = registration.get("protocol_file_sha256")
    registration_sha = registration.get("commit_sha")
    registration_file_sha256 = registration.get("file_sha256")
    registration_nonce = registration.get("registration_nonce")
    registration_parent_shas = registration.get("parent_shas")
    if not isinstance(registration_sha, str) or len(registration_sha) != 40:
        errors.append("execution contract does not bind the exact Owner-signed successor-registration commit")
    if registration_profile not in {"R3_BOOTSTRAP_FIXED_PATH", SUCCESSOR_PROTOCOL_ID}:
        errors.append("execution contract names an unsupported successor-registration profile")
    if not isinstance(registration_file_sha256, str) or len(registration_file_sha256) != 64:
        errors.append("execution contract does not bind the successor-registration file digest")
    if not isinstance(registration_nonce, str) or len(registration_nonce) < 32:
        errors.append("execution contract does not bind the exact successor-registration nonce")
    if (
        not isinstance(registration_parent_shas, list)
        or len(registration_parent_shas) != 2
        or any(not isinstance(parent, str) or not re.fullmatch(r"[0-9a-f]{40}", parent) for parent in registration_parent_shas)
    ):
        errors.append("execution contract does not bind the exact ordered two-parent registration commit")

    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    try:
        source_digest = digest(CURRENT_TASK_PATH)
        identity_digest = digest(TASK_IDENTITY_MODEL_PATH)
        execution_digest = digest(execution_path)
    except OSError as error:
        return {}, [f"canonical task identity digest could not be read: {error}"]

    context = {
        "task_id": task_id,
        "formal_ordinal": ordinal,
        "task_branch": branch,
        "receipt_branch": receipt_branch,
        "formal_base_main_sha": formal_base_main_sha,
        "current_task_source_sha256": source_digest,
        "task_identity_model_sha256": identity_digest,
        "execution_contract_sha256": execution_digest,
        "successor_registration_commit_sha": registration_sha,
        "successor_registration_file_sha256": registration_file_sha256,
        "successor_registration_nonce": registration_nonce,
        "successor_registration_parent_shas": registration_parent_shas,
        "successor_registration_profile": registration_profile,
        "successor_registration_path": successor_registration_path,
        "successor_registration_id": successor_registration_id,
        "successor_protocol_blob_sha": successor_protocol_blob_sha,
        "successor_protocol_file_sha256": successor_protocol_file_sha256,
    }
    if not errors:
        if registration_profile == SUCCESSOR_PROTOCOL_ID:
            ledger, ledger_errors = read_authenticated_successor_control_ledger()
            errors.extend(ledger_errors)
            if ledger is not None:
                matches = [row for row in ledger["registrations"] if row["path"] == successor_registration_path]
                if len(matches) != 1:
                    errors.append("execution contract does not resolve to exactly one append-only successor registration")
                else:
                    registration_evidence = matches[0]
                    statement = registration_evidence["statement"]
                    predecessor_match = re.fullmatch(r"IGNITION-[0-9]{8}-(?P<ordinal>[0-9]{3})", statement["predecessor_task_id"])
                    inventory_errors = validate_successor_registration_statement(
                        statement,
                        expected_base_main_sha=formal_base_main_sha,
                        expected_predecessor_task_id=statement["predecessor_task_id"],
                        expected_predecessor_ordinal=int(predecessor_match.group("ordinal")) if predecessor_match else -1,
                        existing_registrations=[row for row in ledger["registrations"] if row["path"] != successor_registration_path],
                    )
                    errors.extend(inventory_errors)
                    if registration_evidence["statement"]["registration_id"] in ledger["superseded_registration_ids"]:
                        errors.append("execution contract selects an Owner-superseded task registration")
                    protocol_digest = hashlib.sha256(SUCCESSOR_PROTOCOL_PATH.read_bytes()).hexdigest()
                    if not any(row["statement"]["protocol_sha256"] == protocol_digest for row in ledger["migrations"]):
                        errors.append("successor protocol has no effective Owner-verified Formal migration witness")
                    if (
                        statement["task_id"] != task_id or statement["formal_ordinal"] != ordinal
                        or statement["work_branch"] != branch or statement["receipt_branch"] != receipt_branch
                        or statement["formal_base_main_sha"] != formal_base_main_sha
                        or statement["registration_nonce"] != registration_nonce
                        or registration_evidence["commit_sha"] != registration_sha
                        or registration_evidence["file_sha256"] != registration_file_sha256
                        or registration_evidence["parents"] != registration_parent_shas
                        or registration.get("registration_id") != statement["registration_id"]
                        or registration.get("protocol_blob_sha") != statement["protocol_blob_sha"]
                        or registration.get("protocol_file_sha256") != statement["protocol_file_sha256"]
                        or statement["protocol_blob_sha"] != git_blob_sha(SUCCESSOR_PROTOCOL_PATH)
                    ):
                        errors.append("Owner-signed successor registration differs from the exact task contract, protocol, base, nonce or ordered parents")
                    try:
                        current_task_content = _gh_api_json(
                            f"repos/{PUBLIC_REPOSITORY}/contents/{quote(relative(CURRENT_TASK_PATH), safe='/')}?ref={quote(formal_base_main_sha, safe='')}"
                        )
                        task_bytes, _ = _decode_control_file(current_task_content, PUBLIC_REPOSITORY, relative(CURRENT_TASK_PATH), formal_base_main_sha)
                        predecessor_id = json.loads(task_bytes.decode("utf-8"))["current_task"]["task_id"]
                        if statement["predecessor_task_id"] != predecessor_id:
                            errors.append("successor registration predecessor does not equal the canonical task at its signed Formal base")
                    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                        errors.append(f"canonical predecessor readback failed closed: {error}")
                    context["successor_registration"] = registration_evidence
                    context["successor_control_ledger"] = ledger
        else:
            registration_evidence, registration_errors = read_authenticated_successor_registration(
                registration_sha,
                expected_file_sha256=registration_file_sha256,
                expected_formal_base_main_sha=formal_base_main_sha,
                expected_nonce=registration_nonce,
                expected_parent_shas=registration_parent_shas,
            )
            errors.extend(registration_errors)
            if registration_evidence is not None:
                statement = registration_evidence["statement"]
                if (
                    statement["task_id"] != task_id or statement["formal_ordinal"] != ordinal
                    or statement["work_branch"] != branch or statement["receipt_branch"] != receipt_branch
                    or statement["formal_base_main_sha"] != formal_base_main_sha
                    or statement["registration_nonce"] != registration_nonce
                    or registration_evidence["parents"] != registration_parent_shas
                ):
                    errors.append("Owner-signed successor registration does not match the exact task, ordinal, branches, base, nonce and ordered signed-merge parents")
                if statement["r3_protocol_candidate_blob_sha"] != git_blob_sha():
                    errors.append("Owner-signed successor registration is stale for the exact R3 protocol blob")
                context["successor_registration"] = registration_evidence
    return context, errors


def _gh_api_json(endpoint: str) -> dict[str, Any] | list[Any]:
    """Read GitHub through the user's existing OAuth-backed gh session."""
    result = subprocess.run(
        ["gh", "api", endpoint], check=True, capture_output=True, text=True, timeout=30
    )
    return json.loads(result.stdout)


def _verified_owner_commit(commit: dict[str, Any], owner_id: int) -> tuple[bool, str]:
    """Require Owner authorship plus a verified Owner or GitHub web-flow commit."""
    author_id = (commit.get("author") or {}).get("id")
    committer = commit.get("committer") or {}
    committer_id = committer.get("id")
    verification = (commit.get("commit") or {}).get("verification") or {}
    owner_committer = committer_id == owner_id
    github_web_flow_committer = (
        committer_id == GITHUB_WEB_FLOW_ACCOUNT_ID and committer.get("login") == "web-flow"
    )
    if author_id != owner_id or not (owner_committer or github_web_flow_committer):
        return False, "commit author must be the Owner and committer must be the Owner or GitHub web-flow"
    if verification.get("verified") is not True or verification.get("reason") != "valid":
        return False, "GitHub did not verify the Owner commit signature as valid"
    if not isinstance(verification.get("signature"), str) or not verification["signature"].strip():
        return False, "GitHub commit verification has no signature payload"
    if not isinstance(verification.get("payload"), str) or not verification["payload"].strip():
        return False, "GitHub commit verification has no signed commit payload"
    return True, ""


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def _commit_from_api(
    repository: str,
    commit_sha: str,
    api: Callable[[str], dict[str, Any] | list[Any]],
    cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if commit_sha not in cache:
        commit = api(f"repos/{repository}/commits/{commit_sha}")
        if not isinstance(commit, dict) or commit.get("sha") != commit_sha:
            raise ValueError(f"GitHub commit readback is invalid for {repository}@{commit_sha}")
        tree_sha = (commit.get("commit", {}).get("tree") or {}).get("sha")
        if not isinstance(tree_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", tree_sha):
            raise ValueError(f"GitHub commit has no exact tree SHA for {repository}@{commit_sha}")
        cache[commit_sha] = commit
    return cache[commit_sha]


def _tree_path_entry(
    repository: str,
    tree_sha: str,
    path: str,
    api: Callable[[str], dict[str, Any] | list[Any]],
) -> dict[str, str] | None:
    """Read one exact Git tree path without relying on GitHub's path-history API."""
    if not re.fullmatch(r"[0-9a-f]{40}", tree_sha):
        raise ValueError("Git tree SHA is not an exact SHA-1")
    parts = path.split("/")
    if not path or any(not part or part in {".", ".."} for part in parts):
        raise ValueError("control path is empty or contains an unsafe segment")
    current_tree = tree_sha
    for index, part in enumerate(parts):
        tree = api(f"repos/{repository}/git/trees/{current_tree}")
        if not isinstance(tree, dict) or tree.get("truncated") is True or not isinstance(tree.get("tree"), list):
            raise ValueError(f"Git tree readback is invalid or truncated for {repository}:{path}")
        matches = [entry for entry in tree["tree"] if isinstance(entry, dict) and entry.get("path") == part]
        if not matches:
            return None
        if len(matches) != 1:
            raise ValueError(f"Git tree contains an ambiguous path segment for {repository}:{path}")
        entry = matches[0]
        if index == len(parts) - 1:
            if (
                entry.get("type") != "blob"
                or not isinstance(entry.get("sha"), str)
                or not re.fullmatch(r"[0-9a-f]{40}", entry["sha"])
                or entry.get("mode") not in {"100644", "100755"}
            ):
                raise ValueError(f"fixed control path is not a Git blob for {repository}:{path}")
            return {"sha": entry["sha"], "mode": str(entry.get("mode", "")), "type": "blob"}
        if entry.get("type") != "tree" or not isinstance(entry.get("sha"), str):
            return None
        current_tree = entry["sha"]
    return None


def _path_entry_for_commit(
    repository: str,
    commit_sha: str,
    path: str,
    api: Callable[[str], dict[str, Any] | list[Any]],
    cache: dict[str, dict[str, Any]],
) -> dict[str, str] | None:
    commit = _commit_from_api(repository, commit_sha, api, cache)
    tree_sha = commit["commit"]["tree"]["sha"]
    return _tree_path_entry(repository, tree_sha, path, api)


def _latest_first_parent_path_update(
    repository: str,
    path: str,
    main_sha: str,
    api: Callable[[str], dict[str, Any] | list[Any]],
    cache: dict[str, dict[str, Any]],
) -> tuple[str, dict[str, str] | None, dict[str, str] | None]:
    """Find the newest main first-parent commit that changes this path's tree entry.

    A commits?path query is deliberately not used: GitHub can return an unsigned
    staging commit instead of the signed web-merge commit for merge-heavy paths.
    """
    cursor = main_sha
    for _ in range(MAX_FIRST_PARENT_CONTROL_PATH_SCAN):
        commit = _commit_from_api(repository, cursor, api, cache)
        parents = commit.get("parents")
        if not isinstance(parents, list):
            raise ValueError(f"GitHub commit parents are unreadable for {repository}@{cursor}")
        if not parents:
            raise ValueError(f"fixed control path has no first-parent update on {repository}/main")
        first_parent = parents[0].get("sha") if isinstance(parents[0], dict) else None
        if not isinstance(first_parent, str) or not re.fullmatch(r"[0-9a-f]{40}", first_parent):
            raise ValueError(f"first parent is unreadable for {repository}@{cursor}")
        after = _path_entry_for_commit(repository, cursor, path, api, cache)
        before = _path_entry_for_commit(repository, first_parent, path, api, cache)
        if after != before:
            return cursor, after, before
        cursor = first_parent
    raise ValueError(f"first-parent control-path scan exceeded {MAX_FIRST_PARENT_CONTROL_PATH_SCAN} commits")


def _decode_control_file(content: Any, repository: str, path: str, ref: str) -> tuple[bytes, str]:
    if (
        not isinstance(content, dict)
        or content.get("path") != path
        or content.get("type") != "file"
        or content.get("encoding") != "base64"
        or not isinstance(content.get("content"), str)
    ):
        raise ValueError(f"fixed control path is not readable at {repository}:{path}@{ref}")
    raw = base64.b64decode("".join(content["content"].split()), validate=True)
    blob_sha = _git_blob_sha(raw)
    if content.get("sha") != blob_sha:
        raise ValueError(f"GitHub blob SHA does not bind exact control-file bytes at {repository}:{path}@{ref}")
    return raw, blob_sha


def _read_authenticated_control_path_commit(
    repository: str,
    path: str,
    commit_sha: str | None,
    owner_id: int,
    *,
    expected_file_sha256: str | None = None,
    expected_parent_shas: list[str] | None = None,
    expected_nonce: str | None = None,
    allow_historical_authorization_update: bool = False,
    api: Callable[[str], dict[str, Any] | list[Any]],
) -> tuple[dict[str, Any] | None, list[str]]:
    """Bind a verified Owner signature to the latest fixed-path content update on current main."""
    try:
        if commit_sha is not None and (
            not isinstance(commit_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", commit_sha)
        ):
            return None, [f"fixed control-record commit SHA is not exact for {repository}:{path}"]
        cache: dict[str, dict[str, Any]] = {}
        branch = api(f"repos/{repository}/branches/main")
        main_sha = branch.get("commit", {}).get("sha") if isinstance(branch, dict) else None
        if not isinstance(main_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", main_sha):
            return None, [f"{repository}/main exact commit SHA is unreadable"]
        latest_sha, latest_entry, _latest_before = _latest_first_parent_path_update(
            repository, path, main_sha, api, cache
        )
        if commit_sha is None:
            commit_sha = latest_sha
        if latest_sha != commit_sha:
            return None, [f"signed control record is not the latest first-parent content update to {path} on {repository}/main"]
        if latest_entry is None:
            return None, [f"fixed control path is absent from {repository}/main: {path}"]

        ancestry = api(f"repos/{repository}/compare/{commit_sha}...{main_sha}")
        if not isinstance(ancestry, dict) or ancestry.get("status") not in {"ahead", "identical"}:
            return None, [f"signed control commit is not an ancestor of the exact current {repository}/main tip"]

        commit = _commit_from_api(repository, commit_sha, api, cache)
        signature_ok, signature_error = _verified_owner_commit(commit, owner_id)
        if not signature_ok:
            return None, [f"Owner signature failed closed for {repository}:{path}: {signature_error}"]
        parents = commit.get("parents")
        if not isinstance(parents, list) or len(parents) not in {1, 2}:
            return None, [f"signed control commit has an unsupported parent count for {repository}:{path}"]
        parent_shas = [parent.get("sha") if isinstance(parent, dict) else None for parent in parents]
        if any(not isinstance(parent_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", parent_sha) for parent_sha in parent_shas):
            return None, [f"signed control commit has an unreadable parent for {repository}:{path}"]
        if expected_parent_shas is not None and parent_shas != expected_parent_shas:
            return None, [f"signed control commit parent order differs from the exact expected parents for {repository}:{path}"]
        committer_id = (commit.get("committer") or {}).get("id")
        if committer_id == GITHUB_WEB_FLOW_ACCOUNT_ID and len(parents) != 2:
            return None, [f"GitHub web-flow signed control commit is not a two-parent merge for {repository}:{path}"]

        after_entry = _path_entry_for_commit(repository, commit_sha, path, api, cache)
        before_entry = _path_entry_for_commit(repository, parent_shas[0], path, api, cache)
        if after_entry is None or after_entry != latest_entry:
            return None, [f"signed commit tree does not bind the latest exact fixed-path blob for {repository}:{path}"]
        if before_entry is not None:
            if not allow_historical_authorization_update or path != OWNER_AUTHORIZATION_PATH:
                return None, [f"fixed Owner control path already existed in the signed commit's first parent; replay/update is rejected for {repository}:{path}"]
            if before_entry.get("sha") == after_entry.get("sha"):
                return None, [f"fixed Owner control blob is unchanged from its first parent; replay is rejected for {repository}:{path}"]
        second_parent_entry = None
        if len(parent_shas) == 2:
            second_parent_entry = _path_entry_for_commit(repository, parent_shas[1], path, api, cache)
            if committer_id == GITHUB_WEB_FLOW_ACCOUNT_ID and second_parent_entry != after_entry:
                return None, [f"signed web merge tree differs from its reviewed second-parent fixed path for {repository}:{path}"]

        signed_content = api(f"repos/{repository}/contents/{quote(path, safe='/')}?ref={quote(commit_sha, safe='')}")
        current_content = api(f"repos/{repository}/contents/{quote(path, safe='/')}?ref={quote(main_sha, safe='')}")
        signed_raw, signed_blob_sha = _decode_control_file(signed_content, repository, path, commit_sha)
        current_raw, current_blob_sha = _decode_control_file(current_content, repository, path, main_sha)
        if signed_blob_sha != after_entry["sha"] or current_blob_sha != latest_entry["sha"]:
            return None, [f"GitHub file bytes do not match the signed and current Git tree blobs for {repository}:{path}"]
        if signed_raw != current_raw or signed_blob_sha != current_blob_sha:
            return None, [f"current main fixed-path bytes differ from the exact signed commit for {repository}:{path}"]
        file_sha256 = hashlib.sha256(signed_raw).hexdigest()
        if expected_file_sha256 is not None and file_sha256 != expected_file_sha256:
            return None, [f"fixed control-file SHA-256 differs from the independently bound digest for {repository}:{path}"]
        if expected_nonce is not None:
            statement = json.loads(signed_raw.decode("utf-8"))
            if statement.get("registration_nonce") != expected_nonce:
                return None, [f"fixed control-file nonce differs from the independently bound registration nonce for {repository}:{path}"]
        commit_date = (commit.get("commit", {}).get("committer") or {}).get("date")
        if not isinstance(commit_date, str) or not commit_date:
            return None, [f"signed control commit has no GitHub committer timestamp for {repository}:{path}"]
        return {
            "raw": signed_raw,
            "file_sha256": file_sha256,
            "blob_sha": signed_blob_sha,
            "commit": commit,
            "committed_at": commit_date,
            "main_sha": main_sha,
            "path_update_commit_sha": latest_sha,
            "path_before": before_entry,
            "path_after": after_entry,
            "second_parent_path": second_parent_entry,
            "parents": parent_shas,
        }, []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"authenticated fixed control-path readback failed closed: {error.__class__.__name__}: {error}"]


def read_authenticated_successor_root_authority(
    *, github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Authenticate the one-time governance mandate from its exact Owner merge.

    This root act is external to R3. The function deliberately does not use the
    R3 transition receipt or its fixed bootstrap authorization as the source of
    authority for this amendment.
    """
    api = github_api or _gh_api_json
    try:
        contract = load_json(SUCCESSOR_PROTOCOL_PATH)["root_authority"]
        public_repo = api(f"repos/{PUBLIC_REPOSITORY}")
        control_repo = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}")
        owner_id = (public_repo.get("owner") or {}).get("id")
        if not isinstance(owner_id, int) or owner_id != contract["owner_actor_id"]:
            return None, ["Formal repository Owner differs from the exact Owner identified by the root governance mandate"]
        if (control_repo.get("owner") or {}).get("id") != owner_id:
            return None, ["1111 owner identity differs from the Formal repository Owner"]
        if control_repo.get("private") is not True or control_repo.get("default_branch") != "main":
            return None, ["root-authority source is not confirmed as private 1111/main"]

        pr = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/pulls/{SUCCESSOR_ROOT_PR_NUMBER}")
        if not isinstance(pr, dict):
            return None, ["root-authority PR #163 metadata is unreadable"]
        base = pr.get("base") or {}
        head = pr.get("head") or {}
        merged_by = pr.get("merged_by") or {}
        if (
            pr.get("number") != SUCCESSOR_ROOT_PR_NUMBER
            or pr.get("state") != "closed"
            or pr.get("merged") is not True
            or merged_by.get("id") != owner_id
            or base.get("ref") != "main"
            or base.get("sha") != SUCCESSOR_ROOT_BASE_SHA
            or head.get("sha") != SUCCESSOR_ROOT_HEAD_SHA
            or pr.get("merge_commit_sha") != SUCCESSOR_ROOT_MERGE_SHA
            or not isinstance(pr.get("merged_at"), str)
        ):
            return None, ["PR #163 is not the exact manually Owner-merged root-authority transaction"]

        files = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/pulls/{SUCCESSOR_ROOT_PR_NUMBER}/files?per_page=100")
        expected_files = {
            SUCCESSOR_ROOT_AUTHORITY_PATH: SUCCESSOR_ROOT_AUTHORITY_BLOB,
            SUCCESSOR_ROOT_INSTRUCTION_PATH: SUCCESSOR_ROOT_INSTRUCTION_BLOB,
        }
        if not isinstance(files, list) or len(files) != len(expected_files):
            return None, ["PR #163 changed-file inventory is incomplete or contains unexpected paths"]
        observed_files = {
            row.get("filename"): row for row in files if isinstance(row, dict)
        }
        if set(observed_files) != set(expected_files) or any(
            observed_files[path].get("status") != "added"
            or observed_files[path].get("sha") != blob
            for path, blob in expected_files.items()
        ):
            return None, ["PR #163 file paths/status/blob IDs differ from the exact reviewed root-authority proposal"]

        merge = _commit_from_api(OWNER_AUTHORIZATION_REPOSITORY, SUCCESSOR_ROOT_MERGE_SHA, api, {})
        parents = [row.get("sha") for row in merge.get("parents", []) if isinstance(row, dict)]
        if parents != SUCCESSOR_ROOT_PARENTS:
            return None, ["PR #163 Owner merge has wrong ordered base/head parents"]
        if (merge.get("commit", {}).get("tree") or {}).get("sha") != SUCCESSOR_ROOT_TREE_SHA:
            return None, ["PR #163 Owner merge tree differs from the verified reviewed tree"]
        signed, signature_error = _verified_owner_commit(merge, owner_id)
        if not signed:
            return None, [f"PR #163 Owner merge signature is invalid: {signature_error}"]
        main_branch = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/branches/main")
        main_sha = (main_branch.get("commit") or {}).get("sha") if isinstance(main_branch, dict) else None
        ancestry = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/compare/{SUCCESSOR_ROOT_MERGE_SHA}...{main_sha}")
        if not isinstance(ancestry, dict) or ancestry.get("status") not in {"ahead", "identical"}:
            return None, ["PR #163 root-authority merge is not an ancestor of current 1111/main"]

        readbacks: dict[str, dict[str, Any]] = {}
        for path, blob_sha, file_sha256 in (
            (SUCCESSOR_ROOT_AUTHORITY_PATH, SUCCESSOR_ROOT_AUTHORITY_BLOB, SUCCESSOR_ROOT_AUTHORITY_SHA256),
            (SUCCESSOR_ROOT_INSTRUCTION_PATH, SUCCESSOR_ROOT_INSTRUCTION_BLOB, SUCCESSOR_ROOT_INSTRUCTION_SHA256),
        ):
            binding, binding_errors = _read_authenticated_control_path_commit(
                OWNER_AUTHORIZATION_REPOSITORY,
                path,
                SUCCESSOR_ROOT_MERGE_SHA,
                owner_id,
                expected_file_sha256=file_sha256,
                expected_parent_shas=SUCCESSOR_ROOT_PARENTS,
                api=api,
            )
            if binding_errors or binding is None:
                return None, [f"root-authority file {path} failed exact readback: {error}" for error in binding_errors]
            if binding["blob_sha"] != blob_sha:
                return None, [f"root-authority file {path} Git blob differs from the reviewed file"]
            readbacks[path] = binding

        authority = json.loads(readbacks[SUCCESSOR_ROOT_AUTHORITY_PATH]["raw"].decode("utf-8"))
        if (
            authority.get("record_id") != "IGNITION-20261104-OWNER-ROOT-GOVERNANCE-AUTHORITY-R0"
            or authority.get("status") != "PROPOSED_PENDING_OWNER_VERIFIED_MERGE"
            or authority.get("activation", {}).get("effective_only_after_verified_owner_merge") is not True
            or authority.get("activation", {}).get("r3_validator_is_not_the_authority_for_this_root_act") is not True
            or authority.get("scope", {}).get("kind") != "ONE_TIME_GOVERNANCE_PROTOCOL_AMENDMENT_MANDATE"
            or authority.get("scope", {}).get("task_identity_rule") is None
            or authority.get("immutable_history", {}).get("retroactive_cure_for_pr_267") != "FORBIDDEN"
        ):
            return None, ["merged root-authority record does not contain the exact narrow external-to-R3 authority terms"]
        return {
            "repository": OWNER_AUTHORIZATION_REPOSITORY,
            "branch": "main",
            "pull_request_number": SUCCESSOR_ROOT_PR_NUMBER,
            "merge_commit_sha": SUCCESSOR_ROOT_MERGE_SHA,
            "merge_tree_sha": SUCCESSOR_ROOT_TREE_SHA,
            "ordered_parents": parents,
            "owner_actor_id": owner_id,
            "merged_by_id": merged_by.get("id"),
            "signature_verified": True,
            "signature_reason": "valid",
            "main_sha": main_sha,
            "files": {
                path: {
                    "blob_sha": binding["blob_sha"],
                    "sha256": binding["file_sha256"],
                    "update_commit_sha": binding["path_update_commit_sha"],
                }
                for path, binding in readbacks.items()
            },
        }, []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"root governance authority readback failed closed: {error.__class__.__name__}: {error}"]


def read_authenticated_task22_amendment_preparation_authority(
    *, github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Verify the external #163 + #165 authority for this candidate's Draft prep.

    This one-time amendment bootstrap is intentionally independent of the
    successor PREPARATION_ONLY ledger, which is part of the candidate and is
    not effective yet.
    """
    api = github_api or _gh_api_json
    try:
        contract = load_json(SUCCESSOR_PROTOCOL_PATH)["amendment_preparation_authority"]
        root, root_errors = read_authenticated_successor_root_authority(github_api=api)
        if root_errors or root is None:
            return None, [f"Task22 preparation lacks the live #163 root authority: {error}" for error in root_errors]
        if root["merge_commit_sha"] != contract["root_authority_merge_commit_sha"]:
            return None, ["Task22 preparation root merge differs from the exact #163 mandate"]

        repo = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}")
        owner_id = (repo.get("owner") or {}).get("id")
        if owner_id != 49422864 or repo.get("private") is not True or repo.get("default_branch") != "main":
            return None, ["Task22 identity source is not the verified private 1111/main Owner repository"]
        pr = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/pulls/{TASK22_IDENTITY_PR_NUMBER}")
        base, head = (pr.get("base") or {}), (pr.get("head") or {})
        if (
            pr.get("number") != TASK22_IDENTITY_PR_NUMBER or pr.get("state") != "closed"
            or pr.get("merged") is not True or (pr.get("merged_by") or {}).get("id") != owner_id
            or base.get("ref") != "main" or base.get("sha") != TASK22_IDENTITY_BASE_SHA
            or head.get("sha") != TASK22_IDENTITY_HEAD_SHA
            or pr.get("merge_commit_sha") != TASK22_IDENTITY_MERGE_SHA
        ):
            return None, ["Task22 identity assignment is not the exact Owner-merged #165 transaction"]

        files = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/pulls/{TASK22_IDENTITY_PR_NUMBER}/files?per_page=100")
        if (
            not isinstance(files, list) or len(files) != 1
            or files[0].get("filename") != TASK22_IDENTITY_PATH
            or files[0].get("status") != "added"
            or files[0].get("sha") != TASK22_IDENTITY_TREE_BLOB
        ):
            return None, ["PR #165 does not add exactly the expected Task22 identity-assignment file"]

        merge = _commit_from_api(OWNER_AUTHORIZATION_REPOSITORY, TASK22_IDENTITY_MERGE_SHA, api, {})
        parents = [row.get("sha") for row in merge.get("parents", []) if isinstance(row, dict)]
        if parents != [TASK22_IDENTITY_BASE_SHA, TASK22_IDENTITY_HEAD_SHA]:
            return None, ["PR #165 Owner merge has wrong ordered base/head parents"]
        signed, signature_error = _verified_owner_commit(merge, owner_id)
        if not signed:
            return None, [f"PR #165 Owner merge signature is invalid: {signature_error}"]
        main = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/branches/main")
        main_sha = (main.get("commit") or {}).get("sha") if isinstance(main, dict) else None
        ancestry = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/compare/{TASK22_IDENTITY_MERGE_SHA}...{main_sha}")
        if not isinstance(ancestry, dict) or ancestry.get("status") not in {"ahead", "identical"}:
            return None, ["PR #165 identity assignment is not ancestral to current 1111/main"]
        identity = contract["identity_assignment_file"]
        binding, binding_errors = _read_authenticated_control_path_commit(
            OWNER_AUTHORIZATION_REPOSITORY, identity["path"], TASK22_IDENTITY_MERGE_SHA, owner_id,
            expected_file_sha256=identity["sha256"],
            expected_parent_shas=[TASK22_IDENTITY_BASE_SHA, TASK22_IDENTITY_HEAD_SHA], api=api,
        )
        if binding_errors or binding is None:
            return None, [f"PR #165 identity file failed exact signed readback: {error}" for error in binding_errors]
        if binding["blob_sha"] != identity["git_blob_sha"]:
            return None, ["PR #165 identity-assignment blob differs from the Owner-merged file"]
        assignment = json.loads(binding["raw"].decode("utf-8"))
        assigned = assignment["explicit_identity_assignment"]
        root_binding = assignment["root_authority_binding"]
        scope = assignment["authorization_scope_after_verified_owner_merge"]
        prohibited_actions = scope.get("prohibited")
        if (
            root_binding.get("verified_owner_merge_sha") != root["merge_commit_sha"]
            or root_binding.get("effective") is not True
            or assigned.get("task_id") != contract["task_id"]
            or assigned.get("formal_ordinal") != contract["formal_ordinal"]
            or assigned.get("formal_base_main_sha_observed") != "87d7f8d3114e859a59585da336fb6301ee4cbbd3"
            or assigned.get("proposed_work_branch") != contract["work_branch"]
            or assigned.get("proposed_receipt_branch") != contract["receipt_branch"]
            or not isinstance(prohibited_actions, list)
            or not any("Stage A 023" in item for item in prohibited_actions)
            or not any("Branch-protection" in item for item in prohibited_actions)
            or not any("Formal main direct write" in item for item in prohibited_actions)
            or "Draft PR" not in scope.get("permitted", "")
        ):
            return None, ["Owner-merged #165 identity, #163 root binding, or narrow preparation scope differs from this candidate"]
        return {
            "root_authority": root,
            "repository": OWNER_AUTHORIZATION_REPOSITORY,
            "pull_request_number": TASK22_IDENTITY_PR_NUMBER,
            "merge_commit_sha": TASK22_IDENTITY_MERGE_SHA,
            "ordered_parents": parents,
            "owner_actor_id": owner_id,
            "signature_verified": True,
            "signature_reason": "valid",
            "main_sha": main_sha,
            "file_path": identity["path"],
            "file_blob_sha": binding["blob_sha"],
            "file_sha256": binding["file_sha256"],
            "task_id": assigned["task_id"],
            "formal_ordinal": assigned["formal_ordinal"],
            "work_branch": assigned["proposed_work_branch"],
            "receipt_branch": assigned["proposed_receipt_branch"],
            "permitted": contract["permitted"],
            "prohibited": contract["prohibited"],
        }, []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"Task22 #163/#165 preparation authority failed closed: {error.__class__.__name__}: {error}"]


def validate_task22_local_preparation_checkout(
    authority: dict[str, Any],
    *,
    github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Confirm this exact assigned branch is clean, pushed, and based on main."""
    api = github_api or _gh_api_json
    try:
        contract = load_json(SUCCESSOR_PROTOCOL_PATH)["amendment_preparation_authority"]
        branch = subprocess.run(
            ["git", "branch", "--show-current"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
        head_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
        ).stdout
        if branch != contract["work_branch"]:
            return None, ["local checkout is not the Owner-assigned Task22 work branch"]
        if status:
            return None, ["Task22 checkout has uncommitted changes; exact branch head cannot be presented for Draft review"]
        main = api(f"repos/{PUBLIC_REPOSITORY}/branches/main")
        main_sha = (main.get("commit") or {}).get("sha") if isinstance(main, dict) else None
        if main_sha != "87d7f8d3114e859a59585da336fb6301ee4cbbd3":
            return None, ["Formal main advanced from the exact #165-assigned Task22 base; stop and rebase only under renewed evidence"]
        task_branch = api(f"repos/{PUBLIC_REPOSITORY}/branches/{quote(branch, safe='')}")
        remote_head = (task_branch.get("commit") or {}).get("sha") if isinstance(task_branch, dict) else None
        if remote_head != head_sha:
            return None, ["pushed Task22 branch head differs from the exact locally verified candidate head"]
        ancestry = api(f"repos/{PUBLIC_REPOSITORY}/compare/{main_sha}...{head_sha}")
        if not isinstance(ancestry, dict) or ancestry.get("status") not in {"ahead", "identical"}:
            return None, ["exact Task22 candidate head is not based on the authorized Formal main SHA"]
        if authority.get("task_id") != contract["task_id"] or authority.get("work_branch") != branch:
            return None, ["verified #165 assignment does not match the exact local task branch identity"]
        return {"branch": branch, "head_sha": head_sha, "base_main_sha": main_sha, "remote_head_sha": remote_head}, []
    except (OSError, subprocess.SubprocessError, KeyError, TypeError, ValueError) as error:
        return None, [f"Task22 local Draft-preparation checkout failed closed: {error.__class__.__name__}: {error}"]


def read_authenticated_historical_adjudication(
    *, github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Re-read the signed #162 control record and preserve #267's disposition."""
    api = github_api or _gh_api_json
    try:
        public_repo = api(f"repos/{PUBLIC_REPOSITORY}")
        control_repo = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}")
        owner_id = (public_repo.get("owner") or {}).get("id")
        if not isinstance(owner_id, int) or owner_id != (control_repo.get("owner") or {}).get("id"):
            return None, ["Formal and 1111 repository Owner identities do not match"]
        pr = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/pulls/{HISTORICAL_ADJUDICATION_PR_NUMBER}")
        if (
            not isinstance(pr, dict)
            or pr.get("merged") is not True
            or pr.get("merge_commit_sha") != HISTORICAL_ADJUDICATION_MERGE_SHA
            or (pr.get("merged_by") or {}).get("id") != owner_id
        ):
            return None, ["1111 PR #162 is not the exact Owner-merged historical adjudication transaction"]
        expected_files = {
            HISTORICAL_R3_BLOCKER_PATH: HISTORICAL_R3_BLOCKER_BLOB,
            HISTORICAL_OWNER_DECISION_PATH: HISTORICAL_OWNER_DECISION_BLOB,
            HISTORICAL_AUDIT_PATH: HISTORICAL_AUDIT_BLOB,
        }
        files = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/pulls/{HISTORICAL_ADJUDICATION_PR_NUMBER}/files?per_page=100")
        observed = {row.get("filename"): row for row in files if isinstance(row, dict)} if isinstance(files, list) else {}
        if set(observed) != set(expected_files) or any(
            observed[path].get("status") != "added" or observed[path].get("sha") != blob
            for path, blob in expected_files.items()
        ):
            return None, ["PR #162 historical adjudication file inventory differs from its Owner-merged immutable contents"]
        merge = _commit_from_api(OWNER_AUTHORIZATION_REPOSITORY, HISTORICAL_ADJUDICATION_MERGE_SHA, api, {})
        expected_parents = ["e6cbef3dc78b541a8c3a9382e49b587562051c87", "6d998d35f07ff98fb63c7861d27b4e222dc0e3f2"]
        parents = [row.get("sha") for row in merge.get("parents", []) if isinstance(row, dict)]
        if parents != expected_parents:
            return None, ["PR #162 merge parent order differs from the exact adjudication base and reviewed head"]
        signed, signature_error = _verified_owner_commit(merge, owner_id)
        if not signed:
            return None, [f"PR #162 Owner merge signature is invalid: {signature_error}"]
        main_branch = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/branches/main")
        main_sha = (main_branch.get("commit") or {}).get("sha") if isinstance(main_branch, dict) else None
        ancestry = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/compare/{HISTORICAL_ADJUDICATION_MERGE_SHA}...{main_sha}")
        if not isinstance(ancestry, dict) or ancestry.get("status") not in {"ahead", "identical"}:
            return None, ["Owner-merged historical adjudication PR #162 is not ancestral to current 1111/main"]
        contents: dict[str, str] = {}
        for path, blob_sha in expected_files.items():
            binding, binding_errors = _read_authenticated_control_path_commit(
                OWNER_AUTHORIZATION_REPOSITORY,
                path,
                HISTORICAL_ADJUDICATION_MERGE_SHA,
                owner_id,
                expected_parent_shas=expected_parents,
                api=api,
            )
            if binding_errors or binding is None:
                return None, [f"historical adjudication path {path} failed exact readback: {error}" for error in binding_errors]
            if binding["blob_sha"] != blob_sha:
                return None, [f"historical adjudication path {path} was changed after PR #162"]
            contents[path] = binding["raw"].decode("utf-8")
        audit = contents[HISTORICAL_AUDIT_PATH]
        blocker = contents[HISTORICAL_R3_BLOCKER_PATH]
        decision = contents[HISTORICAL_OWNER_DECISION_PATH]
        if "NOT_COMPLIANT" not in audit or "NOT_COMPLIANT" not in decision:
            return None, ["Owner-merged PR #162 does not preserve the #267 NOT_COMPLIANT adjudication"]
        if "BLOCKED_WITH_EVIDENCE" not in blocker:
            return None, ["Owner-merged PR #162 does not preserve the separate #267 R3 witness blocker"]
        return {
            "repository": OWNER_AUTHORIZATION_REPOSITORY,
            "pr_number": HISTORICAL_ADJUDICATION_PR_NUMBER,
            "merge_commit_sha": HISTORICAL_ADJUDICATION_MERGE_SHA,
            "ordered_parents": parents,
            "main_sha": main_sha,
            "owner_actor_id": owner_id,
            "signature_verified": True,
            "signature_reason": "valid",
            "pr_267_disposition": "NOT_COMPLIANT",
            "r3_witness_disposition": "BLOCKED_WITH_EVIDENCE",
            "files": expected_files,
        }, []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"historical #267 adjudication readback failed closed: {error.__class__.__name__}: {error}"]


def _require_owner_verified_control_pr_merge(
    commit_sha: str,
    owner_id: int,
    api: Callable[[str], dict[str, Any] | list[Any]],
    cache: dict[str, dict[str, Any]],
    expected_path: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Require a signed Owner-authored, web-flow, main-targeted PR merge."""
    try:
        commit = _commit_from_api(OWNER_AUTHORIZATION_REPOSITORY, commit_sha, api, cache)
        valid, signature_error = _verified_owner_commit(commit, owner_id)
        if not valid:
            return None, [signature_error]
        parents = commit.get("parents")
        if not isinstance(parents, list) or len(parents) != 2:
            return None, ["append-only control record must enter through a two-parent merge commit"]
        committer = commit.get("committer") or {}
        if committer.get("id") != GITHUB_WEB_FLOW_ACCOUNT_ID or committer.get("login") != "web-flow":
            return None, ["append-only control record must use GitHub's verified web-flow PR merger attribution"]
        linked_prs = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/commits/{commit_sha}/pulls")
        if not isinstance(linked_prs, list) or len(linked_prs) != 1:
            return None, ["control-record merge commit must resolve to exactly one GitHub pull request"]
        pr = linked_prs[0]
        if (
            not isinstance(pr, dict)
            or pr.get("merged") is not True
            or pr.get("merge_commit_sha") != commit_sha
            or (pr.get("merged_by") or {}).get("id") != owner_id
            or (pr.get("base") or {}).get("ref") != "main"
            or (pr.get("base") or {}).get("sha") != parents[0].get("sha")
            or (pr.get("head") or {}).get("sha") != parents[1].get("sha")
        ):
            return None, ["control-record PR was not merged by the Owner into 1111/main"]
        changed_files = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/pulls/{pr['number']}/files?per_page=100")
        if not isinstance(changed_files, list) or len(changed_files) != 1 or changed_files[0].get("filename") != expected_path or changed_files[0].get("status") != "added":
            return None, ["each Owner control-record PR must add exactly its one immutable ledger file"]
        signed_path = _path_entry_for_commit(OWNER_AUTHORIZATION_REPOSITORY, commit_sha, expected_path, api, cache)
        if signed_path is None or changed_files[0].get("sha") != signed_path.get("sha"):
            return None, ["Owner control-record PR file blob differs from the signed merge tree"]
        return {"commit": commit, "pr": pr, "path": expected_path}, []
    except (OSError, subprocess.SubprocessError, KeyError, TypeError, ValueError) as error:
        return None, [f"Owner verified control-PR readback failed closed: {error.__class__.__name__}: {error}"]


def validate_successor_append_only_addition(
    path: str,
    *,
    status: str,
    already_added: bool,
    blob_sha: Any,
    first_parent_sha: Any,
    before_entry: dict[str, Any] | None,
    after_entry: dict[str, Any] | None,
    second_parent_entry: dict[str, Any] | None,
) -> list[str]:
    """Validate that a ledger path is introduced once, unchanged from PR head."""
    errors: list[str] = []
    if status != "added":
        errors.append(f"append-only control ledger path was modified, deleted or renamed: {path}")
    if already_added:
        errors.append(f"append-only control ledger path was added more than once: {path}")
    if not isinstance(blob_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", blob_sha):
        errors.append(f"ledger addition does not expose the exact blob SHA: {path}")
    if not isinstance(first_parent_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", first_parent_sha):
        errors.append(f"ledger addition has no exact first-parent merge base: {path}")
    if before_entry is not None or after_entry is None:
        errors.append(f"ledger path must be newly added to its first-parent tree: {path}")
    if after_entry is not None and after_entry.get("sha") != blob_sha:
        errors.append(f"ledger file differs from the exact added blob SHA: {path}")
    if after_entry is None or second_parent_entry != after_entry:
        errors.append(f"ledger file was not added with identical reviewed second-parent bytes: {path}")
    return errors


def validate_successor_ledger_uniqueness(records: list[dict[str, Any]]) -> list[str]:
    """Enforce non-replayable identities/nonces across the append-only ledger."""
    errors: list[str] = []
    groups = {
        record_type: [row for row in records if row.get("statement", {}).get("record_type") == record_type]
        for record_type in (
            "TASK_REGISTRATION", "PREPARATION_AUTHORIZATION", "FINAL_TRANSACTION_AUTHORIZATION",
            "AUTHORIZATION_REVOCATION", "REGISTRATION_SUPERSESSION", "OWNER_EXACT_HEAD_REVIEW",
            "PUBLICATION_WITNESS", "PROTOCOL_MIGRATION_WITNESS",
        )
    }

    def unique(rows: list[dict[str, Any]], key: str, label: str) -> None:
        values = [row["statement"].get(key) for row in rows]
        if len(values) != len(set(values)):
            errors.append(f"successor ledger repeats {label}")

    for key, label in (
        ("registration_id", "registration_id"), ("task_id", "task_id"),
        ("formal_ordinal", "formal_ordinal"), ("work_branch", "work branch"),
        ("receipt_branch", "receipt branch"),
    ):
        unique(groups["TASK_REGISTRATION"], key, label)
    unique(groups["PREPARATION_AUTHORIZATION"], "preparation_id", "preparation_id")
    unique(groups["FINAL_TRANSACTION_AUTHORIZATION"], "authorization_id", "authorization_id")
    all_auth_ids = [
        row["statement"].get(key)
        for row, key in (
            *((row, "preparation_id") for row in groups["PREPARATION_AUTHORIZATION"]),
            *((row, "authorization_id") for row in groups["FINAL_TRANSACTION_AUTHORIZATION"]),
        )
    ]
    if len(all_auth_ids) != len(set(all_auth_ids)):
        errors.append("successor ledger repeats an authorization ID across preparation and final phases")
    unique(groups["FINAL_TRANSACTION_AUTHORIZATION"], "transaction_id", "transaction_id")
    unique(groups["AUTHORIZATION_REVOCATION"], "revocation_id", "revocation_id")
    unique(groups["REGISTRATION_SUPERSESSION"], "supersession_id", "supersession_id")
    unique(groups["OWNER_EXACT_HEAD_REVIEW"], "review_id", "owner exact-head review ID")
    unique(groups["PUBLICATION_WITNESS"], "transaction_id", "published transaction ID")
    unique(groups["PROTOCOL_MIGRATION_WITNESS"], "protocol_sha256", "protocol migration digest")

    nonce_fields = ("registration_nonce", "preparation_nonce", "authorization_nonce", "revocation_nonce", "supersession_nonce", "review_nonce")
    nonces = [
        row["statement"].get(field)
        for row in records
        for field in nonce_fields
        if row.get("statement", {}).get(field) is not None
    ]
    if len(nonces) != len(set(nonces)):
        errors.append("successor ledger repeats a nonce across record types")
    return errors


def validate_successor_registration_statement(
    statement: dict[str, Any],
    *,
    expected_base_main_sha: str,
    expected_predecessor_task_id: str,
    expected_predecessor_ordinal: int,
    existing_registrations: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Validate an Owner-proposed identity against its signed full collision inventory."""
    schema = load_json(SUCCESSOR_SCHEMA_PATH)
    errors = _schema_errors(statement, {"$ref": "#/$defs/taskRegistrationRecord", "$defs": schema["$defs"]})
    if errors:
        return errors
    if statement["formal_base_main_sha"] != expected_base_main_sha:
        errors.append("successor registration does not bind the exact observed Formal main base")
    if statement["predecessor_task_id"] != expected_predecessor_task_id or statement["predecessor_ordinal"] != expected_predecessor_ordinal:
        errors.append("successor registration predecessor differs from the canonical task identity at its exact base")
    if statement["protocol_blob_sha"] != git_blob_sha(SUCCESSOR_PROTOCOL_PATH):
        errors.append("successor registration is stale for the exact successor protocol blob")
    if statement["protocol_file_sha256"] != hashlib.sha256(SUCCESSOR_PROTOCOL_PATH.read_bytes()).hexdigest():
        errors.append("successor registration is stale for the exact successor protocol file bytes")
    task_match = re.fullmatch(r"IGNITION-[0-9]{8}-(?P<ordinal>[0-9]{3})", statement["task_id"])
    predecessor_match = re.fullmatch(r"IGNITION-[0-9]{8}-(?P<ordinal>[0-9]{3})", statement["predecessor_task_id"])
    if task_match is None or int(task_match.group("ordinal")) != statement["formal_ordinal"]:
        errors.append("Owner-selected task_id does not encode its explicitly registered formal ordinal")
    if predecessor_match is None or int(predecessor_match.group("ordinal")) != statement["predecessor_ordinal"]:
        errors.append("registered predecessor task_id does not encode its explicitly recorded ordinal")
    if statement["transaction_protocol_id"] != SUCCESSOR_PROTOCOL_ID or statement["owner_actor_id"] != 49422864:
        errors.append("successor registration is not an Owner record for the exact versioned protocol")
    inventory = statement["conflict_inventory"]
    inventory_payload = {key: value for key, value in inventory.items() if key != "inventory_sha256"}
    computed_inventory_sha = hashlib.sha256(
        json.dumps(inventory_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if computed_inventory_sha != inventory["inventory_sha256"]:
        errors.append("successor registration collision-inventory digest differs from its exact canonical bytes")
    identities = inventory["formal_task_identities"]
    task_ids = [row["task_id"] for row in identities]
    ordinals = [row["formal_ordinal"] for row in identities]
    work_branches = [row["work_branch"] for row in identities]
    receipt_branches = [row["receipt_branch"] for row in identities]
    if any(len(values) != len(set(values)) for values in (task_ids, ordinals, work_branches, receipt_branches)):
        errors.append("signed successor collision inventory contains duplicate task IDs, ordinals or branches")
    identity_by_id = {row["task_id"]: row for row in identities}
    merged_ids = set(inventory["merged_task_ids"])
    open_ids = set(inventory["open_task_ids"])
    if merged_ids & open_ids:
        errors.append("collision inventory marks a task both merged and open")
    if not merged_ids.issubset(identity_by_id) or not open_ids.issubset(identity_by_id):
        errors.append("collision inventory merged/open task sets reference missing identities")
    if any(identity_by_id[task_id]["lifecycle_state"] != "MERGED" for task_id in merged_ids):
        errors.append("collision inventory merged-task set disagrees with task lifecycle values")
    if any(identity_by_id[task_id]["lifecycle_state"] != "OPEN" for task_id in open_ids):
        errors.append("collision inventory open-task set disagrees with task lifecycle values")
    expected_merged_ids = {row["task_id"] for row in identities if row["lifecycle_state"] == "MERGED"}
    expected_open_ids = {row["task_id"] for row in identities if row["lifecycle_state"] == "OPEN"}
    if merged_ids != expected_merged_ids or open_ids != expected_open_ids:
        errors.append("collision inventory merged/open ID lists do not cover every declared task identity")
    prior = identity_by_id.get(expected_predecessor_task_id)
    if prior is None or prior["formal_ordinal"] != expected_predecessor_ordinal or expected_predecessor_task_id not in merged_ids:
        errors.append("successor predecessor is not an exact merged identity in the signed conflict inventory")
    if (
        statement["task_id"] in identity_by_id
        or statement["formal_ordinal"] in ordinals
        or statement["work_branch"] in work_branches
        or statement["receipt_branch"] in receipt_branches
    ):
        errors.append("successor task identity, ordinal or branch is already assigned in the signed conflict inventory")
    if statement["task_id"] in {"IGNITION-20260829-148", "IGNITION-20261024-020", "IGNITION-20261101-021"} or statement["formal_ordinal"] in {20, 21, 148}:
        errors.append("successor registration may not reuse Task20, Task21 or the fixed Task148 registration identity")
    for existing in existing_registrations or []:
        prior_statement = existing.get("statement", existing)
        if (
            statement["registration_id"] == prior_statement.get("registration_id")
            or statement["task_id"] == prior_statement.get("task_id")
            or statement["formal_ordinal"] == prior_statement.get("formal_ordinal")
            or statement["registration_nonce"] == prior_statement.get("registration_nonce")
            or statement["work_branch"] == prior_statement.get("work_branch")
            or statement["receipt_branch"] == prior_statement.get("receipt_branch")
        ):
            errors.append("successor registration duplicates a prior immutable registration identity or nonce")
            break
    return errors


def read_authenticated_successor_control_ledger(
    *,
    github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
    require_root_authority: bool = True,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Read and verify the append-only R3 successor registration/auth ledger.

    The complete 1111 first-parent history is inspected so a later edit,
    deletion, rename, replay, or unsigned addition cannot be hidden by the
    latest tree. Every ledger addition must be an Owner-signed web-flow PR
    merge. Historical fixed R3 records live outside these new ledger paths.
    """
    api = github_api or _gh_api_json
    errors: list[str] = []
    try:
        if require_root_authority:
            root, root_errors = read_authenticated_successor_root_authority(github_api=api)
            errors.extend(root_errors)
            if root_errors or root is None:
                return None, errors
            history, history_errors = read_authenticated_historical_adjudication(github_api=api)
            errors.extend(history_errors)
            if history_errors or history is None:
                return None, errors

        repo = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}")
        owner_id = (repo.get("owner") or {}).get("id")
        if owner_id != 49422864:
            return None, ["1111 repository Owner differs from the root governance authority"]
        if repo.get("private") is not True or repo.get("default_branch") != "main":
            return None, ["successor control ledger is not confirmed on private 1111/main"]
        branch = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/branches/main")
        main_sha = (branch.get("commit") or {}).get("sha") if isinstance(branch, dict) else None
        if not isinstance(main_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", main_sha):
            return None, ["1111/main exact tip is unreadable"]
        cache: dict[str, dict[str, Any]] = {}
        main_commit = _commit_from_api(OWNER_AUTHORIZATION_REPOSITORY, main_sha, api, cache)
        main_tree_sha = (main_commit.get("commit", {}).get("tree") or {}).get("sha")
        tree = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/git/trees/{main_tree_sha}?recursive=1")
        if not isinstance(tree, dict) or tree.get("truncated") is True or not isinstance(tree.get("tree"), list):
            return None, ["1111/main recursive tree is incomplete; append-only ledger inventory cannot be established"]
        current_entries = {
            row.get("path"): row for row in tree["tree"]
            if isinstance(row, dict) and any(row.get("path", "").startswith(prefix) for prefix in SUCCESSOR_LEDGER_PREFIXES)
        }
        for path, entry in current_entries.items():
            if not isinstance(path, str) or not any(path.startswith(prefix) for prefix in SUCCESSOR_LEDGER_PREFIXES):
                continue
            relative_name = path.rsplit("/", 1)[-1]
            if not relative_name.endswith(".json") or relative_name == ".json" or entry.get("type") != "blob":
                errors.append(f"successor ledger contains an invalid path or non-file entry: {path}")
        if errors:
            return None, errors

        # Track every path creation/change along 1111/main's first-parent chain.
        additions: dict[str, dict[str, Any]] = {}
        cursor = main_sha
        control_merge_cache: dict[str, dict[str, Any]] = {}
        for _ in range(MAX_FIRST_PARENT_CONTROL_PATH_SCAN):
            commit = _commit_from_api(OWNER_AUTHORIZATION_REPOSITORY, cursor, api, cache)
            changed = commit.get("files")
            if not isinstance(changed, list) or len(changed) >= 300:
                return None, [f"first-parent commit file inventory is missing or truncated at {cursor}; ledger immutability cannot be proved"]
            parent_list = commit.get("parents")
            if not isinstance(parent_list, list):
                return None, [f"first-parent ancestry is unreadable at {cursor}"]
            parent_sha = parent_list[0].get("sha") if parent_list and isinstance(parent_list[0], dict) else None
            for file_change in changed:
                if not isinstance(file_change, dict):
                    continue
                path = file_change.get("filename")
                if not isinstance(path, str) or not any(path.startswith(prefix) for prefix in SUCCESSOR_LEDGER_PREFIXES):
                    continue
                if file_change.get("status") != "added" or path in additions:
                    addition_errors = validate_successor_append_only_addition(
                        path, status=file_change.get("status"), already_added=path in additions,
                        blob_sha=file_change.get("sha"), first_parent_sha=parent_sha,
                        before_entry=None, after_entry=None, second_parent_entry=None,
                    )
                    return None, [f"ledger path history failed closed at {cursor}: {item}" for item in addition_errors]
                if not isinstance(file_change.get("sha"), str) or not re.fullmatch(r"[0-9a-f]{40}", file_change["sha"]):
                    return None, [f"ledger addition does not expose the exact blob SHA: {path}"]
                if not parent_sha:
                    return None, [f"ledger addition has no first-parent merge base: {path}"]
                control_merge, merge_errors = _require_owner_verified_control_pr_merge(
                    cursor, owner_id, api, control_merge_cache, path
                )
                if merge_errors or control_merge is None:
                    return None, [f"ledger path addition is not a verified Owner PR merge: {error}" for error in merge_errors]
                after = _path_entry_for_commit(OWNER_AUTHORIZATION_REPOSITORY, cursor, path, api, cache)
                before = _path_entry_for_commit(OWNER_AUTHORIZATION_REPOSITORY, parent_sha, path, api, cache)
                second_parent_sha = parent_list[1].get("sha") if len(parent_list) == 2 and isinstance(parent_list[1], dict) else None
                second_parent = _path_entry_for_commit(OWNER_AUTHORIZATION_REPOSITORY, second_parent_sha, path, api, cache) if second_parent_sha else None
                addition_errors = validate_successor_append_only_addition(
                    path, status=file_change.get("status"), already_added=path in additions,
                    blob_sha=file_change.get("sha"), first_parent_sha=parent_sha,
                    before_entry=before, after_entry=after, second_parent_entry=second_parent,
                )
                if addition_errors:
                    return None, [f"ledger path history failed closed at {cursor}: {item}" for item in addition_errors]
                additions[path] = {"commit_sha": cursor, "blob_sha": after["sha"], "parents": [row.get("sha") for row in parent_list]}
            if not parent_list:
                break
            if not isinstance(parent_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", parent_sha):
                return None, [f"first parent is malformed at {cursor}"]
            cursor = parent_sha
        else:
            return None, [f"1111/main first-parent scan exceeded {MAX_FIRST_PARENT_CONTROL_PATH_SCAN} commits"]

        if set(additions) != set(current_entries):
            missing = sorted(set(additions) - set(current_entries))
            unregistered = sorted(set(current_entries) - set(additions))
            return None, [f"append-only ledger tree/history mismatch: deleted={missing}, unsigned_or_untracked={unregistered}"]

        schema = load_json(SUCCESSOR_SCHEMA_PATH)
        records: list[dict[str, Any]] = []
        for path in sorted(current_entries):
            raw_content = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/contents/{quote(path, safe='/')}?ref={quote(main_sha, safe='')}")
            raw, blob_sha = _decode_control_file(raw_content, OWNER_AUTHORIZATION_REPOSITORY, path, main_sha)
            if blob_sha != current_entries[path].get("sha") or blob_sha != additions[path]["blob_sha"]:
                return None, [f"main ledger bytes differ from the signed append-only tree entry: {path}"]
            statement = json.loads(raw.decode("utf-8"))
            if path.startswith(SUCCESSOR_REGISTRATION_PREFIX):
                def_name = "taskRegistrationRecord"
                expected_id = statement.get("registration_id")
            elif path.startswith(SUCCESSOR_AUTHORIZATION_PREFIX):
                if statement.get("record_type") == "PREPARATION_AUTHORIZATION":
                    def_name = "preparationAuthorizationRecord"
                    expected_id = statement.get("preparation_id")
                elif statement.get("record_type") == "FINAL_TRANSACTION_AUTHORIZATION":
                    def_name = "finalTransactionAuthorizationRecord"
                    expected_id = statement.get("authorization_id")
                else:
                    return None, [f"successor authorization path has an unsupported record type: {path}"]
            elif path.startswith(SUCCESSOR_REVOCATION_PREFIX):
                def_name = "authorizationRevocationRecord"
                expected_id = statement.get("revocation_id")
            elif path.startswith(SUCCESSOR_SUPERSESSION_PREFIX):
                def_name = "registrationSupersessionRecord"
                expected_id = statement.get("supersession_id")
            elif path.startswith(SUCCESSOR_REVIEW_PREFIX):
                def_name = "ownerExactHeadReviewRecord"
                expected_id = statement.get("review_id")
            elif path.startswith(SUCCESSOR_PUBLICATION_PREFIX):
                def_name = "publicationWitnessRecord"
                expected_id = statement.get("transaction_id")
            else:
                def_name = "migrationWitness"
                expected_id = statement.get("protocol_sha256")
            schema_errors = _schema_errors(statement, {"$ref": f"#/$defs/{def_name}", "$defs": schema["$defs"]})
            if schema_errors:
                return None, [f"invalid signed successor control record at {path}: {item}" for item in schema_errors]
            if path.rsplit("/", 1)[-1] != f"{expected_id}.json":
                return None, [f"successor control-record path does not bind its immutable record ID: {path}"]
            metadata = additions[path]
            binding, binding_errors = _read_authenticated_control_path_commit(
                OWNER_AUTHORIZATION_REPOSITORY,
                path,
                metadata["commit_sha"],
                owner_id,
                expected_file_sha256=hashlib.sha256(raw).hexdigest(),
                expected_parent_shas=metadata["parents"],
                api=api,
            )
            if binding_errors or binding is None:
                return None, [f"successor control record failed Owner signature/path readback: {item}" for item in binding_errors]
            records.append({
                "path": path,
                "statement": statement,
                "commit_sha": metadata["commit_sha"],
                "parents": metadata["parents"],
                "blob_sha": blob_sha,
                "file_sha256": hashlib.sha256(raw).hexdigest(),
                "committed_at": binding["committed_at"],
                "signature_verified": True,
                "signature_reason": "valid",
            })

        # Enforce global uniqueness, including across different ledger record types.
        registrations = [row for row in records if row["statement"]["record_type"] == "TASK_REGISTRATION"]
        preparation_authorizations = [row for row in records if row["statement"]["record_type"] == "PREPARATION_AUTHORIZATION"]
        authorizations = [row for row in records if row["statement"]["record_type"] == "FINAL_TRANSACTION_AUTHORIZATION"]
        revocations = [row for row in records if row["statement"]["record_type"] == "AUTHORIZATION_REVOCATION"]
        supersessions = [row for row in records if row["statement"]["record_type"] == "REGISTRATION_SUPERSESSION"]
        owner_reviews = [row for row in records if row["statement"]["record_type"] == "OWNER_EXACT_HEAD_REVIEW"]
        publications = [row for row in records if row["statement"]["record_type"] == "PUBLICATION_WITNESS"]
        migrations = [row for row in records if row["statement"]["record_type"] == "PROTOCOL_MIGRATION_WITNESS"]
        errors.extend(validate_successor_ledger_uniqueness(records))
        for row in registrations:
            statement = row["statement"]
            registration_errors = validate_successor_registration_statement(
                statement,
                expected_base_main_sha=statement["formal_base_main_sha"],
                expected_predecessor_task_id=statement["predecessor_task_id"],
                expected_predecessor_ordinal=statement["predecessor_ordinal"],
                existing_registrations=[other for other in registrations if other["path"] != row["path"]],
            )
            errors.extend(f"successor registration {statement['registration_id']}: {item}" for item in registration_errors)
            task_match = re.fullmatch(r"IGNITION-[0-9]{8}-(?P<ordinal>[0-9]{3})", statement["task_id"])
            if task_match is None or int(task_match.group("ordinal")) != statement["formal_ordinal"]:
                errors.append("successor task_id is not the Owner-selected task identity matching its explicit formal ordinal")
            try:
                current_formal_main = api(f"repos/{PUBLIC_REPOSITORY}/branches/main")
                current_formal_main_sha = (current_formal_main.get("commit") or {}).get("sha") if isinstance(current_formal_main, dict) else None
                base_ancestry = api(
                    f"repos/{PUBLIC_REPOSITORY}/compare/{statement['formal_base_main_sha']}...{current_formal_main_sha}"
                )
                if not isinstance(base_ancestry, dict) or base_ancestry.get("status") not in {"ahead", "identical"}:
                    errors.append("successor registration Formal base is not ancestral to current Formal main")
                protocol_at_base = api(
                    f"repos/{PUBLIC_REPOSITORY}/contents/{quote(relative(SUCCESSOR_PROTOCOL_PATH), safe='/')}?ref={quote(statement['formal_base_main_sha'], safe='')}"
                )
                protocol_raw, protocol_blob = _decode_control_file(
                    protocol_at_base, PUBLIC_REPOSITORY, relative(SUCCESSOR_PROTOCOL_PATH), statement["formal_base_main_sha"]
                )
                if (
                    protocol_blob != statement["protocol_blob_sha"]
                    or hashlib.sha256(protocol_raw).hexdigest() != statement["protocol_file_sha256"]
                ):
                    errors.append("successor registration base does not contain its exact migrated protocol version")
                public_main_content = api(
                    f"repos/{PUBLIC_REPOSITORY}/contents/{quote(relative(CURRENT_TASK_PATH), safe='/')}?ref={quote(statement['formal_base_main_sha'], safe='')}"
                )
                predecessor_raw, _ = _decode_control_file(
                    public_main_content, PUBLIC_REPOSITORY, relative(CURRENT_TASK_PATH), statement["formal_base_main_sha"]
                )
                predecessor_task = json.loads(predecessor_raw.decode("utf-8"))["current_task"]["task_id"]
                if predecessor_task != statement["predecessor_task_id"]:
                    errors.append("successor registration predecessor differs from the canonical current task at its exact Formal base")
                commit_time = datetime.fromisoformat(row["committed_at"].replace("Z", "+00:00"))
                registered_time = datetime.fromisoformat(statement["registered_at"].replace("Z", "+00:00"))
                if registered_time > commit_time:
                    errors.append("successor registration timestamp is later than its Owner-signed merge commit")
            except (OSError, subprocess.SubprocessError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                errors.append(f"successor registration exact-base predecessor check failed closed: {error}")
        registration_by_id = {row["statement"]["registration_id"]: row for row in registrations}
        preparation_by_id = {row["statement"]["preparation_id"]: row for row in preparation_authorizations}
        authorization_by_id = {row["statement"]["authorization_id"]: row for row in authorizations}
        revoked_ids: set[str] = set()
        for row in revocations:
            statement = row["statement"]
            if statement["authorization_record_type"] == "PREPARATION_AUTHORIZATION":
                target = preparation_by_id.get(statement["authorization_id"])
                target_type = "PREPARATION_AUTHORIZATION"
            else:
                target = authorization_by_id.get(statement["authorization_id"])
                target_type = "FINAL_TRANSACTION_AUTHORIZATION"
            if (
                target is None
                or target["file_sha256"] != statement["authorization_file_sha256"]
                or target["statement"]["record_type"] != target_type
            ):
                errors.append("revocation does not bind an exact existing Owner authorization")
            else:
                target_time, target_errors = _parse_control_time(target["committed_at"], "authorization commit time")
                record_time, record_errors = _parse_control_time(row["committed_at"], "revocation commit time")
                revoked_at, revoked_errors = _parse_control_time(statement["revoked_at"], "authorization revoked_at")
                errors.extend(target_errors + record_errors + revoked_errors)
                if target_time and record_time and record_time <= target_time:
                    errors.append("authorization revocation must be Owner-signed after the exact authorization")
                if revoked_at and record_time and revoked_at > record_time:
                    errors.append("revocation effective timestamp is later than its signed control merge")
            if statement["authorization_id"] in revoked_ids:
                errors.append("one authorization has more than one immutable revocation record")
            revoked_ids.add(statement["authorization_id"])
        superseded_ids: set[str] = set()
        for row in supersessions:
            statement = row["statement"]
            prior_id = statement["supersedes_registration_id"]
            replacement_id = statement["replacement_registration_id"]
            prior = registration_by_id.get(prior_id)
            replacement = registration_by_id.get(replacement_id)
            if prior is None or replacement is None or prior_id == replacement_id:
                errors.append("registration supersession must bind two distinct immutable existing registrations")
            elif (
                prior["statement"]["task_id"] == replacement["statement"]["task_id"]
                or prior["statement"]["formal_ordinal"] == replacement["statement"]["formal_ordinal"]
            ):
                errors.append("supersession may not release or reuse a task ID or formal ordinal")
            else:
                supersession_time, supersession_errors = _parse_control_time(row["committed_at"], "supersession commit time")
                signed_time, signed_errors = _parse_control_time(statement["superseded_at"], "registration superseded_at")
                errors.extend(supersession_errors + signed_errors)
                if supersession_time and signed_time and signed_time > supersession_time:
                    errors.append("registration supersession timestamp is later than its Owner-signed merge")
                for related in (prior, replacement):
                    related_time, related_errors = _parse_control_time(related["committed_at"], "registration merge time")
                    errors.extend(related_errors)
                    if related_time and supersession_time and related_time >= supersession_time:
                        errors.append("registration supersession must follow both immutable task-registration merges")
            if prior_id in superseded_ids:
                errors.append("one registration has more than one supersession record")
            superseded_ids.add(prior_id)
        for row in preparation_authorizations:
            statement = row["statement"]
            registration = registration_by_id.get(statement["registration_id"])
            if registration is None or registration["statement"]["task_id"] != statement["task_id"] or registration["statement"]["formal_ordinal"] != statement["formal_ordinal"]:
                errors.append("preparation authorization does not bind its exact signed task registration")
            else:
                if (
                    statement["protocol_blob_sha"] != git_blob_sha(SUCCESSOR_PROTOCOL_PATH)
                    or statement["protocol_file_sha256"] != hashlib.sha256(SUCCESSOR_PROTOCOL_PATH.read_bytes()).hexdigest()
                    or registration["statement"]["protocol_blob_sha"] != statement["protocol_blob_sha"]
                    or registration["statement"]["protocol_file_sha256"] != statement["protocol_file_sha256"]
                    or statement["base_main_sha"] != registration["statement"]["formal_base_main_sha"]
                    or statement["work_branch"] != registration["statement"]["work_branch"]
                ):
                    errors.append("preparation authorization differs from its exact registered branch, base or protocol version")
                registration_time, registration_errors = _parse_control_time(registration["committed_at"], "registration commit time")
                authorization_time, authorization_errors = _parse_control_time(row["committed_at"], "preparation authorization commit time")
                approved_at, approved_errors = _parse_control_time(statement["approved_at"], "preparation authorization approved_at")
                expires_at, expiry_errors = _parse_control_time(statement["expires_at"], "preparation authorization expires_at")
                errors.extend(registration_errors + authorization_errors + approved_errors + expiry_errors)
                if registration_time and authorization_time and authorization_time <= registration_time:
                    errors.append("preparation authorization must follow its immutable registration")
                if approved_at and authorization_time and approved_at > authorization_time:
                    errors.append("preparation authorization approval timestamp is later than its signed merge")
                if approved_at and expires_at and expires_at <= approved_at:
                    errors.append("preparation authorization expiry does not follow its approval timestamp")
        for row in authorizations:
            statement = row["statement"]
            registration = registration_by_id.get(statement["registration_id"])
            preparation = preparation_by_id.get(statement["preparation_id"])
            if registration is None or preparation is None:
                errors.append("final transaction authorization does not bind an existing signed registration and preparation grant")
                continue
            prep_statement = preparation["statement"]
            if (
                statement["task_id"] != registration["statement"]["task_id"]
                or statement["formal_ordinal"] != registration["statement"]["formal_ordinal"]
                or statement["registration_id"] != prep_statement["registration_id"]
                or statement["task_id"] != prep_statement["task_id"]
                or statement["formal_ordinal"] != prep_statement["formal_ordinal"]
                or statement["base_main_sha"] != prep_statement["base_main_sha"]
                or statement["protocol_blob_sha"] != prep_statement["protocol_blob_sha"]
                or statement["protocol_file_sha256"] != prep_statement["protocol_file_sha256"]
            ):
                errors.append("final transaction authorization differs from its exact preparation grant or task registration")
            registration_time, registration_errors = _parse_control_time(registration["committed_at"], "registration commit time")
            preparation_time, prep_errors = _parse_control_time(preparation["committed_at"], "preparation commit time")
            authorization_time, authorization_errors = _parse_control_time(row["committed_at"], "final transaction authorization commit time")
            approved_at, approved_errors = _parse_control_time(statement["approved_at"], "final transaction authorization approved_at")
            expires_at, expiry_errors = _parse_control_time(statement["expires_at"], "final transaction authorization expires_at")
            errors.extend(registration_errors + prep_errors + authorization_errors + approved_errors + expiry_errors)
            if registration_time and authorization_time and authorization_time <= registration_time:
                errors.append("final transaction authorization must follow its immutable registration")
            if preparation_time and authorization_time and authorization_time <= preparation_time:
                errors.append("final transaction authorization must follow its signed preparation grant")
            if approved_at and authorization_time and approved_at > authorization_time:
                errors.append("final transaction authorization approval timestamp is later than its signed merge")
            if approved_at and expires_at and expires_at <= approved_at:
                errors.append("final transaction authorization expiry does not follow its approval timestamp")
        for row in publications:
            statement = row["statement"]
            auth = authorization_by_id.get(statement["authorization_id"])
            registration = registration_by_id.get(statement["registration_id"])
            if auth is None or registration is None:
                errors.append("publication witness does not bind an existing authorization and registration")
                continue
            auth_statement = auth["statement"]
            reg_statement = registration["statement"]
            if (
                auth_statement["preparation_id"] != statement["preparation_id"]
                or auth_statement["transaction_id"] != statement["transaction_id"]
                or auth_statement["authorization_id"] != statement["authorization_id"]
                or auth_statement["registration_id"] != statement["registration_id"]
                or auth_statement["task_id"] != statement["task_id"]
                or auth_statement["formal_ordinal"] != statement["formal_ordinal"]
                or auth_statement["pr_number"] != statement["pr_number"]
                or auth_statement["candidate_head_sha"] != statement["candidate_head_sha"]
                or auth_statement["base_main_sha"] != statement["base_main_sha"]
                or auth_statement["protocol_blob_sha"] != statement["protocol_blob_sha"]
                or auth_statement["protocol_file_sha256"] != statement["protocol_file_sha256"]
                or reg_statement["task_id"] != statement["task_id"]
                or reg_statement["formal_ordinal"] != statement["formal_ordinal"]
            ):
                errors.append("publication witness fields differ from its signed authorization or task registration")
            if statement["actual_final_main_parents"] != [statement["base_main_sha"], statement["candidate_head_sha"]]:
                errors.append("publication witness merge parents are not ordered [base, candidate head]")
            if statement["remote_main_sha"] != statement["actual_final_main_sha"] or statement["fresh_clone_sha"] != statement["actual_final_main_sha"]:
                errors.append("publication witness remote main and fresh clone must equal its exact final main SHA")
            if statement["projection_check"]["source_sha"] != statement["actual_final_main_sha"] or statement["projection_check"]["unexpected_changed_paths"]:
                errors.append("publication witness projection receipt is stale or reports unexpected changed paths")
        for row in migrations:
            statement = row["statement"]
            if statement["protocol_sha256"] != hashlib.sha256(SUCCESSOR_PROTOCOL_PATH.read_bytes()).hexdigest():
                errors.append("migration witness digest does not match the exact successor protocol bytes")
            if statement["root_authority_merge_commit_sha"] != SUCCESSOR_ROOT_MERGE_SHA:
                errors.append("migration witness does not bind the verified external Owner root authority")
            if statement["independent_reviewer_id"] == statement["pr_author_id"] or statement["independent_reviewer_id"] == owner_id:
                errors.append("migration witness independent reviewer must differ from both PR author and Owner")
        if errors:
            return None, errors
        for row in migrations:
            errors.extend(
                f"successor migration witness {row['statement']['protocol_sha256']}: {item}"
                for item in validate_successor_migration_witness_live(
                    row["statement"], signed_record=row, owner_id=owner_id,
                    owner_review_records=owner_reviews, github_api=api
                )
            )
        for row in publications:
            errors.extend(
                f"successor publication witness {row['statement']['transaction_id']}: {item}"
                for item in validate_successor_publication_witness_live(
                    row["statement"], signed_record=row, owner_id=owner_id, github_api=api
                )
            )
        if errors:
            return None, errors
        return {
            "repository": OWNER_AUTHORIZATION_REPOSITORY,
            "main_sha": main_sha,
            "records": records,
            "registrations": registrations,
            "authorizations": authorizations,
            "preparation_authorizations": preparation_authorizations,
            "revocations": revocations,
            "supersessions": supersessions,
            "owner_reviews": owner_reviews,
            "publications": publications,
            "migrations": migrations,
            "revoked_authorization_ids": sorted(revoked_ids),
            "superseded_registration_ids": sorted(superseded_ids),
        }, []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"successor append-only control ledger failed closed: {error.__class__.__name__}: {error}"]


def _parse_control_time(value: str, label: str) -> tuple[datetime | None, list[str]]:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None, [f"{label} must include an explicit timezone"]
        return parsed.astimezone(timezone.utc), []
    except (AttributeError, TypeError, ValueError):
        return None, [f"{label} is not a valid timezone-aware timestamp"]


def _successor_authorization_revocation_errors(
    ledger: dict[str, Any], *, authorization_id: str, authorization_record_type: str,
    authorization_file_sha256: str, valid_through: str,
) -> list[str]:
    errors: list[str] = []
    cutoff, cutoff_errors = _parse_control_time(valid_through, "authorization revocation cutoff")
    errors.extend(cutoff_errors)
    for revoked in ledger.get("revocations", []):
        revocation = revoked["statement"]
        if (
            revocation.get("authorization_id") != authorization_id
            or revocation.get("authorization_record_type") != authorization_record_type
        ):
            continue
        if revocation.get("authorization_file_sha256") != authorization_file_sha256:
            errors.append("authorization revocation does not bind the exact signed authorization bytes")
        revoked_at, revoked_errors = _parse_control_time(revocation.get("revoked_at"), "authorization revoked_at")
        errors.extend(revoked_errors)
        if revoked_at and cutoff and revoked_at <= cutoff:
            errors.append(f"Owner {authorization_record_type.lower()} was revoked before the authorized boundary")
    return errors


def validate_successor_preparation_authorization_statement(
    preparation_id: str,
    *,
    ledger: dict[str, Any],
    task_id: str,
    formal_ordinal: int,
    registration_id: str,
    work_branch: str,
    base_main_sha: str,
    protocol_blob_sha: str,
    protocol_file_sha256: str,
    candidate_seed_sha256: str,
    action: str,
    valid_through: str,
) -> list[str]:
    """Validate the no-PR-yet PREPARATION_ONLY grant for one allowed action."""
    errors: list[str] = []
    rows = [
        row for row in ledger.get("preparation_authorizations", [])
        if row["statement"].get("preparation_id") == preparation_id
    ]
    if len(rows) != 1:
        return ["preparation grant does not resolve to exactly one immutable signed 1111 ledger record"]
    row = rows[0]
    signed = row["statement"]
    schema = load_json(SUCCESSOR_SCHEMA_PATH)
    errors.extend(_schema_errors(signed, {"$ref": "#/$defs/preparationAuthorizationRecord", "$defs": schema["$defs"]}))
    for field, expected_value in (
        ("preparation_id", preparation_id), ("task_id", task_id), ("formal_ordinal", formal_ordinal),
        ("registration_id", registration_id), ("work_branch", work_branch), ("base_main_sha", base_main_sha),
        ("protocol_blob_sha", protocol_blob_sha), ("protocol_file_sha256", protocol_file_sha256),
        ("candidate_seed_sha256", candidate_seed_sha256), ("scope", "PREPARATION_ONLY"),
        ("allowed_actions", ["PUSH_REGISTERED_BRANCH", "CREATE_DRAFT_PULL_REQUEST", "COLLECT_REQUIRED_CHECKS"]),
        ("owner_actor_id", 49422864),
    ):
        if signed.get(field) != expected_value:
            errors.append(f"PREPARATION_ONLY {field} does not bind the exact registered candidate scope")
    if action not in signed.get("allowed_actions", []):
        errors.append("PREPARATION_ONLY grant does not authorize this action")
    expected_evidence = {
        "path": f"{SUCCESSOR_AUTHORIZATION_PREFIX}{preparation_id}.json",
        "statement": signed, "file_sha256": row.get("file_sha256"),
        "signature_verified": True, "signature_reason": "valid",
    }
    if row.get("path") != expected_evidence["path"] or row.get("signature_verified") is not True or row.get("signature_reason") != "valid":
        errors.append("PREPARATION_ONLY evidence differs from the exact Owner-signed append-only record")
    registration_rows = [
        item for item in ledger.get("registrations", [])
        if item["statement"].get("registration_id") == registration_id
    ]
    if len(registration_rows) != 1:
        errors.append("PREPARATION_ONLY grant has no unique exact signed task registration")
    else:
        registration = registration_rows[0]["statement"]
        if (
            registration.get("task_id") != task_id
            or registration.get("formal_ordinal") != formal_ordinal
            or registration.get("work_branch") != work_branch
            or registration.get("formal_base_main_sha") != base_main_sha
            or registration.get("protocol_blob_sha") != protocol_blob_sha
            or registration.get("protocol_file_sha256") != protocol_file_sha256
        ):
            errors.append("PREPARATION_ONLY grant differs from its exact signed task registration")
        registration_time, reg_errors = _parse_control_time(registration_rows[0]["committed_at"], "registration commit time")
        prep_commit_time, commit_errors = _parse_control_time(row["committed_at"], "preparation authorization commit time")
        errors.extend(reg_errors + commit_errors)
        if registration_time and prep_commit_time and prep_commit_time <= registration_time:
            errors.append("PREPARATION_ONLY grant must be Owner-signed after its task registration")
    approved_at, approved_errors = _parse_control_time(signed.get("approved_at"), "preparation authorization approved_at")
    committed_at, committed_errors = _parse_control_time(row.get("committed_at"), "preparation authorization signed commit time")
    expires_at, expiry_errors = _parse_control_time(signed.get("expires_at"), "preparation authorization expires_at")
    cutoff, cutoff_errors = _parse_control_time(valid_through, "preparation action cutoff")
    errors.extend(approved_errors + committed_errors + expiry_errors + cutoff_errors)
    if approved_at and committed_at and approved_at > committed_at:
        errors.append("PREPARATION_ONLY approval timestamp is later than its Owner-signed merge")
    if committed_at and cutoff and committed_at >= cutoff:
        errors.append("PREPARATION_ONLY grant was not signed before the authorized action")
    if approved_at and cutoff and approved_at >= cutoff:
        errors.append("PREPARATION_ONLY grant was not approved before the authorized action")
    if approved_at and expires_at and expires_at <= approved_at:
        errors.append("PREPARATION_ONLY expiry does not follow its approval timestamp")
    if expires_at and cutoff and expires_at <= cutoff:
        errors.append("PREPARATION_ONLY grant is expired at the authorized action")
    errors.extend(_successor_authorization_revocation_errors(
        ledger, authorization_id=preparation_id, authorization_record_type="PREPARATION_AUTHORIZATION",
        authorization_file_sha256=row.get("file_sha256", ""), valid_through=valid_through,
    ))
    return errors


def validate_successor_transaction_authorization_statement(
    evidence: dict[str, Any],
    *,
    ledger: dict[str, Any],
    task_id: str,
    formal_ordinal: int,
    registration_id: str,
    transaction_id: str,
    pr_number: int,
    candidate_head_sha: str,
    base_main_sha: str,
    protocol_blob_sha: str,
    protocol_file_sha256: str,
    preparation_valid_through: str,
    valid_through: str,
) -> list[str]:
    """Require both stages: valid prep at PR creation, then exact final grant."""
    errors: list[str] = []
    statement = evidence.get("statement") if isinstance(evidence, dict) else None
    if not isinstance(statement, dict):
        return ["successor final transaction authorization evidence has no signed statement"]
    auth_rows = [
        row for row in ledger.get("authorizations", [])
        if row["statement"].get("authorization_id") == statement.get("authorization_id")
    ]
    if len(auth_rows) != 1:
        return ["final transaction authorization does not resolve to exactly one immutable signed 1111 ledger record"]
    row = auth_rows[0]
    signed = row["statement"]
    for field, expected_value in (
        ("record_type", "FINAL_TRANSACTION_AUTHORIZATION"), ("scope", "FINAL_TRANSACTION"),
        ("task_id", task_id), ("formal_ordinal", formal_ordinal), ("registration_id", registration_id),
        ("transaction_id", transaction_id), ("pr_number", pr_number),
        ("candidate_head_sha", candidate_head_sha), ("base_main_sha", base_main_sha),
        ("protocol_blob_sha", protocol_blob_sha), ("protocol_file_sha256", protocol_file_sha256),
        ("owner_actor_id", 49422864),
    ):
        if signed.get(field) != expected_value:
            errors.append(f"FINAL_TRANSACTION {field} does not bind the exact PR transaction")
    expected_evidence = {
        "record_type": "FINAL_TRANSACTION_AUTHORIZATION", "statement": signed,
        "authorization_repository": OWNER_AUTHORIZATION_REPOSITORY,
        "authorization_path": row["path"], "authorization_commit_sha": row["commit_sha"],
        "authorization_parent_shas": row["parents"], "authorization_file_sha256": row["file_sha256"],
        "authorization_blob_sha": row["blob_sha"], "authorization_committed_at": row["committed_at"],
        "authorization_signature_verified": True, "authorization_signature_reason": "valid",
    }
    if evidence != expected_evidence:
        errors.append("transaction authorization evidence differs from the exact signed 1111 final-authorization record")

    preparation_id = signed.get("preparation_id")
    preparation_rows = [
        item for item in ledger.get("preparation_authorizations", [])
        if item["statement"].get("preparation_id") == preparation_id
    ]
    registration_rows = [
        item for item in ledger.get("registrations", [])
        if item["statement"].get("registration_id") == registration_id
    ]
    if len(preparation_rows) != 1 or len(registration_rows) != 1:
        errors.append("FINAL_TRANSACTION lacks one exact signed preparation grant and task registration")
    else:
        prep_row, reg_row = preparation_rows[0], registration_rows[0]
        prep = prep_row["statement"]
        errors.extend(validate_successor_preparation_authorization_statement(
            preparation_id, ledger=ledger, task_id=task_id, formal_ordinal=formal_ordinal,
            registration_id=registration_id, work_branch=reg_row["statement"]["work_branch"],
            base_main_sha=base_main_sha, protocol_blob_sha=protocol_blob_sha,
            protocol_file_sha256=protocol_file_sha256, candidate_seed_sha256=prep.get("candidate_seed_sha256", ""),
            action="CREATE_DRAFT_PULL_REQUEST", valid_through=preparation_valid_through,
        ))
        if (
            prep_row["commit_sha"] == row["commit_sha"]
            or signed.get("preparation_id") != prep.get("preparation_id")
            or signed.get("registration_id") != prep.get("registration_id")
            or signed.get("task_id") != prep.get("task_id")
            or signed.get("formal_ordinal") != prep.get("formal_ordinal")
            or signed.get("base_main_sha") != prep.get("base_main_sha")
            or signed.get("protocol_blob_sha") != prep.get("protocol_blob_sha")
            or signed.get("protocol_file_sha256") != prep.get("protocol_file_sha256")
        ):
            errors.append("FINAL_TRANSACTION does not extend the exact preceding PREPARATION_ONLY grant")

    approved_at, approved_errors = _parse_control_time(signed.get("approved_at"), "final authorization approved_at")
    signed_at, signed_errors = _parse_control_time(row.get("committed_at"), "final authorization signed commit time")
    expires_at, expiry_errors = _parse_control_time(signed.get("expires_at"), "final authorization expires_at")
    cutoff, cutoff_errors = _parse_control_time(valid_through, "final authorization validity cutoff")
    errors.extend(approved_errors + signed_errors + expiry_errors + cutoff_errors)
    if approved_at and signed_at and approved_at > signed_at:
        errors.append("FINAL_TRANSACTION approval timestamp is later than its Owner-signed merge")
    if signed_at and cutoff and signed_at >= cutoff:
        errors.append("FINAL_TRANSACTION was not signed before validation or PR merge")
    if approved_at and cutoff and approved_at >= cutoff:
        errors.append("FINAL_TRANSACTION was not approved before validation or PR merge")
    if approved_at and expires_at and expires_at <= approved_at:
        errors.append("FINAL_TRANSACTION expiry does not follow its approval timestamp")
    if expires_at and cutoff and expires_at <= cutoff:
        errors.append("FINAL_TRANSACTION is expired at validation or PR merge")
    errors.extend(_successor_authorization_revocation_errors(
        ledger, authorization_id=signed.get("authorization_id", ""),
        authorization_record_type="FINAL_TRANSACTION_AUTHORIZATION",
        authorization_file_sha256=row.get("file_sha256", ""), valid_through=valid_through,
    ))
    if registration_id in ledger.get("superseded_registration_ids", []):
        supersessions = [
            item for item in ledger.get("supersessions", [])
            if item["statement"].get("supersedes_registration_id") == registration_id
        ]
        if any(
            (lambda parsed: parsed is not None and cutoff is not None and parsed <= cutoff)(
                _parse_control_time(item["statement"].get("superseded_at"), "registration superseded_at")[0]
            ) for item in supersessions
        ):
            errors.append("successor task registration was superseded before the authorized PR merge")
    return errors


def validate_successor_owner_exact_head_review_record(
    review_row: dict[str, Any] | None,
    *,
    owner_id: int,
    task_id: str,
    formal_ordinal: int,
    registration_id: str,
    pr_number: int,
    author_id: int,
    base_sha: str,
    head_sha: str,
    diff_sha256: str,
    protocol_sha256: str,
    valid_through: str,
) -> list[str]:
    """Require a separate Owner-signed, append-only review of this exact PR diff."""
    if review_row is None:
        return ["Owner exact-head review record is missing"]
    signed = review_row.get("statement")
    if not isinstance(signed, dict):
        return ["Owner exact-head review record has no signed statement"]
    errors: list[str] = []
    schema = load_json(SUCCESSOR_SCHEMA_PATH)
    errors.extend(_schema_errors(signed, {"$ref": "#/$defs/ownerExactHeadReviewRecord", "$defs": schema["$defs"]}))
    for field, value in (
        ("record_type", "OWNER_EXACT_HEAD_REVIEW"), ("owner_actor_id", owner_id),
        ("task_id", task_id), ("formal_ordinal", formal_ordinal), ("registration_id", registration_id),
        ("formal_pr_number", pr_number), ("pr_author_id", author_id),
        ("formal_base_sha", base_sha), ("formal_candidate_head_sha", head_sha),
        ("formal_pr_diff_sha256", diff_sha256), ("protocol_sha256", protocol_sha256),
        ("decision", "APPROVE"), ("scope", "OWNER_REVIEW_EXACT_FORMAL_PR_HEAD"),
    ):
        if signed.get(field) != value:
            errors.append(f"Owner exact-head review {field} does not bind the exact PR diff and head")
    if review_row.get("path") != f"{SUCCESSOR_REVIEW_PREFIX}{signed.get('review_id')}.json":
        errors.append("Owner exact-head review ledger path differs from its immutable review ID")
    if review_row.get("signature_verified") is not True or review_row.get("signature_reason") != "valid":
        errors.append("Owner exact-head review record lacks a verified Owner signature")
    reviewed_at, reviewed_errors = _parse_control_time(signed.get("reviewed_at"), "Owner reviewed_at")
    committed_at, committed_errors = _parse_control_time(review_row.get("committed_at"), "Owner review signed commit time")
    cutoff, cutoff_errors = _parse_control_time(valid_through, "Owner review validity cutoff")
    errors.extend(reviewed_errors + committed_errors + cutoff_errors)
    if reviewed_at and committed_at and reviewed_at > committed_at:
        errors.append("Owner exact-head review time is later than its signed append-only record")
    if reviewed_at and cutoff and reviewed_at >= cutoff:
        errors.append("Owner exact-head review was not completed before the Formal merge")
    if committed_at and cutoff and committed_at >= cutoff:
        errors.append("Owner exact-head review record was not signed before the Formal merge")
    if not isinstance(signed.get("review_summary"), str) or not signed["review_summary"].strip():
        errors.append("Owner exact-head review summary is empty")
    return errors


def _review_body_evidence_errors(body: Any) -> list[str]:
    if not isinstance(body, str) or not body.strip():
        return ["independent GitHub review body is empty"]
    independence = re.search(r"(?im)^\s*independence\s*:\s*(\S.*)$", body)
    assessment = re.search(r"(?im)^\s*assessment\s*:\s*(\S.*)$", body)
    errors = []
    if independence is None or not independence.group(1).strip():
        errors.append("independent reviewer must include a non-empty Independence: attestation")
    if assessment is None or not assessment.group(1).strip():
        errors.append("independent reviewer must include a substantive Assessment: section")
    return errors


def read_live_successor_pr_diff_sha256(
    pr_number: int,
    *,
    base_sha: str,
    head_sha: str,
    github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
) -> tuple[str | None, list[str]]:
    """Hash a stable exact-base/head changed-file inventory for Owner review."""
    api = github_api or _gh_api_json
    try:
        files: list[dict[str, Any]] = []
        for page in range(1, 101):
            batch = api(f"repos/{PUBLIC_REPOSITORY}/pulls/{pr_number}/files?per_page=100&page={page}")
            if not isinstance(batch, list):
                return None, ["Formal PR changed-file inventory is unreadable"]
            files.extend(row for row in batch if isinstance(row, dict))
            if len(batch) < 100:
                break
        else:
            return None, ["Formal PR changed-file inventory exceeded its bounded pagination limit"]
        normalized = []
        for item in files:
            normalized.append({
                "filename": item.get("filename"), "status": item.get("status"), "sha": item.get("sha"),
                "additions": item.get("additions"), "deletions": item.get("deletions"), "changes": item.get("changes"),
                "patch_sha256": hashlib.sha256(item.get("patch", "").encode("utf-8")).hexdigest()
                if isinstance(item.get("patch"), str) else None,
            })
        paths = [item["filename"] for item in normalized]
        if not normalized or any(not isinstance(path, str) for path in paths) or len(paths) != len(set(paths)):
            return None, ["Formal PR changed-file inventory is empty, duplicated, or missing a path"]
        payload = {"pr_number": pr_number, "base_sha": base_sha, "head_sha": head_sha, "files": sorted(normalized, key=lambda item: item["filename"])}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return digest, []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"Formal PR changed-file inventory failed closed: {error.__class__.__name__}: {error}"]


def validate_successor_review_gate(
    reviews: list[dict[str, Any]],
    *,
    author_id: int,
    owner_id: int,
    head_sha: str,
    authorized_reviewer_ids: set[int] | None = None,
    valid_through: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    """Select the live independent review; Owner review is optional GitHub corroboration."""
    errors: list[str] = []
    cutoff, cutoff_errors = _parse_control_time(valid_through, "review validity cutoff")
    errors.extend(cutoff_errors)
    latest: dict[int, dict[str, Any]] = {}
    for review in reviews:
        actor_id = review.get("actor_id")
        if not isinstance(actor_id, int):
            errors.append("live PR review lacks an exact reviewer actor ID")
            continue
        submitted, submitted_errors = _parse_control_time(review.get("submitted_at"), "review submitted_at")
        if submitted_errors:
            errors.extend(submitted_errors)
            continue
        if cutoff is not None and submitted is not None and submitted > cutoff:
            continue
        old = latest.get(actor_id)
        key = (review.get("submitted_at", ""), review.get("review_id", 0))
        old_key = (old.get("submitted_at", ""), old.get("review_id", 0)) if old else None
        if old is None or key > old_key:
            latest[actor_id] = review

    def is_valid(review: dict[str, Any] | None) -> bool:
        if (
            not review or review.get("state") != "APPROVED"
            or review.get("commit_sha") != head_sha or review.get("user_type") != "User"
        ):
            return False
        body_errors = _review_body_evidence_errors(review.get("body"))
        if body_errors:
            errors.extend(body_errors)
            return False
        submitted, submitted_errors = _parse_control_time(review.get("submitted_at"), "review submitted_at")
        if submitted_errors:
            errors.extend(submitted_errors)
            return False
        return cutoff is None or submitted is not None and submitted <= cutoff

    owner_review = latest.get(owner_id)
    if (
        not owner_review or owner_review.get("state") != "APPROVED"
        or owner_review.get("commit_sha") != head_sha or owner_review.get("user_type") != "User"
    ):
        owner_review = None
    independent = next((
        review for actor_id, review in latest.items()
        if actor_id != author_id and actor_id != owner_id
        and (authorized_reviewer_ids is None or actor_id in authorized_reviewer_ids)
        and is_valid(review)
    ), None)
    if author_id == owner_id:
        # GitHub bars the PR author from approving their own pull request. The
        # separately signed Owner exact-head record is checked by its caller.
        pass
    if independent is None:
        errors.append("no distinct non-author, non-Owner human reviewer approved the exact head with review evidence")
    return independent, owner_review, errors


def read_live_successor_pr_reviews(
    pr_number: int,
    *,
    github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]] | None, list[str]]:
    """Read live exact-head reviews without imposing repository write access."""
    api = github_api or _gh_api_json
    try:
        repo = api(f"repos/{PUBLIC_REPOSITORY}")
        owner_id = (repo.get("owner") or {}).get("id")
        pr = api(f"repos/{PUBLIC_REPOSITORY}/pulls/{pr_number}")
        if not isinstance(owner_id, int) or owner_id != 49422864 or pr.get("number") != pr_number:
            return None, None, ["Formal repository Owner or requested pull request identity differs from the successor policy"]
        raw_reviews: list[dict[str, Any]] = []
        for page in range(1, 51):
            batch = api(f"repos/{PUBLIC_REPOSITORY}/pulls/{pr_number}/reviews?per_page=100&page={page}")
            if not isinstance(batch, list):
                return None, None, ["GitHub PR review list is unreadable"]
            raw_reviews.extend(row for row in batch if isinstance(row, dict))
            if len(batch) < 100:
                break
        else:
            return None, None, ["GitHub PR review history exceeded the bounded pagination limit"]
        normalized: list[dict[str, Any]] = []
        for review in raw_reviews:
            user = review.get("user") or {}
            actor_id = user.get("id")
            if not isinstance(actor_id, int):
                return None, None, ["GitHub PR review lacks its exact reviewer identity"]
            normalized.append({
                "review_id": review.get("id"), "actor_id": actor_id,
                "state": review.get("state"), "commit_sha": review.get("commit_id"),
                "submitted_at": review.get("submitted_at"), "review_url": review.get("html_url"),
                "author_association": review.get("author_association", "NONE"),
                "user_type": user.get("type"), "body": review.get("body", ""),
            })
        return {"pull_request": pr, "owner_id": owner_id}, normalized, []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return None, None, [f"live successor PR/review readback failed closed: {error.__class__.__name__}: {error}"]
def read_live_successor_required_contexts(
    head_sha: str,
    *,
    github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
) -> tuple[list[dict[str, Any]] | None, list[str]]:
    """Require the exact inherited check contexts and app IDs on one exact candidate SHA."""
    api = github_api or _gh_api_json
    errors: list[str] = []
    try:
        payload = api(f"repos/{PUBLIC_REPOSITORY}/commits/{head_sha}/check-runs?per_page=100")
        check_runs = payload.get("check_runs", []) if isinstance(payload, dict) else None
        if not isinstance(check_runs, list):
            return None, ["exact-head GitHub check-run readback is unreadable"]
        observed: list[dict[str, Any]] = []
        for requirement in load_json(SUCCESSOR_PROTOCOL_PATH)["inherits_from"]["required_status_check_contexts"]:
            candidates = [
                row for row in check_runs
                if isinstance(row, dict)
                and row.get("name") == requirement["context"]
                and (row.get("app") or {}).get("id") == requirement["app_id"]
                and row.get("head_sha") == head_sha
            ]
            if not candidates:
                errors.append(f"required context {requirement['context']} has no exact-head GitHub check run")
                continue
            latest = max(candidates, key=lambda row: (row.get("started_at") or "", row.get("id", 0)))
            if latest.get("status") != "completed" or latest.get("conclusion") != "success":
                errors.append(f"required context {requirement['context']} did not pass on the exact candidate head")
                continue
            observed.append({
                "context": requirement["context"], "app_id": requirement["app_id"], "sha": head_sha,
                "conclusion": "success", "check_run_id": latest["id"],
                "check_url": latest.get("html_url"), "completed_at": latest.get("completed_at"),
            })
        return observed, errors
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"exact-head required context readback failed closed: {error.__class__.__name__}: {error}"]


def _valid_successor_context_set(
    observed: list[dict[str, Any]], expected: list[dict[str, Any]], exact_sha: str
) -> list[str]:
    def key(row: dict[str, Any]) -> tuple[Any, ...]:
        return (
            row.get("context"), row.get("app_id"), row.get("sha"), row.get("conclusion"),
            row.get("check_run_id"), row.get("check_url"), row.get("completed_at"),
        )
    if sorted(map(key, observed)) != sorted(map(key, expected)):
        return ["signed required-context evidence differs from the live exact-SHA GitHub readback"]
    if len(observed) != len(expected) or any(row.get("sha") != exact_sha or row.get("conclusion") != "success" for row in observed):
        return ["required contexts are missing, duplicated, stale or unsuccessful"]
    return []


def validate_successor_migration_witness_live(
    statement: dict[str, Any],
    *,
    signed_record: dict[str, Any],
    owner_id: int,
    github_api: Callable[[str], dict[str, Any] | list[Any]],
    owner_review_records: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Revalidate the exact merge, independent review, Owner record and checks."""
    errors: list[str] = []
    try:
        if statement["protocol_sha256"] != hashlib.sha256(SUCCESSOR_PROTOCOL_PATH.read_bytes()).hexdigest():
            return ["migration witness does not bind the exact successor protocol bytes"]
        pr = github_api(f"repos/{PUBLIC_REPOSITORY}/pulls/{statement['formal_pr_number']}")
        if not isinstance(pr, dict):
            return ["successor-protocol Formal migration PR is unreadable"]
        base, head = pr.get("base") or {}, pr.get("head") or {}
        if (
            pr.get("number") != statement["formal_pr_number"]
            or pr.get("state") != "closed" or pr.get("merged") is not True
            or base.get("ref") != "main" or base.get("sha") != statement["formal_base_sha"]
            or head.get("sha") != statement["formal_candidate_head_sha"]
            or pr.get("merge_commit_sha") != statement["formal_merge_commit_sha"]
            or (pr.get("merged_by") or {}).get("id") != owner_id
            or pr.get("draft") is True
        ):
            return ["Formal migration witness does not match the exact Owner-merged non-draft PR refs"]
        merge = _commit_from_api(PUBLIC_REPOSITORY, statement["formal_merge_commit_sha"], github_api, {})
        parents = [item.get("sha") for item in merge.get("parents", []) if isinstance(item, dict)]
        tree_sha = (merge.get("commit", {}).get("tree") or {}).get("sha")
        if parents != [statement["formal_base_sha"], statement["formal_candidate_head_sha"]]:
            errors.append("Formal migration merge does not have exact ordered [base, candidate head] parents")
        if parents != statement["formal_merge_parents"] or tree_sha != statement["formal_merge_tree_sha"]:
            errors.append("Formal migration witness tree or ordered parents differ from the live merge commit")
        protocol_content = github_api(
            f"repos/{PUBLIC_REPOSITORY}/contents/{quote(relative(SUCCESSOR_PROTOCOL_PATH), safe='/')}?ref={quote(statement['formal_merge_commit_sha'], safe='')}"
        )
        protocol_raw, protocol_blob = _decode_control_file(
            protocol_content, PUBLIC_REPOSITORY, relative(SUCCESSOR_PROTOCOL_PATH), statement["formal_merge_commit_sha"]
        )
        if protocol_blob != git_blob_sha(SUCCESSOR_PROTOCOL_PATH) or hashlib.sha256(protocol_raw).hexdigest() != statement["protocol_sha256"]:
            errors.append("merged Formal main does not contain the exact witnessed successor-protocol blob and digest")
        current_main = github_api(f"repos/{PUBLIC_REPOSITORY}/branches/main")
        current_main_sha = (current_main.get("commit") or {}).get("sha") if isinstance(current_main, dict) else None
        ancestry = github_api(f"repos/{PUBLIC_REPOSITORY}/compare/{statement['formal_merge_commit_sha']}...{current_main_sha}")
        if not isinstance(ancestry, dict) or ancestry.get("status") not in {"ahead", "identical"}:
            errors.append("Formal migration merge is not an ancestor of current Formal main")

        pr_meta, reviews, review_errors = read_live_successor_pr_reviews(statement["formal_pr_number"], github_api=github_api)
        errors.extend(review_errors)
        if pr_meta is not None and reviews is not None:
            normalized_pr = pr_meta["pull_request"]
            author_id = (normalized_pr.get("user") or {}).get("id")
            if author_id != statement["pr_author_id"]:
                errors.append("migration witness PR author differs from live GitHub PR metadata")
            independent, _, gate_errors = validate_successor_review_gate(
                reviews, author_id=author_id, owner_id=owner_id,
                head_sha=statement["formal_candidate_head_sha"], authorized_reviewer_ids=None,
                valid_through=pr["merged_at"],
            )
            errors.extend(gate_errors)
            if independent is not None and (
                independent["review_id"] != statement["independent_review_id"]
                or independent["actor_id"] != statement["independent_reviewer_id"]
                or independent["commit_sha"] != statement["independent_review_commit_sha"]
                or hashlib.sha256(independent["body"].encode("utf-8")).hexdigest() != statement["independent_review_body_sha256"]
            ):
                errors.append("migration witness does not identify the live independent exact-head approval")
            elif independent is None:
                errors.append("migration witness has no independently attested exact-head GitHub review")

            diff_sha256, diff_errors = read_live_successor_pr_diff_sha256(
                statement["formal_pr_number"], base_sha=statement["formal_base_sha"],
                head_sha=statement["formal_candidate_head_sha"], github_api=github_api,
            )
            errors.extend(diff_errors)
            owner_review_matches = [
                row for row in (owner_review_records or [])
                if row.get("statement", {}).get("review_id") == statement["owner_review_record_id"]
            ]
            if len(owner_review_matches) != 1:
                errors.append("migration witness Owner exact-head review ID does not resolve to one signed ledger record")
            else:
                owner_review_record = owner_review_matches[0]
                owner_statement = owner_review_record["statement"]
                if (
                    owner_review_record.get("commit_sha") != statement["owner_review_record_commit_sha"]
                    or owner_review_record.get("file_sha256") != statement["owner_review_record_file_sha256"]
                    or owner_statement.get("formal_candidate_head_sha") != statement["owner_reviewed_head_sha"]
                ):
                    errors.append("migration witness differs from the signed Owner review record identity or bytes")
                errors.extend(validate_successor_owner_exact_head_review_record(
                    owner_review_record, owner_id=owner_id,
                    task_id=owner_statement.get("task_id", ""),
                    formal_ordinal=owner_statement.get("formal_ordinal", -1),
                    registration_id=owner_statement.get("registration_id", ""),
                    pr_number=statement["formal_pr_number"], author_id=author_id,
                    base_sha=statement["formal_base_sha"], head_sha=statement["formal_candidate_head_sha"],
                    diff_sha256=diff_sha256 or "", protocol_sha256=statement["protocol_sha256"],
                    valid_through=pr["merged_at"],
                ))
        live_contexts, context_errors = read_live_successor_required_contexts(
            statement["formal_candidate_head_sha"], github_api=github_api
        )
        errors.extend(context_errors)
        if live_contexts is not None:
            errors.extend(_valid_successor_context_set(statement["required_check_contexts"], live_contexts, statement["formal_candidate_head_sha"]))
        merged_at, merged_errors = _parse_control_time(pr["merged_at"], "Formal migration merged_at")
        witnessed_at, witnessed_errors = _parse_control_time(statement["witnessed_at"], "migration witness witnessed_at")
        control_commit_at, commit_errors = _parse_control_time(signed_record["committed_at"], "migration witness signed commit time")
        errors.extend(merged_errors + witnessed_errors + commit_errors)
        if merged_at and witnessed_at and witnessed_at <= merged_at:
            errors.append("migration witness must be created after the actual Formal PR merge")
        if merged_at and live_contexts is not None:
            for context in live_contexts:
                completed_at, completed_errors = _parse_control_time(context.get("completed_at"), "required check completed_at")
                errors.extend(completed_errors)
                if completed_at and completed_at >= merged_at:
                    errors.append(f"migration required context {context.get('context')} did not finish before the Formal merge")
        if witnessed_at and control_commit_at and witnessed_at > control_commit_at:
            errors.append("migration witness timestamp is later than its Owner-signed 1111 merge")
        if statement["merge_method"] != "MERGE_COMMIT" or statement["branch_protection_verified"] is not True:
            errors.append("migration witness does not attest a protected normal merge-commit transaction")
        live_protection, protection_errors = read_live_branch_protection(github_api=github_api)
        errors.extend(protection_errors)
        if live_protection is not None and (
            live_protection.get("rules_sha256") != statement["branch_protection_rules_sha256"]
            or live_protection.get("protected") is not True
            or live_protection.get("admin_enforcement_enabled") is not True
        ):
            errors.append("migration witness branch-protection digest differs from the live protected-main readback")
        return errors
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as error:
        return [f"successor migration live verification failed closed: {error.__class__.__name__}: {error}"]


def validate_successor_publication_witness_live(
    statement: dict[str, Any],
    *,
    signed_record: dict[str, Any],
    owner_id: int,
    github_api: Callable[[str], dict[str, Any] | list[Any]],
) -> list[str]:
    """Verify a successor publication witness against its merged PR and final main SHA."""
    errors: list[str] = []
    try:
        pr = github_api(f"repos/{PUBLIC_REPOSITORY}/pulls/{statement['pr_number']}")
        if not isinstance(pr, dict):
            return ["successor publication PR is unreadable"]
        base, head = pr.get("base") or {}, pr.get("head") or {}
        if (
            pr.get("merged") is not True or pr.get("state") != "closed"
            or base.get("ref") != "main" or base.get("sha") != statement["base_main_sha"]
            or head.get("sha") != statement["candidate_head_sha"]
            or pr.get("merge_commit_sha") != statement["actual_final_main_sha"]
            or (pr.get("merged_by") or {}).get("id") != owner_id
        ):
            return ["publication witness does not bind the exact Owner-merged release PR"]
        merge = _commit_from_api(PUBLIC_REPOSITORY, statement["actual_final_main_sha"], github_api, {})
        parents = [item.get("sha") for item in merge.get("parents", []) if isinstance(item, dict)]
        tree_sha = (merge.get("commit", {}).get("tree") or {}).get("sha")
        if parents != statement["actual_final_main_parents"] or parents != [statement["base_main_sha"], statement["candidate_head_sha"]]:
            errors.append("successor release final-main merge has wrong ordered parents")
        if tree_sha != statement["actual_final_main_tree_sha"]:
            errors.append("successor release final-main tree differs from the signed witness")
        main = github_api(f"repos/{PUBLIC_REPOSITORY}/branches/main")
        main_sha = (main.get("commit") or {}).get("sha") if isinstance(main, dict) else None
        ancestry = github_api(f"repos/{PUBLIC_REPOSITORY}/compare/{statement['actual_final_main_sha']}...{main_sha}")
        if not isinstance(ancestry, dict) or ancestry.get("status") not in {"ahead", "identical"}:
            errors.append("published final main SHA is not ancestral to current Formal main")
        contexts, context_errors = read_live_successor_required_contexts(statement["actual_final_main_sha"], github_api=github_api)
        errors.extend(context_errors)
        if contexts is not None:
            errors.extend(_valid_successor_context_set(statement["required_postpublication_checks"], contexts, statement["actual_final_main_sha"]))
        workflow_checks, workflow_errors = read_live_postpublication_checks(
            statement["actual_final_main_sha"],
            required_workflows=load_json(PROTOCOL_PATH)["postpublication"]["required_workflow_names"],
            github_api=github_api,
        )
        errors.extend(workflow_errors)
        if statement["remote_main_sha"] != statement["actual_final_main_sha"] or statement["fresh_clone_sha"] != statement["actual_final_main_sha"]:
            errors.append("signed publication witness remote main and fresh clone do not equal the exact final main SHA")
        if statement["projection_check"]["source_sha"] != statement["actual_final_main_sha"] or statement["projection_check"]["unexpected_changed_paths"]:
            errors.append("successor publication projection check is stale or reports unexpected changed paths")
        witness_time, witness_errors = _parse_control_time(statement["witnessed_at"], "publication witnessed_at")
        merge_time, merge_errors = _parse_control_time(pr["merged_at"], "release PR merged_at")
        commit_time, commit_errors = _parse_control_time(signed_record["committed_at"], "publication witness signed commit time")
        errors.extend(witness_errors + merge_errors + commit_errors)
        if merge_time and witness_time and witness_time <= merge_time:
            errors.append("publication witness must be created after the release PR merge")
        if witness_time and commit_time and witness_time > commit_time:
            errors.append("publication witness timestamp is later than its Owner-signed 1111 merge")
        if merge_time:
            for context in statement["required_postpublication_checks"]:
                completed_at, completed_errors = _parse_control_time(context.get("completed_at"), "postpublication check completed_at")
                errors.extend(completed_errors)
                if completed_at and completed_at <= merge_time:
                    errors.append(f"postpublication required context {context.get('context')} did not finish after the Formal merge")
        if not workflow_checks:
            errors.append("successor publication witness lacks successful final-main postpublication workflows")
        return errors
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as error:
        return [f"successor publication live verification failed closed: {error.__class__.__name__}: {error}"]


def read_authenticated_successor_registration(
    commit_sha: str,
    *,
    expected_file_sha256: str | None = None,
    expected_formal_base_main_sha: str | None = None,
    expected_nonce: str | None = None,
    expected_parent_shas: list[str] | None = None,
    github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Verify the Owner-signed, unique task/ordinal registration on 1111/main."""
    api = github_api or _gh_api_json
    try:
        actor = api("user")
        public_repo = api(f"repos/{PUBLIC_REPOSITORY}")
        public_main = api(f"repos/{PUBLIC_REPOSITORY}/branches/main")
        control_repo = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}")
        owner_id = public_repo.get("owner", {}).get("id")
        actor_id = actor.get("id")
        if actor_id != owner_id or actor_id != control_repo.get("owner", {}).get("id"):
            return None, ["authenticated GitHub actor is not the Owner of both repositories"]
        if control_repo.get("private") is not True or control_repo.get("default_branch") != "main":
            return None, ["1111 registration source is not confirmed private/main"]
        binding, binding_errors = _read_authenticated_control_path_commit(
            OWNER_AUTHORIZATION_REPOSITORY,
            SUCCESSOR_REGISTRATION_PATH,
            commit_sha,
            actor_id,
            expected_file_sha256=expected_file_sha256,
            expected_parent_shas=expected_parent_shas,
            expected_nonce=expected_nonce,
            api=api,
        )
        if binding_errors or binding is None:
            return None, [f"Owner-signed successor registration binding failed: {item}" for item in binding_errors]
        commit = binding["commit"]
        raw = binding["raw"]
        file_sha256 = binding["file_sha256"]
        statement = json.loads(raw.decode("utf-8"))
        schema = load_json(SCHEMA_PATH)
        errors = _schema_errors(statement, {"$ref": "#/$defs/successorRegistrationStatement", "$defs": schema["$defs"]})
        if errors:
            return None, [f"Owner-signed successor registration is invalid: {item}" for item in errors]
        if statement["task_id"] == "IGNITION-20260829-148" or statement["formal_ordinal"] == 148:
            return None, ["successor registration may not reuse Task148 identity or ordinal"]
        formal_base_sha = expected_formal_base_main_sha or public_main.get("commit", {}).get("sha")
        if expected_formal_base_main_sha and statement["formal_base_main_sha"] != expected_formal_base_main_sha:
            return None, ["successor registration base SHA differs from the exact admitted PR base"]
        if not expected_formal_base_main_sha and formal_base_sha != statement["formal_base_main_sha"]:
            return None, ["successor registration base SHA is not the current live public main SHA"]
        if not isinstance(formal_base_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", formal_base_sha):
            return None, ["successor registration base SHA is not a readable exact Git commit"]
        current_task_content = api(
            f"repos/{PUBLIC_REPOSITORY}/contents/{quote(relative(CURRENT_TASK_PATH), safe='/')}?ref={quote(formal_base_sha, safe='')}"
        )
        if current_task_content.get("path") != relative(CURRENT_TASK_PATH) or current_task_content.get("type") != "file" or current_task_content.get("encoding") != "base64":
            return None, ["canonical current-task source cannot be read at the exact registered base SHA"]
        current_task_raw = base64.b64decode("".join(current_task_content["content"].split()), validate=True)
        current_task_id = json.loads(current_task_raw.decode("utf-8")).get("current_task", {}).get("task_id")
        if not isinstance(current_task_id, str) or statement["prior_task_id"] != current_task_id:
            return None, ["successor registration predecessor does not equal the canonical current task at its exact base SHA"]
        inventory = statement["conflict_inventory"]
        inventory_payload = {key: value for key, value in inventory.items() if key != "inventory_sha256"}
        computed_inventory_digest = hashlib.sha256(
            json.dumps(inventory_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        if computed_inventory_digest != inventory["inventory_sha256"]:
            return None, ["successor registration conflict-inventory digest does not match its exact inventory bytes"]
        identities = inventory["formal_task_identities"]
        task_ids = [item["task_id"] for item in identities]
        ordinals = [item["formal_ordinal"] for item in identities]
        work_branches = [item["work_branch"] for item in identities]
        receipt_branches = [item["receipt_branch"] for item in identities]
        if any(len(items) != len(set(items)) for items in (task_ids, ordinals, work_branches, receipt_branches)):
            return None, ["successor registration inventory contains colliding formal task IDs, ordinals or branches"]
        identity_by_id = {item["task_id"]: item for item in identities}
        if statement["task_id"] in identity_by_id or statement["formal_ordinal"] in ordinals:
            return None, ["successor task ID or formal ordinal is already assigned in the signed conflict inventory"]
        if statement["work_branch"] in work_branches or statement["receipt_branch"] in receipt_branches:
            return None, ["successor work or receipt branch is already assigned in the signed conflict inventory"]
        merged_ids = set(inventory["merged_task_ids"])
        open_ids = set(inventory["open_task_ids"])
        if merged_ids & open_ids:
            return None, ["conflict inventory marks the same task both merged and open"]
        if not merged_ids.issubset(identity_by_id) or not open_ids.issubset(identity_by_id):
            return None, ["merged/open task lists include an ID absent from formal_task_identities"]
        if any(identity_by_id[task_id]["lifecycle_state"] != "MERGED" for task_id in merged_ids):
            return None, ["merged task list conflicts with the formal identity lifecycle state"]
        if any(identity_by_id[task_id]["lifecycle_state"] != "OPEN" for task_id in open_ids):
            return None, ["open task list conflicts with the formal identity lifecycle state"]
        if statement["prior_task_id"] not in identity_by_id:
            return None, ["prior_task_id is not present in the signed formal identity inventory"]
        if statement["prior_task_id"] not in merged_ids or identity_by_id[statement["prior_task_id"]]["lifecycle_state"] != "MERGED":
            return None, ["canonical prior task must be listed as merged in the signed formal identity inventory"]
        committed_at = (commit.get("commit", {}).get("committer") or {}).get("date")
        if not committed_at:
            return None, ["Owner-signed task-registration commit has no committer timestamp"]
        if expected_nonce is not None and statement["registration_nonce"] != expected_nonce:
            return None, ["successor-registration nonce differs from the exact execution-contract binding"]
        if expected_parent_shas is not None and binding["parents"] != expected_parent_shas:
            return None, ["successor-registration parents differ from the exact ordered execution-contract binding"]
        if datetime.fromisoformat(statement["registered_at"].replace("Z", "+00:00")) > datetime.fromisoformat(committed_at.replace("Z", "+00:00")):
            return None, ["successor registration timestamp is later than its signed commit"]
        return {
            "statement": statement,
            "repository": OWNER_AUTHORIZATION_REPOSITORY,
            "path": SUCCESSOR_REGISTRATION_PATH,
            "commit_sha": commit_sha,
            "committed_at": committed_at,
            "file_sha256": file_sha256,
            "git_blob_sha": binding["blob_sha"],
            "parents": binding["parents"],
            "main_sha": binding["main_sha"],
            "path_update_commit_sha": binding["path_update_commit_sha"],
            "signature_verified": True,
            "signature_reason": "valid",
        }, []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"authenticated 1111 successor registration readback failed closed: {error.__class__.__name__}: {error}"]


def read_authenticated_owner_authorization(
    commit_sha: str,
    *,
    github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Fetch an immutable 1111 approval and bind it to the live OAuth identity."""
    api = github_api or _gh_api_json
    try:
        actor = api("user")
        public_repo = api(f"repos/{PUBLIC_REPOSITORY}")
        private_repo = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}")
        actor_id = actor.get("id")
        public_owner_id = public_repo.get("owner", {}).get("id")
        private_owner_id = private_repo.get("owner", {}).get("id")
        if not isinstance(actor_id, int) or actor_id != public_owner_id or actor_id != private_owner_id:
            return None, ["authenticated GitHub actor is not the Owner of both the release and authorization repositories"]
        if private_repo.get("private") is not True:
            return None, ["1111 authorization repository is not confirmed private by the authenticated GitHub API"]
        if private_repo.get("default_branch") != "main":
            return None, ["1111 default branch is not main, so the fixed authorization source cannot be verified"]
        binding, binding_errors = _read_authenticated_control_path_commit(
            OWNER_AUTHORIZATION_REPOSITORY,
            OWNER_AUTHORIZATION_PATH,
            commit_sha,
            actor_id,
            allow_historical_authorization_update=True,
            api=api,
        )
        if binding_errors or binding is None:
            return None, [f"fixed 1111 authorization binding failed: {item}" for item in binding_errors]
        commit = binding["commit"]
        returned_sha = commit["sha"]
        commit_author_id = (commit.get("author") or {}).get("id")
        commit_committer_id = (commit.get("committer") or {}).get("id")
        raw = binding["raw"]
        statement = json.loads(raw.decode("utf-8"))
        schema = load_json(SCHEMA_PATH)
        statement_errors = _schema_errors(
            statement, {"$ref": "#/$defs/ownerAuthorizationStatement", "$defs": schema["$defs"]}
        )
        if statement_errors:
            return None, [f"1111 Owner authorization statement is invalid: {item}" for item in statement_errors]
        if statement["owner_actor_id"] != actor_id:
            return None, ["1111 authorization statement Owner does not match the authenticated GitHub actor"]
        commit_date = (commit.get("commit", {}).get("committer") or {}).get("date")
        if not commit_date:
            return None, ["fixed 1111 authorization commit has no GitHub committer timestamp"]
        if datetime.fromisoformat(statement["approved_at"].replace("Z", "+00:00")) > datetime.fromisoformat(commit_date.replace("Z", "+00:00")):
            return None, ["Owner authorization time is later than the fixed 1111 commit that is supposed to contain it"]
        evidence = {
            **statement,
            "authorization_repository": OWNER_AUTHORIZATION_REPOSITORY,
            "authorization_path": OWNER_AUTHORIZATION_PATH,
            "authorization_commit_sha": returned_sha,
            "authorization_committed_at": binding["committed_at"],
            "authorization_file_sha256": binding["file_sha256"],
            "authorization_signature_verified": True,
            "authorization_signature_reason": "valid",
        }
        meta = {
            "authenticated_actor_id": actor_id,
            "authorization_commit_author_id": commit_author_id,
            "authorization_commit_committer_id": commit_committer_id,
            "authorization_repository_owner_id": private_owner_id,
            "authorization_readback_commit_sha": returned_sha,
            "authorization_file_sha256": evidence["authorization_file_sha256"],
            "authorization_signature_verified": True,
            "authorization_signature_reason": "valid",
        }
        return {"evidence": evidence, "meta": meta}, []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"authenticated 1111 authorization readback failed closed: {error.__class__.__name__}: {error}"]


def read_live_transition_witness(
    transition_receipt: dict[str, Any],
    *,
    owner_authorization: dict[str, Any],
    github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Read the exact final-SHA witness from its fixed path on private 1111 main."""
    api = github_api or _gh_api_json
    try:
        actor_id = owner_authorization["meta"]["authenticated_actor_id"]
        binding, binding_errors = _read_authenticated_control_path_commit(
            OWNER_AUTHORIZATION_REPOSITORY, TRANSITION_WITNESS_PATH, None, actor_id, api=api
        )
        if binding_errors or binding is None:
            return None, [f"fixed 1111 transition-witness binding failed: {item}" for item in binding_errors]
        commit_sha = binding["path_update_commit_sha"]
        commit = binding["commit"]
        author_id = (commit.get("author") or {}).get("id")
        committer_id = (commit.get("committer") or {}).get("id")
        ancestry = api(
            f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/compare/{owner_authorization['evidence']['authorization_commit_sha']}...{commit_sha}"
        )
        if not isinstance(ancestry, dict) or ancestry.get("status") != "ahead":
            return None, ["signed 1111 witness is not a descendant of the exact signed Owner authorization commit"]
        raw = binding["raw"]
        witnessed_receipt = json.loads(raw.decode("utf-8"))
        if witnessed_receipt != transition_receipt:
            return None, ["caller-supplied transition receipt differs from the exact 1111 main-branch witness file"]

        auth_content = api(
            f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/contents/{OWNER_AUTHORIZATION_PATH}?ref={commit_sha}"
        )
        auth_raw, auth_blob_sha = _decode_control_file(
            auth_content, OWNER_AUTHORIZATION_REPOSITORY, OWNER_AUTHORIZATION_PATH, commit_sha
        )
        witness_cache = {commit_sha: commit}
        auth_entry = _path_entry_for_commit(
            OWNER_AUTHORIZATION_REPOSITORY, commit_sha, OWNER_AUTHORIZATION_PATH, api, witness_cache
        )
        if auth_entry is None or auth_entry["sha"] != auth_blob_sha:
            return None, ["R3 witness commit no longer contains the fixed Owner authorization record"]
        if hashlib.sha256(auth_raw).hexdigest() != owner_authorization["evidence"]["authorization_file_sha256"]:
            return None, ["R3 witness commit contains a different Owner authorization file"]

        committed_at = binding["committed_at"]
        if not committed_at:
            return None, ["fixed 1111 witness commit has no GitHub committer timestamp"]
        committed_time = datetime.fromisoformat(committed_at.replace("Z", "+00:00"))
        published_time = datetime.fromisoformat(transition_receipt["published_at"].replace("Z", "+00:00"))
        required_prior_times = [
            datetime.fromisoformat(transition_receipt["pr_merged_at"].replace("Z", "+00:00")),
            *[
                datetime.fromisoformat(check["completed_at"].replace("Z", "+00:00"))
                for check in transition_receipt["postpublication_checks"]
            ],
        ]
        if published_time < max(required_prior_times) or committed_time < published_time:
            return None, ["1111 witness timestamp does not follow the actual PR merge and all required final-SHA checks"]
        return {
            "witness_repository": OWNER_AUTHORIZATION_REPOSITORY,
            "witness_branch": "main",
            "witness_path": TRANSITION_WITNESS_PATH,
            "witness_readback_commit_sha": commit_sha,
            "witness_commit_author_id": author_id,
            "witness_commit_committer_id": committer_id,
            "witness_signature_verified": True,
            "witness_signature_reason": "valid",
            "witness_committed_at": committed_at,
            "witness_file_sha256": hashlib.sha256(raw).hexdigest(),
        }, []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"fixed 1111 transition-witness readback failed closed: {error.__class__.__name__}: {error}"]


def read_live_branch_protection(
    *, github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None
) -> tuple[dict[str, Any] | None, list[str]]:
    """Read and enforce actual PR-only, required-check and no-bypass rules."""
    api = github_api or _gh_api_json
    try:
        branch = api(f"repos/{PUBLIC_REPOSITORY}/branches/main")
        protection = api(f"repos/{PUBLIC_REPOSITORY}/branches/main/protection")
        rules = api(f"repos/{PUBLIC_REPOSITORY}/rules/branches/main")
        rulesets = api(f"repos/{PUBLIC_REPOSITORY}/rulesets?includes_parents=true&per_page=100")
        repository = api(f"repos/{PUBLIC_REPOSITORY}")
        if not isinstance(protection, dict) or not isinstance(rules, list) or not isinstance(rulesets, list):
            return None, ["GitHub protection, effective-rule or ruleset endpoint returned an invalid shape"]
        if len(rulesets) >= 100:
            return None, ["ruleset listing may be truncated; paginate before treating protection as complete"]

        def status_contexts(value: Any) -> tuple[list[dict[str, Any]], bool]:
            if not isinstance(value, dict):
                return [], False
            contexts = value.get("checks")
            if isinstance(contexts, list) and contexts:
                if any(
                    not isinstance(item, dict)
                    or not isinstance(item.get("context"), str)
                    or type(item.get("app_id")) is not int
                    for item in contexts
                ):
                    raise ValueError("classic required status-check context/app bindings are malformed")
                normalized = [
                    {"context": item.get("context"), "app_id": item.get("app_id")}
                    for item in contexts
                ]
                return sorted(normalized, key=lambda row: (str(row["context"]), str(row["app_id"]))), value.get("strict") is True
            legacy = value.get("contexts")
            if isinstance(legacy, list):
                return sorted(
                    [{"context": item, "app_id": None} for item in legacy if isinstance(item, str)],
                    key=lambda row: row["context"],
                ), value.get("strict") is True
            return [], value.get("strict") is True

        def targets_main(ruleset: dict[str, Any]) -> bool:
            if ruleset.get("target") not in {"branch", "push"}:
                return False
            conditions = ruleset.get("conditions")
            if conditions is None:
                return True
            if not isinstance(conditions, dict):
                raise ValueError("ruleset branch conditions are not readable")
            refs = conditions.get("ref_name")
            if not isinstance(refs, dict):
                return True
            includes = refs.get("include", [])
            excludes = refs.get("exclude", [])
            if not isinstance(includes, list) or not isinstance(excludes, list) or any(
                not isinstance(value, str) for value in (*includes, *excludes)
            ):
                raise ValueError("ruleset ref include/exclude lists are not readable")
            candidates = ("refs/heads/main", "~DEFAULT_BRANCH", "main")
            included = not includes or any(
                fnmatch.fnmatchcase(candidate, pattern)
                for pattern in includes if isinstance(pattern, str)
                for candidate in candidates
            )
            excluded = any(
                fnmatch.fnmatchcase(candidate, pattern)
                for pattern in excludes if isinstance(pattern, str)
                for candidate in candidates
            )
            return included and not excluded

        if any(not isinstance(item, dict) for item in rulesets):
            raise ValueError("ruleset listing contains a malformed entry")
        if any(item.get("enforcement") not in {"active", "evaluate", "disabled"} for item in rulesets):
            raise ValueError("ruleset enforcement state is unknown")
        applicable_rulesets = [item for item in rulesets if targets_main(item)]
        active_rulesets = [item for item in applicable_rulesets if item.get("enforcement") == "active"]
        ruleset_bypass_count = 0
        ruleset_contexts: list[dict[str, Any]] = []
        ruleset_pr_rule_present = False
        ruleset_approval_counts: list[int] = []
        ruleset_status_required = False
        ruleset_status_strict = True
        for ruleset in active_rulesets:
            actors = ruleset.get("bypass_actors")
            if not isinstance(actors, list):
                raise ValueError("applicable ruleset bypass_actors is missing or unreadable")
            ruleset_bypass_count += len(actors)
            for rule in ruleset.get("rules", []):
                if not isinstance(rule, dict):
                    raise ValueError("applicable ruleset contains a malformed rule")
                params = rule.get("parameters") or {}
                if not isinstance(params, dict):
                    raise ValueError("applicable ruleset rule parameters are malformed")
                if rule.get("type") == "pull_request":
                    ruleset_pr_rule_present = True
                    count = params.get("required_approving_review_count")
                    if type(count) is not int or count < 0:
                        raise ValueError("ruleset approval count is not a non-negative integer")
                    ruleset_approval_counts.append(count)
                    if params.get("require_code_owner_review") is True or params.get("require_last_push_approval") is True:
                        raise ValueError("ruleset adds an independent-review requirement incompatible with a single Owner")
                if rule.get("type") == "required_status_checks":
                    ruleset_status_required = True
                    strict_value = params.get("strict_required_status_checks_policy")
                    if strict_value is not True:
                        ruleset_status_strict = False
                    checks = params.get("required_status_checks", [])
                    if not isinstance(checks, list):
                        raise ValueError("ruleset required_status_checks is not a list")
                    if any(
                        not isinstance(item, dict)
                        or not isinstance(item.get("context"), str)
                        or type(item.get("integration_id")) is not int
                        for item in checks
                    ):
                        raise ValueError("ruleset required status-check context/app bindings are malformed")
                    ruleset_contexts.extend(
                        {"context": item.get("context"), "app_id": item.get("integration_id")}
                        for item in checks
                    )

        status = protection.get("required_status_checks")
        review = protection.get("required_pull_request_reviews")
        classic_contexts, classic_status_strict = status_contexts(status)
        classic_approval_count = 0
        classic_pr_bypass_count = 0
        code_owner_review_required = False
        last_push_approval_required = False
        if isinstance(review, dict):
            classic_approval_count = review.get("required_approving_review_count")
            if type(classic_approval_count) is not int or classic_approval_count < 0:
                raise ValueError("classic required approval count is not a non-negative integer")
            code_owner_review_required = review.get("require_code_owner_reviews") is True
            last_push_approval_required = review.get("require_last_push_approval") is True
            if code_owner_review_required or last_push_approval_required:
                raise ValueError("classic protection adds an independent-review requirement incompatible with a single Owner")
            bypass_allowances = review.get("bypass_pull_request_allowances", {})
            if bypass_allowances is None:
                bypass_allowances = {}
            if not isinstance(bypass_allowances, dict):
                raise ValueError("classic pull-request bypass allowances are malformed")
            allowance_lists = [bypass_allowances.get(key, []) for key in ("users", "teams", "apps")]
            if any(not isinstance(value, list) for value in allowance_lists):
                raise ValueError("classic pull-request bypass allowance lists are malformed")
            classic_pr_bypass_count = sum(len(value) for value in allowance_lists)

        effective_ruleset_contexts: list[dict[str, Any]] = []
        effective_ruleset_approval_counts: list[int] = []
        effective_ruleset_pr_rule_present = False
        for rule in rules:
            parameters = rule.get("parameters") or {}
            if not isinstance(parameters, dict):
                raise ValueError("effective branch-rule parameters are malformed")
            if rule.get("type") == "required_status_checks":
                checks = parameters.get("required_status_checks", [])
                if not isinstance(checks, list):
                    raise ValueError("effective required_status_checks is not a list")
                if any(
                    not isinstance(item, dict)
                    or not isinstance(item.get("context"), str)
                    or type(item.get("integration_id")) is not int
                    for item in checks
                ):
                    raise ValueError("effective status-check context/app bindings are malformed")
                effective_ruleset_contexts.extend(
                    {"context": item.get("context"), "app_id": item.get("integration_id")}
                    for item in checks
                )
                ruleset_status_required = True
                if parameters.get("strict_required_status_checks_policy") is not True:
                    ruleset_status_strict = False
            elif rule.get("type") == "pull_request":
                effective_ruleset_pr_rule_present = True
                count = parameters.get("required_approving_review_count")
                if type(count) is not int or count < 0:
                    raise ValueError("effective ruleset approval count is invalid")
                effective_ruleset_approval_counts.append(count)
                if parameters.get("require_code_owner_review") is True or parameters.get("require_last_push_approval") is True:
                    raise ValueError("effective ruleset adds an independent-review requirement incompatible with a single Owner")

        all_contexts = classic_contexts + effective_ruleset_contexts + ruleset_contexts
        normalized_contexts = sorted(
            { (row.get("context"), row.get("app_id")) for row in all_contexts if isinstance(row.get("context"), str) },
            key=lambda pair: (pair[0], -1 if pair[1] is None else pair[1]),
        )
        required_contexts = load_json(PROTOCOL_PATH)["prepublication"]["required_status_check_contexts"]
        required_context_pairs = sorted(
            {(item["context"], item["app_id"]) for item in required_contexts},
            key=lambda pair: (pair[0], pair[1]),
        )
        required_status_present = isinstance(status, dict) or ruleset_status_required or any(
            item.get("type") == "required_status_checks" for item in rules
        )
        strict_checks = (status is None or classic_status_strict) and ruleset_status_strict
        approval_counts = [classic_approval_count, *effective_ruleset_approval_counts, *ruleset_approval_counts]
        approval_count = max(approval_counts, default=0)
        pull_request_required = isinstance(review, dict) or effective_ruleset_pr_rule_present or ruleset_pr_rule_present
        for field in ("enforce_admins", "allow_force_pushes", "allow_deletions", "required_linear_history"):
            if not isinstance(protection.get(field), dict) or type(protection[field].get("enabled")) is not bool:
                raise ValueError(f"classic protection field {field} is missing or unreadable")
        admin_enforced = protection["enforce_admins"]["enabled"] is True
        force_push_allowed = protection["allow_force_pushes"]["enabled"] is True
        deletions_allowed = protection["allow_deletions"]["enabled"] is True
        linear_history_required = protection["required_linear_history"]["enabled"] is True or any(
            item.get("type") == "required_linear_history" for item in rules
        ) or any(
            rule.get("type") == "required_linear_history"
            for ruleset in active_rulesets for rule in ruleset.get("rules", [])
        )
        no_bypass_confirmed = admin_enforced and ruleset_bypass_count == 0 and classic_pr_bypass_count == 0
        merge_settings = {
            "allow_merge_commit": repository.get("allow_merge_commit") is True,
            "allow_squash_merge": repository.get("allow_squash_merge") is True,
            "allow_rebase_merge": repository.get("allow_rebase_merge") is True,
        }
        all_check_names = sorted({row[0] for row in normalized_contexts})
        ruleset_sha = hashlib.sha256(json.dumps(rulesets, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        snapshot = {
            "target_branch": "main",
            "protected": branch.get("protected") is True,
            "pull_request_required": pull_request_required,
            "required_approval_count": approval_count,
            "required_review": approval_count > 0,
            "code_owner_review_required": code_owner_review_required,
            "last_push_approval_required": last_push_approval_required,
            "linear_history_required": linear_history_required,
            "required_status_checks": required_status_present,
            "required_status_check_contexts": [{"context": name, "app_id": app_id} for name, app_id in normalized_contexts],
            "status_checks_strict": strict_checks,
            "admin_enforcement_enabled": admin_enforced,
            "no_bypass_confirmed": no_bypass_confirmed,
            "ruleset_bypass_actor_count": ruleset_bypass_count,
            "classic_pr_bypass_actor_count": classic_pr_bypass_count,
            "force_push_allowed": force_push_allowed,
            "deletions_allowed": deletions_allowed,
            "push_restrictions_enabled": bool(protection.get("restrictions")),
            "required_check_names": all_check_names,
            "ruleset_sha256": ruleset_sha,
            **merge_settings,
        }
        if not snapshot["protected"]:
            return None, ["GitHub reports that main is not a protected branch"]
        expected_policy = load_json(PROTOCOL_PATH)["branch_protection_requirements"]
        errors: list[str] = []
        if not snapshot["pull_request_required"]:
            errors.append("GitHub does not require a pull request before main can be updated")
        if approval_count != expected_policy["minimum_approving_reviews"]:
            errors.append("live approval count differs from the single-owner zero-approval policy")
        if code_owner_review_required or last_push_approval_required:
            errors.append("live review rules require an independent reviewer and cannot be satisfied by the single Owner")
        if not required_status_present or normalized_contexts != required_context_pairs:
            errors.append("live required status-check contexts do not exactly match the three required R3 checks")
        if not strict_checks:
            errors.append("required status checks are not configured to require an up-to-date base")
        if not no_bypass_confirmed:
            errors.append("administrator enforcement is off or a classic/ruleset bypass actor is configured")
        if snapshot["force_push_allowed"] or snapshot["deletions_allowed"]:
            errors.append("main permits force pushes or deletion")
        if linear_history_required:
            errors.append("main requires linear history and cannot accept the required merge commit")
        if not merge_settings["allow_merge_commit"] or merge_settings["allow_squash_merge"] or merge_settings["allow_rebase_merge"]:
            errors.append("repository merge settings do not enforce the R3 merge-commit path")
        exact_rule_payload = {
            "classic_branch_protection": protection,
            "effective_branch_rules": rules,
            "all_rulesets_including_parents": rulesets,
            "repository_merge_settings": merge_settings,
        }
        digest = hashlib.sha256(json.dumps(exact_rule_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        observed = {
            "status": "VERIFIED",
            **snapshot,
            "rules_sha256": digest,
            "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "ruleset_count": len(rulesets),
        }
        return observed, errors
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"live GitHub branch-protection readback failed closed: {error.__class__.__name__}: {error}"]


def read_live_postpublication_checks(
    final_sha: str,
    *,
    required_workflows: list[str],
    github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
) -> tuple[list[dict[str, Any]] | None, list[str]]:
    """Read successful push workflows whose actual head is the final main SHA."""
    api = github_api or _gh_api_json
    try:
        payload = api(f"repos/{PUBLIC_REPOSITORY}/actions/runs?head_sha={final_sha}&per_page=100")
        runs = payload.get("workflow_runs", [])
        checks: list[dict[str, Any]] = []
        errors: list[str] = []
        for name in required_workflows:
            candidates = [
                run for run in runs
                if run.get("name") == name and run.get("event") == "push" and run.get("head_branch") == "main" and run.get("head_sha") == final_sha
            ]
            if not candidates:
                errors.append(f"no live push workflow run for {name} is bound to final main SHA {final_sha}")
                continue
            run = max(candidates, key=lambda item: (item.get("run_number", 0), item.get("run_attempt", 0), item.get("updated_at", "")))
            if run.get("status") != "completed" or run.get("conclusion") != "success":
                errors.append(f"live final-main workflow {name} did not complete successfully")
                continue
            checks.append({
                "name": name,
                "sha": run["head_sha"],
                "conclusion": run["conclusion"],
                "completed_at": run["updated_at"],
                "check_url": run["html_url"],
                "workflow_run_id": str(run["id"]),
                "event": run["event"],
            })
        return checks, errors
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"live final-main Actions readback failed closed: {error.__class__.__name__}: {error}"]


def read_live_merged_pr(
    pr_number: int, *, github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None
) -> tuple[dict[str, Any] | None, list[str]]:
    api = github_api or _gh_api_json
    try:
        pr = api(f"repos/{PUBLIC_REPOSITORY}/pulls/{pr_number}")
        if pr.get("number") != pr_number or pr.get("state") != "closed" or pr.get("merged") is not True:
            return None, ["GitHub does not report the exact transition PR as closed and merged"]
        if pr.get("base", {}).get("ref") != "main" or not pr.get("merged_at"):
            return None, ["merged PR has no verified main base or merge timestamp"]
        if not isinstance(pr.get("merge_commit_sha"), str) or len(pr["merge_commit_sha"]) != 40:
            return None, ["merged PR has no exact GitHub merge commit SHA"]
        return {
            "pr_number": pr_number,
            "pr_url": pr.get("html_url"),
            "head_ref": pr.get("head", {}).get("ref"),
            "head_sha": pr.get("head", {}).get("sha"),
            "merge_commit_sha": pr.get("merge_commit_sha"),
            "merged_at": pr["merged_at"],
        }, []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"live merged PR readback failed closed: {error.__class__.__name__}: {error}"]


def read_live_main_sha(*, github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None) -> tuple[str | None, list[str]]:
    api = github_api or _gh_api_json
    try:
        branch = api(f"repos/{PUBLIC_REPOSITORY}/branches/main")
        sha = branch.get("commit", {}).get("sha")
        if not isinstance(sha, str) or len(sha) != 40:
            return None, ["live main branch response has no exact commit SHA"]
        return sha, []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"live refs/heads/main readback failed closed: {error.__class__.__name__}: {error}"]


def read_live_commit_structure(
    sha: str, *, github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None
) -> tuple[dict[str, Any] | None, list[str]]:
    """Read the tree and ordered parents from the actual GitHub commit object."""
    api = github_api or _gh_api_json
    try:
        commit = api(f"repos/{PUBLIC_REPOSITORY}/commits/{sha}")
        tree_sha = commit.get("commit", {}).get("tree", {}).get("sha")
        parents = [parent.get("sha") for parent in commit.get("parents", [])]
        if commit.get("sha") != sha or not isinstance(tree_sha, str) or len(tree_sha) != 40:
            return None, ["live GitHub commit object is missing or has no exact tree SHA"]
        if any(not isinstance(parent, str) or len(parent) != 40 for parent in parents):
            return None, ["live GitHub commit object has an invalid parent SHA"]
        return {"sha": sha, "tree_sha": tree_sha, "parents": parents}, []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"live GitHub commit-object readback failed closed: {error.__class__.__name__}: {error}"]


def resolve_effective_protocol(
    transition_receipt: dict[str, Any] | None,
    *,
    observations: dict[str, Any] | None,
    repository_owner_id: int | None,
    protocol_blob_sha: str | None = None,
    github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
    allow_main_descendant: bool = False,
) -> tuple[str, list[str]]:
    """Return R3 only after Owner, immutable 1111, live rules and final-SHA evidence agree.

    Before activation, R2 remains current. Once a merge-bound activation claim
    exists, failed or unavailable revalidation leaves R3 blocked and effective;
    only the separate signed protected-PR restoration path can select R2 again.
    """
    activation_claimed = (
        allow_main_descendant
        and isinstance(transition_receipt, dict)
        and transition_receipt.get("pr_merged") is True
        and isinstance(transition_receipt.get("actual_final_main_sha"), str)
        and bool(re.fullmatch(r"[0-9a-f]{40}", transition_receipt["actual_final_main_sha"]))
        and transition_receipt.get("pr_merge_commit_sha") == transition_receipt.get("actual_final_main_sha")
    )
    if transition_receipt is None:
        return "R2", ["no independent R3 transition receipt was supplied"]
    if observations is None:
        current = "R3" if activation_claimed else "R2"
        return current, ["no independent GitHub and fresh-clone observations were supplied"]

    schema = load_json(SCHEMA_PATH)
    errors = _schema_errors(transition_receipt, {"$ref": "#/$defs/activationReceipt", "$defs": schema["$defs"]})
    errors.extend(_schema_errors(observations, {"$ref": "#/$defs/liveObservations", "$defs": schema["$defs"]}))
    if errors:
        current = "R3" if activation_claimed else "R2"
        return current, [f"invalid R3 transition receipt: {item}" for item in errors]

    owner_authorization_matches = False
    successor_registration_matches = False
    transition_witness_matches = False
    live_pr_matches = False
    final_commit_matches = False
    final_protocol_blob_matches = False

    expected_blob = protocol_blob_sha or git_blob_sha()
    if transition_receipt["r3_protocol_blob_sha"] != expected_blob:
        errors.append("transition receipt does not bind the checked-out R3 protocol blob")
    if transition_receipt["prepublication_validation_status"] != "VALIDATED" or observations["prepublication_validation_status"] != "VALIDATED":
        errors.append("exact prepublication evidence record was not validated")
    if transition_receipt["prepublication_record_sha256"] != observations["prepublication_record_sha256"]:
        errors.append("independent readback does not match the exact prepublication evidence record")
    final_sha = transition_receipt["actual_final_main_sha"]
    if transition_receipt["pr_merged"] is not True or transition_receipt["pr_merge_commit_sha"] != final_sha:
        errors.append("GitHub PR merge commit SHA does not equal the witnessed final main SHA")
    if observations["pr_merged"] is not True or observations["pr_number"] != transition_receipt["pr_number"]:
        errors.append("live GitHub PR readback does not confirm the exact transition PR is merged")
    if observations["pr_url"] != transition_receipt["pr_url"] or observations["pr_base_branch"] != transition_receipt["pr_base_branch"] or observations["pr_head_ref"] != transition_receipt["pr_head_ref"]:
        errors.append("live PR URL or base/head refs differ from the transition receipt")
    live_pr, pr_errors = read_live_merged_pr(transition_receipt["pr_number"], github_api=github_api)
    errors.extend(pr_errors)
    if live_pr is not None:
        live_pr_matches = (
            live_pr["pr_url"] == transition_receipt["pr_url"]
            and live_pr["head_ref"] == transition_receipt["pr_head_ref"]
            and live_pr["head_sha"] == transition_receipt["candidate_head_sha"]
            and live_pr["merge_commit_sha"] == final_sha
            and live_pr["merged_at"] == transition_receipt["pr_merged_at"]
            and observations["pr_merged_at"] == live_pr["merged_at"]
            and transition_receipt["pr_merged"] is True
            and observations["pr_merged"] is True
        )
        if live_pr["pr_url"] != transition_receipt["pr_url"] or live_pr["head_ref"] != transition_receipt["pr_head_ref"] or live_pr["head_sha"] != transition_receipt["candidate_head_sha"] or live_pr["merge_commit_sha"] != final_sha:
            errors.append("authenticated GitHub PR metadata differs from the transition receipt")
        if live_pr["merged_at"] != transition_receipt["pr_merged_at"] or observations["pr_merged_at"] != live_pr["merged_at"]:
            errors.append("GitHub PR merge timestamp differs from the transition receipt readback")
    if transition_receipt["pr_head_ref"] != transition_receipt["task_branch"]:
        errors.append("transition PR head ref does not equal the authorized task branch")
    if observations["pr_merge_commit_sha"] != final_sha or observations["pr_head_sha"] != transition_receipt["candidate_head_sha"]:
        errors.append("live GitHub PR merge or head SHA differs from the transition receipt")
    if observations["remote_main_sha"] != final_sha:
        errors.append("live remote refs/heads/main does not equal the witnessed final main SHA")
    if observations["final_main_tree_sha"] != transition_receipt["actual_final_main_tree_sha"]:
        errors.append("live final commit tree differs from the transition receipt")
    if observations["final_main_parents"] != transition_receipt["actual_final_main_parents"]:
        errors.append("live final commit parents differ from the transition receipt")
    if transition_receipt["observed_remote_main_sha"] != final_sha or transition_receipt["fresh_main_clone_head_sha"] != final_sha or observations["fresh_main_clone_head_sha"] != final_sha:
        errors.append("remote main and fresh-clone HEAD must both equal the witnessed actual final main SHA")
    if transition_receipt["actual_final_main_parents"] != [transition_receipt["base_main_sha"], transition_receipt["candidate_head_sha"]]:
        errors.append("final main parents must be [base main SHA, candidate head SHA] in order")
    if transition_receipt["actual_final_main_tree_sha"] != transition_receipt["merge_preview_tree_sha"] or transition_receipt["candidate_tree_sha"] != transition_receipt["merge_preview_tree_sha"]:
        errors.append("candidate, tested merge preview and final main trees differ")
    if transition_receipt["merge_preview_parents"] != [transition_receipt["base_main_sha"], transition_receipt["candidate_head_sha"]]:
        errors.append("merge-preview parents must be [base main SHA, candidate head SHA] in order")

    approval = transition_receipt["owner_approval"]
    auth_commit = approval["authorization_commit_sha"]
    live_auth, auth_errors = read_authenticated_owner_authorization(auth_commit, github_api=github_api)
    errors.extend(auth_errors)
    if live_auth is not None:
        actual_approval = live_auth["evidence"]
        meta = live_auth["meta"]
        owner_authorization_matches = (
            approval == actual_approval
            and observations["owner_authorization"] == actual_approval
            and repository_owner_id is not None
            and actual_approval["owner_actor_id"] == repository_owner_id
            and observations["repository_owner_id"] == repository_owner_id
            and actual_approval["approved_pr_number"] == transition_receipt["pr_number"]
            and actual_approval["approved_head_sha"] == transition_receipt["candidate_head_sha"]
            and actual_approval["approved_base_sha"] == transition_receipt["base_main_sha"]
            and actual_approval["r3_protocol_blob_sha"] == transition_receipt["r3_protocol_blob_sha"]
        )
        if approval != actual_approval or observations["owner_authorization"] != actual_approval:
            errors.append("Owner authorization does not equal the exact 1111 file read at its fixed commit")
        if repository_owner_id is None or actual_approval["owner_actor_id"] != repository_owner_id:
            errors.append("transition approval is not bound to the authenticated repository Owner identity")
        if observations["repository_owner_id"] != repository_owner_id:
            errors.append("live repository Owner identity differs from the supplied repository metadata")
        for key, value in meta.items():
            if observations[key] != value:
                errors.append(f"live Owner authorization identity/readback mismatch: {key}")
        if actual_approval["approved_pr_number"] != transition_receipt["pr_number"] or actual_approval["approved_head_sha"] != transition_receipt["candidate_head_sha"]:
            errors.append("Owner authorization does not bind the exact transition PR and candidate head")
        if actual_approval["approved_base_sha"] != transition_receipt["base_main_sha"] or actual_approval["r3_protocol_blob_sha"] != transition_receipt["r3_protocol_blob_sha"]:
            errors.append("Owner authorization is stale for the admitted base SHA or activation-time R3 protocol blob")
        registration, registration_errors = read_authenticated_successor_registration(
            actual_approval["successor_registration_commit_sha"],
            expected_file_sha256=actual_approval["successor_registration_file_sha256"],
            expected_formal_base_main_sha=transition_receipt["base_main_sha"],
            github_api=github_api,
        )
        errors.extend(registration_errors)
        if registration is not None:
            registered = registration["statement"]
            successor_registration_matches = (
                actual_approval["task_id"] == registered["task_id"]
                and actual_approval["formal_ordinal"] == registered["formal_ordinal"]
                and actual_approval["approved_head_sha"] == transition_receipt["candidate_head_sha"]
                and transition_receipt["task_branch"] == registered["work_branch"]
                and transition_receipt["pr_head_ref"] == registered["work_branch"]
                and registered["r3_protocol_candidate_blob_sha"] == transition_receipt["r3_protocol_blob_sha"]
            )
            if (
                actual_approval["task_id"] != registered["task_id"]
                or actual_approval["formal_ordinal"] != registered["formal_ordinal"]
                or actual_approval["approved_head_sha"] != transition_receipt["candidate_head_sha"]
                or transition_receipt["task_branch"] != registered["work_branch"]
                or transition_receipt["pr_head_ref"] != registered["work_branch"]
                or registered["r3_protocol_candidate_blob_sha"] != transition_receipt["r3_protocol_blob_sha"]
            ):
                errors.append("Owner authorization or merged PR does not match the exact signed successor registration")
        approved_at = datetime.fromisoformat(actual_approval["approved_at"].replace("Z", "+00:00"))
        authorized_commit_at = datetime.fromisoformat(actual_approval["authorization_committed_at"].replace("Z", "+00:00"))
        if live_pr is not None:
            merged_at = datetime.fromisoformat(live_pr["merged_at"].replace("Z", "+00:00"))
            if approved_at >= merged_at or authorized_commit_at >= merged_at:
                errors.append("Owner authorization was not committed before the GitHub PR merge")
        witness_meta, witness_errors = read_live_transition_witness(
            transition_receipt, owner_authorization=live_auth, github_api=github_api
        )
        errors.extend(witness_errors)
        if witness_meta is not None:
            transition_witness_matches = all(observations.get(key) == value for key, value in witness_meta.items())
            for key, value in witness_meta.items():
                if observations[key] != value:
                    errors.append(f"live 1111 witness readback mismatch: {key}")

    live_main_sha, main_errors = read_live_main_sha(github_api=github_api)
    errors.extend(main_errors)
    if live_main_sha != final_sha:
        if allow_main_descendant and live_main_sha:
            ancestry = (github_api or _gh_api_json)(
                f"repos/{PUBLIC_REPOSITORY}/compare/{final_sha}...{live_main_sha}"
            )
            if not isinstance(ancestry, dict) or ancestry.get("status") != "ahead":
                errors.append("current main is not a strict descendant of the witnessed R3 activation commit")
        else:
            errors.append("live GitHub refs/heads/main does not equal the witnessed actual final main SHA")
    live_commit, commit_errors = read_live_commit_structure(final_sha, github_api=github_api)
    errors.extend(commit_errors)
    if live_commit is not None:
        final_commit_matches = (
            live_commit["tree_sha"] == transition_receipt["actual_final_main_tree_sha"]
            and live_commit["tree_sha"] == observations["final_main_tree_sha"]
            and live_commit["tree_sha"] == transition_receipt["merge_preview_tree_sha"]
            and live_commit["parents"] == transition_receipt["actual_final_main_parents"]
            and live_commit["parents"] == observations["final_main_parents"]
            and live_commit["parents"] == [transition_receipt["base_main_sha"], transition_receipt["candidate_head_sha"]]
        )
        if not final_commit_matches:
            errors.append("live GitHub final-main commit tree or ordered parents differ from the witnessed activation")
        if live_commit["tree_sha"] != transition_receipt["actual_final_main_tree_sha"] or live_commit["tree_sha"] != observations["final_main_tree_sha"]:
            errors.append("live GitHub final-main commit tree differs from the transition receipt or observation")
        if live_commit["parents"] != transition_receipt["actual_final_main_parents"] or live_commit["parents"] != observations["final_main_parents"]:
            errors.append("live GitHub final-main commit parents differ from the transition receipt or observation")

    live_protocol_blob, _, protocol_file_errors = _read_live_file_identity(
        PUBLIC_REPOSITORY, relative(PROTOCOL_PATH), final_sha, github_api=github_api or _gh_api_json,
    )
    errors.extend(protocol_file_errors)
    final_protocol_blob_matches = live_protocol_blob == transition_receipt["r3_protocol_blob_sha"]
    if not final_protocol_blob_matches:
        errors.append("activation final-main commit does not contain the exact witnessed R3 protocol blob")

    live_protection, protection_errors = read_live_branch_protection(github_api=github_api)
    errors.extend(protection_errors)
    if live_protection is not None:
        recorded = observations["branch_protection_rules"]
        receipt_digest = transition_receipt["branch_protection_rules_sha256"]
        if live_protection["rules_sha256"] != receipt_digest or observations["branch_protection_rules_sha256"] != receipt_digest:
            errors.append("live branch-protection rules changed or do not match the immutable transition receipt")
        if {key: recorded[key] for key in live_protection if key != "observed_at" and key != "ruleset_count"} != {key: value for key, value in live_protection.items() if key != "observed_at" and key != "ruleset_count"}:
            errors.append("recorded branch-protection details differ from the live GitHub API readback")
        if recorded["required_check_names"] != observations["required_check_names"]:
            errors.append("required check contexts differ from the exact live branch-protection rules")
    if transition_receipt["merge_method"] != "MERGE_COMMIT":
        errors.append("R3 bootstrap supports only a GitHub merge commit")

    receipt_checks = transition_receipt["postpublication_checks"]
    observed_checks = observations["postpublication_checks"]
    required_post_checks = load_json(PROTOCOL_PATH)["postpublication"]["required_workflow_names"]
    live_checks, live_check_errors = read_live_postpublication_checks(final_sha, required_workflows=required_post_checks, github_api=github_api)
    errors.extend(live_check_errors)
    errors.extend(_check_set(receipt_checks, required_post_checks, final_sha, "receipt postpublication"))
    errors.extend(_check_set(observed_checks, required_post_checks, final_sha, "live postpublication"))
    if live_checks is not None and (receipt_checks != live_checks or observed_checks != live_checks):
        errors.append("receipt and observation postpublication checks differ from the live GitHub Actions readback")

    required_contexts = load_json(PROTOCOL_PATH)["prepublication"]["required_status_check_contexts"]
    protection_snapshot = observations["branch_protection_rules"]
    activation_protection_matches = (
        transition_receipt["branch_protection_verified"] is True
        and observations["branch_protection_status"] == "VERIFIED"
        and transition_receipt["branch_protection_rules_sha256"] == observations["branch_protection_rules_sha256"]
        and protection_snapshot.get("rules_sha256") == transition_receipt["branch_protection_rules_sha256"]
        and protection_snapshot.get("pull_request_required") is True
        and protection_snapshot.get("required_approval_count") == 0
        and protection_snapshot.get("status_checks_strict") is True
        and protection_snapshot.get("admin_enforcement_enabled") is True
        and protection_snapshot.get("no_bypass_confirmed") is True
        and protection_snapshot.get("force_push_allowed") is False
        and protection_snapshot.get("deletions_allowed") is False
        and protection_snapshot.get("required_status_check_contexts") == sorted(
            required_contexts, key=lambda item: (item["context"], item["app_id"])
        )
        and sorted(transition_receipt["required_status_check_contexts"], key=lambda item: (item["context"], item["app_id"]))
        == sorted(required_contexts, key=lambda item: (item["context"], item["app_id"]))
        and observations["required_check_names"] == sorted(item["context"] for item in required_contexts)
    )
    activation_check_set_matches = (
        not _check_set(receipt_checks, required_post_checks, final_sha, "receipt postpublication")
        and not _check_set(observed_checks, required_post_checks, final_sha, "live postpublication")
        and receipt_checks == observed_checks
        and live_checks == receipt_checks
    )
    activation_proven = (
        allow_main_descendant
        and owner_authorization_matches
        and successor_registration_matches
        and transition_witness_matches
        and live_pr_matches
        and final_commit_matches
        and final_protocol_blob_matches
        and activation_protection_matches
        and activation_check_set_matches
        and transition_receipt["merge_method"] == "MERGE_COMMIT"
        and transition_receipt["pr_merged"] is True
        and observations["pr_merged"] is True
        and transition_receipt["pr_merge_commit_sha"] == final_sha
        and observations["pr_merge_commit_sha"] == final_sha
        and observations["remote_main_sha"] == final_sha
        and observations["fresh_main_clone_head_sha"] == final_sha
        and transition_receipt["observed_remote_main_sha"] == final_sha
        and transition_receipt["fresh_main_clone_head_sha"] == final_sha
    )
    if errors:
        if activation_claimed:
            if not activation_proven:
                errors.insert(0, "R3 activation is claimed by a merge-bound receipt but could not be fully reverified; R3 stays effective until signed R2 restoration")
            return "R3", errors
        return "R2", errors
    return "R3", []


def read_authenticated_r2_restore_authorization(
    commit_sha: str,
    *,
    expected_file_sha256: str | None = None,
    github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Read a separate, signed Owner instruction whose sole action is RESTORE_R2_ONLY."""
    api = github_api or _gh_api_json
    try:
        actor = api("user")
        public_repo = api(f"repos/{PUBLIC_REPOSITORY}")
        control_repo = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}")
        actor_id = actor.get("id")
        if actor_id != public_repo.get("owner", {}).get("id") or actor_id != control_repo.get("owner", {}).get("id"):
            return None, ["authenticated actor is not the Owner of both repositories"]
        if control_repo.get("private") is not True or control_repo.get("default_branch") != "main":
            return None, ["R2 restoration authorization source is not confirmed private 1111/main"]
        binding, binding_errors = _read_authenticated_control_path_commit(
            OWNER_AUTHORIZATION_REPOSITORY, R2_RESTORE_AUTHORIZATION_PATH, commit_sha, actor_id,
            expected_file_sha256=expected_file_sha256, api=api,
        )
        if binding_errors or binding is None:
            return None, [f"R2 restoration authorization binding failed: {item}" for item in binding_errors]
        commit = binding["commit"]
        raw = binding["raw"]
        file_sha256 = binding["file_sha256"]
        if expected_file_sha256 and file_sha256 != expected_file_sha256:
            return None, ["R2 restoration authorization digest differs from the independent receipt"]
        statement = json.loads(raw.decode("utf-8"))
        schema = load_json(SCHEMA_PATH)
        errors = _schema_errors(statement, {"$ref": "#/$defs/restoreAuthorizationStatement", "$defs": schema["$defs"]})
        if errors:
            return None, [f"invalid R2 restoration authorization: {item}" for item in errors]
        if statement["owner_actor_id"] != actor_id:
            return None, ["R2 restoration authorization names a different Owner account"]
        committed_at = binding["committed_at"]
        if not committed_at:
            return None, ["R2 restoration authorization commit has no committer timestamp"]
        if datetime.fromisoformat(statement["approved_at"].replace("Z", "+00:00")) > datetime.fromisoformat(committed_at.replace("Z", "+00:00")):
            return None, ["R2 restoration authorization time is later than its signed commit"]
        return {
            "statement": statement,
            "authorization_repository": OWNER_AUTHORIZATION_REPOSITORY,
            "authorization_path": R2_RESTORE_AUTHORIZATION_PATH,
            "authorization_commit_sha": commit_sha,
            "authorization_committed_at": committed_at,
            "authorization_file_sha256": file_sha256,
            "authorization_signature_verified": True,
            "authorization_signature_reason": "valid",
        }, []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"authenticated R2 restoration authorization readback failed closed: {error.__class__.__name__}: {error}"]


def read_live_r2_restoration_witness(
    recovery_receipt: dict[str, Any],
    *,
    restore_authorization: dict[str, Any],
    github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Require the latest signed 1111 witness to carry the exact restored-main receipt."""
    api = github_api or _gh_api_json
    try:
        owner_id = restore_authorization["statement"]["owner_actor_id"]
        binding, binding_errors = _read_authenticated_control_path_commit(
            OWNER_AUTHORIZATION_REPOSITORY, R2_RESTORATION_WITNESS_PATH, None, owner_id, api=api
        )
        if binding_errors or binding is None:
            return None, [f"R2 restoration witness binding failed: {item}" for item in binding_errors]
        witness_sha = binding["path_update_commit_sha"]
        commit = binding["commit"]
        auth_ancestry = api(
            f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/compare/{restore_authorization['authorization_commit_sha']}...{witness_sha}"
        )
        if not isinstance(auth_ancestry, dict) or auth_ancestry.get("status") != "ahead":
            return None, ["R2 restoration witness is not a descendant of its signed Owner authorization"]
        raw = binding["raw"]
        actual = json.loads(raw.decode("utf-8"))
        if actual != recovery_receipt:
            return None, ["caller-supplied R2 restoration receipt differs from the exact 1111 witness file"]
        auth_content = api(
            f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/contents/{R2_RESTORE_AUTHORIZATION_PATH}?ref={witness_sha}"
        )
        auth_raw, auth_blob_sha = _decode_control_file(
            auth_content, OWNER_AUTHORIZATION_REPOSITORY, R2_RESTORE_AUTHORIZATION_PATH, witness_sha
        )
        witness_cache = {witness_sha: commit}
        auth_entry = _path_entry_for_commit(
            OWNER_AUTHORIZATION_REPOSITORY, witness_sha, R2_RESTORE_AUTHORIZATION_PATH, api, witness_cache
        )
        if auth_entry is None or auth_entry["sha"] != auth_blob_sha:
            return None, ["signed restoration witness does not retain its Owner authorization file"]
        if hashlib.sha256(auth_raw).hexdigest() != recovery_receipt["owner_authorization_file_sha256"]:
            return None, ["restoration witness contains a different Owner authorization record"]
        committed_at = binding["committed_at"]
        if not committed_at:
            return None, ["R2 restoration witness commit has no committer timestamp"]
        return {
            "witness_commit_sha": witness_sha,
            "witness_file_sha256": hashlib.sha256(raw).hexdigest(),
            "witness_signature_verified": True,
            "witness_signature_reason": "valid",
            "witness_committed_at": committed_at,
        }, []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"live R2 restoration witness readback failed closed: {error.__class__.__name__}: {error}"]


def _read_live_file_identity(
    repository: str, path: str, ref: str, *, github_api: Callable[[str], dict[str, Any] | list[Any]]
) -> tuple[str | None, str | None, list[str]]:
    try:
        content = github_api(f"repos/{repository}/contents/{path}?ref={quote(ref, safe='')}")
        if content.get("path") != path or content.get("type") != "file" or content.get("encoding") != "base64":
            return None, None, [f"GitHub file readback is invalid for {repository}:{path}@{ref}"]
        raw = base64.b64decode("".join(content["content"].split()), validate=True)
        return content.get("sha"), hashlib.sha256(raw).hexdigest(), []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return None, None, [f"GitHub file readback failed closed: {error.__class__.__name__}: {error}"]


def resolve_effective_protocol_with_recovery(
    transition_receipt: dict[str, Any] | None,
    *,
    observations: dict[str, Any] | None,
    repository_owner_id: int | None,
    recovery_state: dict[str, Any] | None = None,
    recovery_state_file_sha256: str | None = None,
    recovery_receipt: dict[str, Any] | None = None,
    recovery_observations: dict[str, Any] | None = None,
    protocol_blob_sha: str | None = None,
    github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
) -> tuple[str, list[str]]:
    """Select R2 only after a complete signed R3→R2 restoration witness."""
    current, errors = resolve_effective_protocol(
        transition_receipt, observations=observations, repository_owner_id=repository_owner_id,
        protocol_blob_sha=protocol_blob_sha, github_api=github_api, allow_main_descendant=True,
    )
    if current != "R3":
        return current, errors
    if recovery_state is None:
        return "R3", errors
    schema = load_json(SCHEMA_PATH)
    state_errors = _schema_errors(recovery_state, {"$ref": "#/$defs/recoveryState", "$defs": schema["$defs"]})
    if state_errors:
        return "R3", [f"invalid R2 recovery state; R3 remains effective: {item}" for item in state_errors]
    target_r2_blob = git_blob_sha(R2_PROTOCOL_PATH)
    if recovery_state["source_r3_protocol_blob_sha"] != transition_receipt["r3_protocol_blob_sha"]:
        return "R3", ["recovery state is not bound to the effective R3 protocol blob"]
    if recovery_state["target_r2_protocol_blob_sha"] != target_r2_blob:
        return "R3", ["recovery state does not target the exact preserved R2 protocol blob"]
    if recovery_state["status"] == "NOT_REQUESTED":
        if recovery_receipt is not None or recovery_observations is not None:
            return "R3", ["R2 restoration evidence was supplied without a RESTORE_R2_PENDING main state"]
        return "R3", errors
    if recovery_receipt is None or recovery_observations is None or recovery_state_file_sha256 is None:
        return "R3", ["R2 restoration lacks a signed Owner authorization, merged-PR record or final-main witness"]
    receipt_errors = _schema_errors(recovery_receipt, {"$ref": "#/$defs/recoveryReceipt", "$defs": schema["$defs"]})
    observation_errors = _schema_errors(recovery_observations, {"$ref": "#/$defs/recoveryObservations", "$defs": schema["$defs"]})
    if receipt_errors or observation_errors:
        return "R3", [f"invalid R2 restoration evidence; R3 remains effective: {item}" for item in receipt_errors + observation_errors]
    api = github_api or _gh_api_json
    errors = []
    if recovery_state["status"] != "RESTORE_R2_PENDING":
        errors.append("R2 restoration state is not pending")
    if recovery_receipt["source_r3_protocol_blob_sha"] != recovery_state["source_r3_protocol_blob_sha"]:
        errors.append("R2 restoration witness source R3 blob differs from the pending state")
    if recovery_receipt["target_r2_protocol_blob_sha"] != target_r2_blob:
        errors.append("R2 restoration witness does not identify the exact R2 blob")
    if recovery_receipt["recovery_state_file_sha256"] != recovery_state_file_sha256:
        errors.append("R2 restoration witness does not bind the exact pending state file bytes")
    if recovery_receipt["pr_number"] <= 0 or recovery_receipt["candidate_head_sha"] != recovery_observations["recovery_pr_head_sha"]:
        errors.append("restoration PR number or candidate SHA differs from the independent observation")
    if recovery_receipt["final_main_sha"] != recovery_receipt["remote_main_sha"] or recovery_receipt["final_main_sha"] != recovery_receipt["fresh_clone_sha"]:
        errors.append("restoration final SHA differs from remote main or fresh clone")
    if recovery_receipt["final_main_sha"] != recovery_observations["recovery_pr_merge_commit_sha"]:
        errors.append("restoration final SHA differs from the exact GitHub merge commit")
    if recovery_observations["recovery_pr_base_sha"] != recovery_receipt["base_main_sha"]:
        errors.append("restoration base SHA differs from its recovery PR base")
    if recovery_receipt["final_main_parents"] != [recovery_receipt["base_main_sha"], recovery_receipt["candidate_head_sha"]]:
        errors.append("restoration merge commit parents are not [base, candidate] in order")
    if recovery_receipt["merge_preview_parents"] != [recovery_receipt["base_main_sha"], recovery_receipt["candidate_head_sha"]]:
        errors.append("restoration preview parents are not [base, candidate] in order")
    if recovery_receipt["final_main_tree_sha"] != recovery_receipt["merge_preview_tree_sha"]:
        errors.append("restoration final tree differs from the tested merge-preview tree")
    if recovery_observations["current_main_sha"] != recovery_receipt["final_main_sha"] and recovery_observations["current_main_sha"] != recovery_observations.get("remote_main_sha"):
        errors.append("current main observation is internally inconsistent")
    if recovery_observations["recovery_pr_merged"] is not True:
        errors.append("GitHub does not confirm a merged protected recovery PR")
    if recovery_observations["recovery_pr_merge_commit_sha"] != recovery_receipt["final_main_sha"]:
        errors.append("GitHub recovery PR merge commit differs from the receipt")
    if recovery_observations["recovery_pr_base_sha"] != recovery_receipt["base_main_sha"]:
        errors.append("GitHub recovery PR base differs from the receipt")
    if recovery_observations["final_tree_sha"] != recovery_receipt["final_main_tree_sha"] or recovery_observations["final_parents"] != recovery_receipt["final_main_parents"]:
        errors.append("GitHub final commit tree or parents differ from the receipt")
    if recovery_observations["remote_main_sha"] != recovery_observations["current_main_sha"]:
        errors.append("live remote main differs from the current main observation")
    if recovery_observations["fresh_clone_sha"] != recovery_receipt["final_main_sha"]:
        errors.append("fresh-clone HEAD differs from the restoration final SHA")
    if recovery_observations["current_r2_protocol_blob_sha"] != target_r2_blob:
        errors.append("current main does not contain the exact R2 protocol blob")
    if recovery_observations["current_recovery_state_file_sha256"] != recovery_state_file_sha256:
        errors.append("current main does not contain the exact pending recovery-state bytes")
    required_contexts = load_json(PROTOCOL_PATH)["prepublication"]["required_status_check_contexts"]
    if recovery_observations["required_status_check_contexts"] != required_contexts or recovery_receipt["required_status_check_contexts"] != required_contexts:
        errors.append("recovery did not use every exact R3 required status context/app ID")
    if recovery_receipt["branch_protection_rules_sha256"] != recovery_observations["branch_protection_rules_sha256"]:
        errors.append("recovery witness and live observation use different protected-main rules")
    if recovery_receipt["owner_authorization_commit_sha"] != recovery_observations["authorization_commit_sha"]:
        errors.append("restoration receipt and live observation bind different Owner authorization commits")
    if recovery_observations["authorization_signature_verified"] is not True or recovery_observations["authorization_signature_reason"] != "valid":
        errors.append("Owner restoration authorization lacks a verified GitHub signature")
    if recovery_observations["witness_signature_verified"] is not True or recovery_observations["witness_signature_reason"] != "valid":
        errors.append("R2 restoration witness lacks a verified GitHub signature")

    authorization, authorization_errors = read_authenticated_r2_restore_authorization(
        recovery_receipt["owner_authorization_commit_sha"],
        expected_file_sha256=recovery_receipt["owner_authorization_file_sha256"], github_api=api,
    )
    errors.extend(authorization_errors)
    if authorization is not None:
        statement = authorization["statement"]
        expected_fields = {
            "action": "RESTORE_R2_ONLY", "scope": "ONE_TIME_R3_TO_R2_RESTORATION_ONLY",
            "source_r3_protocol_blob_sha": recovery_state["source_r3_protocol_blob_sha"],
            "target_r2_protocol_blob_sha": target_r2_blob,
            "recovery_state_file_sha256": recovery_state_file_sha256,
            "pr_number": recovery_receipt["pr_number"], "task_id": recovery_receipt["task_id"],
            "formal_ordinal": recovery_receipt["formal_ordinal"],
            "work_branch": recovery_receipt["work_branch"],
            "candidate_head_sha": recovery_receipt["candidate_head_sha"],
            "base_main_sha": recovery_receipt["base_main_sha"],
            "merge_preview_sha": recovery_receipt["merge_preview_sha"],
            "merge_preview_tree_sha": recovery_receipt["merge_preview_tree_sha"],
            "prepublication_record_sha256": recovery_receipt["prepublication_record_sha256"],
        }
        for key, value in expected_fields.items():
            if statement.get(key) != value:
                errors.append(f"RESTORE_R2_ONLY authorization does not bind {key}")
        if statement["owner_actor_id"] != repository_owner_id or statement["owner_actor_id"] != recovery_observations["repository_owner_id"]:
            errors.append("R2 restoration authorization is not bound to the repository Owner")

    live_pr, pr_errors = read_live_merged_pr(recovery_receipt["pr_number"], github_api=api)
    errors.extend(pr_errors)
    if live_pr is not None and (
        live_pr["head_sha"] != recovery_receipt["candidate_head_sha"]
        or live_pr["merge_commit_sha"] != recovery_receipt["final_main_sha"]
        or live_pr["head_ref"] != recovery_receipt["work_branch"]
    ):
        errors.append("live GitHub recovery PR metadata differs from the signed restoration record")

    live_protection, protection_errors = read_live_branch_protection(github_api=api)
    errors.extend(protection_errors)
    if live_protection is not None and live_protection["rules_sha256"] != recovery_receipt["branch_protection_rules_sha256"]:
        errors.append("live branch protections differ from those witnessed for the recovery merge")
    live_main_sha, main_errors = read_live_main_sha(github_api=api)
    errors.extend(main_errors)
    if live_main_sha != recovery_observations["current_main_sha"]:
        errors.append("current main SHA differs from its live GitHub ref")
    if live_main_sha and live_main_sha != recovery_receipt["final_main_sha"]:
        ancestry = api(f"repos/{PUBLIC_REPOSITORY}/compare/{recovery_receipt['final_main_sha']}...{live_main_sha}")
        if not isinstance(ancestry, dict) or ancestry.get("status") != "ahead":
            errors.append("current main is not a descendant of the witnessed R2 restoration commit")
    live_final, final_errors = read_live_commit_structure(recovery_receipt["final_main_sha"], github_api=api)
    errors.extend(final_errors)
    if live_final is not None and (live_final["tree_sha"] != recovery_receipt["final_main_tree_sha"] or live_final["parents"] != recovery_receipt["final_main_parents"]):
        errors.append("live restoration commit object differs from the witnessed tree or parent order")
    current_r2_blob, _, r2_file_errors = _read_live_file_identity(
        PUBLIC_REPOSITORY, relative(R2_PROTOCOL_PATH), live_main_sha or recovery_receipt["final_main_sha"], github_api=api,
    )
    errors.extend(r2_file_errors)
    if current_r2_blob != target_r2_blob:
        errors.append("current main no longer carries the exact R2 protocol blob")
    state_blob, state_digest, state_file_errors = _read_live_file_identity(
        PUBLIC_REPOSITORY, relative(RECOVERY_STATE_PATH), live_main_sha or recovery_receipt["final_main_sha"], github_api=api,
    )
    errors.extend(state_file_errors)
    if state_digest != recovery_state_file_sha256:
        errors.append("current main recovery-state file differs from the exact pending state")

    candidate_commit, candidate_errors = read_live_commit_structure(recovery_receipt["candidate_head_sha"], github_api=api)
    preview_commit, preview_errors = read_live_commit_structure(recovery_receipt["merge_preview_sha"], github_api=api)
    errors.extend(candidate_errors)
    errors.extend(preview_errors)
    if candidate_commit is not None and candidate_commit["tree_sha"] != recovery_receipt["merge_preview_tree_sha"]:
        errors.append("recovery candidate tree differs from its tested merge preview")
    if preview_commit is not None and preview_commit["parents"] != recovery_receipt["merge_preview_parents"]:
        errors.append("live recovery merge-preview parents differ from the receipt")
    if preview_commit is not None and preview_commit["tree_sha"] != recovery_receipt["merge_preview_tree_sha"]:
        errors.append("live recovery merge-preview tree differs from the receipt")

    live_checks, check_errors = read_live_postpublication_checks(
        recovery_receipt["final_main_sha"],
        required_workflows=load_json(PROTOCOL_PATH)["postpublication"]["required_workflow_names"], github_api=api,
    )
    errors.extend(check_errors)
    errors.extend(_check_set(recovery_receipt["postpublication_checks"], load_json(PROTOCOL_PATH)["postpublication"]["required_workflow_names"], recovery_receipt["final_main_sha"], "R2 restoration postpublication"))
    if live_checks is not None and live_checks != recovery_receipt["postpublication_checks"]:
        errors.append("R2 restoration postpublication checks differ from authenticated Actions readback")

    witness_meta, witness_errors = read_live_r2_restoration_witness(
        recovery_receipt, restore_authorization=authorization or {"statement": {"owner_actor_id": repository_owner_id}}, github_api=api,
    ) if authorization else (None, ["signed R2 restoration authorization is missing"])
    errors.extend(witness_errors)
    if witness_meta is not None:
        if witness_meta["witness_commit_sha"] != recovery_observations["witness_commit_sha"]:
            errors.append("live signed R2 restoration witness commit differs from the independent observation")
        if witness_meta["witness_file_sha256"] != recovery_observations["witness_file_sha256"]:
            errors.append("live signed R2 restoration witness differs from the receipt")
        if datetime.fromisoformat(witness_meta["witness_committed_at"].replace("Z", "+00:00")) < datetime.fromisoformat(recovery_receipt["published_at"].replace("Z", "+00:00")):
            errors.append("R2 restoration witness predates the final publication observation")

    if errors:
        return "R3", [f"R2 restoration did not verify; R3 remains effective: {item}" for item in errors]
    return "R2", []


def _check_set(
    checks: list[dict[str, Any]], required_names: list[str], expected_sha: str, label: str
) -> list[str]:
    errors: list[str] = []
    names = [check["name"] for check in checks]
    if sorted(names) != sorted(required_names) or len(names) != len(set(names)):
        errors.append(f"{label} checks do not exactly match the observed required-check set")
    for check in checks:
        if check["sha"] != expected_sha:
            errors.append(f"{label} check {check['name']} is bound to a different SHA")
        if check["conclusion"] != "success":
            errors.append(f"{label} check {check['name']} is not a completed success")
        if check["event"] != "push" or not check["workflow_run_id"]:
            errors.append(f"{label} check {check['name']} is not an identified push workflow run")
    return errors


def _pull_request_workflow_errors(
    checks: list[dict[str, Any]], *, pr_number: int, head_sha: str, base_sha: str,
    preview_sha: str, required_workflows: list[str], required_check_names: list[str]
) -> list[str]:
    errors: list[str] = []
    names = [check["workflow_name"] for check in checks]
    if sorted(names) != sorted(required_workflows) or len(names) != len(set(names)):
        errors.append("pull_request workflow evidence does not exactly cover the R3-required workflow set")
    if len({check["workflow_run_id"] for check in checks}) != len(checks):
        errors.append("pull_request workflow evidence reuses a workflow run ID")
    if len({check["check_run_id"] for check in checks}) != len(checks):
        errors.append("pull_request workflow evidence reuses a GitHub check-run ID")
    seen_check_contexts = set()
    expected_checkout_ref = f"refs/remotes/pull/{pr_number}/merge"
    for check in checks:
        details = urlparse(check["check_run_url"])
        expected_path = f"/{PUBLIC_REPOSITORY}/actions/runs/{check['workflow_run_id']}/job/{check['check_run_id']}"
        if details.netloc != "github.com" or details.path != expected_path:
            errors.append(f"check run {check['check_run_name']} details URL does not bind its workflow and check-run IDs")
        if check["event"] != "pull_request" or check["pull_request_number"] != pr_number:
            errors.append(f"workflow {check['workflow_name']} is not a pull_request run for PR #{pr_number}")
        if check["base_sha"] != base_sha or check["head_sha"] != head_sha:
            errors.append(f"workflow {check['workflow_name']} is bound to a stale PR base or head SHA")
        if check["check_run_sha"] != head_sha:
            errors.append(f"check run {check['check_run_name']} is not associated with the exact PR head SHA")
        if check["checkout_ref"] != expected_checkout_ref or check["checkout_sha"] != preview_sha:
            errors.append(f"workflow {check['workflow_name']} did not check out the exact GitHub PR merge-preview ref")
        if check["conclusion"] != "success":
            errors.append(f"workflow {check['workflow_name']} did not complete successfully")
        seen_check_contexts.add(check["check_run_name"])
    if not set(required_check_names).issubset(seen_check_contexts):
        errors.append("the actual branch-protection required check contexts are absent from the successful PR runs")
    return errors


def _suite_receipt_errors(receipt: dict[str, Any], *, canonical_identity: dict[str, Any], expected: dict[str, Any], candidate_sha: str) -> list[str]:
    errors: list[str] = []
    if receipt["task_id"] != canonical_identity.get("task_id"):
        errors.append("full-suite receipt task ID does not match the current authorized task")
    if receipt["task_branch"] != canonical_identity.get("task_branch"):
        errors.append("full-suite receipt branch does not match the current authorized task")
    if receipt["sha"] != candidate_sha:
        errors.append("full-suite receipt is not bound to the exact candidate SHA")
    if receipt["inventory_sha256"] != expected.get("test_inventory_sha256"):
        errors.append("full-suite inventory digest is not from the bound current run")
    if receipt["test_count"] != expected.get("test_count"):
        errors.append("full-suite test count is not from the bound current run")
    if receipt["environment_sha256"] != expected.get("environment_sha256"):
        errors.append("full-suite environment digest differs from the recorded run environment")
    started = datetime.fromisoformat(receipt["started_at"].replace("Z", "+00:00"))
    finished = datetime.fromisoformat(receipt["finished_at"].replace("Z", "+00:00"))
    elapsed = (finished - started).total_seconds()
    if elapsed < 0 or abs(elapsed - receipt["duration_seconds"]) > 1.1:
        errors.append("canonical full-suite elapsed time does not match its recorded start and finish")
    if receipt["process_exit_code"] != 0 or receipt["termination_reason"] != "NATURAL_PROCESS_EXIT":
        errors.append("canonical full-suite process did not exit successfully and naturally")
    if any(receipt[field] != 0 for field in ("failures", "errors", "skips")):
        errors.append("canonical full-suite receipt contains a failure, error or skip")
    if not receipt["clean_before"] or not receipt["clean_after"] or receipt["watchdog_used"]:
        errors.append("canonical full-suite receipt is not a clean natural run")
    return errors


def validate_suite_receipt(
    receipt: dict[str, Any], *, canonical_identity: dict[str, Any], expected: dict[str, Any], candidate_sha: str
) -> list[str]:
    schema = load_json(SCHEMA_PATH)
    errors = _schema_errors(receipt, {"$ref": "#/$defs/suiteReceipt", "$defs": schema["$defs"]})
    if errors:
        return errors
    return _suite_receipt_errors(receipt, canonical_identity=canonical_identity, expected=expected, candidate_sha=candidate_sha)


def _successor_transaction_record_schema() -> dict[str, Any]:
    """Use the unchanged R3 evidence shape with successor-only auth/review fields."""
    schema = copy.deepcopy(load_json(SCHEMA_PATH))
    successor_schema = load_json(SUCCESSOR_SCHEMA_PATH)
    definitions = schema["$defs"]
    definitions["successorTransactionAuthorizationRecord"] = successor_schema["$defs"]["finalTransactionAuthorizationRecord"]
    definitions["successorAuthorizationEvidence"] = copy.deepcopy(
        successor_schema["$defs"]["successorAuthorizationEvidence"]
    )
    definitions["successorAuthorizationEvidence"]["properties"]["statement"]["$ref"] = (
        "#/$defs/successorTransactionAuthorizationRecord"
    )
    definitions["successorPullRequestReview"] = successor_schema["$defs"]["successorPullRequestReview"]
    definitions["successorRequiredCheck"] = successor_schema["$defs"]["requiredCheck"]
    transaction = definitions["transactionRecord"]
    transaction["properties"]["owner_approval"] = {"$ref": "#/$defs/successorAuthorizationEvidence"}
    transaction["required"].append("transaction_id")
    transaction["properties"]["transaction_id"] = {"$ref": "#/$defs/safeId"}
    transaction["required"].append("required_context_evidence")
    transaction["properties"]["required_context_evidence"] = {
        "type": "array", "minItems": 3, "items": {"$ref": "#/$defs/successorRequiredCheck"}
    }
    transaction["properties"]["pull_request_reviews"]["items"] = {
        "$ref": "#/$defs/successorPullRequestReview"
    }
    identity = transaction["properties"]["task_identity"]
    for field in (
        "successor_registration_profile", "successor_registration_path", "successor_registration_id",
        "successor_protocol_blob_sha", "successor_protocol_file_sha256",
    ):
        identity["required"].append(field)
    identity["properties"].update({
        "successor_registration_profile": {"const": SUCCESSOR_PROTOCOL_ID},
        "successor_registration_path": {
            "type": "string",
            "pattern": "^instructions/goal-mode/r3-successors/registrations/[A-Za-z0-9][A-Za-z0-9._-]{7,127}\\.json$",
        },
        "successor_registration_id": {"$ref": "#/$defs/safeId"},
        "successor_protocol_blob_sha": {"$ref": "#/$defs/sha1"},
        "successor_protocol_file_sha256": {"$ref": "#/$defs/sha256"},
    })
    return schema


def validate_transaction_record(
    record: dict[str, Any],
    *,
    phase: str,
    expected: dict[str, Any],
    synthetic: bool = False,
    successor_mode: bool = False,
    github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None,
) -> list[str]:
    """Validate a future R3 transaction against live observations.

    `expected` supplies exact GitHub PR/ref and branch-protection observations,
    test-run inventory and repository Owner metadata. Formal task identity is
    loaded from the checked-out canonical sources. `synthetic` is only for unit
    fixtures; the CLI never enables it.
    """
    errors: list[str] = []
    schema = _successor_transaction_record_schema() if successor_mode else load_json(SCHEMA_PATH)
    errors.extend(_schema_errors(record, {"$ref": "#/$defs/transactionRecord", "$defs": schema["$defs"]}))
    if errors:
        return errors
    if phase not in {"prepublication", "postpublication"}:
        return ["phase must be prepublication or postpublication"]

    if synthetic:
        canonical_identity = expected
    else:
        canonical_identity, identity_errors = authoritative_task_context()
        errors.extend(identity_errors)
        if identity_errors:
            return errors

    if successor_mode and canonical_identity.get("successor_registration_profile") != SUCCESSOR_PROTOCOL_ID:
        errors.append("successor transaction validation requires a canonical task bound to the effective successor profile")
    if not successor_mode and canonical_identity.get("successor_registration_profile") == SUCCESSOR_PROTOCOL_ID:
        errors.append("successor-profile task cannot use the legacy fixed-bootstrap transaction validator")
    successor_ledger = (
        expected.get("successor_control_ledger") if synthetic
        else canonical_identity.get("successor_control_ledger")
    ) if successor_mode else None
    if successor_mode:
        if not isinstance(successor_ledger, dict):
            errors.append("successor transaction lacks the authenticated append-only 1111 control ledger")
        else:
            protocol_digest = hashlib.sha256(SUCCESSOR_PROTOCOL_PATH.read_bytes()).hexdigest()
            if len([row for row in successor_ledger.get("migrations", []) if row["statement"].get("protocol_sha256") == protocol_digest]) != 1:
                errors.append("successor transaction protocol is not uniquely effective through a verified migration witness")
    if errors:
        return errors

    identity = record["task_identity"]
    for key in (
        "task_id", "formal_ordinal", "task_branch", "current_task_source_sha256",
        "task_identity_model_sha256", "execution_contract_sha256",
        "successor_registration_commit_sha", "successor_registration_file_sha256",
        "successor_registration_nonce", "successor_registration_parent_shas",
    ):
        if identity[key] != canonical_identity.get(key):
            errors.append(f"task identity field {key} differs from the exact authorized current task source")
    if successor_mode:
        for key in (
            "successor_registration_profile", "successor_registration_path", "successor_registration_id",
            "successor_protocol_blob_sha", "successor_protocol_file_sha256",
        ):
            if identity[key] != canonical_identity.get(key):
                errors.append(f"task identity field {key} differs from the exact successor registration")
        if identity["successor_protocol_blob_sha"] != git_blob_sha(SUCCESSOR_PROTOCOL_PATH):
            errors.append("task contract does not bind the exact successor protocol blob")
        if identity["successor_protocol_file_sha256"] != hashlib.sha256(SUCCESSOR_PROTOCOL_PATH.read_bytes()).hexdigest():
            errors.append("task contract does not bind the exact successor protocol bytes")
        if record["transaction_id"] != record["owner_approval"]["statement"]["transaction_id"]:
            errors.append("transaction ID differs from its exact Owner authorization record")

    pr = record["pull_request"]
    refs = record["refs"]
    expected_pr_number = expected.get("pr_number")
    if pr["number"] != expected_pr_number:
        errors.append("pull request number differs from the admitted PR")
    if pr["head_sha"] != expected.get("candidate_head_sha"):
        errors.append("PR head differs from the exact tested candidate SHA")
    if pr["head_branch"] != canonical_identity.get("task_branch"):
        errors.append("PR head branch differs from the canonical task branch")
    if pr["base_branch"] != expected.get("base_branch", "main"):
        errors.append("PR base branch differs from the observed target branch")
    if refs["base_main_sha"] != expected.get("base_main_sha"):
        errors.append("base main advanced or differs from the tested base SHA")
    if refs["candidate_tree_sha"] != expected.get("candidate_tree_sha"):
        errors.append("candidate tree differs from the tested candidate tree SHA")
    if refs["merge_preview_sha"] != expected.get("merge_preview_sha"):
        errors.append("merge preview ref changed since it was tested")
    if refs["merge_preview_tree_sha"] != expected.get("merge_preview_tree_sha"):
        errors.append("merge preview tree changed since it was tested")
    if refs["merge_preview_parents"] != [refs["base_main_sha"], pr["head_sha"]]:
        errors.append("merge preview parents must be [base main SHA, candidate head SHA] in order")
    if refs["merge_preview_tree_sha"] != refs["candidate_tree_sha"]:
        errors.append("tested merge-preview tree differs from the candidate tree")

    paths = record["changed_paths"]
    if sorted(paths["reviewed_paths"]) != sorted(paths["observed_paths"]):
        errors.append("observed changed paths include an unreviewed or missing path")
    if sorted(paths["reviewed_paths"]) != sorted(expected.get("reviewed_changed_paths", [])):
        errors.append("reviewed path manifest differs from the exact approved scope")
    if sorted(paths["observed_paths"]) != sorted(expected.get("observed_changed_paths", [])):
        errors.append("observed changed paths differ from the exact GitHub PR file list")

    protection = record["branch_protection"]
    live_protection = expected.get("branch_protection_rules")
    required_names = expected.get("required_check_names")
    if not isinstance(required_names, list) or live_protection is None:
        errors.append("required checks and branch rules must come from a successful live GitHub protection read")
    else:
        if protection["rules_sha256"] != expected.get("branch_protection_rules_sha256") or protection["rules_sha256"] != live_protection.get("rules_sha256"):
            errors.append("branch-protection rules digest differs from the live GitHub observation")
        if protection["required_check_names"] != required_names or live_protection.get("required_check_names") != required_names:
            errors.append("required check contexts differ from the exact live GitHub branch rules")
        if protection["status"] != "VERIFIED" or protection["target_branch"] != "main" or protection["protected"] is not True:
            errors.append("main branch protection is unknown, absent or targets another branch")
        if protection["pull_request_required"] is not True:
            errors.append("GitHub does not enforce pull requests before updating main")
        if protection["required_approval_count"] != 0:
            errors.append("GitHub approval count violates the single-owner zero-approval policy")
        if protection["code_owner_review_required"] or protection["last_push_approval_required"]:
            errors.append("GitHub requires an independent reviewer, which the single Owner cannot provide")
        if protection["linear_history_required"]:
            errors.append("GitHub requires linear history and conflicts with the R3 merge-commit method")
        normalized_recorded_contexts = sorted(
            protection["required_status_check_contexts"], key=lambda item: (item["context"], item["app_id"])
        )
        normalized_protocol_contexts = sorted(
            load_json(PROTOCOL_PATH)["prepublication"]["required_status_check_contexts"],
            key=lambda item: (item["context"], item["app_id"]),
        )
        if normalized_recorded_contexts != normalized_protocol_contexts:
            errors.append("required status contexts/app IDs differ from the exact R3 contract")
        if protection["status_checks_strict"] is not True:
            errors.append("required checks do not require an up-to-date base")
        if protection["admin_enforcement_enabled"] is not True or protection["no_bypass_confirmed"] is not True:
            errors.append("main protection permits an administrator/ruleset bypass")
        if protection["ruleset_bypass_actor_count"] != 0 or protection["classic_pr_bypass_actor_count"] != 0:
            errors.append("main protection contains one or more explicit bypass actors")
        if protection["force_push_allowed"] is not False or protection["deletions_allowed"] is not False:
            errors.append("main protection permits force push or branch deletion")
        if not protection["allow_merge_commit"] or protection["allow_squash_merge"] or protection["allow_rebase_merge"]:
            errors.append("repository settings do not allow only the supported merge-commit path")
        stable_fields = [key for key in live_protection if key not in {"observed_at", "ruleset_count"}]
        if any(protection.get(key) != live_protection.get(key) for key in stable_fields):
            errors.append("recorded branch-protection details differ from the exact live GitHub observation")
        required_workflows = load_json(PROTOCOL_PATH)["prepublication"]["required_workflow_names"]
        if record["required_check_names"] != required_names:
            errors.append("recorded required check names differ from the live branch-rule contexts")
        errors.extend(_pull_request_workflow_errors(
            record["pull_request_workflow_checks"], pr_number=pr["number"], head_sha=pr["head_sha"],
            base_sha=refs["base_main_sha"], preview_sha=refs["merge_preview_sha"],
            required_workflows=required_workflows, required_check_names=required_names,
        ))

    suite_receipts = record["canonical_full_suite_receipts"]
    if not suite_receipts:
        errors.append("at least one complete natural canonical full-suite receipt is required to establish evidence sufficiency")
    run_ids = [receipt["run_id"] for receipt in suite_receipts]
    if len(run_ids) != len(set(run_ids)):
        errors.append("canonical full-suite receipts must have distinct run IDs")
    for receipt in suite_receipts:
        errors.extend(_suite_receipt_errors(receipt, canonical_identity=canonical_identity, expected=expected, candidate_sha=pr["head_sha"]))

    revalidation = record["canonical_full_suite_evidence_revalidation"]
    for key, expected_key in (
        ("candidate_head_sha", "candidate_head_sha"),
        ("inventory_sha256", "test_inventory_sha256"),
        ("test_count", "test_count"),
        ("environment_sha256", "environment_sha256"),
    ):
        if revalidation[key] != expected.get(expected_key):
            errors.append(f"independent canonical-suite revalidation {key} differs from the exact candidate evidence")
    if sorted(revalidation["receipt_run_ids"]) != sorted(run_ids):
        errors.append("independent canonical-suite revalidation does not cover every exact receipt run ID")
    matching_revalidation_checks = [
        check for check in record["pull_request_workflow_checks"]
        if check["workflow_name"] == revalidation["workflow_name"]
        and check["workflow_run_id"] == revalidation["workflow_run_id"]
        and check["check_run_id"] == revalidation["check_run_id"]
        and check["check_run_url"] == revalidation["check_run_url"]
        and check["conclusion"] == revalidation["conclusion"]
        and check["head_sha"] == revalidation["candidate_head_sha"]
    ]
    if len(matching_revalidation_checks) != 1:
        errors.append("independent canonical-suite revalidation is not bound to one successful exact-head PR validator check")

    approval = record["owner_approval"]
    if successor_mode:
        owner_id = expected.get("repository_owner_id", 49422864)
        if owner_id != 49422864:
            errors.append("successor transaction Owner identity differs from the verified root-authority Owner")
        if synthetic:
            live_pr_meta = None
            live_reviews = record["pull_request_reviews"]
            authorized_reviewers = expected.get("authorized_reviewer_ids")
            live_contexts = expected.get("live_required_contexts")
            live_merge_time = expected.get("pr_merged_at") if phase == "postpublication" else None
            live_pull = {}
            live_author_id = pr["author_id"]
            preparation_valid_through = expected.get("pr_created_at")
        else:
            live_pr_meta, live_reviews, pr_review_errors = read_live_successor_pr_reviews(
                pr["number"], github_api=github_api
            )
            errors.extend(pr_review_errors)
            if live_pr_meta is None or live_reviews is None:
                live_reviews = []
                live_pull = {}
                live_author_id = pr["author_id"]
                preparation_valid_through = expected.get("pr_created_at")
            else:
                live_pull = live_pr_meta["pull_request"]
                live_author_id = (live_pull.get("user") or {}).get("id")
                preparation_valid_through = live_pull.get("created_at")
                if (
                    live_pull.get("number") != pr["number"]
                    or (live_pull.get("base") or {}).get("ref") != "main"
                    or (live_pull.get("base") or {}).get("sha") != refs["base_main_sha"]
                    or (live_pull.get("head") or {}).get("ref") != pr["head_branch"]
                    or (live_pull.get("head") or {}).get("sha") != pr["head_sha"]
                    or live_pull.get("html_url") != pr["url"]
                    or live_author_id != pr["author_id"]
                    or live_pull.get("draft") is not False
                ):
                    errors.append("successor transaction PR metadata differs from exact live GitHub refs, author or non-draft state")
                if phase == "prepublication":
                    if live_pull.get("state") != "open" or live_pull.get("merged") is True:
                        errors.append("successor prepublication validation requires the exact PR to remain open and unmerged")
                else:
                    if (
                        live_pull.get("state") != "closed" or live_pull.get("merged") is not True
                        or (live_pull.get("merged_by") or {}).get("id") != owner_id
                        or live_pull.get("merge_commit_sha") != record["publication"]["actual_final_main_sha"]
                    ):
                        errors.append("successor postpublication validation requires the exact Owner-merged PR")
                if live_reviews != record["pull_request_reviews"]:
                    errors.append("recorded successor PR reviews differ from the exact live GitHub review history")
                authorized_reviewers = None
                live_merge_time = live_pull.get("merged_at") if phase == "postpublication" else None
            live_contexts, live_context_errors = read_live_successor_required_contexts(
                pr["head_sha"], github_api=github_api
            )
            errors.extend(live_context_errors)
            if phase == "prepublication":
                live_branch_rules, branch_errors = read_live_branch_protection(github_api=github_api)
                errors.extend(branch_errors)
                if live_branch_rules is not None:
                    stable_live = {key: value for key, value in live_branch_rules.items() if key not in {"observed_at", "ruleset_count"}}
                    stable_recorded = {key: value for key, value in protection.items() if key not in {"observed_at", "ruleset_count"}}
                    if stable_recorded != stable_live:
                        errors.append("successor candidate branch-protection record differs from the live GitHub rules")

        if live_contexts is None:
            errors.append("successor transaction has no live exact-head required-context readback")
        else:
            errors.extend(_valid_successor_context_set(
                record["required_context_evidence"], live_contexts, pr["head_sha"]
            ))
        cutoff = live_merge_time or expected.get("observed_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        independent_review, owner_review, review_errors = validate_successor_review_gate(
            live_reviews, author_id=pr["author_id"], owner_id=owner_id, head_sha=pr["head_sha"],
            authorized_reviewer_ids=authorized_reviewers, valid_through=cutoff,
        )
        errors.extend(review_errors)
        if owner_review is not None and owner_review["actor_id"] != owner_id:
            errors.append("Owner exact-head review is not from the root-authority Owner")
        protocol_digest = hashlib.sha256(SUCCESSOR_PROTOCOL_PATH.read_bytes()).hexdigest()
        if synthetic:
            diff_sha256 = expected.get("formal_pr_diff_sha256")
        else:
            diff_sha256, diff_errors = read_live_successor_pr_diff_sha256(
                pr["number"], base_sha=refs["base_main_sha"], head_sha=pr["head_sha"], github_api=github_api
            )
            errors.extend(diff_errors)
        owner_review_records = successor_ledger.get("owner_reviews", [])
        matching_owner_records = [
            row for row in owner_review_records
            if row["statement"].get("formal_pr_number") == pr["number"]
            and row["statement"].get("pr_author_id") == live_author_id
            and row["statement"].get("formal_base_sha") == refs["base_main_sha"]
            and row["statement"].get("formal_candidate_head_sha") == pr["head_sha"]
            and row["statement"].get("formal_pr_diff_sha256") == diff_sha256
            and row["statement"].get("protocol_sha256") == protocol_digest
        ]
        if len(matching_owner_records) != 1:
            errors.append("successor PR lacks exactly one Owner-signed exact-head review record for its live diff")
        else:
            errors.extend(validate_successor_owner_exact_head_review_record(
                matching_owner_records[0], owner_id=owner_id,
                task_id=identity["task_id"], formal_ordinal=identity["formal_ordinal"],
                registration_id=identity["successor_registration_id"],
                pr_number=pr["number"], author_id=live_author_id,
                base_sha=refs["base_main_sha"], head_sha=pr["head_sha"],
                diff_sha256=diff_sha256, protocol_sha256=protocol_digest, valid_through=cutoff,
            ))
        registration_id = identity["successor_registration_id"]
        errors.extend(validate_successor_transaction_authorization_statement(
            approval, ledger=successor_ledger,
            task_id=identity["task_id"], formal_ordinal=identity["formal_ordinal"],
            registration_id=registration_id, transaction_id=record["transaction_id"],
            pr_number=pr["number"], candidate_head_sha=pr["head_sha"], base_main_sha=refs["base_main_sha"],
            protocol_blob_sha=identity["successor_protocol_blob_sha"],
            protocol_file_sha256=identity["successor_protocol_file_sha256"],
            preparation_valid_through=preparation_valid_through,
            valid_through=cutoff,
        ))
    else:
        if approval["owner_actor_id"] != expected.get("repository_owner_id"):
            errors.append("approval actor is not the observed repository Owner")
        if approval["task_id"] != identity["task_id"] or approval["formal_ordinal"] != identity["formal_ordinal"]:
            errors.append("Owner transition authorization does not bind the exact registered task ID and ordinal")
        if approval["successor_registration_commit_sha"] != identity["successor_registration_commit_sha"] or approval["successor_registration_file_sha256"] != identity["successor_registration_file_sha256"]:
            errors.append("Owner transition authorization does not bind the exact signed successor-registration record")
        if approval["approved_pr_number"] != pr["number"] or approval["approved_head_sha"] != pr["head_sha"] or approval["approved_base_sha"] != refs["base_main_sha"]:
            errors.append("Owner transition authorization does not bind the exact PR, head and base")
        if approval["r3_protocol_blob_sha"] != expected.get("r3_protocol_blob_sha", git_blob_sha()):
            errors.append("Owner transition authorization does not bind the exact R3 protocol version")
        if approval["authorization_commit_sha"] != expected.get("owner_authorization_commit_sha") or approval["authorization_file_sha256"] != expected.get("owner_authorization_file_sha256"):
            errors.append("Owner transition authorization differs from the immutable 1111 readback")
    if protection["required_review"] and not successor_mode:
        author_id = pr.get("author_id")
        valid_review = any(
            review["state"] == "APPROVED" and review["actor_id"] != author_id and review["commit_sha"] == pr["head_sha"]
            for review in record["pull_request_reviews"]
        )
        if not valid_review:
            errors.append("verified branch rules require an independent APPROVED review on the exact PR head")
    if phase == "prepublication":
        if pr["state"] != "OPEN" or record["publication"]["status"] != "NOT_MERGED":
            errors.append("prepublication evidence requires an open PR and NOT_MERGED state")
        if successor_mode and any(
            row["statement"].get("transaction_id") == record["transaction_id"]
            for row in successor_ledger.get("publications", [])
        ):
            errors.append("successor transaction already has an immutable publication witness and cannot be replayed")
    else:
        if pr["state"] != "MERGED":
            errors.append("postpublication validation requires the PR to be actually merged")
        publication = record["publication"]
        final_sha = publication["actual_final_main_sha"]
        if publication["status"] != "PUBLISHED_AND_VERIFIED":
            errors.append("postpublication state is not PUBLISHED_AND_VERIFIED")
        if not final_sha:
            errors.append("actual final main SHA is missing")
        if publication["actual_final_main_parents"] != [refs["base_main_sha"], pr["head_sha"]]:
            errors.append("final main parents differ from [base main SHA, candidate head SHA]")
        if publication["actual_final_main_tree_sha"] != refs["merge_preview_tree_sha"]:
            errors.append("actual final main tree differs from the tested merge-preview tree")
        if publication["observed_remote_main_sha"] != final_sha:
            errors.append("remote refs/heads/main does not equal the actual final main SHA")
        if publication["observed_remote_main_sha"] != expected.get("remote_main_sha"):
            errors.append("published main SHA differs from the independent remote-ref observation")
        if publication["fresh_main_checkout_sha"] != final_sha:
            errors.append("fresh main checkout does not equal the actual final main SHA")
        if publication["fresh_main_checkout_sha"] != expected.get("fresh_main_checkout_sha"):
            errors.append("fresh checkout SHA differs from the independent clean-clone observation")
        if publication["actual_final_main_tree_sha"] != expected.get("actual_final_main_tree_sha"):
            errors.append("final main tree differs from the observed GitHub commit object")
        if publication["actual_final_main_parents"] != expected.get("actual_final_main_parents"):
            errors.append("final main parents differ from the observed GitHub commit object")
        post_names = expected.get("required_postpublication_check_names", required_names or [])
        errors.extend(_check_set(publication["postpublication_checks"], post_names, final_sha or "", "postpublication"))
        if publication["postpublication_checks"] != expected.get("postpublication_checks"):
            errors.append("postpublication check receipts differ from the live GitHub check readback")
        projection = publication["projection_check"]
        if projection is None or projection["source_sha"] != final_sha or projection["unexpected_changed_paths"]:
            errors.append("final-SHA projection check is missing, stale or reports unexpected generated paths")
        if projection != expected.get("projection_check"):
            errors.append("projection check differs from the exact final-main validation receipt")
        if successor_mode:
            witnesses = [
                row for row in successor_ledger.get("publications", [])
                if row["statement"].get("transaction_id") == record["transaction_id"]
            ]
            if len(witnesses) != 1:
                errors.append("postpublication successor transaction lacks exactly one signed append-only 1111 publication witness")
            else:
                witness_row = witnesses[0]
                witness = witness_row["statement"]
                auth_statement = approval["statement"]
                expected_witness_fields = {
                    "status": "PUBLISHED_AND_VERIFIED",
                    "transaction_id": record["transaction_id"],
                    "preparation_id": auth_statement["preparation_id"],
                    "registration_id": identity["successor_registration_id"],
                    "authorization_id": auth_statement["authorization_id"],
                    "task_id": identity["task_id"], "formal_ordinal": identity["formal_ordinal"],
                    "pr_number": pr["number"], "candidate_head_sha": pr["head_sha"],
                    "base_main_sha": refs["base_main_sha"],
                    "protocol_blob_sha": identity["successor_protocol_blob_sha"],
                    "protocol_file_sha256": identity["successor_protocol_file_sha256"],
                    "actual_final_main_sha": final_sha,
                    "actual_final_main_tree_sha": publication["actual_final_main_tree_sha"],
                    "actual_final_main_parents": publication["actual_final_main_parents"],
                    "remote_main_sha": publication["observed_remote_main_sha"],
                    "fresh_clone_sha": publication["fresh_main_checkout_sha"],
                    "projection_check": projection,
                }
                for key, value in expected_witness_fields.items():
                    if witness.get(key) != value:
                        errors.append(f"signed successor publication witness does not bind exact transaction field {key}")
                if witness["prepublication_record_sha256"] != expected.get("prepublication_record_sha256"):
                    errors.append("publication witness does not bind the exact prepublication transaction record digest")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-successor", action="store_true")
    parser.add_argument("--verify-amendment-preparation", action="store_true")
    parser.add_argument("--preparation-id")
    parser.add_argument("--preparation-action", choices=["PUSH_REGISTERED_BRANCH", "CREATE_DRAFT_PULL_REQUEST", "COLLECT_REQUIRED_CHECKS"])
    parser.add_argument("--preparation-candidate-seed-sha256")
    parser.add_argument("--preparation-at")
    parser.add_argument("--transition-receipt", type=Path)
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--repository-owner-id", type=int)
    parser.add_argument("--recovery-receipt", type=Path)
    parser.add_argument("--recovery-observations", type=Path)
    parser.add_argument("--transaction-record", type=Path)
    parser.add_argument("--expected-context", type=Path)
    parser.add_argument("--phase", choices=["prepublication", "postpublication"])
    parser.add_argument("--successor-profile", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    has_transition = any((args.transition_receipt, args.observations, args.repository_owner_id is not None))
    if has_transition and not all((args.transition_receipt, args.observations, args.repository_owner_id is not None)):
        parser.error("transition selection requires --transition-receipt, --observations and --repository-owner-id")
    has_recovery_evidence = any((args.recovery_receipt, args.recovery_observations))
    if has_recovery_evidence and (not has_transition or not all((args.recovery_receipt, args.recovery_observations))):
        parser.error("R2 recovery selection requires a complete transition receipt/observation and both recovery receipt/observations")
    if args.transaction_record and (not args.expected_context or not args.phase):
        parser.error("--transaction-record requires --expected-context and --phase")
    if args.phase and not args.transaction_record:
        parser.error("--phase requires --transaction-record")
    if args.successor_profile and not args.transaction_record:
        parser.error("--successor-profile requires --transaction-record")
    if args.check_successor and not SUCCESSOR_PROTOCOL_PATH.is_file():
        parser.error("--check-successor requires the versioned successor protocol file")

    contract_errors = validate_contract()
    if args.check_successor or args.successor_profile:
        contract_errors.extend(validate_successor_protocol_contract())
    if contract_errors:
        print("RELEASE_TRANSACTION_PROTOCOL_R3_INVALID", file=sys.stderr)
        for error in contract_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    if args.verify_amendment_preparation:
        authority, authority_errors = read_authenticated_task22_amendment_preparation_authority()
        if authority_errors or authority is None:
            print("TASK22_AMENDMENT_PREPARATION_AUTHORITY_INVALID", file=sys.stderr)
            for error in authority_errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        checkout, checkout_errors = validate_task22_local_preparation_checkout(authority)
        if checkout_errors or checkout is None:
            print("TASK22_AMENDMENT_DRAFT_CHECKOUT_INVALID", file=sys.stderr)
            for error in checkout_errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        print(
            "TASK22_AMENDMENT_DRAFT_PREPARATION_AUTHORIZED "
            f"task={authority['task_id']} branch={checkout['branch']} head={checkout['head_sha']} base={checkout['base_main_sha']} "
            "scope=prepare/push/draft/collect-checks-only"
        )
        return 0

    preparation_args = (args.preparation_id, args.preparation_action, args.preparation_candidate_seed_sha256)
    if any(preparation_args):
        if not all(preparation_args):
            parser.error("PREPARATION_ONLY validation requires --preparation-id, --preparation-action and --preparation-candidate-seed-sha256")
        if any((args.transaction_record, args.phase, args.successor_profile, args.verify_amendment_preparation)):
            parser.error("PREPARATION_ONLY validation is a separate action and cannot be combined with a transaction or amendment-prep check")
        identity, identity_errors = authoritative_task_context()
        if identity_errors:
            print("R3_SUCCESSOR_PREPARATION_IDENTITY_INVALID", file=sys.stderr)
            for error in identity_errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        ledger = identity.get("successor_control_ledger")
        if not isinstance(ledger, dict):
            print("R3_SUCCESSOR_PREPARATION_LEDGER_MISSING", file=sys.stderr)
            return 1
        authorized_at = args.preparation_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        errors = validate_successor_preparation_authorization_statement(
            args.preparation_id, ledger=ledger, task_id=identity["task_id"],
            formal_ordinal=identity["formal_ordinal"], registration_id=identity["successor_registration_id"],
            work_branch=identity["task_branch"], base_main_sha=identity["formal_base_main_sha"],
            protocol_blob_sha=identity["successor_protocol_blob_sha"],
            protocol_file_sha256=identity["successor_protocol_file_sha256"],
            candidate_seed_sha256=args.preparation_candidate_seed_sha256,
            action=args.preparation_action, valid_through=authorized_at,
        )
        if errors:
            print("R3_SUCCESSOR_PREPARATION_AUTHORIZATION_INVALID", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        print(
            "R3_SUCCESSOR_PREPARATION_ONLY_OK "
            f"preparation_id={args.preparation_id} action={args.preparation_action} "
            f"task={identity['task_id']} branch={identity['task_branch']}"
        )
        return 0

    current = "R2"
    activation_errors = ["no independent R3 transition receipt was supplied"]
    if has_transition:
        current, activation_errors = resolve_effective_protocol_with_recovery(
            load_json(args.transition_receipt),
            observations=load_json(args.observations),
            repository_owner_id=args.repository_owner_id,
            recovery_state=load_json(RECOVERY_STATE_PATH),
            recovery_state_file_sha256=hashlib.sha256(RECOVERY_STATE_PATH.read_bytes()).hexdigest(),
            recovery_receipt=load_json(args.recovery_receipt) if args.recovery_receipt else None,
            recovery_observations=load_json(args.recovery_observations) if args.recovery_observations else None,
        )
    if args.transaction_record:
        if args.successor_profile:
            errors = validate_transaction_record(
                load_json(args.transaction_record), phase=args.phase,
                expected=load_json(args.expected_context), successor_mode=True,
            )
            if errors:
                print("RELEASE_TRANSACTION_R3_SUCCESSOR_RECORD_INVALID", file=sys.stderr)
                for error in errors:
                    print(f"- {error}", file=sys.stderr)
                return 1
            if args.phase == "prepublication":
                print("RELEASE_TRANSACTION_R3_SUCCESSOR_PREFLIGHT_OK")
            else:
                print("RELEASE_TRANSACTION_R3_SUCCESSOR_RECORD_OK phase=postpublication")
            return 0
        if current == "R3" and activation_errors:
            print("R3_TRANSACTION_REJECTED: R3 remains effective but its live governance evidence is blocked", file=sys.stderr)
            for error in activation_errors:
                print(f"- {error}", file=sys.stderr)
            return 2
        if args.phase == "postpublication" and current != "R3":
            print("R3_TRANSACTION_REJECTED: R2 remains the effective policy", file=sys.stderr)
            for error in activation_errors:
                print(f"- {error}", file=sys.stderr)
            return 2
        if not args.expected_context or not args.phase:
            parser.error("--transaction-record requires --expected-context and --phase")
        errors = validate_transaction_record(
            load_json(args.transaction_record), phase=args.phase, expected=load_json(args.expected_context)
        )
        if errors:
            print("RELEASE_TRANSACTION_R3_RECORD_INVALID", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        if args.phase == "prepublication":
            print(f"RELEASE_TRANSACTION_R3_PREFLIGHT_OK current={current}")
        else:
            print("RELEASE_TRANSACTION_R3_RECORD_OK phase=postpublication")
        return 0

    if current == "R3":
        if activation_errors:
            print("RELEASE_TRANSACTION_PROTOCOL_R3_CURRENT_BLOCKED", file=sys.stderr)
            for error in activation_errors:
                print(f"- {error}", file=sys.stderr)
            return 2
        print("RELEASE_TRANSACTION_PROTOCOL_R3_CURRENT")
    else:
        print(f"RELEASE_TRANSACTION_PROTOCOL_R3_CANDIDATE_OK current=R2 path={relative(PROTOCOL_PATH)}")
        for error in activation_errors:
            print(f"- {error}")
    if args.check_successor:
        print("RELEASE_TRANSACTION_PROTOCOL_R3_SUCCESSOR_CANDIDATE_NOT_EFFECTIVE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
