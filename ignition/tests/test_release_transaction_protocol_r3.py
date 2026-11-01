from __future__ import annotations

import base64
from contextlib import redirect_stderr
import hashlib
from io import StringIO
import json
import re
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote

from tools import validate_release_transaction_protocol as r2
from tools import validate_release_transaction_protocol_r3 as r3


def _check(name: str, sha: str) -> dict[str, str]:
    run_id = {
        "release-transaction-protocol-validation": 2001,
        "foundation-validation": 2002,
        "repository-path-accounting-preflight": 2003,
    }[name]
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


def _registration_statement() -> dict[str, object]:
    inventory = {
        "merged_task_ids": ["SYNTHETIC_PRIOR"], "open_task_pr_numbers": [], "open_task_ids": [],
        "formal_task_identities": [{
            "task_id": "SYNTHETIC_PRIOR", "formal_ordinal": 149, "work_branch": "synthetic/prior",
            "receipt_branch": "synthetic/prior-receipt", "lifecycle_state": "MERGED", "evidence_ref": "fixture:prior",
        }],
        "1111_task_receipt_refs": ["relay/receipts/SYNTHETIC_PRIOR"],
    }
    inventory["inventory_sha256"] = hashlib.sha256(
        json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "registration_status": "OWNER_REGISTERED", "task_id": "SYNTHETIC_FIXTURE_ONLY",
        "formal_ordinal": 1, "work_branch": "synthetic/fixture-only", "receipt_branch": "synthetic/fixture-only-receipt",
        "formal_base_main_sha": "a" * 40, "r3_protocol_candidate_blob_sha": r3.git_blob_sha(),
        "registration_nonce": "n" * 32, "prior_task_id": "SYNTHETIC_PRIOR",
        "conflict_inventory": inventory, "registered_at": "2026-10-18T05:00:00Z",
    }


