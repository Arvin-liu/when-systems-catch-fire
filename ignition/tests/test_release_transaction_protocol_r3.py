from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
import time
import unittest
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from tools import validate_release_transaction_protocol as r2
from tools import validate_release_transaction_protocol_r3 as r3


def _check(name: str, sha: str) -> dict[str, str]:
    run_id = 2001 if name == "release-transaction-protocol-validation" else 2002
    return {
        "name": name, "sha": sha, "conclusion": "success", "completed_at": "2026-10-18T06:00:00Z",
        "check_url": f"https://github.com/Arvin-liu/when-systems-catch-fire/actions/runs/{run_id}",
        "workflow_run_id": str(run_id), "event": "push",
    }


def _suite(run_id: str, task_id: str, branch: str, sha: str) -> dict[str, object]:
    started_at = datetime.now(timezone.utc)
    monotonic_start = time.monotonic()
    result = subprocess.run([sys.executable, "-c", "raise SystemExit(0)"], check=False, capture_output=True)
    elapsed = time.monotonic() - monotonic_start
    finished_at = datetime.now(timezone.utc)
    return {
        "run_id": run_id, "task_id": task_id, "task_branch": branch, "sha": sha,
        "inventory_sha256": "1" * 64, "test_count": 3, "environment_sha256": "2" * 64,
        "duration_seconds": round(elapsed, 3),
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "finished_at": finished_at.isoformat().replace("+00:00", "Z"),
        "process_exit_code": result.returncode, "termination_reason": "NATURAL_PROCESS_EXIT",
        "failures": 0, "errors": 0, "skips": 0, "clean_before": True, "clean_after": True,
        "watchdog_used": False, "conclusion": "success",
        "source_url": f"https://github.com/Arvin-liu/when-systems-catch-fire/actions/runs/{run_id}",
    }


def _owner_statement(
    *, pr_number: int = 301, head_sha: str = "b" * 40, base_sha: str = "a" * 40,
    actor_id: int = 49422864, protocol_blob_sha: str | None = None,
) -> dict[str, object]:
    return {
        "approved": True, "owner_actor_id": actor_id, "approved_pr_number": pr_number,
        "approved_head_sha": head_sha, "approved_base_sha": base_sha,
        "r3_protocol_blob_sha": protocol_blob_sha or r3.git_blob_sha(),
        "scope": "ONE_TIME_R3_BOOTSTRAP_ONLY",
        "r2_duration_policy_exception": "R2_MINIMUM_NATURAL_WINDOW_14400S_NOT_CARRIED_FORWARD_IN_R3",
        "approved_at": "2026-10-18T05:30:00Z",
    }


def _owner_evidence(statement: dict[str, object] | None = None) -> dict[str, object]:
    statement = statement or _owner_statement()
    content = json.dumps(statement, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        **statement, "authorization_repository": "Arvin-liu/1111",
        "authorization_path": r3.OWNER_AUTHORIZATION_PATH,
        "authorization_commit_sha": "f" * 40,
        "authorization_committed_at": "2026-10-18T06:00:00Z",
        "authorization_file_sha256": hashlib.sha256(content).hexdigest(),
    }


