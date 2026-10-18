#!/usr/bin/env python3
"""Validate the R3 candidate contract and exact protected-PR evidence.

R3 remains a candidate until an independent Owner-approved 1111 witness binds
the actual final main SHA. Without that witness, R2 remains effective.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
PROTOCOL_PATH = ROOT / "data/operations/release-transaction-protocol-r3.json"
SCHEMA_PATH = ROOT / "schemas/operations/release-transaction-protocol-r3.schema.json"
R2_PROTOCOL_PATH = ROOT / "data/operations/release-transaction-protocol-r2.json"
CURRENT_TASK_PATH = ROOT / "data/operations/current-task-lineage-status.json"
TASK_IDENTITY_MODEL_PATH = ROOT / "data/operations/task-identity-model-r1.json"


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
    if preserved["canonical_full_suite"] != r2_gates["canonical_full_suite"]:
        errors.append("R3 must preserve the exact R2 canonical full-suite requirements")
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


def resolve_effective_protocol(
    transition_receipt: dict[str, Any] | None,
    *,
    observations: dict[str, Any] | None,
    repository_owner_id: int | None,
    protocol_blob_sha: str | None = None,
) -> tuple[str, list[str]]:
    """Return R3 only when an independent witness matches authenticated live reads."""
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
    if transition_receipt["pr_merged"] is not True:
        errors.append("GitHub does not report the exact transition PR as merged")
    if transition_receipt["pr_merge_commit_sha"] != final_sha:
        errors.append("GitHub PR merge commit SHA does not equal the witnessed final main SHA")
    if observations["pr_merged"] is not True or observations["pr_number"] != transition_receipt["pr_number"]:
        errors.append("live GitHub PR readback does not confirm the exact transition PR is merged")
    if observations["pr_url"] != transition_receipt["pr_url"] or observations["pr_base_branch"] != transition_receipt["pr_base_branch"] or observations["pr_head_ref"] != transition_receipt["pr_head_ref"]:
        errors.append("live PR URL or base/head refs differ from the transition receipt")
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
    if transition_receipt["observed_remote_main_sha"] != final_sha:
        errors.append("receipt remote-main observation does not equal its actual final main SHA")
    if transition_receipt["fresh_main_clone_head_sha"] != final_sha:
        errors.append("fresh main checkout does not equal the witnessed final main SHA")
    if observations["fresh_main_clone_head_sha"] != final_sha:
        errors.append("live fresh-clone HEAD does not equal the witnessed final main SHA")
    if transition_receipt["actual_final_main_parents"] != [
        transition_receipt["base_main_sha"], transition_receipt["candidate_head_sha"]
    ]:
        errors.append("final main parents must be [base main SHA, candidate head SHA] in order")
    if transition_receipt["actual_final_main_tree_sha"] != transition_receipt["merge_preview_tree_sha"]:
        errors.append("final main tree does not equal the tested merge-preview tree")
    if transition_receipt["candidate_tree_sha"] != transition_receipt["merge_preview_tree_sha"]:
        errors.append("candidate tree does not equal the tested merge-preview tree")
    if transition_receipt["merge_preview_parents"] != [transition_receipt["base_main_sha"], transition_receipt["candidate_head_sha"]]:
        errors.append("merge-preview parents must be [base main SHA, candidate head SHA] in order")
    approval = transition_receipt["owner_approval"]
    if repository_owner_id is None or approval["owner_actor_id"] != repository_owner_id:
        errors.append("transition approval is not bound to the observed repository Owner identity")
    if approval["approved_pr_number"] != transition_receipt["pr_number"]:
        errors.append("Owner approval does not bind the witnessed PR number")
    if approval["approved_head_sha"] != transition_receipt["candidate_head_sha"]:
        errors.append("Owner approval does not bind the exact candidate head SHA")
    if observations["repository_owner_id"] != repository_owner_id:
        errors.append("live repository Owner identity differs from the supplied repository metadata")
    if observations["owner_review_actor_id"] != repository_owner_id:
        errors.append("live PR review is not from the repository Owner")
    if observations["owner_review_pr_number"] != transition_receipt["pr_number"]:
        errors.append("live Owner review does not bind the exact transition PR")
    if observations["owner_review_head_sha"] != transition_receipt["candidate_head_sha"]:
        errors.append("live Owner review does not bind the exact candidate head")
    if observations["owner_review_state"] != "APPROVED" or observations["owner_review_url"] != approval["review_url"]:
        errors.append("live Owner review is not the exact approved review recorded by the transition receipt")
    if observations["branch_protection_status"] != "VERIFIED" or observations["branch_protection_rules_sha256"] != transition_receipt["branch_protection_rules_sha256"]:
        errors.append("live branch-protection observation is missing or differs from the transition receipt")
    protection = observations["branch_protection_rules"]
    if (
        protection["target_branch"] != "main"
        or protection["required_review"] is not True
        or protection["required_status_checks"] is not True
        or protection["bypass_enabled"] is not False
        or protection["direct_main_push_allowed"] is not False
    ):
        errors.append("live branch-protection rules do not establish protected PR-only admission")
    if protection["required_check_names"] != observations["required_check_names"]:
        errors.append("required checks differ from the effective branch-protection rules")
    if transition_receipt["merge_method"] != "MERGE_COMMIT":
        errors.append("R3 bootstrap supports only a protected GitHub merge commit")
    receipt_checks = transition_receipt["postpublication_checks"]
    observed_checks = observations["postpublication_checks"]
    check_names = observations["required_check_names"]
    errors.extend(_check_set(receipt_checks, check_names, final_sha, "receipt postpublication"))
    errors.extend(_check_set(observed_checks, check_names, final_sha, "live postpublication"))
    if receipt_checks != observed_checks:
        errors.append("independent receipt postpublication checks differ from live GitHub check readback")

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
    return errors


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

    required_names = expected.get("required_check_names")
    if not isinstance(required_names, list) or not required_names:
        errors.append("required check names must come from a verified branch-protection observation")
    else:
        errors.extend(_check_set(record["candidate_checks"], required_names, pr["head_sha"], "candidate"))
        errors.extend(_check_set(record["merge_preview_checks"], required_names, refs["merge_preview_sha"], "merge-preview"))

    suite_receipts = record["canonical_full_suite_receipts"]
    if len(suite_receipts) != 2:
        errors.append("exactly two natural canonical full-suite receipts are required")
    run_ids = [receipt["run_id"] for receipt in suite_receipts]
    if len(run_ids) != len(set(run_ids)):
        errors.append("canonical full-suite receipts must have distinct run IDs")
    for receipt in suite_receipts:
        if receipt["task_id"] != canonical_identity.get("task_id"):
            errors.append("full-suite receipt task ID does not match the current authorized task")
        if receipt["task_branch"] != canonical_identity.get("task_branch"):
            errors.append("full-suite receipt branch does not match the current authorized task")
        if receipt["sha"] != pr["head_sha"]:
            errors.append("full-suite receipt is not bound to the exact candidate SHA")
        if receipt["inventory_sha256"] != expected.get("test_inventory_sha256"):
            errors.append("full-suite inventory digest is not from the bound current run")
        if receipt["test_count"] != expected.get("test_count"):
            errors.append("full-suite test count is not from the bound current run")
        if receipt["environment_sha256"] != expected.get("environment_sha256"):
            errors.append("full-suite environment digest differs from the recorded run environment")
        if receipt["duration_seconds"] < 14400:
            errors.append("canonical full-suite run did not meet the natural 14,400-second window")
        if any(receipt[field] != 0 for field in ("failures", "errors", "skips")):
            errors.append("canonical full-suite receipt contains a failure, error or skip")
        if not receipt["clean_before"] or not receipt["clean_after"] or receipt["watchdog_used"]:
            errors.append("canonical full-suite receipt is not a clean natural run")

    protection = record["branch_protection"]
    if protection["status"] != "VERIFIED" or protection["target_branch"] != "main":
        errors.append("effective main branch protection is unknown or targets another branch")
    if not protection["required_review"] or not protection["required_status_checks"] or protection["bypass_enabled"]:
        errors.append("required review/check protection or no-bypass condition is not established")
    if protection["rules_sha256"] != expected.get("branch_protection_rules_sha256"):
        errors.append("branch-protection rules digest differs from the live protected-branch observation")

    approval = record["owner_approval"]
    if approval["owner_actor_id"] != expected.get("repository_owner_id"):
        errors.append("approval actor is not the observed repository Owner")
    if approval["approved_pr_number"] != pr["number"] or approval["approved_head_sha"] != pr["head_sha"]:
        errors.append("Owner approval does not bind the exact PR and candidate head")
    if approval["review_state"] != expected.get("owner_review_state") or approval["review_url"] != expected.get("owner_review_url"):
        errors.append("Owner approval does not match the exact live GitHub review observation")
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
