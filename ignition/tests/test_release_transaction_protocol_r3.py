from __future__ import annotations

import unittest

from tools import validate_release_transaction_protocol as r2
from tools import validate_release_transaction_protocol_r3 as r3


def _check(name: str, sha: str) -> dict[str, str]:
    return {"name": name, "sha": sha, "conclusion": "success", "completed_at": "2026-10-18T06:00:00Z"}


def _suite(run_id: str, task_id: str, branch: str, sha: str) -> dict[str, object]:
    return {
        "run_id": run_id,
        "task_id": task_id,
        "task_branch": branch,
        "sha": sha,
        "inventory_sha256": "1" * 64,
        "test_count": 3,
        "environment_sha256": "2" * 64,
        "duration_seconds": 14400,
        "failures": 0,
        "errors": 0,
        "skips": 0,
        "clean_before": True,
        "clean_after": True,
        "watchdog_used": False,
        "conclusion": "success",
        "source_url": "https://github.com/Arvin-liu/when-systems-catch-fire/actions/runs/1001",
    }


def _context() -> dict[str, object]:
    return {
        "task_id": "SYNTHETIC_FIXTURE_ONLY",
        "formal_ordinal": 1,  # Schema-only synthetic value; never a formal task assignment.
        "task_branch": "synthetic/fixture-only",
        "current_task_source_sha256": "3" * 64,
        "task_identity_model_sha256": "6" * 64,
        "execution_contract_sha256": "4" * 64,
        "pr_number": 301,
        "repository_owner_id": 49422864,
        "candidate_head_sha": "b" * 40,
        "candidate_tree_sha": "c" * 40,
        "base_main_sha": "a" * 40,
        "merge_preview_sha": "d" * 40,
        "merge_preview_tree_sha": "c" * 40,
        "required_check_names": ["ci-a", "ci-b"],
        "required_postpublication_check_names": ["ci-a", "ci-b"],
        "test_inventory_sha256": "1" * 64,
        "test_count": 3,
        "environment_sha256": "2" * 64,
        "reviewed_changed_paths": ["ignition/tools/release.py", "ignition/tests/test_release.py"],
        "observed_changed_paths": ["ignition/tools/release.py", "ignition/tests/test_release.py"],
        "branch_protection_rules_sha256": "5" * 64,
        "base_branch": "main",
        "owner_review_state": "APPROVED",
        "owner_review_url": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/301#pullrequestreview-1",
        "remote_main_sha": "e" * 40,
        "fresh_main_checkout_sha": "e" * 40,
        "actual_final_main_tree_sha": "c" * 40,
        "actual_final_main_parents": ["a" * 40, "b" * 40],
        "postpublication_checks": [_check(name, "e" * 40) for name in ("ci-a", "ci-b")],
        "projection_check": {"status": "PASS", "source_sha": "e" * 40, "unexpected_changed_paths": []},
    }


def _record() -> dict[str, object]:
    context = _context()
    candidate_sha = str(context["candidate_head_sha"])
    preview_sha = str(context["merge_preview_sha"])
    return {
        "task_identity": {key: context[key] for key in (
            "task_id", "formal_ordinal", "task_branch", "current_task_source_sha256", "task_identity_model_sha256", "execution_contract_sha256"
        )},
        "pull_request": {
            "number": 301,
            "url": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/301",
            "base_branch": "main",
            "head_branch": context["task_branch"],
            "state": "OPEN",
            "draft": False,
            "head_sha": candidate_sha,
        },
        "refs": {
            "base_main_sha": context["base_main_sha"],
            "candidate_tree_sha": context["candidate_tree_sha"],
            "merge_preview_sha": preview_sha,
            "merge_preview_tree_sha": context["merge_preview_tree_sha"],
            "merge_preview_parents": [context["base_main_sha"], candidate_sha],
        },
        "changed_paths": {
            "reviewed_paths": ["ignition/tools/release.py", "ignition/tests/test_release.py"],
            "observed_paths": ["ignition/tools/release.py", "ignition/tests/test_release.py"],
        },
        "required_check_names": context["required_check_names"],
        "candidate_checks": [_check(name, candidate_sha) for name in context["required_check_names"]],
        "merge_preview_checks": [_check(name, preview_sha) for name in context["required_check_names"]],
        "canonical_full_suite_receipts": [
            _suite("run-1", str(context["task_id"]), str(context["task_branch"]), candidate_sha),
            _suite("run-2", str(context["task_id"]), str(context["task_branch"]), candidate_sha),
        ],
        "merge_method": "MERGE_COMMIT",
        "branch_protection": {
            "status": "VERIFIED",
            "target_branch": "main",
            "required_review": True,
            "required_status_checks": True,
            "bypass_enabled": False,
            "observed_at": "2026-10-18T05:00:00Z",
            "rules_sha256": "5" * 64,
        },
        "owner_approval": {
            "approved": True,
            "owner_actor_id": 49422864,
            "approved_pr_number": 301,
            "approved_head_sha": candidate_sha,
            "review_state": "APPROVED",
            "scope": "EXACT_RELEASE_PR_ONLY",
            "review_url": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/301#pullrequestreview-1",
            "approved_at": "2026-10-18T05:30:00Z",
        },
        "publication": {
            "status": "NOT_MERGED",
            "actual_final_main_sha": None,
            "actual_final_main_tree_sha": None,
            "actual_final_main_parents": None,
            "observed_remote_main_sha": None,
            "fresh_main_checkout_sha": None,
            "postpublication_checks": [],
            "projection_check": None,
        },
    }


