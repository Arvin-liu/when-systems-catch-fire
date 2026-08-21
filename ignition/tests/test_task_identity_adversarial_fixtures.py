from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from tools import advance_current_task as advancement
from tools import build_current_snapshot
from tools import build_publication_witness as witness
from tools import validate_current_task_lineage as task_lineage
from tools import validate_post_publication_current as checker
from tools import validate_release_candidate_task_identity as gate


class TaskIdentityAdversarialFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = checker.load_json(
            checker.ROOT / "data/operations/iterations/132/fixtures/release-task-identity-negative-fixtures-r1.json"
        )

    def setUp(self) -> None:
        self.contract = gate.load_json(gate.CONTRACT_PATH)
        self.lineage = gate.load_json(gate.LINEAGE_PATH)
        self.lifecycle = gate.load_json(gate.LIFECYCLE_PATH)
        self.snapshot = gate.load_json(gate.SNAPSHOT_PATH)
        self.progress = gate.load_progress()
        self.surface_documents = {
            surface["path"]: (gate.REPO_ROOT / surface["path"]).read_text(encoding="utf-8")
            for surface in gate.current_surface_compiler.load_json(gate.current_surface_compiler.CONTRACT_PATH)["surfaces"]
        }

    def candidate_gate(self, mutation: str) -> list[str]:
        contract = copy.deepcopy(self.contract)
        lineage = copy.deepcopy(self.lineage)
        lifecycle = copy.deepcopy(self.lifecycle)
        snapshot = copy.deepcopy(self.snapshot)
        surfaces = dict(self.surface_documents)
        if mutation == "lineage_current_task_131":
            lineage["current_task"]["task_id"] = "IGNITION-20260821-131"
        elif mutation == "lifecycle_task_131":
            lifecycle["task_id"] = "IGNITION-20260821-131"
        elif mutation == "snapshot_current_task_131":
            snapshot["current_task"]["task_id"] = "IGNITION-20260821-131"
        elif mutation == "lifecycle_architecture_task_132":
            lifecycle["latest_architecture_changing_task"] = gate.EXPECTED_TASK_ID
        elif mutation == "replace_current_task_in_surface":
            path = next(iter(surfaces))
            surfaces[path] = surfaces[path].replace(gate.EXPECTED_TASK_ID, "IGNITION-20260821-131", 1)
        else:
            raise AssertionError(mutation)
        return gate.validate_documents(
            contract=contract,
            lineage=lineage,
            lifecycle=lifecycle,
            snapshot=snapshot,
            progress=self.progress,
            observed_branch=self.contract["expected_task_branch"],
            surface_documents=surfaces,
        )

    @staticmethod
    def witness_kwargs(sha: str) -> dict[str, object]:
        return {
            "task_id": "IGNITION-20260822-132",
            "formal_result_task_id": "IGNITION-20260822-132",
            "subject_repository": "Arvin-liu/when-systems-catch-fire",
            "candidate_sha": sha,
            "fresh_clone_head_sha": sha,
            "fresh_clone_branch": "main",
            "fresh_clone_clean": True,
            "semantic_gates": {
                "post_publication_validator": "PASS",
                "current_facts": "PASS",
                "current_snapshot": "PASS",
                "current_surface_compiler": "PASS",
                "typed_semantic_gate": "PASS",
                "task_lineage": "PASS",
                "current_state_sync": "PASS",
                "clean_worktree": "PASS",
            },
            "receipt_ref": "agent-results/IGNITION-20260822-132-publication-witness.json",
            "observed_at": "2026-08-22T00:00:00+00:00",
        }

    def test_all_fixture_cases_have_expected_result_and_reason(self) -> None:
        self.assertEqual(len(self.fixture["cases"]), 14)
        for case in self.fixture["cases"]:
            with self.subTest(case_id=case["case_id"]):
                expected_status = case["expected_status"]
                reason = case["reason_code"]
                kind = case["kind"]
                mutation = case["mutation"]
                if kind == "candidate_gate":
                    errors = self.candidate_gate(mutation)
                    self.assertEqual(expected_status, "FAIL")
                    self.assertTrue(any(reason in error for error in errors), errors)
                elif case["case_id"] == "witness-131-sha-132-candidate":
                    sha = "a" * 40
                    with patch.object(witness, "git", side_effect=witness_test_git(sha)):
                        document = witness.build_witness(**self.witness_kwargs(sha))
                    document["task_id"] = "IGNITION-20260821-131"
                    document["task_binding"]["exact_match"] = False
                    errors = witness.validate_witness(document)
                    self.assertEqual(expected_status, "FAIL")
                    self.assertTrue(any(reason in error for error in errors), errors)
                elif case["case_id"] == "remote-sha-match-task-identity-mismatch":
                    sha = "a" * 40
                    with patch.object(checker, "git", side_effect=checker_test_git(sha, sha)):
                        result = checker.run_checks(
                            post_publication=True,
                            expected_sha=sha,
                            expected_task_id="IGNITION-20260821-131",
                            formal_result_task_id="IGNITION-20260821-131",
                        )
                    self.assertEqual(result["result"], expected_status, result["errors"])
                    self.assertTrue(any(reason in error for error in result["errors"]), result["errors"])
                elif case["case_id"] == "task-id-rollback":
                    backward = copy.deepcopy(self.contract)
                    backward["task_id"] = "IGNITION-20260821-131"
                    backward["identity_expectations"]["current_formal_task"] = "IGNITION-20260821-131"
                    with self.assertRaises(advancement.AdvancementError):
                        advancement.advance_document(self.lineage, backward)
                elif case["case_id"] == "unknown-task-without-contract":
                    unknown = copy.deepcopy(self.contract)
                    unknown["task_id"] = "IGNITION-20260822-999"
                    unknown["identity_expectations"]["current_formal_task"] = "IGNITION-20260822-999"
                    with self.assertRaises(advancement.AdvancementError):
                        advancement.advance_document(self.lineage, unknown)
                elif case["case_id"] == "historical-task-131-document-is-legal":
                    historical_path = gate.REPO_ROOT / "ignition/data/operations/iterations/131/step11-final-publication-contract.json"
                    self.assertTrue(historical_path.is_file())
                    self.assertIn("IGNITION-20260821-131", historical_path.read_text(encoding="utf-8"))
                    self.assertEqual(gate.validate_documents(
                        contract=self.contract,
                        lineage=self.lineage,
                        lifecycle=self.lifecycle,
                        snapshot=self.snapshot,
                        progress=self.progress,
                        observed_branch=self.contract["expected_task_branch"],
                        surface_documents=self.surface_documents,
                    ), [])
                elif case["case_id"] == "publication-ref-unreachable":
                    with patch.object(checker, "git", side_effect=unreachable_git):
                        result = checker.run_checks(post_publication=True, expected_sha="a" * 40)
                    self.assertEqual(result["result"], expected_status, result["errors"])
                    self.assertTrue(any("fresh fetch of origin main failed" in error for error in result["errors"]))
                elif case["case_id"] == "publication-witness-missing":
                    witness_path = gate.REPO_ROOT / "ignition/agent-results/IGNITION-20260822-132-publication-witness.json"
                    self.assertFalse(witness_path.exists())
                elif case["case_id"] == "owner-epistemic-authority-promotion":
                    promoted = copy.deepcopy(self.lineage)
                    promoted["current_state"]["epistemically_accepted"] = 1
                    errors = task_lineage.validate(promoted)
                    self.assertEqual(expected_status, "FAIL")
                    self.assertTrue(any(case["reason_code"] in error for error in errors), errors)
                elif case["case_id"] == "same-task-advancement-rerun":
                    updated, changed = advancement.advance_document(self.lineage, self.contract)
                    self.assertEqual(expected_status, "PASS")
                    self.assertFalse(changed)
                    self.assertEqual(updated, self.lineage)
                else:
                    raise AssertionError(case["case_id"])