def _owner_statement(
    *, pr_number: int = 301, head_sha: str = "b" * 40, base_sha: str = "a" * 40,
    actor_id: int = 49422864, protocol_blob_sha: str | None = None,
) -> dict[str, object]:
    return {
        "approved": True, "owner_actor_id": actor_id, "approved_pr_number": pr_number,
        "approved_head_sha": head_sha, "approved_base_sha": base_sha,
        "r3_protocol_blob_sha": protocol_blob_sha or r3.git_blob_sha(),
        "task_id": "SYNTHETIC_FIXTURE_ONLY", "formal_ordinal": 1,
        "successor_registration_commit_sha": "5" * 40,
        "successor_registration_file_sha256": hashlib.sha256(
            json.dumps(_registration_statement(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "scope": "ONE_TIME_R3_BOOTSTRAP_ONLY",
        "r2_duration_policy_exception": "R2_MINIMUM_NATURAL_WINDOW_14400S_NOT_CARRIED_FORWARD_IN_R3",
        "r2_full_suite_count_policy_exception": "R2_FIXED_TWO_RUNS_REPLACED_BY_EVIDENCE_SUFFICIENCY_AND_INDEPENDENT_REVALIDATION_WITHOUT_FIXED_COUNT",
        "r2_publication_method_exception": "R2_FAST_FORWARD_SHA_EQUALITY_REPLACED_BY_PROTECTED_PR_MERGE_COMMIT_WITH_FINAL_MAIN_TREE_PARENT_REMOTE_AND_FRESH_CLONE_WITNESS",
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
        "authorization_signature_verified": True, "authorization_signature_reason": "valid",
    }


class _PrivateGitFixture:
    """Small GitHub Git Data API model with first-parent and web-merge trees."""

    def __init__(self, registration: bytes, owner_authorization: bytes, actor_id: int):
        self.actor_id = actor_id
        self.main_sha = "6" * 40
        self.calls: list[str] = []
        self.commits: dict[str, dict[str, object]] = {}
        self.snapshots: dict[str, dict[str, bytes]] = {}
        self.trees: dict[str, dict[str, object]] = {}
        self.materialize_witness = True
        self.registration_sha = "5" * 40
        self.staging_sha = "538ebc673b13fd8d376a704ab3bb2b8fc325d86c"
        self.base_sha = "d451305c4c606460665a30ffb523db59edd58e5d"
        self.authorization_sha = "f" * 40
        self.witness_sha = "6" * 40
        self.registration_raw = registration
        self.owner_authorization_raw = owner_authorization
        self.add_commit(self.base_sha, [], {}, date="2026-10-18T04:00:00Z", signed=False)
        self.add_commit(
            self.staging_sha, [self.base_sha], {r3.SUCCESSOR_REGISTRATION_PATH: registration},
            date="2026-10-18T05:50:00Z", signed=False,
        )
        self.add_commit(
            self.registration_sha, [self.base_sha, self.staging_sha],
            {r3.SUCCESSOR_REGISTRATION_PATH: registration},
            date="2026-10-18T05:55:00Z", committer_id=r3.GITHUB_WEB_FLOW_ACCOUNT_ID,
            committer_login="web-flow", signed=True,
        )
        self.add_commit(
            self.authorization_sha, [self.registration_sha], {
                r3.SUCCESSOR_REGISTRATION_PATH: registration,
                r3.OWNER_AUTHORIZATION_PATH: owner_authorization,
            }, date="2026-10-18T06:00:00Z", signed=True,
        )

    def _tree(self, files: dict[str, bytes]) -> str:
        root: dict[str, object] = {}
        for path, raw in files.items():
            parts = path.split("/")
            node = root
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = raw

        def build(node: dict[str, object]) -> str:
            entries = []
            api_entries = []
            for name, value in sorted(node.items()):
                if isinstance(value, dict):
                    sha = build(value)
                    item = {"path": name, "mode": "040000", "type": "tree", "sha": sha}
                else:
                    sha = r3._git_blob_sha(value)
                    item = {"path": name, "mode": "100644", "type": "blob", "sha": sha}
                api_entries.append(item)
                entries.append((name, item["mode"], item["type"], sha))
            raw_tree = json.dumps(entries, separators=(",", ":")).encode("utf-8")
            sha = hashlib.sha1(b"tree " + str(len(raw_tree)).encode("ascii") + b"\0" + raw_tree).hexdigest()
            self.trees[sha] = {"truncated": False, "tree": api_entries}
            return sha

        return build(root)

    def add_commit(
        self,
        sha: str,
        parents: list[str],
        files: dict[str, bytes],
        *,
        date: str,
        signed: bool,
        committer_id: int = 49422864,
        committer_login: str = "Arvin-liu",
    ) -> None:
        tree_sha = self._tree(files)
        self.snapshots[sha] = dict(files)
        verification = {
            "verified": signed,
            "reason": "valid" if signed else "unsigned",
            "signature": "fixture-signature" if signed else None,
            "payload": "fixture-payload" if signed else None,
        }
        self.commits[sha] = {
            "sha": sha,
            "author": {"id": self.actor_id, "login": "Arvin-liu"},
            "committer": {"id": committer_id, "login": committer_login},
            "commit": {"tree": {"sha": tree_sha}, "committer": {"date": date}, "verification": verification},
            "parents": [{"sha": parent} for parent in parents],
        }

    def _materialize_witness(self) -> None:
        if self.witness_sha in self.commits:
            return
        receipt = _activation_receipt()
        witness = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("utf-8")
        files = dict(self.snapshots[self.authorization_sha])
        files[r3.TRANSITION_WITNESS_PATH] = witness
        staging_sha = "9" * 40
        self.add_commit(
            staging_sha, [self.authorization_sha], files,
            date="2026-10-18T06:35:00Z", signed=False,
        )
        self.add_commit(
            self.witness_sha, [self.authorization_sha, staging_sha], files,
            date="2026-10-18T06:40:00Z", committer_id=r3.GITHUB_WEB_FLOW_ACCOUNT_ID,
            committer_login="web-flow", signed=True,
        )

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        pending = [descendant]
        visited: set[str] = set()
        while pending:
            current = pending.pop()
            if current == ancestor:
                return True
            if current in visited:
                continue
            visited.add(current)
            pending.extend(parent["sha"] for parent in self.commits.get(current, {}).get("parents", []))
        return False

    def __call__(self, endpoint: str):
        self.calls.append(endpoint)
        prefix = "repos/Arvin-liu/1111/"
        if not endpoint.startswith(prefix):
            raise KeyError(endpoint)
        tail = endpoint[len(prefix):]
        if tail == "branches/main":
            return {"commit": {"sha": self.main_sha}}
        if tail.startswith("commits/"):
            sha = tail[len("commits/"):]
            if sha == self.witness_sha:
                self._materialize_witness()
            if sha in self.commits:
                return self.commits[sha]
        if tail.startswith("git/trees/"):
            tree_sha = tail[len("git/trees/"):]
            if tree_sha in self.trees:
                return self.trees[tree_sha]
        if tail.startswith("contents/") and "?ref=" in tail:
            path_ref, ref = tail[len("contents/"):].split("?ref=", 1)
            path = path_ref
            if ref == self.witness_sha:
                self._materialize_witness()
            if ref in self.snapshots and path in self.snapshots[ref]:
                raw = self.snapshots[ref][path]
                return {
                    "path": path, "type": "file", "encoding": "base64",
                    "sha": r3._git_blob_sha(raw), "content": base64.b64encode(raw).decode("ascii"),
                }
        if tail.startswith("compare/"):
            left, right = tail[len("compare/"):].split("...", 1)
            left = self.main_sha if left == "main" else left
            right = self.main_sha if right == "main" else right
            if right == self.witness_sha:
                self._materialize_witness()
            if left == right:
                return {"status": "identical"}
            if self.is_ancestor(left, right):
                return {"status": "ahead"}
            if self.is_ancestor(right, left):
                return {"status": "behind"}
            return {"status": "diverged"}
        raise KeyError(endpoint)


def _github_api(
    statement: dict[str, object] | None = None, *, actor_id: int = 49422864,
    commit_sha: str = "f" * 40, registration_statement: dict[str, object] | None = None,
):
    statement = statement or _owner_statement(actor_id=actor_id)
    content = json.dumps(statement, sort_keys=True, separators=(",", ":")).encode("utf-8")
    registration = registration_statement or _registration_statement()
    registration_content = json.dumps(registration, sort_keys=True, separators=(",", ":")).encode("utf-8")
    registration_sha = "5" * 40
    private = _PrivateGitFixture(registration_content, content, actor_id)
    values = {
        "user": {"login": "Arvin-liu", "id": actor_id},
        "repos/Arvin-liu/when-systems-catch-fire": {
            "owner": {"id": 49422864}, "allow_merge_commit": True,
            "allow_squash_merge": False, "allow_rebase_merge": False,
        },
        "repos/Arvin-liu/1111": {"owner": {"id": 49422864}, "private": True, "default_branch": "main"},
        f"repos/Arvin-liu/when-systems-catch-fire/contents/{r3.relative(r3.CURRENT_TASK_PATH)}?ref={'a' * 40}": {
            "path": r3.relative(r3.CURRENT_TASK_PATH), "type": "file", "encoding": "base64",
            "content": base64.b64encode(json.dumps({"current_task": {"task_id": "SYNTHETIC_PRIOR"}}).encode("utf-8")).decode("ascii"),
        },
        f"repos/Arvin-liu/1111/commits?path={quote(r3.SUCCESSOR_REGISTRATION_PATH, safe='')}&sha=main&per_page=1": [{"sha": private.staging_sha}],
        "repos/Arvin-liu/when-systems-catch-fire/branches/main": {"protected": True, "commit": {"sha": "e" * 40}},
        f"repos/Arvin-liu/when-systems-catch-fire/commits/{'e' * 40}": {
            "sha": "e" * 40, "commit": {"tree": {"sha": "c" * 40}},
            "parents": [{"sha": "a" * 40}, {"sha": "b" * 40}],
        },
        f"repos/Arvin-liu/when-systems-catch-fire/contents/{r3.relative(r3.PROTOCOL_PATH)}?ref={'e' * 40}": {
            "path": r3.relative(r3.PROTOCOL_PATH), "type": "file", "encoding": "base64",
            "sha": r3.git_blob_sha(),
            "content": base64.b64encode(r3.PROTOCOL_PATH.read_bytes()).decode("ascii"),
        },
        "repos/Arvin-liu/when-systems-catch-fire/pulls/301": {
            "number": 301, "state": "closed", "merged": True,
            "base": {"ref": "main"}, "head": {"ref": "synthetic/fixture-only", "sha": "b" * 40},
            "merge_commit_sha": "e" * 40,
            "merged_at": "2026-10-18T06:30:00Z",
            "html_url": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/301",
        },
        "repos/Arvin-liu/when-systems-catch-fire/branches/main/protection": {
            "required_status_checks": {"strict": True, "checks": [
                {"context": item["context"], "app_id": item["app_id"]}
                for item in r3.load_json(r3.PROTOCOL_PATH)["prepublication"]["required_status_check_contexts"]
            ]},
            "required_pull_request_reviews": {"required_approving_review_count": 0,
                "bypass_pull_request_allowances": {"users": [], "teams": [], "apps": []}},
            "enforce_admins": {"enabled": True}, "allow_force_pushes": {"enabled": False},
            "allow_deletions": {"enabled": False}, "required_linear_history": {"enabled": False},
            "restrictions": None,
        },
        "repos/Arvin-liu/when-systems-catch-fire/rules/branches/main": [],
        "repos/Arvin-liu/when-systems-catch-fire/rulesets?includes_parents=true&per_page=100": [],
    }
    def read(endpoint: str):
        if endpoint.startswith("repos/Arvin-liu/1111/") and endpoint not in values:
            return private(endpoint)
        if endpoint not in values:
            prefix = "repos/Arvin-liu/when-systems-catch-fire/actions/runs?head_sha="
            if endpoint.startswith(prefix) and endpoint.endswith("&per_page=100"):
                final_sha = endpoint[len(prefix):-len("&per_page=100")]
                return {
                    "workflow_runs": [
                        {"name": "release-transaction-protocol-validation", "id": 2001, "event": "push", "head_branch": "main", "head_sha": final_sha, "status": "completed", "conclusion": "success", "updated_at": "2026-10-18T06:00:00Z", "html_url": "https://github.com/Arvin-liu/when-systems-catch-fire/actions/runs/2001", "run_number": 1, "run_attempt": 1},
                        {"name": "foundation-validation", "id": 2002, "event": "push", "head_branch": "main", "head_sha": final_sha, "status": "completed", "conclusion": "success", "updated_at": "2026-10-18T06:00:00Z", "html_url": "https://github.com/Arvin-liu/when-systems-catch-fire/actions/runs/2002", "run_number": 1, "run_attempt": 1},
                        {"name": "repository-path-accounting-preflight", "id": 2003, "event": "push", "head_branch": "main", "head_sha": final_sha, "status": "completed", "conclusion": "success", "updated_at": "2026-10-18T06:00:00Z", "html_url": "https://github.com/Arvin-liu/when-systems-catch-fire/actions/runs/2003", "run_number": 1, "run_attempt": 1},
                    ]
                }
            raise KeyError(endpoint)
        return values[endpoint]
    read.control = private
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
    api = _github_api()
    registration = _registration_statement()
    return {
        "task_id": "SYNTHETIC_FIXTURE_ONLY", "formal_ordinal": 1,
        "task_branch": "synthetic/fixture-only", "current_task_source_sha256": "3" * 64,
        "task_identity_model_sha256": "6" * 64, "execution_contract_sha256": "4" * 64,
        "successor_registration_commit_sha": "5" * 40,
        "successor_registration_file_sha256": owner["successor_registration_file_sha256"],
        "successor_registration_nonce": registration["registration_nonce"],
        "successor_registration_parent_shas": [api.control.base_sha, api.control.staging_sha],
        "pr_number": 301, "repository_owner_id": 49422864,
        "candidate_head_sha": "b" * 40, "candidate_tree_sha": "c" * 40,
        "base_main_sha": "a" * 40, "merge_preview_sha": "d" * 40,
        "merge_preview_tree_sha": "c" * 40,
        "required_check_names": list(protection["required_check_names"]),
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
        _workflow_check(name, 1001 + i, name)
        for i, name in enumerate(context["required_workflow_names"])
    ]
    return {
        "task_identity": {key: context[key] for key in (
            "task_id", "formal_ordinal", "task_branch", "current_task_source_sha256",
            "task_identity_model_sha256", "execution_contract_sha256",
            "successor_registration_commit_sha", "successor_registration_file_sha256",
            "successor_registration_nonce", "successor_registration_parent_shas"
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
        ],
        "canonical_full_suite_evidence_revalidation": {
            "workflow_name": "release-transaction-protocol-validation",
            "workflow_run_id": workflow_checks[0]["workflow_run_id"],
            "check_run_id": workflow_checks[0]["check_run_id"],
            "candidate_head_sha": candidate_sha,
            "inventory_sha256": context["test_inventory_sha256"],
            "test_count": context["test_count"],
            "environment_sha256": context["environment_sha256"],
            "receipt_run_ids": ["run-1"],
            "conclusion": "success",
            "check_run_url": workflow_checks[0]["check_run_url"],
        },
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
        "required_status_check_contexts": r3.load_json(r3.PROTOCOL_PATH)["prepublication"]["required_status_check_contexts"],
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
        "branch_protection_rules": context["branch_protection_rules"], "required_check_names": context["required_check_names"],
        "postpublication_checks": [_check(name, "e" * 40) for name in context["required_postpublication_check_names"]],
        "authenticated_actor_id": 49422864, "authorization_commit_author_id": 49422864,
        "authorization_commit_committer_id": 49422864,
        "authorization_repository_owner_id": 49422864, "authorization_readback_commit_sha": "f" * 40,
        "authorization_file_sha256": owner["authorization_file_sha256"], "owner_authorization": owner,
        "authorization_signature_verified": True, "authorization_signature_reason": "valid",
        "witness_repository": "Arvin-liu/1111", "witness_branch": "main",
        "witness_path": r3.TRANSITION_WITNESS_PATH, "witness_readback_commit_sha": "6" * 40,
        "witness_commit_author_id": 49422864, "witness_commit_committer_id": 19864447,
        "witness_signature_verified": True, "witness_signature_reason": "valid",
        "witness_committed_at": "2026-10-18T06:40:00Z",
        "witness_file_sha256": hashlib.sha256(witness_raw).hexdigest(),
    }


def _recovery_fixture():
    def canonical_bytes(value: object) -> bytes:
        return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def file_object(path: str, raw: bytes) -> dict[str, object]:
        git_header = f"blob {len(raw)}\0".encode("ascii")
        return {
            "path": path, "type": "file", "encoding": "base64",
            "content": base64.b64encode(raw).decode("ascii"),
            "sha": hashlib.sha1(git_header + raw).hexdigest(),
        }

    final_sha, recovery_head, preview_sha = "5" * 40, "7" * 40, "8" * 40
    base_sha, final_tree = "e" * 40, "9" * 40
    auth_sha, witness_sha = "1" * 40, "2" * 40
    contexts = r3.load_json(r3.PROTOCOL_PATH)["prepublication"]["required_status_check_contexts"]
    main_api = _github_api()
    protection, protection_errors = r3.read_live_branch_protection(github_api=main_api)
    assert protection and not protection_errors

    state = {
        "schema_version": "release-transaction-recovery-state-r1",
        "contract_id": "RELEASE_TRANSACTION_RECOVERY_STATE",
        "status": "RESTORE_R2_PENDING",
        "source_r3_protocol_blob_sha": r3.git_blob_sha(),
        "target_r2_protocol_blob_sha": r3.git_blob_sha(r3.R2_PROTOCOL_PATH),
        "scope": "RESTORE_R2_ONLY", "requested_at": "2026-10-19T04:00:00Z",
        "reason": "synthetic fixture: validate R3 to R2 recovery binding",
    }
    state_raw = canonical_bytes(state)
    state_digest = hashlib.sha256(state_raw).hexdigest()
    statement = {
        "action": "RESTORE_R2_ONLY", "scope": "ONE_TIME_R3_TO_R2_RESTORATION_ONLY",
        "owner_actor_id": 49422864, "source_r3_protocol_blob_sha": state["source_r3_protocol_blob_sha"],
        "target_r2_protocol_blob_sha": state["target_r2_protocol_blob_sha"],
        "recovery_state_file_sha256": state_digest, "pr_number": 302,
        "task_id": "SYNTHETIC_FIXTURE_ONLY", "formal_ordinal": 1,
        "work_branch": "synthetic/r2-restore", "candidate_head_sha": recovery_head,
        "base_main_sha": base_sha, "merge_preview_sha": preview_sha,
        "merge_preview_tree_sha": final_tree, "prepublication_record_sha256": "a" * 64,
        "approved_at": "2026-10-19T05:00:00Z", "reason": "synthetic positive fixture",
    }
    auth_raw = canonical_bytes(statement)
    auth_file_sha = hashlib.sha256(auth_raw).hexdigest()
    receipt = {
        "status": "R2_RESTORED_AND_VERIFIED", "scope": "ONE_TIME_R3_TO_R2_RESTORATION_ONLY",
        "source_r3_protocol_blob_sha": state["source_r3_protocol_blob_sha"],
        "target_r2_protocol_blob_sha": state["target_r2_protocol_blob_sha"],
        "recovery_state_file_sha256": state_digest, "owner_authorization_commit_sha": auth_sha,
        "owner_authorization_file_sha256": auth_file_sha, "prepublication_record_sha256": "a" * 64,
        "pr_number": 302, "task_id": "SYNTHETIC_FIXTURE_ONLY", "formal_ordinal": 1,
        "work_branch": "synthetic/r2-restore", "candidate_head_sha": recovery_head,
        "base_main_sha": base_sha, "merge_preview_sha": preview_sha,
        "merge_preview_tree_sha": final_tree, "merge_preview_parents": [base_sha, recovery_head],
        "final_main_sha": final_sha, "final_main_tree_sha": final_tree,
        "final_main_parents": [base_sha, recovery_head], "remote_main_sha": final_sha,
        "fresh_clone_sha": final_sha,
        "postpublication_checks": [_check(name, final_sha) for name in r3.load_json(r3.PROTOCOL_PATH)["postpublication"]["required_workflow_names"]],
        "published_at": "2026-10-19T07:00:00Z", "branch_protection_rules_sha256": protection["rules_sha256"],
        "required_status_check_contexts": contexts,
    }
    witness_raw = canonical_bytes(receipt)
    witness_file_sha = hashlib.sha256(witness_raw).hexdigest()
    control = main_api.control
    control._materialize_witness()
    parent_sha = control.main_sha
    auth_files = dict(control.snapshots[parent_sha])
    auth_files[r3.R2_RESTORE_AUTHORIZATION_PATH] = auth_raw
    control.add_commit(
        auth_sha, [parent_sha], auth_files, date="2026-10-19T05:30:00Z", signed=True,
    )
    witness_files = dict(auth_files)
    witness_files[r3.R2_RESTORATION_WITNESS_PATH] = witness_raw
    control.add_commit(
        witness_sha, [auth_sha], witness_files, date="2026-10-19T07:10:00Z", signed=True,
    )
    control.main_sha = witness_sha
    recovery_observations = {
        "repository_owner_id": 49422864, "current_main_sha": final_sha,
        "recovery_pr_merged": True, "recovery_pr_merge_commit_sha": final_sha,
        "recovery_pr_head_sha": recovery_head, "recovery_pr_base_sha": base_sha,
        "final_tree_sha": final_tree, "final_parents": [base_sha, recovery_head],
        "remote_main_sha": final_sha, "fresh_clone_sha": final_sha,
        "current_r2_protocol_blob_sha": state["target_r2_protocol_blob_sha"],
        "current_recovery_state_file_sha256": state_digest,
        "authorization_commit_sha": auth_sha, "authorization_signature_verified": True,
        "authorization_signature_reason": "valid", "witness_commit_sha": witness_sha,
        "witness_file_sha256": witness_file_sha, "witness_signature_verified": True,
        "witness_signature_reason": "valid", "branch_protection_rules_sha256": protection["rules_sha256"],
        "required_status_check_contexts": contexts, "postpublication_checks": receipt["postpublication_checks"],
    }

    def api(endpoint: str):
        if endpoint == "repos/Arvin-liu/when-systems-catch-fire/branches/main":
            return {"protected": True, "commit": {"sha": final_sha}}
        if endpoint == f"repos/Arvin-liu/when-systems-catch-fire/pulls/302":
            return {
                "number": 302, "state": "closed", "merged": True,
                "base": {"ref": "main", "sha": base_sha},
                "head": {"ref": "synthetic/r2-restore", "sha": recovery_head},
                "merge_commit_sha": final_sha, "merged_at": "2026-10-19T06:30:00Z",
                "html_url": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/302",
            }
        if endpoint == f"repos/Arvin-liu/when-systems-catch-fire/commits/{final_sha}":
            return {"sha": final_sha, "commit": {"tree": {"sha": final_tree}}, "parents": [{"sha": base_sha}, {"sha": recovery_head}]}
        if endpoint == f"repos/Arvin-liu/when-systems-catch-fire/commits/{recovery_head}":
            return {"sha": recovery_head, "commit": {"tree": {"sha": final_tree}}, "parents": [{"sha": base_sha}]}
        if endpoint == f"repos/Arvin-liu/when-systems-catch-fire/commits/{preview_sha}":
            return {"sha": preview_sha, "commit": {"tree": {"sha": final_tree}}, "parents": [{"sha": base_sha}, {"sha": recovery_head}]}
        if endpoint == f"repos/Arvin-liu/when-systems-catch-fire/compare/{'e' * 40}...{final_sha}":
            return {"status": "ahead"}
        if endpoint == f"repos/Arvin-liu/when-systems-catch-fire/contents/{r3.relative(r3.R2_PROTOCOL_PATH)}?ref={final_sha}":
            return file_object(r3.relative(r3.R2_PROTOCOL_PATH), r3.R2_PROTOCOL_PATH.read_bytes())
        if endpoint == f"repos/Arvin-liu/when-systems-catch-fire/contents/{r3.relative(r3.RECOVERY_STATE_PATH)}?ref={final_sha}":
            return file_object(r3.relative(r3.RECOVERY_STATE_PATH), state_raw)
        return main_api(endpoint)

    return state, state_digest, statement, receipt, recovery_observations, api


class ReleaseTransactionProtocolR3Tests(unittest.TestCase):
    def _validate(self, record: dict[str, object], phase: str, expected: dict[str, object]) -> list[str]:
        return r3.validate_transaction_record(record, phase=phase, expected=expected, synthetic=True)

    def test_single_owner_protection_requires_pr_zero_reviews_exact_checks_and_no_bypass(self) -> None:
        api = _github_api()
        protection, errors = r3.read_live_branch_protection(github_api=api)
        self.assertEqual(errors, [])
        self.assertTrue(protection["pull_request_required"])
        self.assertEqual(protection["required_approval_count"], 0)
        self.assertEqual(protection["required_status_check_contexts"], [
            {"context": "foundation-validation", "app_id": 15368},
            {"context": "release-transaction-protocol-validation", "app_id": 15368},
            {"context": "repository-path-accounting-preflight", "app_id": 15368},
        ])
        self.assertTrue(protection["status_checks_strict"])
        self.assertTrue(protection["admin_enforcement_enabled"])
        self.assertTrue(protection["no_bypass_confirmed"])
        self.assertFalse(protection["force_push_allowed"])
        self.assertFalse(protection["deletions_allowed"])
        weakened_rules = [
            (lambda value: value.update(required_pull_request_reviews=None), "pull request"),
            (lambda value: value.update(required_status_checks={"strict": False, "checks": []}), "status-check contexts"),
            (lambda value: value.update(enforce_admins={"enabled": False}), "administrator enforcement"),
        ]
        for mutate, expected in weakened_rules:
            def weakened(request: str):
                value = api(request)
                if request.endswith("/branches/main/protection"):
                    value = dict(value)
                    mutate(value)
                return value
            observed, errors = r3.read_live_branch_protection(github_api=weakened)
            self.assertIsNotNone(observed)
            self.assertTrue(any(expected in error for error in errors), errors)

    def test_foundation_required_check_context_is_unique_and_owned_by_final_gate(self) -> None:
        workflow_path = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "foundation-validation.yml"
        workflow_text = workflow_path.read_text(encoding="utf-8")
        route_job = re.search(r"(?ms)^  route:\n(?P<body>(?:^    .*\n|^\n)*)", workflow_text)
        self.assertIsNotNone(route_job)
        route_display_name = re.search(r"(?m)^    name:\s*(\S+)\s*$", route_job.group("body"))
        self.assertIsNotNone(route_display_name)
        final_gate = re.search(r"(?ms)^  validate:\n(?P<body>(?:^    .*\n|^\n)*)", workflow_text)
        self.assertIsNotNone(final_gate)
        final_gate_display_name = re.search(r"(?m)^    name:\s*(\S+)\s*$", final_gate.group("body"))
        self.assertIsNotNone(final_gate_display_name)
        contexts = r3.load_json(r3.PROTOCOL_PATH)["prepublication"]["required_status_check_contexts"]
        foundation_contexts = [item["context"] for item in contexts if item["context"] == "foundation-validation"]
        self.assertEqual(foundation_contexts, [final_gate_display_name.group(1)])
        self.assertNotEqual(route_display_name.group(1), final_gate_display_name.group(1))
        self.assertEqual(
            len(re.findall(r"(?m)^    name:\s*foundation-validation\s*$", workflow_text)),
            1,
            "the required Foundation check context must identify one workflow job only",
        )

    def test_github_unsigned_owner_attribution_is_rejected(self) -> None:
        commit = {
            "author": {"id": 49422864}, "committer": {"id": 49422864},
            "commit": {"verification": {"verified": False, "reason": "unsigned"}},
        }
        valid, reason = r3._verified_owner_commit(commit, 49422864)
        self.assertFalse(valid)
        self.assertIn("did not verify", reason)

    def test_verified_github_web_flow_commit_preserves_owner_author_attribution(self) -> None:
        web_flow_commit = {
            "author": {"id": 49422864, "login": "Arvin-liu"},
            "committer": {"id": 19864447, "login": "web-flow"},
            "commit": {"verification": {
                "verified": True, "reason": "valid", "signature": "verified-signature",
                "payload": "verified-commit-payload",
            }},
        }
        valid, reason = r3._verified_owner_commit(web_flow_commit, 49422864)
        self.assertTrue(valid, reason)

        foreign_committer = json.loads(json.dumps(web_flow_commit))
        foreign_committer["committer"] = {"id": 99, "login": "other-user"}
        valid, reason = r3._verified_owner_commit(foreign_committer, 49422864)
        self.assertFalse(valid)
        self.assertIn("committer must be", reason)

        unsigned_web_flow = json.loads(json.dumps(web_flow_commit))
        unsigned_web_flow["commit"]["verification"] = {
            "verified": False, "reason": "unsigned", "signature": None, "payload": None,
        }
        valid, reason = r3._verified_owner_commit(unsigned_web_flow, 49422864)
        self.assertFalse(valid)
        self.assertIn("did not verify", reason)

        for field in ("signature", "payload"):
            empty_signed_field = json.loads(json.dumps(web_flow_commit))
            empty_signed_field["commit"]["verification"][field] = "  "
            valid, reason = r3._verified_owner_commit(empty_signed_field, 49422864)
            self.assertFalse(valid)
            self.assertIn("no signed commit" if field == "payload" else "no signature", reason)

    def test_successor_registration_binds_unique_task_ordinal_branches_and_inventory(self) -> None:
        registration = _registration_statement()
        content = json.dumps(registration, sort_keys=True, separators=(",", ":")).encode("utf-8")
        api = _github_api()
        evidence, errors = r3.read_authenticated_successor_registration(
            "5" * 40, expected_file_sha256=hashlib.sha256(content).hexdigest(),
            expected_formal_base_main_sha="a" * 40, expected_nonce="n" * 32,
            expected_parent_shas=[api.control.base_sha, api.control.staging_sha], github_api=api,
        )
        self.assertEqual(errors, [])
        self.assertEqual(evidence["statement"]["formal_ordinal"], 1)
        self.assertEqual(evidence["signature_verified"], True)
        self.assertEqual(evidence["parents"], [api.control.base_sha, api.control.staging_sha])
        self.assertEqual(evidence["path_update_commit_sha"], "5" * 40)
        self.assertEqual(api.control.commits["5" * 40]["committer"], {"id": 19864447, "login": "web-flow"})
        self.assertFalse(any("commits?path=" in endpoint for endpoint in api.control.calls))

        wrong_predecessor = _registration_statement()
        wrong_predecessor["prior_task_id"] = "IGNITION-20260829-147"
        wrong_content = json.dumps(wrong_predecessor, sort_keys=True, separators=(",", ":")).encode("utf-8")
        _, errors = r3.read_authenticated_successor_registration(
            "5" * 40, expected_file_sha256=hashlib.sha256(wrong_content).hexdigest(),
            expected_formal_base_main_sha="a" * 40,
            github_api=_github_api(registration_statement=wrong_predecessor),
        )
        self.assertTrue(any("predecessor does not equal the canonical current task" in item for item in errors), errors)

        duplicate = json.loads(json.dumps(registration))
        duplicate["conflict_inventory"]["formal_task_identities"].append(dict(
            duplicate["conflict_inventory"]["formal_task_identities"][0], task_id="ANOTHER_ID"
        ))
        inventory = duplicate["conflict_inventory"]
        inventory_payload = {key: value for key, value in inventory.items() if key != "inventory_sha256"}
        inventory["inventory_sha256"] = hashlib.sha256(
            json.dumps(inventory_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        duplicate_api = _github_api(registration_statement=duplicate)
        evidence, errors = r3.read_authenticated_successor_registration(
            "5" * 40, expected_formal_base_main_sha="a" * 40, github_api=duplicate_api,
        )
        self.assertIsNone(evidence)
        self.assertTrue(any("colliding formal task IDs, ordinals" in error for error in errors))

        task148 = dict(registration, task_id="IGNITION-20260829-148", formal_ordinal=148)
        evidence, errors = r3.read_authenticated_successor_registration(
            "5" * 40, expected_formal_base_main_sha="a" * 40,
            github_api=_github_api(registration_statement=task148),
        )
        self.assertIsNone(evidence)
        self.assertTrue(any("may not reuse Task148" in error for error in errors))

    def test_successor_registration_rejects_update_to_historical_fixed_path(self) -> None:
        api = _github_api()
        control = api.control
        control._materialize_witness()
        parent_sha = control.witness_sha
        renewed_statement = dict(
            _registration_statement(),
            registration_nonce="p" * 32,
            registered_at="2026-10-18T06:50:00Z",
        )
        renewed_raw = json.dumps(renewed_statement, sort_keys=True, separators=(",", ":")).encode("utf-8")
        renewed_files = dict(control.snapshots[parent_sha])
        renewed_files[r3.SUCCESSOR_REGISTRATION_PATH] = renewed_raw
        staging_sha = "7" * 40
        merge_sha = "8" * 40
        control.add_commit(
            staging_sha, [parent_sha], renewed_files,
            date="2026-10-18T06:55:00Z", signed=False,
        )
        control.add_commit(
            merge_sha, [parent_sha, staging_sha], renewed_files,
            date="2026-10-18T07:00:00Z", committer_id=r3.GITHUB_WEB_FLOW_ACCOUNT_ID,
            committer_login="web-flow", signed=True,
        )
        control.main_sha = merge_sha

        evidence, errors = r3.read_authenticated_successor_registration(
            merge_sha,
            expected_file_sha256=hashlib.sha256(renewed_raw).hexdigest(),
            expected_formal_base_main_sha="a" * 40,
            expected_nonce="p" * 32,
            expected_parent_shas=[parent_sha, staging_sha],
            github_api=api,
        )
        self.assertIsNone(evidence)
        self.assertTrue(
            any("already existed in the signed commit's first parent" in error for error in errors),
            errors,
        )

    def test_signed_registration_rejects_staging_nonce_parent_and_later_replay(self) -> None:
        content = json.dumps(_registration_statement(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(content).hexdigest()
        api = _github_api()
        _, errors = r3.read_authenticated_successor_registration(
            "5" * 40, expected_file_sha256=digest, expected_formal_base_main_sha="a" * 40,
            expected_nonce="wrong-registration-nonce-0123456789", github_api=api,
        )
        self.assertTrue(any("nonce differs" in error for error in errors), errors)

        _, errors = r3.read_authenticated_successor_registration(
            "5" * 40, expected_file_sha256=digest, expected_formal_base_main_sha="a" * 40,
            expected_parent_shas=[api.control.staging_sha, api.control.base_sha], github_api=api,
        )
        self.assertTrue(any("parent order differs" in error for error in errors), errors)

        api.control.main_sha = api.control.staging_sha
        _, errors = r3.read_authenticated_successor_registration(
            api.control.staging_sha, expected_formal_base_main_sha="a" * 40, github_api=api,
        )
        self.assertTrue(any("signature failed closed" in error for error in errors), errors)

        api = _github_api()
        api.control._materialize_witness()
        prior_files = dict(api.control.snapshots[api.control.main_sha])
        changed_registration = dict(_registration_statement(), registered_at="2026-10-18T05:01:00Z")
        changed_raw = json.dumps(changed_registration, sort_keys=True, separators=(",", ":")).encode("utf-8")
        prior_files[r3.SUCCESSOR_REGISTRATION_PATH] = changed_raw
        later_sha = "8" * 40
        api.control.add_commit(
            later_sha, [api.control.main_sha], prior_files, date="2026-10-18T06:50:00Z", signed=True,
        )
        revert_sha = "a" * 40
        reverted_files = dict(api.control.snapshots[api.control.main_sha])
        api.control.add_commit(
            revert_sha, [later_sha], reverted_files, date="2026-10-18T06:55:00Z", signed=True,
        )
        api.control.main_sha = revert_sha
        _, errors = r3.read_authenticated_successor_registration(
            "5" * 40, expected_file_sha256=digest, expected_formal_base_main_sha="a" * 40,
            github_api=api,
        )
        self.assertTrue(any("not the latest first-parent content update" in error for error in errors), errors)
        _, errors = r3._read_authenticated_control_path_commit(
            "Arvin-liu/1111", r3.SUCCESSOR_REGISTRATION_PATH, revert_sha, 49422864,
            expected_file_sha256=digest, api=api,
        )
        self.assertTrue(any("already existed in the signed commit's first parent" in error for error in errors), errors)

    def test_registration_readback_rejects_wrong_author_truncated_tree_and_blob_mismatch(self) -> None:
        raw = json.dumps(_registration_statement(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()

        api = _github_api()
        api.control.commits["5" * 40]["author"]["id"] = 7
        _, errors = r3.read_authenticated_successor_registration(
            "5" * 40, expected_file_sha256=digest, expected_formal_base_main_sha="a" * 40,
            github_api=api,
        )
        self.assertTrue(any("commit author must be the Owner" in error for error in errors), errors)

        api = _github_api()
        api.control._materialize_witness()
        main_tree_sha = api.control.commits[api.control.main_sha]["commit"]["tree"]["sha"]
        api.control.trees[main_tree_sha]["truncated"] = True
        _, errors = r3.read_authenticated_successor_registration(
            "5" * 40, expected_file_sha256=digest, expected_formal_base_main_sha="a" * 40,
            github_api=api,
        )
        self.assertTrue(any("truncated" in error for error in errors), errors)

        api = _github_api()
        def bad_blob(request: str):
            value = api(request)
            if request.endswith(f"{r3.SUCCESSOR_REGISTRATION_PATH}?ref={'5' * 40}"):
                value = dict(value)
                value["sha"] = "0" * 40
            return value
        _, errors = r3.read_authenticated_successor_registration(
            "5" * 40, expected_file_sha256=digest, expected_formal_base_main_sha="a" * 40,
            github_api=bad_blob,
        )
        self.assertTrue(any("blob SHA does not bind exact control-file bytes" in error for error in errors), errors)

    def test_r2_recovery_requires_exact_signed_pr_and_fresh_main_witness(self) -> None:
        active_receipt, active_observations = _activation_receipt(), _live_observations()
        state, state_digest, _, receipt, recovery_observations, api = _recovery_fixture()
        current, errors = r3.resolve_effective_protocol_with_recovery(
            active_receipt, observations=active_observations, repository_owner_id=49422864,
            recovery_state=state, recovery_state_file_sha256=state_digest,
            recovery_receipt=receipt, recovery_observations=recovery_observations,
            protocol_blob_sha=r3.git_blob_sha(), github_api=api,
        )
        self.assertEqual((current, errors), ("R2", []))

        tampered = dict(receipt)
        tampered["target_r2_protocol_blob_sha"] = "3" * 40
        current, errors = r3.resolve_effective_protocol_with_recovery(
            active_receipt, observations=active_observations, repository_owner_id=49422864,
            recovery_state=state, recovery_state_file_sha256=state_digest,
            recovery_receipt=tampered, recovery_observations=recovery_observations,
            protocol_blob_sha=r3.git_blob_sha(), github_api=api,
        )
        self.assertEqual(current, "R3")
        self.assertTrue(errors)

        current, errors = r3.resolve_effective_protocol_with_recovery(
            active_receipt, observations=active_observations, repository_owner_id=49422864,
            recovery_state=state, recovery_state_file_sha256=state_digest,
            protocol_blob_sha=r3.git_blob_sha(), github_api=api,
        )
        self.assertEqual(current, "R3")
        self.assertTrue(any("lacks a signed Owner authorization" in error for error in errors))

    def test_validated_r3_activation_never_falls_back_to_r2_on_later_protection_drift(self) -> None:
        active_receipt, active_observations, api = _activation_receipt(), _live_observations(), _github_api()
        recovery_state = r3.load_json(r3.RECOVERY_STATE_PATH)
        recovery_state_digest = hashlib.sha256(r3.RECOVERY_STATE_PATH.read_bytes()).hexdigest()

        def drifted_protection(endpoint: str):
            value = api(endpoint)
            if endpoint.endswith("/branches/main/protection"):
                value = dict(value)
                value["enforce_admins"] = {"enabled": False}
            return value

        current, errors = r3.resolve_effective_protocol_with_recovery(
            active_receipt, observations=active_observations, repository_owner_id=49422864,
            recovery_state=recovery_state, recovery_state_file_sha256=recovery_state_digest,
            protocol_blob_sha=r3.git_blob_sha(), github_api=drifted_protection,
        )
        self.assertEqual(current, "R3")
        self.assertTrue(any("administrator enforcement is off" in error for error in errors), errors)

    def test_merge_bound_r3_activation_claim_stays_blocked_r3_if_witness_readback_is_lost(self) -> None:
        active_receipt, active_observations, api = _activation_receipt(), _live_observations(), _github_api()
        recovery_state = r3.load_json(r3.RECOVERY_STATE_PATH)
        recovery_state_digest = hashlib.sha256(r3.RECOVERY_STATE_PATH.read_bytes()).hexdigest()

        def missing_witness(endpoint: str):
            return api(endpoint)

        api.control.main_sha = api.control.authorization_sha

        current, errors = r3.resolve_effective_protocol_with_recovery(
            active_receipt, observations=active_observations, repository_owner_id=49422864,
            recovery_state=recovery_state, recovery_state_file_sha256=recovery_state_digest,
            protocol_blob_sha=r3.git_blob_sha(), github_api=missing_witness,
        )
        self.assertEqual(current, "R3")
        self.assertTrue(any("no first-parent update" in error for error in errors), errors)

    def test_successor_registration_uses_fresh_versioned_control_path(self) -> None:
        expected = "instructions/goal-mode/IGNITION-R3-ADMISSION-SUCCESSOR-REGISTRATION-R3.json"
        task20_path = "instructions/goal-mode/IGNITION-R3-ADMISSION-SUCCESSOR-REGISTRATION-R2.json"
        self.assertEqual(r3.SUCCESSOR_REGISTRATION_PATH, expected)
        self.assertNotEqual(r3.SUCCESSOR_REGISTRATION_PATH, task20_path)
        self.assertNotEqual(
            r3.SUCCESSOR_REGISTRATION_PATH,
            "instructions/goal-mode/IGNITION-R3-ADMISSION-SUCCESSOR-REGISTRATION-R1.json",
        )
        protocol = r3.load_json(r3.PROTOCOL_PATH)
        self.assertEqual(
            protocol["identity_binding"]["successor_registration"]["authority_path"],
            expected,
        )

    def test_occupied_task20_registration_path_cannot_satisfy_new_successor_path(self) -> None:
        api = _github_api()
        control = api.control
        control._materialize_witness()
        first_parent_sha = control.witness_sha
        files = dict(control.snapshots[first_parent_sha])
        registration = files.pop(r3.SUCCESSOR_REGISTRATION_PATH)
        files["instructions/goal-mode/IGNITION-R3-ADMISSION-SUCCESSOR-REGISTRATION-R2.json"] = registration
        staging_sha = "a" * 40
        merge_sha = "b" * 40
        control.add_commit(
            staging_sha, [first_parent_sha], files,
            date="2026-10-18T07:10:00Z", signed=False,
        )
        control.add_commit(
            merge_sha, [first_parent_sha, staging_sha], files,
            date="2026-10-18T07:20:00Z", committer_id=r3.GITHUB_WEB_FLOW_ACCOUNT_ID,
            committer_login="web-flow", signed=True,
        )
        control.main_sha = merge_sha

        evidence, errors = r3.read_authenticated_successor_registration(merge_sha, github_api=api)
        self.assertIsNone(evidence)
        self.assertTrue(
            any(
                "fixed control path is absent" in error and r3.SUCCESSOR_REGISTRATION_PATH in error
                for error in errors
            ),
            errors,
        )

    def test_contract_preserves_r2_baseline_and_identifies_all_transition_exceptions(self) -> None:
        self.assertEqual(r3.validate_contract(), [])

    def test_recovery_state_must_bind_exact_r3_and_r2_protocol_blobs(self) -> None:
        state = r3.load_json(r3.RECOVERY_STATE_PATH)
        state["source_r3_protocol_blob_sha"] = "0" * 40
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "recovery-state.json"
            path.write_text(json.dumps(state), encoding="utf-8")
            with patch.object(r3, "RECOVERY_STATE_PATH", path):
                errors = r3.validate_contract()
        self.assertTrue(any("recovery state must bind the exact candidate protocol blob" in item for item in errors), errors)

    def test_cli_policy_selection_routes_recovery_evidence_through_resolver(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            transition = Path(temp_dir) / "transition.json"
            observations = Path(temp_dir) / "observations.json"
            recovery = Path(temp_dir) / "recovery.json"
            recovery_observations = Path(temp_dir) / "recovery-observations.json"
            for path in (transition, observations, recovery, recovery_observations):
                path.write_text("{}", encoding="utf-8")
            argv = [
                "validate_release_transaction_protocol_r3.py", "--check",
                "--transition-receipt", str(transition), "--observations", str(observations),
                "--repository-owner-id", "49422864", "--recovery-receipt", str(recovery),
                "--recovery-observations", str(recovery_observations),
            ]
            with patch.object(sys, "argv", argv), patch.object(
                r3, "resolve_effective_protocol_with_recovery", return_value=("R2", [])
            ) as resolver:
                self.assertEqual(r3.main(), 0)
            resolver.assert_called_once()
            kwargs = resolver.call_args.kwargs
            self.assertEqual(kwargs["recovery_receipt"], {})
            self.assertEqual(kwargs["recovery_observations"], {})
            self.assertEqual(kwargs["recovery_state"]["status"], "NOT_REQUESTED")
            self.assertEqual(len(kwargs["recovery_state_file_sha256"]), 64)

            blocked_stderr = StringIO()
            with patch.object(sys, "argv", argv), patch.object(
                r3, "resolve_effective_protocol_with_recovery", return_value=("R3", ["protection drift"])
            ), redirect_stderr(blocked_stderr):
                self.assertEqual(r3.main(), 2)
            self.assertIn("RELEASE_TRANSACTION_PROTOCOL_R3_CURRENT_BLOCKED", blocked_stderr.getvalue())
            self.assertIn("protection drift", blocked_stderr.getvalue())
        self.assertEqual(r2.validate(), [])
        policy = r3.load_json(r3.PROTOCOL_PATH)
        self.assertEqual(policy["status"], "CANDIDATE_NOT_EFFECTIVE")
        self.assertTrue(policy["activation"]["r2_is_current_before_any_merge_bound_activation_claim"])
        self.assertTrue(policy["activation"]["merge_bound_activation_claim_latches_r3_until_signed_r2_restoration"])
        self.assertTrue(policy["activation"]["signed_protected_r2_restoration_is_the_only_postactivation_route_to_r2"])
        duration = policy["canonical_suite_duration_policy"]
        self.assertEqual(
            duration["elapsed_duration_semantics"], "OBSERVED_NATURAL_ELAPSED_SECONDS_ONLY",
        )
        self.assertEqual(duration["r2_duration_exception"]["r2_minimum_natural_window_seconds"], 14400)
        self.assertEqual(duration["r2_duration_exception"]["r3_candidate_duration_threshold"], "NONE")
        self.assertTrue(duration["r2_duration_exception"]["r2_remains_effective_before_activation"])
        self.assertTrue(duration["r2_duration_exception"]["explicit_owner_approval_required"])
        suite_policy = policy["preserved_hard_gates"]["canonical_full_suite"]
        self.assertNotIn("required_runs", suite_policy)
        self.assertEqual(suite_policy["run_count_policy"], "EVIDENCE_DRIVEN_NO_FIXED_COUNT")
        self.assertTrue(suite_policy["independent_revalidation"]["required"])
        self.assertTrue(policy["r2_full_suite_count_exception"]["r2_remains_effective_before_activation"])
        self.assertTrue(policy["r2_publication_method_exception"]["explicit_owner_approval_required"])
        self.assertNotIn("minimum_natural_window_seconds", suite_policy)
        self.assertEqual(
            r2.load_json(r2.PROTOCOL_PATH)["pre_publication_hard_gates"]["canonical_full_suite"]["minimum_natural_window_seconds"],
            14400,
        )
        self.assertEqual(r2.load_json(r2.PROTOCOL_PATH)["pre_publication_hard_gates"]["canonical_full_suite"]["required_runs"], 2)
        self.assertEqual(r2.load_json(r2.PROTOCOL_PATH)["main_mutation_policy"]["mode"], "ORDINARY_FAST_FORWARD_ONLY")

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

    def test_evidence_sufficiency_accepts_one_or_more_receipts_without_fixed_run_count(self) -> None:
        record = _record()
        record["canonical_full_suite_receipts"].extend([
            _suite("run-2", "SYNTHETIC_FIXTURE_ONLY", "synthetic/fixture-only", "b" * 40),
            _suite("run-3", "SYNTHETIC_FIXTURE_ONLY", "synthetic/fixture-only", "b" * 40),
        ])
        record["canonical_full_suite_evidence_revalidation"]["receipt_run_ids"] = ["run-1", "run-2", "run-3"]
        self.assertEqual(self._validate(record, "prepublication", _context()), [])

    def test_independent_revalidation_must_cover_exact_head_inventory_environment_and_all_runs(self) -> None:
        for key, value in (("candidate_head_sha", "f" * 40),
                           ("inventory_sha256", "f" * 64),
                           ("test_count", 1082),
                           ("environment_sha256", "f" * 64)):
            record = _record()
            record["canonical_full_suite_evidence_revalidation"][key] = value
            self.assertTrue(self._validate(record, "prepublication", _context()), key)
        record = _record()
        record["canonical_full_suite_evidence_revalidation"]["receipt_run_ids"] = ["different-run"]
        self.assertTrue(self._validate(record, "prepublication", _context()))

    def test_run_count_exception_and_publication_method_exception_are_explicit_owner_fields(self) -> None:
        for field in ("r2_full_suite_count_policy_exception", "r2_publication_method_exception"):
            statement = _owner_statement()
            del statement[field]
            errors = r3._schema_errors(
                statement,
                {"$ref": "#/$defs/ownerAuthorizationStatement", "$defs": r3.load_json(r3.SCHEMA_PATH)["$defs"]},
            )
            self.assertTrue(errors, field)

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
        self.assertTrue(live_rules["required_status_checks"])
        self.assertEqual(live_rules["required_check_names"], [
            "foundation-validation", "release-transaction-protocol-validation", "repository-path-accounting-preflight"
        ])
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
        self.assertTrue(any("GitHub commit readback is invalid" in error for error in errors), errors)

        receipt, observations = _activation_receipt(), _live_observations()
        active, errors = r3.resolve_effective_protocol(
            receipt, observations=observations, repository_owner_id=49422864, github_api=_github_api(actor_id=7)
        )
        self.assertEqual(active, "R2")
        self.assertTrue(errors)

    def test_r2_restoration_fixed_paths_accept_owner_signed_web_flow_merges(self) -> None:
        _, _, restore_statement, receipt, _, _ = _recovery_fixture()
        api = _github_api()
        control = api.control
        control._materialize_witness()

        def canonical_bytes(value: object) -> bytes:
            return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")

        def add_web_flow_merge(path: str, raw: bytes, parent_sha: str, stage_sha: str, merge_sha: str) -> None:
            files = dict(control.snapshots[parent_sha])
            files[path] = raw
            control.add_commit(stage_sha, [parent_sha], files, date="2026-10-19T05:10:00Z", signed=False)
            control.add_commit(
                merge_sha, [parent_sha, stage_sha], files, date="2026-10-19T05:30:00Z",
                committer_id=r3.GITHUB_WEB_FLOW_ACCOUNT_ID, committer_login="web-flow", signed=True,
            )

        authorization_sha = "c" * 40
        authorization_raw = canonical_bytes(restore_statement)
        add_web_flow_merge(
            r3.R2_RESTORE_AUTHORIZATION_PATH, authorization_raw, control.witness_sha,
            "d" * 40, authorization_sha,
        )
        control.main_sha = authorization_sha

        authorization, errors = r3.read_authenticated_r2_restore_authorization(
            authorization_sha, expected_file_sha256=hashlib.sha256(authorization_raw).hexdigest(),
            github_api=api,
        )
        self.assertEqual(errors, [])
        self.assertIsNotNone(authorization)
        self.assertTrue(authorization["authorization_signature_verified"])
        self.assertEqual(control.commits[authorization_sha]["committer"]["login"], "web-flow")

        witnessed_receipt = dict(receipt, owner_authorization_commit_sha=authorization_sha)
        witness_sha = "e" * 40
        witness_raw = canonical_bytes(witnessed_receipt)
        add_web_flow_merge(
            r3.R2_RESTORATION_WITNESS_PATH, witness_raw, authorization_sha,
            "a" * 40, witness_sha,
        )
        control.main_sha = witness_sha

        witness, errors = r3.read_live_r2_restoration_witness(
            witnessed_receipt, restore_authorization=authorization, github_api=api,
        )
        self.assertEqual(errors, [])
        self.assertIsNotNone(witness)
        self.assertTrue(witness["witness_signature_verified"])
        self.assertEqual(witness["witness_commit_sha"], witness_sha)
        self.assertFalse(any("commits?path=" in endpoint for endpoint in control.calls))

        control.commits[witness_sha]["commit"]["verification"] = {
            "verified": False, "reason": "unsigned", "signature": None, "payload": None,
        }
        witness, errors = r3.read_live_r2_restoration_witness(
            witnessed_receipt, restore_authorization=authorization, github_api=api,
        )
        self.assertIsNone(witness)
        self.assertTrue(any("signature failed closed" in error for error in errors), errors)

    def test_owner_authorization_accepts_only_verified_owner_authored_web_flow_commit(self) -> None:
        base_api = _github_api()
        authorization_sha = "f" * 40
        files = dict(base_api.control.snapshots[authorization_sha])
        staging_sha = "8" * 40
        base_api.control.add_commit(
            staging_sha, [base_api.control.registration_sha], files,
            date="2026-10-18T05:59:00Z", signed=False,
        )
        base_api.control.add_commit(
            authorization_sha, [base_api.control.registration_sha, staging_sha], files,
            date="2026-10-18T06:00:00Z", signed=True,
            committer_id=19864447, committer_login="web-flow",
        )

        def verified_web_flow(endpoint: str):
            return base_api(endpoint)

        evidence, errors = r3.read_authenticated_owner_authorization(
            authorization_sha, github_api=verified_web_flow,
        )
        self.assertEqual(errors, [])
        self.assertIsNotNone(evidence)
        self.assertEqual(evidence["evidence"]["authorization_path"], r3.OWNER_AUTHORIZATION_PATH)
        self.assertEqual(evidence["meta"]["authorization_commit_committer_id"], 19864447)
        self.assertTrue(evidence["meta"]["authorization_signature_verified"])

        def unsigned_web_flow(endpoint: str):
            value = verified_web_flow(endpoint)
            if endpoint == f"repos/Arvin-liu/1111/commits/{authorization_sha}":
                value = dict(value)
                value["commit"] = dict(value["commit"])
                value["commit"]["verification"] = {
                    "verified": False, "reason": "unsigned", "signature": None, "payload": None,
                }
            return value

        evidence, errors = r3.read_authenticated_owner_authorization(
            authorization_sha, github_api=unsigned_web_flow,
        )
        self.assertIsNone(evidence)
        self.assertTrue(any("signature failed closed" in error for error in errors), errors)

    def test_owner_authorization_accepts_unique_historical_path_update_and_rejects_replay_or_tampering(self) -> None:
        api = _github_api()
        control = api.control
        control._materialize_witness()
        original_sha = control.authorization_sha
        original_raw = control.snapshots[original_sha][r3.OWNER_AUTHORIZATION_PATH]
        parent_sha = control.witness_sha

        def canonical_bytes(value: object) -> bytes:
            return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")

        renewed_raw = canonical_bytes(_owner_statement(pr_number=302, head_sha="c" * 40))
        renewed_files = dict(control.snapshots[parent_sha])
        renewed_files[r3.OWNER_AUTHORIZATION_PATH] = renewed_raw
        update_staging_sha = "7" * 40
        update_merge_sha = "8" * 40
        control.add_commit(
            update_staging_sha, [parent_sha], renewed_files,
            date="2026-10-18T06:50:00Z", signed=False,
        )
        control.add_commit(
            update_merge_sha, [parent_sha, update_staging_sha], renewed_files,
            date="2026-10-18T07:00:00Z", committer_id=r3.GITHUB_WEB_FLOW_ACCOUNT_ID,
            committer_login="web-flow", signed=True,
        )
        control.main_sha = update_merge_sha

        evidence, errors = r3.read_authenticated_owner_authorization(update_merge_sha, github_api=api)
        self.assertEqual(errors, [])
        self.assertIsNotNone(evidence)
        self.assertEqual(evidence["evidence"]["approved_pr_number"], 302)
        self.assertTrue(evidence["evidence"]["authorization_signature_verified"])

        stale, errors = r3.read_authenticated_owner_authorization(original_sha, github_api=api)
        self.assertIsNone(stale)
        self.assertTrue(any("not the latest first-parent content update" in error for error in errors), errors)

        def tampered_read(endpoint: str):
            value = api(endpoint)
            exact = (
                f"repos/Arvin-liu/1111/contents/{r3.OWNER_AUTHORIZATION_PATH}"
                f"?ref={update_merge_sha}"
            )
            if endpoint == exact:
                value = dict(value)
                value["content"] = base64.b64encode(renewed_raw + b" ").decode("ascii")
            return value

        tampered, errors = r3.read_authenticated_owner_authorization(
            update_merge_sha, github_api=tampered_read
        )
        self.assertIsNone(tampered)
        self.assertTrue(any("blob SHA does not bind exact control-file bytes" in error for error in errors), errors)

        replay_files = dict(control.snapshots[update_merge_sha])
        replay_files[r3.OWNER_AUTHORIZATION_PATH] = original_raw
        replay_staging_sha = "a" * 40
        replay_merge_sha = "b" * 40
        control.add_commit(
            replay_staging_sha, [update_merge_sha], replay_files,
            date="2026-10-18T07:10:00Z", signed=False,
        )
        control.add_commit(
            replay_merge_sha, [update_merge_sha, replay_staging_sha], replay_files,
            date="2026-10-18T07:20:00Z", committer_id=r3.GITHUB_WEB_FLOW_ACCOUNT_ID,
            committer_login="web-flow", signed=True,
        )
        control.main_sha = replay_merge_sha
        overwritten, errors = r3.read_authenticated_owner_authorization(update_merge_sha, github_api=api)
        self.assertIsNone(overwritten)
        self.assertTrue(any("not the latest first-parent content update" in error for error in errors), errors)
        replay, errors = r3.read_authenticated_owner_authorization(replay_merge_sha, github_api=api)
        self.assertEqual(errors, [])
        self.assertIsNotNone(replay)
        replayed_approval = replay["evidence"]
        self.assertEqual(replayed_approval["approved_pr_number"], 301)
        self.assertEqual(replayed_approval["approved_head_sha"], "b" * 40)

        # A freshly signed path update cannot make that historical approval
        # authorize a different candidate. Replay rejection belongs at the
        # exact PR/head/base admission boundary, not in an expensive scan of
        # every first-parent commit in private-repository history.
        receipt = _activation_receipt()
        receipt["pr_number"] = 302
        receipt["pr_url"] = "https://github.com/Arvin-liu/when-systems-catch-fire/pull/302"
        receipt["candidate_head_sha"] = "c" * 40
        receipt["base_main_sha"] = "d" * 40
        receipt["merge_preview_parents"] = ["d" * 40, "c" * 40]
        receipt["actual_final_main_parents"] = ["d" * 40, "c" * 40]
        receipt["owner_approval"] = replayed_approval
        observations = _live_observations()
        observations["pr_number"] = 302
        observations["pr_url"] = receipt["pr_url"]
        observations["pr_head_sha"] = "c" * 40
        observations["final_main_parents"] = ["d" * 40, "c" * 40]
        observations["owner_authorization"] = replayed_approval
        observations["authorization_file_sha256"] = replayed_approval["authorization_file_sha256"]
        observations["authorization_readback_commit_sha"] = replayed_approval["authorization_commit_sha"]
        observations.update(replay["meta"])
        live_pr = {
            "pr_number": 302, "pr_url": receipt["pr_url"],
            "head_ref": receipt["pr_head_ref"], "head_sha": "c" * 40,
            "merge_commit_sha": receipt["actual_final_main_sha"],
            "merged_at": receipt["pr_merged_at"],
        }
        with patch.object(r3, "read_live_merged_pr", return_value=(live_pr, [])):
            active, errors = r3.resolve_effective_protocol(
                receipt, observations=observations, repository_owner_id=49422864, github_api=api,
            )
        self.assertEqual(active, "R2")
        self.assertTrue(any("Owner authorization does not bind the exact transition PR and candidate head" in error for error in errors), errors)
        self.assertTrue(any("Owner authorization is stale for the admitted base SHA" in error for error in errors), errors)

        original_receipt = _activation_receipt()
        original_receipt["owner_approval"] = replayed_approval
        original_observations = _live_observations()
        original_observations["owner_authorization"] = replayed_approval
        original_observations["authorization_file_sha256"] = replayed_approval["authorization_file_sha256"]
        original_observations["authorization_readback_commit_sha"] = replayed_approval["authorization_commit_sha"]
        original_observations.update(replay["meta"])
        original_live_pr = {
            "pr_number": 301, "pr_url": original_receipt["pr_url"],
            "head_ref": original_receipt["pr_head_ref"], "head_sha": "b" * 40,
            "merge_commit_sha": original_receipt["actual_final_main_sha"],
            "merged_at": original_receipt["pr_merged_at"],
        }
        with patch.object(r3, "read_live_merged_pr", return_value=(original_live_pr, [])):
            active, errors = r3.resolve_effective_protocol(
                original_receipt, observations=original_observations,
                repository_owner_id=49422864, github_api=api,
            )
        self.assertEqual(active, "R2")
        self.assertTrue(any("Owner authorization was not committed before the GitHub PR merge" in error for error in errors), errors)
        self.assertTrue(any("signed 1111 witness is not a descendant of the exact signed Owner authorization commit" in error for error in errors), errors)

    def test_historical_owner_authorization_update_rejects_invalid_signature_identity_tree_and_digest(self) -> None:
        def updated_authorization(
            *,
            signed: bool = True,
            unchanged: bool = False,
            second_parent_uses_old_file: bool = False,
            statement: dict[str, object] | None = None,
        ):
            api = _github_api()
            control = api.control
            control._materialize_witness()
            first_parent_sha = control.witness_sha
            first_parent_files = dict(control.snapshots[first_parent_sha])
            merge_files = dict(first_parent_files)
            if not unchanged:
                updated_statement = dict(statement or _owner_statement(pr_number=302, head_sha="c" * 40))
                updated_raw = json.dumps(updated_statement, sort_keys=True, separators=(",", ":")).encode("utf-8")
                merge_files[r3.OWNER_AUTHORIZATION_PATH] = updated_raw
            else:
                updated_raw = first_parent_files[r3.OWNER_AUTHORIZATION_PATH]
            second_parent_files = first_parent_files if second_parent_uses_old_file else merge_files
            staging_sha = "7" * 40
            merge_sha = "8" * 40
            control.add_commit(
                staging_sha, [first_parent_sha], second_parent_files,
                date="2026-10-18T06:55:00Z", signed=False,
            )
            control.add_commit(
                merge_sha, [first_parent_sha, staging_sha], merge_files,
                date="2026-10-18T07:00:00Z", committer_id=r3.GITHUB_WEB_FLOW_ACCOUNT_ID,
                committer_login="web-flow", signed=signed,
            )
            control.main_sha = merge_sha
            return api, control, merge_sha, updated_raw

        api, _, merge_sha, _ = updated_authorization(signed=False)
        evidence, errors = r3.read_authenticated_owner_authorization(merge_sha, github_api=api)
        self.assertIsNone(evidence)
        self.assertTrue(any("signature failed closed" in error for error in errors), errors)

        api, control, merge_sha, _ = updated_authorization()
        control.commits[merge_sha]["author"]["id"] = 7
        evidence, errors = r3.read_authenticated_owner_authorization(merge_sha, github_api=api)
        self.assertIsNone(evidence)
        self.assertTrue(any("commit author must be the Owner" in error for error in errors), errors)

        api, control, merge_sha, _ = updated_authorization()
        control.commits[merge_sha]["committer"] = {"id": 99, "login": "other-user"}
        evidence, errors = r3.read_authenticated_owner_authorization(merge_sha, github_api=api)
        self.assertIsNone(evidence)
        self.assertTrue(any("committer must be the Owner or GitHub web-flow" in error for error in errors), errors)

        api, _, merge_sha, _ = updated_authorization(unchanged=True)
        evidence, errors = r3.read_authenticated_owner_authorization(merge_sha, github_api=api)
        self.assertIsNone(evidence)
        self.assertTrue(any("not the latest first-parent content update" in error for error in errors), errors)

        api, _, merge_sha, _ = updated_authorization()
        def not_on_main_ancestry(endpoint: str):
            if endpoint == f"repos/Arvin-liu/1111/compare/{merge_sha}...{merge_sha}":
                return {"status": "diverged"}
            return api(endpoint)
        evidence, errors = r3.read_authenticated_owner_authorization(
            merge_sha, github_api=not_on_main_ancestry
        )
        self.assertIsNone(evidence)
        self.assertTrue(any("not an ancestor of the exact current" in error for error in errors), errors)

        api, _, merge_sha, _ = updated_authorization(second_parent_uses_old_file=True)
        evidence, errors = r3.read_authenticated_owner_authorization(merge_sha, github_api=api)
        self.assertIsNone(evidence)
        self.assertTrue(any("second-parent fixed path" in error for error in errors), errors)

        api, _, merge_sha, _ = updated_authorization()
        _, errors = r3._read_authenticated_control_path_commit(
            r3.OWNER_AUTHORIZATION_REPOSITORY,
            r3.OWNER_AUTHORIZATION_PATH,
            merge_sha,
            49422864,
            expected_file_sha256="0" * 64,
            allow_historical_authorization_update=True,
            api=api,
        )
        self.assertTrue(any("SHA-256 differs" in error for error in errors), errors)

        future_statement = dict(_owner_statement(pr_number=302, head_sha="c" * 40))
        future_statement["approved_at"] = "2026-10-18T07:01:00Z"
        api, _, merge_sha, _ = updated_authorization(statement=future_statement)
        evidence, errors = r3.read_authenticated_owner_authorization(merge_sha, github_api=api)
        self.assertIsNone(evidence)
        self.assertTrue(any("authorization time is later than" in error for error in errors), errors)

    def test_r0_owner_authorization_path_is_rejected_after_versioned_rotation(self) -> None:
        api = _github_api()
        control = api.control
        authorization_sha = control.authorization_sha
        files = dict(control.snapshots[authorization_sha])
        raw = files.pop(r3.OWNER_AUTHORIZATION_PATH)
        files["instructions/goal-mode/IGNITION-2026-10-18-R3-ONE-TIME-TRANSITION-AUTHORIZATION-R0.json"] = raw
        tree_sha = control._tree(files)
        control.snapshots[authorization_sha] = files
        control.commits[authorization_sha]["commit"]["tree"]["sha"] = tree_sha

        evidence, errors = r3.read_authenticated_owner_authorization(
            authorization_sha, github_api=api,
        )
        self.assertIsNone(evidence)
        self.assertTrue(any("no first-parent update" in error for error in errors), errors)

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
                value["enforce_admins"] = {"enabled": False}
            return value
        active, errors = r3.resolve_effective_protocol(
            receipt, observations=observations, repository_owner_id=49422864, github_api=changed_rules
        )
        self.assertEqual(active, "R2")
        self.assertTrue(errors)

    def test_ruleset_review_and_required_status_rules_are_read_from_live_endpoint(self) -> None:
        api = _github_api()
        ruleset = {
            "id": 10, "target": "branch", "enforcement": "active", "bypass_actors": [],
            "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
            "rules": [
                {"type": "pull_request", "parameters": {"required_approving_review_count": 1}},
                {"type": "required_status_checks", "parameters": {
                    "strict_required_status_checks_policy": True,
                    "required_status_checks": [{"context": "ruleset/ci", "integration_id": 15368}],
                }},
            ],
        }
        def with_rulesets(endpoint: str):
            if endpoint.endswith("/rulesets?includes_parents=true&per_page=100"):
                return [ruleset]
            return api(endpoint)
        protection, errors = r3.read_live_branch_protection(github_api=with_rulesets)
        self.assertIsNotNone(protection)
        self.assertTrue(any("approval count" in error for error in errors))
        self.assertTrue(any("contexts" in error for error in errors))
        self.assertEqual(protection["ruleset_count"], 1)

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
        self.assertTrue(any("GitHub blob SHA does not bind exact control-file bytes" in error for error in errors), errors)

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

    def test_transaction_record_binds_registration_nonce_and_ordered_parents(self) -> None:
        for field, value in (
            ("successor_registration_nonce", "x" * 32),
            ("successor_registration_parent_shas", ["c" * 40, "d" * 40]),
        ):
            record = _record()
            record["task_identity"][field] = value
            errors = self._validate(record, "prepublication", _context())
            self.assertTrue(any(f"task identity field {field}" in error for error in errors), errors)

    def test_verified_review_rule_requires_independent_exact_head_reviewer(self) -> None:
        api = _github_api()
        def with_review_rule(endpoint: str):
            value = api(endpoint)
            if endpoint.endswith("/branches/main/protection"):
                value["required_pull_request_reviews"] = {"required_approving_review_count": 1}
            return value
        live_protection, errors = r3.read_live_branch_protection(github_api=with_review_rule)
        self.assertTrue(any("approval count" in error for error in errors))
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