def _github_api(statement: dict[str, object] | None = None, *, actor_id: int = 49422864, commit_sha: str = "f" * 40):
    statement = statement or _owner_statement(actor_id=actor_id)
    content = json.dumps(statement, sort_keys=True, separators=(",", ":")).encode("utf-8")
    values = {
        "user": {"login": "Arvin-liu", "id": actor_id},
        "repos/Arvin-liu/when-systems-catch-fire": {"owner": {"id": 49422864}},
        "repos/Arvin-liu/1111": {"owner": {"id": 49422864}, "private": True, "default_branch": "main"},
        f"repos/Arvin-liu/1111/commits/{commit_sha}": {
            "sha": commit_sha, "author": {"id": actor_id}, "committer": {"id": actor_id},
            "commit": {"committer": {"date": "2026-10-18T06:00:00Z"}},
        },
        f"repos/Arvin-liu/1111/contents/{r3.OWNER_AUTHORIZATION_PATH}?ref={commit_sha}": {
            "path": r3.OWNER_AUTHORIZATION_PATH, "type": "file", "encoding": "base64",
            "content": base64.b64encode(content).decode("ascii"),
        },
        f"repos/Arvin-liu/1111/commits?path={quote(r3.TRANSITION_WITNESS_PATH, safe='')}&sha=main&per_page=1": [{"sha": "6" * 40}],
        f"repos/Arvin-liu/1111/commits/{'6' * 40}": {
            "sha": "6" * 40, "author": {"id": actor_id}, "committer": {"id": actor_id},
            "commit": {"committer": {"date": "2026-10-18T06:40:00Z"}},
        },
        f"repos/Arvin-liu/1111/contents/{r3.OWNER_AUTHORIZATION_PATH}?ref={'6' * 40}": {
            "path": r3.OWNER_AUTHORIZATION_PATH, "type": "file", "encoding": "base64",
            "content": base64.b64encode(content).decode("ascii"),
        },
        "repos/Arvin-liu/when-systems-catch-fire/branches/main": {"protected": True, "commit": {"sha": "e" * 40}},
        f"repos/Arvin-liu/when-systems-catch-fire/commits/{'e' * 40}": {
            "sha": "e" * 40, "commit": {"tree": {"sha": "c" * 40}},
            "parents": [{"sha": "a" * 40}, {"sha": "b" * 40}],
        },
        "repos/Arvin-liu/when-systems-catch-fire/pulls/301": {
            "number": 301, "state": "closed", "merged": True,
            "base": {"ref": "main"}, "head": {"ref": "synthetic/fixture-only", "sha": "b" * 40},
            "merge_commit_sha": "e" * 40,
            "merged_at": "2026-10-18T06:30:00Z",
            "html_url": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/301",
        },
        "repos/Arvin-liu/when-systems-catch-fire/branches/main/protection": {
            "required_status_checks": None, "required_pull_request_reviews": None,
            "enforce_admins": {"enabled": False}, "allow_force_pushes": {"enabled": False},
            "allow_deletions": {"enabled": False}, "restrictions": None,
        },
        "repos/Arvin-liu/when-systems-catch-fire/rules/branches/main": [],
    }
    def read(endpoint: str):
        if endpoint not in values:
            witness_prefix = f"repos/Arvin-liu/1111/contents/{r3.TRANSITION_WITNESS_PATH}?ref="
            if endpoint == witness_prefix + "6" * 40:
                receipt_content = json.dumps(_activation_receipt(), sort_keys=True, separators=(",", ":")).encode("utf-8")
                return {
                    "path": r3.TRANSITION_WITNESS_PATH, "type": "file", "encoding": "base64",
                    "content": base64.b64encode(receipt_content).decode("ascii"),
                }
            prefix = "repos/Arvin-liu/when-systems-catch-fire/actions/runs?head_sha="
            if endpoint.startswith(prefix) and endpoint.endswith("&per_page=100"):
                final_sha = endpoint[len(prefix):-len("&per_page=100")]
                return {
                    "workflow_runs": [
                        {"name": "release-transaction-protocol-validation", "id": 2001, "event": "push", "head_branch": "main", "head_sha": final_sha, "status": "completed", "conclusion": "success", "updated_at": "2026-10-18T06:00:00Z", "html_url": "https://github.com/Arvin-liu/when-systems-catch-fire/actions/runs/2001", "run_number": 1, "run_attempt": 1},
                        {"name": "foundation-validation", "id": 2002, "event": "push", "head_branch": "main", "head_sha": final_sha, "status": "completed", "conclusion": "success", "updated_at": "2026-10-18T06:00:00Z", "html_url": "https://github.com/Arvin-liu/when-systems-catch-fire/actions/runs/2002", "run_number": 1, "run_attempt": 1},
                    ]
                }
            raise KeyError(endpoint)
        return values[endpoint]
    return read


def _workflow_check(name: str, run_id: int, check_name: str, *, head_sha: str = "b" * 40, base_sha: str = "a" * 40, preview_sha: str = "d" * 40) -> dict[str, object]:
    return {
        "workflow_name": name, "workflow_run_id": str(run_id), "check_run_id": run_id + 1000,
        "check_run_url": f"https://github.com/Arvin-liu/when-systems-catch-fire/actions/runs/{run_id}/job/{run_id + 1000}",
        "event": "pull_request",
        "pull_request_number": 301, "base_sha": base_sha, "head_sha": head_sha,
        "check_run_name": check_name, "check_run_sha": head_sha,
        "checkout_ref": "refs/remotes/pull/301/merge", "checkout_sha": preview_sha, "conclusion": "success",
    }