def _postpublication_record() -> dict[str, object]:
    record = _record()
    context = _context()
    final_sha = "e" * 40  # GitHub's final commit SHA may differ from the preview SHA.
    publication = record["publication"]
    record["pull_request"]["state"] = "MERGED"
    publication.update({
        "status": "PUBLISHED_AND_VERIFIED",
        "actual_final_main_sha": final_sha,
        "actual_final_main_tree_sha": context["merge_preview_tree_sha"],
        "actual_final_main_parents": [context["base_main_sha"], context["candidate_head_sha"]],
        "observed_remote_main_sha": final_sha,
        "fresh_main_checkout_sha": final_sha,
        "postpublication_checks": [_check(name, final_sha) for name in context["required_postpublication_check_names"]],
        "projection_check": {"status": "PASS", "source_sha": final_sha, "unexpected_changed_paths": []},
    })
    return record


def _activation_receipt() -> dict[str, object]:
    return {
        "status": "PUBLISHED_AND_VERIFIED",
        "migration_scope": "ONE_TIME_R3_BOOTSTRAP_ONLY",
        "r3_protocol_blob_sha": r3.git_blob_sha(),
        "prepublication_record_sha256": "7" * 64,
        "prepublication_validation_status": "VALIDATED",
        "pr_number": 301,
        "pr_url": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/301",
        "pr_base_branch": "main",
        "pr_head_ref": "synthetic/fixture-only",
        "task_branch": "synthetic/fixture-only",
        "pr_merged": True,
        "pr_merge_commit_sha": "e" * 40,
        "base_main_sha": "a" * 40,
        "candidate_head_sha": "b" * 40,
        "candidate_tree_sha": "c" * 40,
        "merge_preview_sha": "d" * 40,
        "merge_preview_tree_sha": "c" * 40,
        "merge_preview_parents": ["a" * 40, "b" * 40],
        "actual_final_main_sha": "e" * 40,
        "actual_final_main_tree_sha": "c" * 40,
        "actual_final_main_parents": ["a" * 40, "b" * 40],
        "observed_remote_main_sha": "e" * 40,
        "fresh_main_clone_head_sha": "e" * 40,
        "merge_method": "MERGE_COMMIT",
        "branch_protection_verified": True,
        "branch_protection_rules_sha256": "5" * 64,
        "owner_approved_before_merge": True,
        "owner_approval": {
            "approved": True,
            "owner_actor_id": 49422864,
            "approved_pr_number": 301,
            "approved_head_sha": "b" * 40,
            "review_state": "APPROVED",
            "scope": "ONE_TIME_R3_BOOTSTRAP_ONLY",
            "review_url": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/301#pullrequestreview-1",
            "approved_at": "2026-10-18T05:30:00Z",
        },
        "postpublication_checks": [_check("ci-a", "e" * 40)],
        "published_at": "2026-10-18T06:30:00Z",
    }


