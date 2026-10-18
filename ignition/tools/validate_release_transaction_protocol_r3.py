#!/usr/bin/env python3
"""Validate the R3 candidate contract and exact protected-PR evidence.

R3 remains a candidate until an independent Owner-approved 1111 witness binds
the actual final main SHA. Without that witness, R2 remains effective.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
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
CURRENT_TASK_PATH = ROOT / "data/operations/current-task-lineage-status.json"
TASK_IDENTITY_MODEL_PATH = ROOT / "data/operations/task-identity-model-r1.json"
OWNER_AUTHORIZATION_REPOSITORY = "Arvin-liu/1111"
OWNER_AUTHORIZATION_PATH = "instructions/goal-mode/IGNITION-2026-10-18-R3-ONE-TIME-TRANSITION-AUTHORIZATION-R0.json"
TRANSITION_WITNESS_PATH = "reports/operations/IGNITION-2026-10-18-R3-PUBLISHED-AND-VERIFIED-R0.json"
PUBLIC_REPOSITORY = "Arvin-liu/when-systems-catch-fire"
R2_CANONICAL_SUITE_MINIMUM_SECONDS = 14400


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
    if execution.get("identity_expectations", {}).get("current_formal_task") != task_id or execution.get("identity_expectations", {}).get("release_candidate_task") != task_id:
        errors.append("lineage, identity model and authorized execution contract task IDs disagree")

    ordinal = next((execution.get(key) for key in ("formal_ordinal", "task_ordinal", "ordinal") if type(execution.get(key)) is int), None)
    branch = execution.get("expected_task_branch")
    if ordinal is None:
        errors.append("canonical execution contract does not bind a formal task ordinal")
    if not isinstance(branch, str) or not branch:
        errors.append("canonical execution contract does not bind an expected task branch")

    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    try:
        source_digest = digest(CURRENT_TASK_PATH)
        identity_digest = digest(TASK_IDENTITY_MODEL_PATH)
        execution_digest = digest(execution_path)
    except OSError as error:
        return {}, [f"canonical task identity digest could not be read: {error}"]

    return {
        "task_id": task_id,
        "formal_ordinal": ordinal,
        "task_branch": branch,
        "current_task_source_sha256": source_digest,
        "task_identity_model_sha256": identity_digest,
        "execution_contract_sha256": execution_digest,
    }, errors


def _gh_api_json(endpoint: str) -> dict[str, Any] | list[Any]:
    """Read GitHub through the user's existing OAuth-backed gh session."""
    result = subprocess.run(
        ["gh", "api", endpoint], check=True, capture_output=True, text=True, timeout=30
    )
    return json.loads(result.stdout)


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
        commit = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/commits/{commit_sha}")
        content = api(
            f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/contents/{OWNER_AUTHORIZATION_PATH}?ref={commit_sha}"
        )
        actor_id = actor.get("id")
        public_owner_id = public_repo.get("owner", {}).get("id")
        private_owner_id = private_repo.get("owner", {}).get("id")
        commit_author_id = (commit.get("author") or {}).get("id")
        commit_committer_id = (commit.get("committer") or {}).get("id")
        returned_sha = commit.get("sha")
        if not isinstance(actor_id, int) or actor_id != public_owner_id or actor_id != private_owner_id:
            return None, ["authenticated GitHub actor is not the Owner of both the release and authorization repositories"]
        if private_repo.get("private") is not True:
            return None, ["1111 authorization repository is not confirmed private by the authenticated GitHub API"]
        if private_repo.get("default_branch") != "main":
            return None, ["1111 default branch is not main, so the fixed authorization source cannot be verified"]
        if returned_sha != commit_sha or commit_author_id != actor_id or commit_committer_id != actor_id:
            return None, ["fixed 1111 authorization commit is missing or is not authored and committed by the authenticated Owner"]
        if content.get("path") != OWNER_AUTHORIZATION_PATH or content.get("type") != "file" or content.get("encoding") != "base64":
            return None, ["fixed 1111 authorization path did not resolve to a readable file at the exact commit"]
        raw = base64.b64decode("".join(content["content"].split()), validate=True)
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
            "authorization_committed_at": commit_date,
            "authorization_file_sha256": hashlib.sha256(raw).hexdigest(),
        }
        meta = {
            "authenticated_actor_id": actor_id,
            "authorization_commit_author_id": commit_author_id,
            "authorization_commit_committer_id": commit_committer_id,
            "authorization_repository_owner_id": private_owner_id,
            "authorization_readback_commit_sha": returned_sha,
            "authorization_file_sha256": evidence["authorization_file_sha256"],
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
        history = api(
            f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/commits?path={quote(TRANSITION_WITNESS_PATH, safe='')}&sha=main&per_page=1"
        )
        if not isinstance(history, list) or not history or not isinstance(history[0].get("sha"), str):
            return None, ["fixed R3 witness file has no commit in the 1111 main-branch history"]
        commit_sha = history[0]["sha"]
        commit = api(f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/commits/{commit_sha}")
        actor_id = owner_authorization["meta"]["authenticated_actor_id"]
        author_id = (commit.get("author") or {}).get("id")
        committer_id = (commit.get("committer") or {}).get("id")
        if commit.get("sha") != commit_sha or author_id != actor_id or committer_id != actor_id:
            return None, ["fixed 1111 witness commit is not attributed to the authenticated Owner"]

        content = api(
            f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/contents/{TRANSITION_WITNESS_PATH}?ref={commit_sha}"
        )
        if content.get("path") != TRANSITION_WITNESS_PATH or content.get("type") != "file" or content.get("encoding") != "base64":
            return None, ["fixed 1111 witness path did not resolve to a readable file at its exact main-branch commit"]
        raw = base64.b64decode("".join(content["content"].split()), validate=True)
        witnessed_receipt = json.loads(raw.decode("utf-8"))
        if witnessed_receipt != transition_receipt:
            return None, ["caller-supplied transition receipt differs from the exact 1111 main-branch witness file"]

        auth_content = api(
            f"repos/{OWNER_AUTHORIZATION_REPOSITORY}/contents/{OWNER_AUTHORIZATION_PATH}?ref={commit_sha}"
        )
        if auth_content.get("path") != OWNER_AUTHORIZATION_PATH or auth_content.get("encoding") != "base64":
            return None, ["R3 witness commit no longer contains the fixed Owner authorization record"]
        auth_raw = base64.b64decode("".join(auth_content["content"].split()), validate=True)
        if hashlib.sha256(auth_raw).hexdigest() != owner_authorization["evidence"]["authorization_file_sha256"]:
            return None, ["R3 witness commit contains a different Owner authorization file"]

        committed_at = (commit.get("commit", {}).get("committer") or {}).get("date")
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
            "witness_committed_at": committed_at,
            "witness_file_sha256": hashlib.sha256(raw).hexdigest(),
        }, []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as error:
        return None, [f"fixed 1111 transition-witness readback failed closed: {error.__class__.__name__}: {error}"]


def read_live_branch_protection(
    *, github_api: Callable[[str], dict[str, Any] | list[Any]] | None = None
) -> tuple[dict[str, Any] | None, list[str]]:
    """Read and hash the actual classic protection and matching rulesets."""
    api = github_api or _gh_api_json
    try:
        branch = api(f"repos/{PUBLIC_REPOSITORY}/branches/main")
        protection = api(f"repos/{PUBLIC_REPOSITORY}/branches/main/protection")
        rules = api(f"repos/{PUBLIC_REPOSITORY}/rules/branches/main")
        status = protection.get("required_status_checks")
        review = protection.get("required_pull_request_reviews")
        if isinstance(status, dict):
            check_names = status.get("contexts") or [row.get("context") for row in status.get("checks", []) if row.get("context")]
        else:
            check_names = []
        ruleset_status_checks: list[str] = []
        ruleset_review_required = False
        ruleset_status_required = False
        if not isinstance(rules, list):
            return None, ["GitHub branch-rules endpoint did not return a ruleset list"]
        for rule in rules:
            parameters = rule.get("parameters") or {}
            if rule.get("type") == "required_status_checks":
                ruleset_status_required = True
                ruleset_status_checks.extend(
                    item.get("context") for item in parameters.get("required_status_checks", [])
                    if item.get("context")
                )
            elif rule.get("type") == "pull_request":
                ruleset_review_required = (
                    ruleset_review_required
                    or parameters.get("required_approving_review_count", 0) > 0
                    or parameters.get("require_code_owner_review") is True
                )
        review_required = bool(
            review and (
                review.get("required_approving_review_count", 0) > 0
                or review.get("require_code_owner_reviews") is True
            )
        ) or ruleset_review_required
        all_check_names = sorted(set(check_names) | set(ruleset_status_checks))
        ruleset_sha = hashlib.sha256(json.dumps(rules, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        snapshot = {
            "target_branch": "main",
            "protected": branch.get("protected") is True,
            "required_review": review_required,
            "required_status_checks": isinstance(status, dict) or ruleset_status_required,
            "admin_enforcement_enabled": protection.get("enforce_admins", {}).get("enabled") is True,
            "force_push_allowed": protection.get("allow_force_pushes", {}).get("enabled") is True,
            "deletions_allowed": protection.get("allow_deletions", {}).get("enabled") is True,
            "push_restrictions_enabled": bool(protection.get("restrictions")),
            "required_check_names": all_check_names,
            "ruleset_sha256": ruleset_sha,
        }
        if not snapshot["protected"]:
            return None, ["GitHub reports that main is not a protected branch"]
        exact_rule_payload = {"classic_branch_protection": protection, "branch_rulesets": rules}
        digest = hashlib.sha256(json.dumps(exact_rule_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        observed = {
            "status": "VERIFIED",
            **snapshot,
            "rules_sha256": digest,
            "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "ruleset_count": len(rules) if isinstance(rules, list) else None,
        }
        return observed, []
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
) -> tuple[str, list[str]]:
    """Return R3 only after OAuth, immutable 1111, live rules and final-SHA readback agree."""
    if transition_receipt is None:
        return "R2", ["no independent R3 transition receipt was supplied"]
    if observations is None:
        return "R2", ["no independent GitHub and fresh-clone observations were supplied"]

    schema = load_json(SCHEMA_PATH)
    errors = _schema_errors(transition_receipt, {"$ref": "#/$defs/activationReceipt", "$defs": schema["$defs"]})
    errors.extend(_schema_errors(observations, {"$ref": "#/$defs/liveObservations", "$defs": schema["$defs"]}))
    if errors:
        return "R2", [f"invalid R3 transition receipt: {item}" for item in errors]

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
        if actual_approval["approved_base_sha"] != transition_receipt["base_main_sha"] or actual_approval["r3_protocol_blob_sha"] != expected_blob:
            errors.append("Owner authorization is stale for the base SHA or R3 protocol blob")
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
            for key, value in witness_meta.items():
                if observations[key] != value:
                    errors.append(f"live 1111 witness readback mismatch: {key}")

    live_main_sha, main_errors = read_live_main_sha(github_api=github_api)
    errors.extend(main_errors)
    if live_main_sha != final_sha:
        errors.append("live GitHub refs/heads/main does not equal the witnessed actual final main SHA")
    live_commit, commit_errors = read_live_commit_structure(final_sha, github_api=github_api)
    errors.extend(commit_errors)
    if live_commit is not None:
        if live_commit["tree_sha"] != transition_receipt["actual_final_main_tree_sha"] or live_commit["tree_sha"] != observations["final_main_tree_sha"]:
            errors.append("live GitHub final-main commit tree differs from the transition receipt or observation")
        if live_commit["parents"] != transition_receipt["actual_final_main_parents"] or live_commit["parents"] != observations["final_main_parents"]:
            errors.append("live GitHub final-main commit parents differ from the transition receipt or observation")

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

    if errors:
        return "R2", errors
    return "R3", []


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
    for key in ("task_id", "formal_ordinal", "task_branch", "current_task_source_sha256", "task_identity_model_sha256", "execution_contract_sha256"):
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
        stable_fields = [key for key in live_protection if key not in {"observed_at", "ruleset_count"}]
        if any(protection.get(key) != live_protection.get(key) for key in stable_fields):
            errors.append("recorded branch-protection details differ from the exact live GitHub observation")
        required_workflows = load_json(PROTOCOL_PATH)["prepublication"]["required_workflow_names"]
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
    parser.add_argument("--transaction-record", type=Path)
    parser.add_argument("--expected-context", type=Path)
    parser.add_argument("--phase", choices=["prepublication", "postpublication"])
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    has_transition = any((args.transition_receipt, args.observations, args.repository_owner_id is not None))
    if has_transition and not all((args.transition_receipt, args.observations, args.repository_owner_id is not None)):
        parser.error("transition selection requires --transition-receipt, --observations and --repository-owner-id")
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
        current, activation_errors = resolve_effective_protocol(
            load_json(args.transition_receipt),
            observations=load_json(args.observations),
            repository_owner_id=args.repository_owner_id,
        )
    if args.transaction_record:
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
        print("RELEASE_TRANSACTION_PROTOCOL_R3_CURRENT")
    else:
        print(f"RELEASE_TRANSACTION_PROTOCOL_R3_CANDIDATE_OK current=R2 path={relative(PROTOCOL_PATH)}")
        for error in activation_errors:
            print(f"- {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