def _context() -> dict[str, object]:
    protection, protection_errors = r3.read_live_branch_protection(github_api=_github_api())
    assert not protection_errors and protection is not None
    workflows = r3.load_json(r3.PROTOCOL_PATH)["prepublication"]["required_workflow_names"]
    post_workflows = r3.load_json(r3.PROTOCOL_PATH)["postpublication"]["required_workflow_names"]
    owner = _owner_evidence()
    return {
        "task_id": "SYNTHETIC_FIXTURE_ONLY", "formal_ordinal": 1,
        "task_branch": "synthetic/fixture-only", "current_task_source_sha256": "3" * 64,
        "task_identity_model_sha256": "6" * 64, "execution_contract_sha256": "4" * 64,
        "pr_number": 301, "repository_owner_id": 49422864,
        "candidate_head_sha": "b" * 40, "candidate_tree_sha": "c" * 40,
        "base_main_sha": "a" * 40, "merge_preview_sha": "d" * 40,
        "merge_preview_tree_sha": "c" * 40, "required_check_names": [],
        "required_workflow_names": workflows, "required_postpublication_check_names": post_workflows,
        "test_inventory_sha256": "1" * 64, "test_count": 3, "environment_sha256": "2" * 64,
        "reviewed_changed_paths": ["ignition/tools/release.py", "ignition/tests/test_release.py"],
        "observed_changed_paths": ["ignition/tools/release.py", "ignition/tests/test_release.py"],
        "branch_protection_rules": protection, "branch_protection_rules_sha256": protection["rules_sha256"],
        "owner_authorization_commit_sha": owner["authorization_commit_sha"],
        "owner_authorization_file_sha256": owner["authorization_file_sha256"],
        "r3_protocol_blob_sha": r3.git_blob_sha(), "owner_authorization": owner,
        "base_branch": "main", "remote_main_sha": "e" * 40,
        "fresh_main_checkout_sha": "e" * 40, "actual_final_main_tree_sha": "c" * 40,
        "actual_final_main_parents": ["a" * 40, "b" * 40],
        "postpublication_checks": [_check(name, "e" * 40) for name in post_workflows],
        "projection_check": {"status": "PASS", "source_sha": "e" * 40, "unexpected_changed_paths": []},
    }


def _record() -> dict[str, object]:
    context = _context()
    candidate_sha = str(context["candidate_head_sha"])
    preview_sha = str(context["merge_preview_sha"])
    workflow_checks = [
        _workflow_check(name, 1001 + i, "preflight" if name == "repository-path-accounting-preflight" else "validate")
        for i, name in enumerate(context["required_workflow_names"])
    ]
    return {
        "task_identity": {key: context[key] for key in (
            "task_id", "formal_ordinal", "task_branch", "current_task_source_sha256",
            "task_identity_model_sha256", "execution_contract_sha256"
        )},
        "pull_request": {
            "number": 301, "url": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/301",
            "base_branch": "main", "head_branch": context["task_branch"], "state": "OPEN",
            "draft": False, "head_sha": candidate_sha, "author_id": 49422864,
        },
        "refs": {
            "base_main_sha": context["base_main_sha"], "candidate_tree_sha": context["candidate_tree_sha"],
            "merge_preview_sha": preview_sha, "merge_preview_tree_sha": context["merge_preview_tree_sha"],
            "merge_preview_parents": [context["base_main_sha"], candidate_sha],
        },
        "changed_paths": {
            "reviewed_paths": list(context["reviewed_changed_paths"]),
            "observed_paths": list(context["observed_changed_paths"]),
        },
        "required_check_names": context["required_check_names"],
        "pull_request_workflow_checks": workflow_checks, "pull_request_reviews": [],
        "canonical_full_suite_receipts": [
            _suite("run-1", str(context["task_id"]), str(context["task_branch"]), candidate_sha),
            _suite("run-2", str(context["task_id"]), str(context["task_branch"]), candidate_sha),
        ],
        "merge_method": "MERGE_COMMIT", "branch_protection": context["branch_protection_rules"],
        "owner_approval": context["owner_authorization"],
        "publication": {
            "status": "NOT_MERGED", "actual_final_main_sha": None, "actual_final_main_tree_sha": None,
            "actual_final_main_parents": None, "observed_remote_main_sha": None,
            "fresh_main_checkout_sha": None, "postpublication_checks": [], "projection_check": None,
        },
    }