def witness_test_git(sha: str):
    def run(*args: str) -> str:
        if args == ("remote",):
            return "origin"
        if args and args[0] == "fetch":
            return ""
        if args[:2] == ("ls-remote", "origin"):
            return f"{sha}\trefs/heads/main"
        if args == ("branch", "--show-current"):
            return "main"
        if args == ("rev-parse", "HEAD"):
            return sha
        if args[:1] == ("status",):
            return ""
        raise AssertionError(args)

    return run


def checker_test_git(head: str, remote: str):
    def run(*args: str) -> str:
        if args == ("remote",):
            return "origin"
        if args and args[0] == "fetch":
            return ""
        if args[:2] == ("ls-remote", "origin"):
            return f"{remote}\trefs/heads/main"
        if args == ("branch", "--show-current"):
            return "main"
        if args == ("rev-parse", "HEAD"):
            return head
        if args[:1] == ("status",):
            return ""
        raise AssertionError(args)

    return run


def unreachable_git(*args: str) -> str:
    if args == ("remote",):
        return "origin"
    if args and args[0] in {"fetch", "ls-remote"}:
        raise checker.GitCommandError("git command failed: remote observation unavailable")
    if args == ("branch", "--show-current"):
        return "main"
    if args == ("rev-parse", "HEAD"):
        return "a" * 40
    if args[:1] == ("status",):
        return ""
    raise AssertionError(args)


if __name__ == "__main__":
    unittest.main()