def _live_observations() -> dict[str, object]:
    return {
        "observation_source": "authenticated_github_and_fresh_clone_readback_and_1111_receipt_readback",
        "observed_at": "2026-10-18T06:35:00Z",
        "repository_owner_id": 49422864,
        "prepublication_record_sha256": "7" * 64,
        "prepublication_validation_status": "VALIDATED",
        "pr_number": 301,
        "pr_url": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/301",
        "pr_base_branch": "main",
        "pr_head_ref": "synthetic/fixture-only",
        "pr_merged": True,
        "pr_merge_commit_sha": "e" * 40,
        "pr_head_sha": "b" * 40,
        "remote_main_sha": "e" * 40,
        "final_main_tree_sha": "c" * 40,
        "final_main_parents": ["a" * 40, "b" * 40],
        "fresh_main_clone_head_sha": "e" * 40,
        "branch_protection_status": "VERIFIED",
        "branch_protection_rules_sha256": "5" * 64,
        "branch_protection_rules": {
            "target_branch": "main",
            "required_review": True,
            "required_status_checks": True,
            "bypass_enabled": False,
            "direct_main_push_allowed": False,
            "required_check_names": ["ci-a"],
        },
        "required_check_names": ["ci-a"],
        "postpublication_checks": [_check("ci-a", "e" * 40)],
        "owner_review_actor_id": 49422864,
        "owner_review_state": "APPROVED",
        "owner_review_pr_number": 301,
        "owner_review_head_sha": "b" * 40,
        "owner_review_url": "https://github.com/Arvin-liu/when-systems-catch-fire/pull/301#pullrequestreview-1",
    }