def _postpublication_record() -> dict[str, object]:
    record = _record()
    context = _context()
    final_sha = "e" * 40
    record["pull_request"]["state"] = "MERGED"
    record["publication"].update({
        "status": "PUBLISHED_AND_VERIFIED", "actual_final_main_sha": final_sha,
        "actual_final_main_tree_sha": context["merge_preview_tree_sha"],
        "actual_final_main_parents": [context["base_main_sha"], context["candidate_head_sha"]],
        "observed_remote_main_sha": final_sha, "fresh_main_checkout_sha": final_sha,
        "postpublication_checks": [_check(name, final_sha) for name in context["required_postpublication_check_names"]],
        "projection_check": {"status": "PASS", "source_sha": final_sha, "unexpected_changed_paths": []},
    })
    return record


def _activation_receipt() -> dict[str, object]:
    context = _context()
    return {
        "status": "PUBLISHED_AND_VERIFIED", "migration_scope": "ONE_TIME_R3_BOOTSTRAP_ONLY",
        "r3_protocol_blob_sha": r3.git_blob_sha(), "prepublication_record_sha256": "7" * 64,
        "prepublication_validation_status": "VALIDATED", "pr_number": 301,
        "pr_url": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/301",
        "pr_base_branch": "main", "pr_head_ref": "synthetic/fixture-only", "task_branch": "synthetic/fixture-only",
        "pr_merged": True, "pr_merged_at": "2026-10-18T06:30:00Z", "pr_merge_commit_sha": "e" * 40,
        "base_main_sha": "a" * 40, "candidate_head_sha": "b" * 40,
        "candidate_tree_sha": "c" * 40, "merge_preview_sha": "d" * 40,
        "merge_preview_tree_sha": "c" * 40, "merge_preview_parents": ["a" * 40, "b" * 40],
        "actual_final_main_sha": "e" * 40, "actual_final_main_tree_sha": "c" * 40,
        "actual_final_main_parents": ["a" * 40, "b" * 40], "observed_remote_main_sha": "e" * 40,
        "fresh_main_clone_head_sha": "e" * 40, "merge_method": "MERGE_COMMIT",
        "branch_protection_verified": True, "branch_protection_rules_sha256": context["branch_protection_rules_sha256"],
        "owner_approved_before_merge": True, "owner_approval": context["owner_authorization"],
        "postpublication_checks": [_check(name, "e" * 40) for name in context["required_postpublication_check_names"]],
        "published_at": "2026-10-18T06:30:00Z",
    }


def _live_observations() -> dict[str, object]:
    context = _context()
    owner = context["owner_authorization"]
    witness_raw = json.dumps(_activation_receipt(), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "observation_source": "authenticated_github_and_fresh_clone_readback_and_1111_receipt_readback",
        "observed_at": "2026-10-18T06:35:00Z", "repository_owner_id": 49422864,
        "prepublication_record_sha256": "7" * 64, "prepublication_validation_status": "VALIDATED",
        "pr_number": 301, "pr_url": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/301",
        "pr_base_branch": "main", "pr_head_ref": "synthetic/fixture-only", "pr_merged": True,
        "pr_merged_at": "2026-10-18T06:30:00Z",
        "pr_merge_commit_sha": "e" * 40, "pr_head_sha": "b" * 40, "remote_main_sha": "e" * 40,
        "final_main_tree_sha": "c" * 40, "final_main_parents": ["a" * 40, "b" * 40],
        "fresh_main_clone_head_sha": "e" * 40, "branch_protection_status": "VERIFIED",
        "branch_protection_rules_sha256": context["branch_protection_rules_sha256"],
        "branch_protection_rules": context["branch_protection_rules"], "required_check_names": [],
        "postpublication_checks": [_check(name, "e" * 40) for name in context["required_postpublication_check_names"]],
        "authenticated_actor_id": 49422864, "authorization_commit_author_id": 49422864,
        "authorization_commit_committer_id": 49422864,
        "authorization_repository_owner_id": 49422864, "authorization_readback_commit_sha": "f" * 40,
        "authorization_file_sha256": owner["authorization_file_sha256"], "owner_authorization": owner,
        "witness_repository": "Arvin-liu/1111", "witness_branch": "main",
        "witness_path": r3.TRANSITION_WITNESS_PATH, "witness_readback_commit_sha": "6" * 40,
        "witness_commit_author_id": 49422864, "witness_commit_committer_id": 49422864,
        "witness_committed_at": "2026-10-18T06:40:00Z",
        "witness_file_sha256": hashlib.sha256(witness_raw).hexdigest(),
    }


