from __future__ import annotations

import unittest
import copy
from unittest.mock import patch

from tools import build_current_snapshot

from tools import validate_post_publication_current as checker


class PostPublicationCurrentTests(unittest.TestCase):
    def test_pre_publication_readiness(self) -> None:
        result = checker.run_checks(post_publication=False)
        self.assertEqual(result["result"], "PASS", result["errors"])
        self.assertEqual(result["mode"], "PRE_PUBLICATION")

    @staticmethod
    def _fake_git(*, head: str, remote: str, branch: str = "main", remotes: str = "origin"):
        def run(*args: str) -> str:
            if args == ("remote",):
                return remotes
            if args and args[0] == "fetch":
                return ""
            if args[:2] == ("ls-remote", "origin"):
                return f"{remote}\trefs/heads/main"
            if args == ("branch", "--show-current"):
                return branch
            if args == ("rev-parse", "HEAD"):
                return head
            if args[:1] == ("status",):
                return ""
            raise AssertionError(f"unexpected git probe: {args}")

        return run

    def test_post_publication_requires_expected_remote_and_local_sha_equality(self) -> None:
        candidate = "a" * 40
        remote = "b" * 40
        fake_git = self._fake_git(head=candidate, remote=remote)
        with patch.object(checker, "git", side_effect=fake_git):
            result = checker.run_checks(post_publication=True, expected_sha=candidate)
        self.assertEqual(result["result"], "FAIL")
        self.assertEqual(result["observed_remote_sha"], remote)
        self.assertTrue(any("remote main SHA differs" in error for error in result["errors"]))

    def test_post_publication_passes_when_content_and_all_three_shas_match(self) -> None:
        candidate = "a" * 40
        fake_git = self._fake_git(head=candidate, remote=candidate)
        with patch.object(checker, "git", side_effect=fake_git):
            result = checker.run_checks(post_publication=True, expected_sha=candidate)
        lifecycle = checker.load_json(checker.LIFECYCLE_PATH)
        terminal_current = lifecycle["content_phase"] == "RELEASE_READY" and lifecycle["current_task_terminal"] is True
        self.assertEqual(result["result"], "PASS" if terminal_current else "FAIL", result["errors"])
        if not terminal_current:
            self.assertTrue(any("requires content_phase RELEASE_READY" in error for error in result["errors"]))
            self.assertTrue(any("requires terminal Current task" in error for error in result["errors"]))
        self.assertEqual(result["observed_ref"], "refs/heads/main")
        self.assertEqual(result["head_sha"], result["observed_remote_sha"])

    def test_matching_remote_sha_does_not_override_task_id_mismatch(self) -> None:
        candidate = "a" * 40
        fake_git = self._fake_git(head=candidate, remote=candidate)
        with patch.object(checker, "git", side_effect=fake_git):
            result = checker.run_checks(
                post_publication=True,
                expected_sha=candidate,
                expected_task_id="IGNITION-20260821-131",
                formal_result_task_id="IGNITION-20260821-131",
            )
        self.assertEqual(result["result"], "FAIL")
        task_check = next(row for row in result["checks"] if row["check"] == "task_id_binding")
        self.assertEqual(task_check["result"], "FAIL")
        self.assertTrue(any("TASK_ID_BINDING_MISMATCH" in error for error in task_check["errors"]))

    def test_missing_origin_is_blocked_with_evidence(self) -> None:
        candidate = "a" * 40
        fake_git = self._fake_git(head=candidate, remote=candidate, remotes="")
        with patch.object(checker, "git", side_effect=fake_git):
            result = checker.run_checks(post_publication=True, expected_sha=candidate)
        self.assertEqual(result["result"], "BLOCKED_WITH_EVIDENCE")
        self.assertTrue(any("origin remote is missing" in error for error in result["errors"]))

    def test_detached_head_is_not_an_allowed_post_publication_mode(self) -> None:
        candidate = "a" * 40
        fake_git = self._fake_git(head=candidate, remote=candidate, branch="")
        with patch.object(checker, "git", side_effect=fake_git):
            result = checker.run_checks(post_publication=True, expected_sha=candidate)
        self.assertEqual(result["result"], "FAIL")
        self.assertTrue(any("branch main" in error for error in result["errors"]))

    def test_remote_parser_rejects_missing_or_ambiguous_ref(self) -> None:
        sha = "a" * 40
        self.assertEqual(checker.parse_remote_ref(""), (None, "remote ref observation is ambiguous or missing for refs/heads/main"))
        parsed, error = checker.parse_remote_ref(f"{sha}\trefs/heads/main\n{sha}\trefs/heads/main")
        self.assertIsNone(parsed)
        self.assertIn("ambiguous", error or "")

    def test_step05_negative_matrix_remains_fail_closed(self) -> None:
        fixture_path = checker.ROOT / "data/operations/iterations/131/fixtures/post-publication-negative-fixtures-r1.json"
        cases = checker.load_json(fixture_path)["cases"]
        base_lifecycle = checker.load_json(checker.LIFECYCLE_PATH)
        snapshot = build_current_snapshot.build_snapshot()
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                if case["kind"] == "remote_probe":
                    fake_git = self._fake_git(
                        head=case["head_sha"],
                        remote=case["remote_sha"],
                        branch=case["branch"],
                        remotes=case.get("remotes", "origin"),
                    )
                    with patch.object(checker, "git", side_effect=fake_git):
                        result = checker.run_checks(post_publication=True, expected_sha=case["expected_sha"])
                    self.assertEqual(result["result"], case["expected_status"], result["errors"])
                elif case["kind"] == "static_semantics":
                    candidate = dict(base_lifecycle)
                    candidate.update(case["overrides"])
                    errors = checker._validate_static_publication_semantics(snapshot, candidate)
                    self.assertTrue(errors)
                else:
                    self.assertEqual(case["expected_witness_state"], "STALE_OBSERVATION")
                    self.assertEqual(case["expected_status"], "OBSERVATION_TIME_ONLY")

    def test_step07_task_binding_negative_fixture_remains_fail_closed(self) -> None:
        fixture_path = checker.ROOT / "data/operations/iterations/133/fixtures/post-publication-task-binding-negative-fixtures-r1.json"
        cases = checker.load_json(fixture_path)["cases"]
        contract = checker.load_json(checker.EXECUTION_CONTRACT_PATH)
        lineage = checker.load_json(checker.LINEAGE_PATH)
        lifecycle_record = checker.load_json(checker.LIFECYCLE_PATH)
        snapshot = build_current_snapshot.build_snapshot()
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                if case["kind"] == "remote_sha_and_task_id":
                    fake_git = self._fake_git(head=case["candidate_sha"], remote=case["remote_sha"])
                    with patch.object(checker, "git", side_effect=fake_git):
                        result = checker.run_checks(
                            post_publication=True,
                            expected_sha=case["candidate_sha"],
                            expected_task_id=case["expected_task_id"],
                            formal_result_task_id=case["formal_result_task_id"],
                        )
                    self.assertEqual(result["result"], case["expected_status"], result["errors"])
                    self.assertTrue(any(case["required_error"] in error for error in result["errors"]))
                    continue

                mutated_contract = copy.deepcopy(contract)
                mutated_lineage = copy.deepcopy(lineage)
                mutated_lifecycle = copy.deepcopy(lifecycle_record)
                mutated_snapshot = copy.deepcopy(snapshot)
                expected_task_id = "IGNITION-20260822-133"
                formal_result_task_id = expected_task_id
                field = case["field"]
                value = case["value"]
                if field == "formal_result_task_id":
                    formal_result_task_id = value
                elif field == "canonical_current_formal_task_id":
                    mutated_lineage["task_identity"]["current_formal_task"] = value
                elif field == "lifecycle_task_id":
                    mutated_lifecycle["task_id"] = value
                elif field == "latest_architecture_changing_task":
                    mutated_contract["identity_expectations"]["latest_architecture_changing_task"] = value
                    mutated_lineage["task_identity"]["latest_architecture_changing_task"] = value
                    mutated_lifecycle["latest_architecture_changing_task"] = value
                    mutated_snapshot["latest_architecture_changing_task"] = value
                errors = checker._validate_task_id_binding(
                    expected_task_id=expected_task_id,
                    formal_result_task_id=formal_result_task_id,
                    contract=mutated_contract,
                    lineage_record=mutated_lineage,
                    lifecycle_record=mutated_lifecycle,
                    snapshot=mutated_snapshot,
                )
                self.assertEqual(case["expected_status"], "FAIL")
                self.assertTrue(any(case["required_error"] in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