class ReleaseTransactionProtocolR3Tests(unittest.TestCase):
    def _validate(self, record: dict[str, object], phase: str, expected: dict[str, object]) -> list[str]:
        return r3.validate_transaction_record(record, phase=phase, expected=expected, synthetic=True)

    def test_r3_contract_is_valid_and_preserves_r2_hard_gates(self) -> None:
        self.assertEqual(r3.validate_contract(), [])
        self.assertEqual(r2.validate(), [])

    def test_unmerged_r3_candidate_cannot_self_authorize(self) -> None:
        policy = r3.load_json(r3.PROTOCOL_PATH)
        policy["status"] = "CURRENT"
        self.assertTrue(r3.validate_contract(policy))
        active, _ = r3.resolve_effective_protocol(
            None, observations=_live_observations(), repository_owner_id=49422864
        )
        self.assertEqual(active, "R2")

    def test_missing_transition_receipt_keeps_r2_current(self) -> None:
        active, _ = r3.resolve_effective_protocol(
            None, observations=_live_observations(), repository_owner_id=49422864
        )
        self.assertEqual(active, "R2")

    def test_exact_owner_approved_final_main_receipt_can_select_r3(self) -> None:
        active, errors = r3.resolve_effective_protocol(
            _activation_receipt(), observations=_live_observations(), repository_owner_id=49422864
        )
        self.assertEqual((active, errors), ("R3", []))

    def test_protection_bypass_and_preview_parent_drift_keep_r2_current(self) -> None:
        cases = []
        bypass = _live_observations()
        bypass["branch_protection_rules"]["bypass_enabled"] = True
        cases.append((_activation_receipt(), bypass))
        direct_push = _live_observations()
        direct_push["branch_protection_rules"]["direct_main_push_allowed"] = True
        cases.append((_activation_receipt(), direct_push))
        wrong_parents = _activation_receipt()
        wrong_parents["merge_preview_parents"] = ["b" * 40, "a" * 40]
        cases.append((wrong_parents, _live_observations()))
        for receipt, observations in cases:
            active, errors = r3.resolve_effective_protocol(
                receipt, observations=observations, repository_owner_id=49422864
            )
            self.assertEqual(active, "R2")
            self.assertTrue(errors)

    def test_candidate_preflight_does_not_change_effective_policy(self) -> None:
        self.assertEqual(self._validate(_record(), "prepublication", _context()), [])
        active, _ = r3.resolve_effective_protocol(
            None, observations=_live_observations(), repository_owner_id=49422864
        )
        self.assertEqual(active, "R2")

    def test_activation_rejects_stale_remote_sha_owner_or_contract_blob(self) -> None:
        receipt = _activation_receipt()
        stale_observations = _live_observations()
        stale_observations["remote_main_sha"] = "f" * 40
        wrong_owner_observations = _live_observations()
        wrong_owner_observations["repository_owner_id"] = 7
        wrong_blob_observations = _live_observations()
        for observations, owner_id, blob_sha in (
            (stale_observations, 49422864, None),
            (wrong_owner_observations, 7, None),
            (wrong_blob_observations, 49422864, "9" * 40),
        ):
            active, errors = r3.resolve_effective_protocol(
                receipt, observations=observations, repository_owner_id=owner_id, protocol_blob_sha=blob_sha
            )
            self.assertEqual(active, "R2")
            self.assertTrue(errors)

    def test_activation_requires_live_merged_pr_and_owner_review_readback(self) -> None:
        observations = _live_observations()
        observations["pr_merged"] = False
        active, errors = r3.resolve_effective_protocol(
            _activation_receipt(), observations=observations, repository_owner_id=49422864
        )
        self.assertEqual(active, "R2")
        self.assertTrue(errors)

    def test_stable_candidate_preview_and_parent_order_pass(self) -> None:
        self.assertEqual(self._validate(_record(), "prepublication", _context()), [])

    def test_advanced_base_rewritten_head_stale_preview_and_tree_mismatch_fail(self) -> None:
        mutations = (
            ("refs", "base_main_sha", "f" * 40),
            ("pull_request", "head_sha", "f" * 40),
            ("refs", "merge_preview_sha", "f" * 40),
            ("refs", "merge_preview_tree_sha", "f" * 40),
        )
        for section, key, value in mutations:
            record = _record()
            record[section][key] = value
            self.assertTrue(self._validate(record, "prepublication", _context()), key)

    def test_reordered_preview_parents_fail_closed(self) -> None:
        record = _record()
        record["refs"]["merge_preview_parents"] = ["b" * 40, "a" * 40]
        self.assertTrue(self._validate(record, "prepublication", _context()))

    def test_unreviewed_extra_generated_path_fails_closed(self) -> None:
        record = _record()
        record["changed_paths"]["observed_paths"].append("ignition/data/derived-generated.json")
        self.assertTrue(self._validate(record, "prepublication", _context()))

    def test_final_sha_may_differ_from_preview_after_exact_main_verification(self) -> None:
        record = _postpublication_record()
        self.assertNotEqual(record["publication"]["actual_final_main_sha"], record["refs"]["merge_preview_sha"])
        self.assertEqual(self._validate(record, "postpublication", _context()), [])

    def test_record_cannot_override_independent_final_main_observation(self) -> None:
        expected = _context()
        expected["remote_main_sha"] = "f" * 40
        self.assertTrue(self._validate(_postpublication_record(), "postpublication", expected))

    def test_divergent_final_tree_parent_or_remote_sha_fails(self) -> None:
        for field, value in (
            ("actual_final_main_tree_sha", "f" * 40),
            ("actual_final_main_parents", ["b" * 40, "a" * 40]),
            ("observed_remote_main_sha", "f" * 40),
        ):
            record = _postpublication_record()
            record["publication"][field] = value
            self.assertTrue(self._validate(record, "postpublication", _context()), field)

    def test_postpublication_checks_and_projection_must_bind_actual_final_sha(self) -> None:
        for mutation in ("check_sha", "projection_sha", "generated_path"):
            record = _postpublication_record()
            publication = record["publication"]
            if mutation == "check_sha":
                publication["postpublication_checks"][0]["sha"] = "f" * 40
            elif mutation == "projection_sha":
                publication["projection_check"]["source_sha"] = "f" * 40
            else:
                publication["projection_check"]["unexpected_changed_paths"].append("ignition/generated/stale.json")
            self.assertTrue(self._validate(record, "postpublication", _context()), mutation)

    def test_failed_or_skipped_check_and_missing_suite_receipt_fail(self) -> None:
        record = _record()
        record["candidate_checks"][0]["conclusion"] = "skipped"
        self.assertTrue(self._validate(record, "prepublication", _context()))
        record = _record()
        record["canonical_full_suite_receipts"].pop()
        self.assertTrue(self._validate(record, "prepublication", _context()))

    def test_historical_task135_receipt_cannot_be_replayed_as_current(self) -> None:
        record = _record()
        record["canonical_full_suite_receipts"][0]["task_id"] = "IGNITION-20260822-135"
        errors = self._validate(record, "prepublication", _context())
        self.assertTrue(any("current authorized task" in error for error in errors))

    def test_squash_rebase_unknown_protection_missing_review_and_fake_owner_fail(self) -> None:
        mutations = (
            ("merge_method", "SQUASH"),
            ("merge_method", "REBASE"),
            ("protection_status", "UNKNOWN"),
            ("bypass", True),
            ("owner_id", 7),
            ("owner_approval", False),
        )
        for mutation, value in mutations:
            record = _record()
            if mutation == "merge_method":
                record[mutation] = value
            elif mutation == "owner_approval":
                record["owner_approval"]["approved"] = value
            elif mutation == "protection_status":
                record["branch_protection"]["status"] = value
            elif mutation == "bypass":
                record["branch_protection"]["bypass_enabled"] = value
            else:
                record["owner_approval"]["owner_actor_id"] = value
            self.assertTrue(self._validate(record, "prepublication", _context()), mutation)


if __name__ == "__main__":
    unittest.main()