class ReleaseTransactionProtocolR3Tests(unittest.TestCase):
    def _validate(self, record: dict[str, object], phase: str, expected: dict[str, object]) -> list[str]:
        return r3.validate_transaction_record(record, phase=phase, expected=expected, synthetic=True)

    def test_contract_preserves_r2_baseline_and_requires_explicit_duration_exception(self) -> None:
        self.assertEqual(r3.validate_contract(), [])
        self.assertEqual(r2.validate(), [])
        policy = r3.load_json(r3.PROTOCOL_PATH)
        self.assertEqual(policy["status"], "CANDIDATE_NOT_EFFECTIVE")
        duration = policy["canonical_suite_duration_policy"]
        self.assertEqual(
            duration["elapsed_duration_semantics"], "OBSERVED_NATURAL_ELAPSED_SECONDS_ONLY",
        )
        self.assertEqual(duration["r2_duration_exception"]["r2_minimum_natural_window_seconds"], 14400)
        self.assertEqual(duration["r2_duration_exception"]["r3_candidate_duration_threshold"], "NONE")
        self.assertTrue(duration["r2_duration_exception"]["r2_remains_effective_before_activation"])
        self.assertTrue(duration["r2_duration_exception"]["explicit_owner_approval_required"])
        self.assertNotIn("minimum_natural_window_seconds", policy["preserved_hard_gates"]["canonical_full_suite"])
        self.assertEqual(
            r2.load_json(r2.PROTOCOL_PATH)["pre_publication_hard_gates"]["canonical_full_suite"]["minimum_natural_window_seconds"],
            14400,
        )

    def test_short_real_natural_suite_process_passes(self) -> None:
        receipt = _record()["canonical_full_suite_receipts"][0]
        errors = r3.validate_suite_receipt(
            receipt, canonical_identity=_context(), expected=_context(), candidate_sha="b" * 40
        )
        self.assertEqual(errors, [])
        self.assertGreaterEqual(receipt["duration_seconds"], 0)
        self.assertEqual(receipt["process_exit_code"], 0)
        self.assertFalse(receipt["watchdog_used"])

    def test_short_timeout_killed_suite_process_fails(self) -> None:
        receipt = _suite("timeout", "SYNTHETIC_FIXTURE_ONLY", "synthetic/fixture-only", "b" * 40)
        with self.assertRaises(subprocess.TimeoutExpired):
            subprocess.run([sys.executable, "-c", "import time; time.sleep(5)"], check=False, capture_output=True, timeout=0.02)
        receipt.update({"process_exit_code": None, "termination_reason": "WATCHDOG_TIMEOUT", "watchdog_used": True, "conclusion": "timed_out"})
        self.assertTrue(r3.validate_suite_receipt(
            receipt, canonical_identity=_context(), expected=_context(), candidate_sha="b" * 40
        ))

    def test_short_natural_completion_is_admitted_by_observed_duration_policy(self) -> None:
        self.assertEqual(self._validate(_record(), "prepublication", _context()), [])

    def test_natural_durations_have_no_minimum_or_maximum_threshold(self) -> None:
        started_at = datetime(2026, 10, 18, 6, 0, tzinfo=timezone.utc)
        for seconds in (600, 14400, 72000):
            with self.subTest(seconds=seconds):
                receipt = _suite(f"natural-{seconds}", "SYNTHETIC_FIXTURE_ONLY", "synthetic/fixture-only", "b" * 40)
                finished_at = started_at + timedelta(seconds=seconds)
                receipt.update({
                    "duration_seconds": seconds,
                    "started_at": started_at.isoformat().replace("+00:00", "Z"),
                    "finished_at": finished_at.isoformat().replace("+00:00", "Z"),
                })
                self.assertEqual(
                    r3.validate_suite_receipt(
                        receipt, canonical_identity=_context(), expected=_context(), candidate_sha="b" * 40
                    ),
                    [],
                )

    def test_natural_suite_duration_must_match_recorded_start_and_finish(self) -> None:
        receipt = _suite("natural-duration-mismatch", "SYNTHETIC_FIXTURE_ONLY", "synthetic/fixture-only", "b" * 40)
        started_at = datetime(2026, 10, 18, 6, 0, tzinfo=timezone.utc)
        receipt.update({
            "duration_seconds": 14401,
            "started_at": started_at.isoformat().replace("+00:00", "Z"),
            "finished_at": (started_at + timedelta(seconds=14500)).isoformat().replace("+00:00", "Z"),
        })
        errors = r3.validate_suite_receipt(
            receipt, canonical_identity=_context(), expected=_context(), candidate_sha="b" * 40
        )
        self.assertIn("canonical full-suite elapsed time does not match its recorded start and finish", errors)

    def test_owner_transition_authorization_is_separate_from_review_and_live_verified(self) -> None:
        receipt, observations, api = _activation_receipt(), _live_observations(), _github_api()
        live_rules, errors = r3.read_live_branch_protection(github_api=api)
        self.assertEqual(errors, [])
        self.assertFalse(live_rules["required_review"])
        self.assertFalse(live_rules["required_status_checks"])
        self.assertEqual(live_rules["required_check_names"], [])
        active, errors = r3.resolve_effective_protocol(
            receipt, observations=observations, repository_owner_id=49422864, github_api=api
        )
        self.assertEqual((active, errors), ("R3", []))
        self.assertNotIn("owner_review_state", observations)

    def test_forged_owner_wrong_pr_head_base_or_protocol_and_stale_commit_fail_closed(self) -> None:
        statements = [
            _owner_statement(actor_id=7), _owner_statement(pr_number=302),
            _owner_statement(head_sha="9" * 40), _owner_statement(base_sha="8" * 40),
            _owner_statement(protocol_blob_sha="9" * 40),
        ]
        for statement in statements:
            receipt, observations = _activation_receipt(), _live_observations()
            approval = _owner_evidence(statement)
            receipt["owner_approval"] = approval
            observations["owner_authorization"] = approval
            observations["authorization_file_sha256"] = approval["authorization_file_sha256"]
            active, errors = r3.resolve_effective_protocol(
                receipt, observations=observations, repository_owner_id=49422864,
                github_api=_github_api(statement, actor_id=statement["owner_actor_id"]),
            )
            self.assertEqual(active, "R2")
            self.assertTrue(errors)

        receipt, observations, api = _activation_receipt(), _live_observations(), _github_api()
        def stale_read(endpoint: str):
            if endpoint.endswith("/commits/" + "f" * 40):
                value = api(endpoint)
                value["sha"] = "9" * 40
                return value
            return api(endpoint)
        active, errors = r3.resolve_effective_protocol(
            receipt, observations=observations, repository_owner_id=49422864, github_api=stale_read
        )
        self.assertEqual(active, "R2")
        self.assertTrue(any("fixed 1111 authorization commit" in error for error in errors))

        receipt, observations = _activation_receipt(), _live_observations()
        active, errors = r3.resolve_effective_protocol(
            receipt, observations=observations, repository_owner_id=49422864, github_api=_github_api(actor_id=7)
        )
        self.assertEqual(active, "R2")
        self.assertTrue(errors)

    def test_owner_transition_requires_explicit_r2_duration_exception(self) -> None:
        statement = _owner_statement()
        del statement["r2_duration_policy_exception"]
        receipt, observations = _activation_receipt(), _live_observations()
        approval = _owner_evidence(statement)
        receipt["owner_approval"] = approval
        observations["owner_authorization"] = approval
        observations["authorization_file_sha256"] = approval["authorization_file_sha256"]
        active, errors = r3.resolve_effective_protocol(
            receipt,
            observations=observations,
            repository_owner_id=49422864,
            github_api=_github_api(statement),
        )
        self.assertEqual(active, "R2")
        self.assertTrue(any("r2_duration_policy_exception" in error for error in errors))

    def test_branch_protection_read_failure_or_stale_rules_fails_closed(self) -> None:
        receipt, observations, api = _activation_receipt(), _live_observations(), _github_api()
        def unavailable(endpoint: str):
            if endpoint.endswith("/branches/main/protection"):
                raise PermissionError("403")
            return api(endpoint)
        active, errors = r3.resolve_effective_protocol(
            receipt, observations=observations, repository_owner_id=49422864, github_api=unavailable
        )
        self.assertEqual(active, "R2")
        self.assertTrue(any("branch-protection readback failed closed" in error for error in errors))

        def changed_rules(endpoint: str):
            value = api(endpoint)
            if endpoint.endswith("/branches/main/protection"):
                value["enforce_admins"] = {"enabled": True}
            return value
        active, errors = r3.resolve_effective_protocol(
            receipt, observations=observations, repository_owner_id=49422864, github_api=changed_rules
        )
        self.assertEqual(active, "R2")
        self.assertTrue(errors)

    def test_ruleset_review_and_required_status_rules_are_read_from_live_endpoint(self) -> None:
        api = _github_api()
        rules = [
            {"type": "pull_request", "parameters": {"required_approving_review_count": 1}},
            {"type": "required_status_checks", "parameters": {
                "required_status_checks": [{"context": "ruleset/ci"}],
            }},
        ]
        def with_rulesets(endpoint: str):
            if endpoint.endswith("/rules/branches/main"):
                return rules
            return api(endpoint)
        protection, errors = r3.read_live_branch_protection(github_api=with_rulesets)
        self.assertEqual(errors, [])
        self.assertTrue(protection["required_review"])
        self.assertTrue(protection["required_status_checks"])
        self.assertEqual(protection["required_check_names"], ["ruleset/ci"])
        self.assertEqual(protection["ruleset_count"], 2)

    def test_caller_receipt_must_match_the_latest_1111_main_witness_file(self) -> None:
        receipt, observations, api = _activation_receipt(), _live_observations(), _github_api()
        endpoint = f"repos/Arvin-liu/1111/contents/{r3.TRANSITION_WITNESS_PATH}?ref={'6' * 40}"
        def altered_witness(request: str):
            value = api(request)
            if request == endpoint:
                content = json.loads(base64.b64decode(value["content"]).decode("utf-8"))
                content["actual_final_main_sha"] = "9" * 40
                value["content"] = base64.b64encode(json.dumps(content).encode("utf-8")).decode("ascii")
            return value
        active, errors = r3.resolve_effective_protocol(
            receipt, observations=observations, repository_owner_id=49422864, github_api=altered_witness
        )
        self.assertEqual(active, "R2")
        self.assertTrue(any("differs from the exact 1111 main-branch witness file" in error for error in errors))

    def test_unmerged_candidate_and_missing_receipt_keep_r2_current(self) -> None:
        policy = r3.load_json(r3.PROTOCOL_PATH)
        policy["status"] = "CURRENT"
        self.assertTrue(r3.validate_contract(policy))
        active, _ = r3.resolve_effective_protocol(None, observations=_live_observations(), repository_owner_id=49422864)
        self.assertEqual(active, "R2")
        active, _ = r3.resolve_effective_protocol(
            _activation_receipt(), observations=_live_observations(), repository_owner_id=49422864, github_api=_github_api()
        )
        self.assertEqual(active, "R3")

    def test_actual_pull_request_run_binds_head_and_merge_checkout_separately(self) -> None:
        self.assertEqual(self._validate(_record(), "prepublication", _context()), [])
        check = _record()["pull_request_workflow_checks"][0]
        self.assertEqual(check["check_run_sha"], "b" * 40)
        self.assertEqual(check["checkout_sha"], "d" * 40)
        self.assertEqual(check["checkout_ref"], "refs/remotes/pull/301/merge")

    def test_observed_github_run_metadata_is_one_pr_run_not_two_sha_check_sets(self) -> None:
        # Read-only metadata captured from the existing #260 Actions run and job log.
        check = {
            "workflow_name": "release-transaction-protocol-validation",
            "workflow_run_id": "39103682067", "event": "pull_request", "pull_request_number": 260,
            "base_sha": "f17477dd9761c898563dbf5670c63914a5ecedfa",
            "head_sha": "031ded9ac726cacad199f3a69f1ef2462cf65d70",
            "check_run_name": "validate", "check_run_sha": "031ded9ac726cacad199f3a69f1ef2462cf65d70",
            "checkout_ref": "refs/remotes/pull/260/merge",
            "checkout_sha": "b0047308664efbc1881f8b717a4525a4d37d5b5c",
            "conclusion": "success", "check_run_id": 117604944266,
            "check_run_url": "https://github.com/Arvin-liu/when-systems-catch-fire/actions/runs/39103682067/job/117604944266",
        }
        self.assertEqual(r3._pull_request_workflow_errors(
            [check], pr_number=260, head_sha="031ded9ac726cacad199f3a69f1ef2462cf65d70",
            base_sha="f17477dd9761c898563dbf5670c63914a5ecedfa",
            preview_sha="b0047308664efbc1881f8b717a4525a4d37d5b5c",
            required_workflows=["release-transaction-protocol-validation"], required_check_names=[],
        ), [])

    def test_candidate_preview_base_and_run_evidence_drift_fail(self) -> None:
        for section, key in (("refs", "base_main_sha"), ("pull_request", "head_sha"),
                             ("refs", "merge_preview_sha"), ("refs", "merge_preview_tree_sha")):
            record = _record()
            record[section][key] = "f" * 40
            self.assertTrue(self._validate(record, "prepublication", _context()), key)
        for field, value in (("check_run_sha", "d" * 40), ("base_sha", "f" * 40),
                             ("checkout_sha", "f" * 40), ("checkout_ref", "refs/heads/main"),
                             ("check_run_url", "https://github.com/Arvin-liu/other/actions/runs/1/job/2"),
                             ("conclusion", "failure")):
            record = _record()
            record["pull_request_workflow_checks"][0][field] = value
            self.assertTrue(self._validate(record, "prepublication", _context()), field)

    def test_verified_review_rule_requires_independent_exact_head_reviewer(self) -> None:
        api = _github_api()
        def with_review_rule(endpoint: str):
            value = api(endpoint)
            if endpoint.endswith("/branches/main/protection"):
                value["required_pull_request_reviews"] = {"required_approving_review_count": 1}
            return value
        live_protection, errors = r3.read_live_branch_protection(github_api=with_review_rule)
        self.assertEqual(errors, [])
        record, expected = _record(), _context()
        record["branch_protection"] = live_protection
        expected["branch_protection_rules"] = live_protection
        expected["branch_protection_rules_sha256"] = live_protection["rules_sha256"]
        record["pull_request_reviews"] = [{
            "actor_id": 49422864, "state": "APPROVED", "commit_sha": "b" * 40,
            "submitted_at": "2026-10-18T06:00:00Z",
            "review_url": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/301#pullrequestreview-1",
        }]
        self.assertTrue(self._validate(record, "prepublication", expected))
        record["pull_request_reviews"][0]["actor_id"] = 7
        self.assertEqual(self._validate(record, "prepublication", expected), [])

    def test_parent_order_scope_historical_and_missing_suite_evidence_fail_closed(self) -> None:
        record = _record()
        record["refs"]["merge_preview_parents"] = ["b" * 40, "a" * 40]
        self.assertTrue(self._validate(record, "prepublication", _context()))
        record = _record()
        record["changed_paths"]["observed_paths"].append("ignition/data/derived-generated.json")
        self.assertTrue(self._validate(record, "prepublication", _context()))
        record = _record()
        record["canonical_full_suite_receipts"][0]["task_id"] = "IGNITION-20260822-135"
        self.assertTrue(self._validate(record, "prepublication", _context()))
        record = _record()
        record["canonical_full_suite_receipts"].pop()
        self.assertTrue(self._validate(record, "prepublication", _context()))

    def test_postpublication_final_main_sha_tree_parents_and_checks_are_exact(self) -> None:
        record = _postpublication_record()
        self.assertNotEqual(record["publication"]["actual_final_main_sha"], record["refs"]["merge_preview_sha"])
        self.assertEqual(self._validate(record, "postpublication", _context()), [])
        for field, value in (("actual_final_main_tree_sha", "f" * 40),
                             ("actual_final_main_parents", ["b" * 40, "a" * 40]),
                             ("observed_remote_main_sha", "f" * 40)):
            changed = _postpublication_record()
            changed["publication"][field] = value
            self.assertTrue(self._validate(changed, "postpublication", _context()), field)
        changed = _postpublication_record()
        changed["publication"]["postpublication_checks"][0]["sha"] = "f" * 40
        self.assertTrue(self._validate(changed, "postpublication", _context()))

    def test_activation_reads_actual_final_main_commit_tree_and_parent_order(self) -> None:
        receipt, observations, api = _activation_receipt(), _live_observations(), _github_api()
        def different_commit(endpoint: str):
            value = api(endpoint)
            if endpoint.endswith("/commits/" + "e" * 40) and endpoint.startswith("repos/Arvin-liu/when-systems-catch-fire/"):
                value["parents"] = list(reversed(value["parents"]))
            return value
        active, errors = r3.resolve_effective_protocol(
            receipt, observations=observations, repository_owner_id=49422864, github_api=different_commit
        )
        self.assertEqual(active, "R2")
        self.assertTrue(any("live GitHub final-main commit parents differ" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
