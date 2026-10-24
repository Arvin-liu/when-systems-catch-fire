#!/usr/bin/env python3
"""Validate the R3 candidate contract and exact protected-PR evidence.

R3 remains a candidate until an independent Owner-approved 1111 witness binds
the actual final main SHA. Without that witness, R2 remains effective.
"""

from __future__ import annotations

import argparse
import base64
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
SUCCESSOR_REGISTRATION_PATH = "instructions/goal-mode/IGNITION-R3-ADMISSION-SUCCESSOR-REGISTRATION-R1.json"
R2_RESTORE_AUTHORIZATION_PATH = "instructions/goal-mode/IGNITION-R3-TO-R2-RESTORE-AUTHORIZATION-R1.json"
TRANSITION_WITNESS_PATH = "reports/operations/IGNITION-2026-10-18-R3-PUBLISHED-AND-VERIFIED-R0.json"
R2_RESTORATION_WITNESS_PATH = "reports/operations/IGNITION-R3-TO-R2-RESTORED-AND-VERIFIED-R1.json"
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
    registration_sha = registration.get("commit_sha")
    registration_file_sha256 = registration.get("file_sha256")
    registration_nonce = registration.get("registration_nonce")
    registration_parent_shas = registration.get("parent_shas")
    if not isinstance(registration_sha, str) or len(registration_sha) != 40:
        errors.append("execution contract does not bind the exact Owner-signed successor-registration commit")
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
    }
    if not errors:
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
    api: Callable[[str], dict[str, Any] | list[Any]],
) -> tuple[dict[str, Any] | None, list[str]]:
    """Bind a verified Owner signature to one new fixed-path commit on current main."""
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
            return None, [f"fixed Owner control path already existed in the signed commit's first parent; replay/update is rejected for {repository}:{path}"]
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
            OWNER_AUTHORIZATION_REPOSITORY, OWNER_AUTHORIZATION_PATH, commit_sha, actor_id, api=api
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


def validate_transaction_record(
    record: dict[str, Any],
    *,
    phase: str,
    expected: dict[str, Any],
    synthetic: bool = False,
) -> list[str]:
    """Validate a future R3 transaction against live observations.

    `expected` supplies exact GitHub PR/ref and branch-protection observations,
    test-run inventory and repository Owner metadata. Formal task identity is
    loaded from the checked-out canonical sources. `synthetic` is only for unit
    fixtures; the CLI never enables it.
    """
    errors: list[str] = []
    schema = load_json(SCHEMA_PATH)
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

    identity = record["task_identity"]
    for key in (
        "task_id", "formal_ordinal", "task_branch", "current_task_source_sha256",
        "task_identity_model_sha256", "execution_contract_sha256",
        "successor_registration_commit_sha", "successor_registration_file_sha256",
        "successor_registration_nonce", "successor_registration_parent_shas",
    ):
        if identity[key] != canonical_identity.get(key):
            errors.append(f"task identity field {key} differs from the exact authorized current task source")

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
    if protection["required_review"]:
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
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--transition-receipt", type=Path)
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--repository-owner-id", type=int)
    parser.add_argument("--recovery-receipt", type=Path)
    parser.add_argument("--recovery-observations", type=Path)
    parser.add_argument("--transaction-record", type=Path)
    parser.add_argument("--expected-context", type=Path)
    parser.add_argument("--phase", choices=["prepublication", "postpublication"])
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

    contract_errors = validate_contract()
    if contract_errors:
        print("RELEASE_TRANSACTION_PROTOCOL_R3_INVALID", file=sys.stderr)
        for error in contract_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
