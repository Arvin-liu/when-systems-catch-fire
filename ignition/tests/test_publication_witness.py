from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from tools import build_publication_witness as witness


class PublicationWitnessTests(unittest.TestCase):
    @staticmethod
    def fake_git(sha: str):
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

    def gates(self) -> dict[str, str]:
        return {
            "post_publication_validator": "PASS",
            "current_facts": "PASS",
            "current_snapshot": "PASS",
            "current_surface_compiler": "PASS",
            "typed_semantic_gate": "PASS",
            "task_lineage": "PASS",
            "current_state_sync": "PASS",
            "clean_worktree": "PASS",
        }

    def kwargs(self, sha: str) -> dict[str, object]:
        return {
            "task_id": "IGNITION-20260822-133",
            "formal_result_task_id": "IGNITION-20260822-133",
            "subject_repository": "Arvin-liu/when-systems-catch-fire",
            "candidate_sha": sha,
            "fresh_clone_head_sha": sha,
            "fresh_clone_branch": "main",
            "fresh_clone_clean": True,
            "semantic_gates": self.gates(),
            "receipt_ref": "agent-results/IGNITION-20260822-133-publication-witness.json",
            "observed_at": "2026-08-21T15:00:00+00:00",
        }

    def test_witness_is_schema_valid_and_observation_scoped(self) -> None:
        sha = "a" * 40
        with patch.object(witness, "git", side_effect=self.fake_git(sha)):
            document = witness.build_witness(**self.kwargs(sha))
        self.assertEqual(witness.validate_witness(document), [])
        self.assertTrue(document["equality"]["exact_match"])
        self.assertEqual(document["witness"]["scope"], "OBSERVATION_TIME_ONLY")
        self.assertFalse(document["witness"]["credentials_included"])
        self.assertTrue(document["task_binding"]["exact_match"])
        self.assertEqual(document["task_binding"]["latest_architecture_changing_task"], "IGNITION-20260821-129")

    def test_witness_rejects_remote_mismatch_before_emission(self) -> None:
        candidate = "a" * 40
        remote = "b" * 40
        with patch.object(witness, "git", side_effect=self.fake_git(remote)):
            with self.assertRaises(witness.WitnessBuildError):
                witness.build_witness(**self.kwargs(candidate))

    def test_schema_rejects_forged_exact_match(self) -> None:
        sha = "a" * 40
        with patch.object(witness, "git", side_effect=self.fake_git(sha)):
            document = witness.build_witness(**self.kwargs(sha))
        forged = copy.deepcopy(document)
        forged["equality"]["exact_match"] = False
        self.assertTrue(witness.validate_witness(forged))

    def test_task_binding_rejects_a_mismatched_formal_result(self) -> None:
        sha = "a" * 40
        with patch.object(witness, "git", side_effect=self.fake_git(sha)):
            document = witness.build_witness(**self.kwargs(sha))
        forged = copy.deepcopy(document)
        forged["task_binding"]["formal_result_task_id"] = "IGNITION-20260821-131"
        forged["task_binding"]["exact_match"] = False
        errors = witness.validate_witness(forged)
        self.assertTrue(any("formal_result_task_id" in error for error in errors))
        self.assertTrue(any("exact_match" in error for error in errors))

    def test_schema_rejects_non_pass_semantic_gate(self) -> None:
        sha = "a" * 40
        with patch.object(witness, "git", side_effect=self.fake_git(sha)):
            document = witness.build_witness(**self.kwargs(sha))
        forged = copy.deepcopy(document)
        forged["current_semantic_gates"]["current_state_sync"] = "FAIL"
        self.assertTrue(witness.validate_witness(forged))

    def test_followup_remote_move_marks_witness_stale(self) -> None:
        sha = "a" * 40
        later = "b" * 40
        with patch.object(witness, "git", side_effect=self.fake_git(sha)):
            document = witness.build_witness(**self.kwargs(sha))
        self.assertEqual(witness.classify_followup_remote_observation(document, later), "STALE_OBSERVATION")
        self.assertEqual(witness.classify_followup_remote_observation(document, sha), "VALID_AT_OBSERVATION_TIME")

    def test_dirty_fresh_clone_cannot_produce_witness(self) -> None:
        sha = "a" * 40
        arguments = self.kwargs(sha)
        arguments["fresh_clone_clean"] = False
        with patch.object(witness, "git", side_effect=self.fake_git(sha)):
            with self.assertRaises(witness.WitnessBuildError):
                witness.build_witness(**arguments)


if __name__ == "__main__":
    unittest.main()
