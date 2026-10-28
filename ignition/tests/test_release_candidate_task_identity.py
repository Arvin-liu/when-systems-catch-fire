from __future__ import annotations

import copy
import unittest

from tools import validate_release_candidate_task_identity as gate


class ReleaseCandidateTaskIdentityTests(unittest.TestCase):
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

    def check(self, **overrides: object) -> list[str]:
        values = {
            "contract": self.contract,
            "lineage": self.lineage,
            "lifecycle": self.lifecycle,
            "snapshot": self.snapshot,
            "progress": self.progress,
            "observed_branch": self.contract["expected_task_branch"],
            "surface_documents": self.surface_documents,
        }
        values.update(overrides)
        return gate.validate_documents(**values)

    def test_current_candidate_identity_passes(self) -> None:
        self.assertEqual(self.check(), [])

    def test_lineage_131_is_rejected(self) -> None:
        lineage = copy.deepcopy(self.lineage)
        lineage["current_task"]["task_id"] = "IGNITION-20260821-131"
        errors = self.check(lineage=lineage)
        self.assertTrue(any("lineage.current_task.task_id" in error for error in errors))

    def test_lifecycle_131_is_rejected(self) -> None:
        lifecycle = copy.deepcopy(self.lifecycle)
        lifecycle["task_id"] = "IGNITION-20260821-131"
        errors = self.check(lifecycle=lifecycle)
        self.assertTrue(any("lifecycle.task_id" in error for error in errors))

    def test_snapshot_131_is_rejected(self) -> None:
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["task_identity"]["current_formal_task"] = "IGNITION-20260821-131"
        errors = self.check(snapshot=snapshot)
        self.assertTrue(any("snapshot.task_identity.current_formal_task" in error for error in errors))

    def test_architecture_changing_task_cannot_be_detached_from_formal(self) -> None:
        lifecycle = copy.deepcopy(self.lifecycle)
        lifecycle["latest_architecture_changing_task"] = "IGNITION-20260825-139"
        errors = self.check(lifecycle=lifecycle)
        self.assertTrue(any("TASK_IDENTITY_MISMATCH:lifecycle.latest_architecture_changing_task" in error for error in errors))

    def test_stale_compiler_output_is_rejected(self) -> None:
        docs = dict(self.surface_documents)
        path = next(iter(docs))
        docs[path] = docs[path].replace(gate.EXPECTED_TASK_ID, "IGNITION-20260821-131", 1)
        errors = self.check(surface_documents=docs)
        self.assertTrue(any("COMPILER_SURFACE_STALE" in error for error in errors))

    def test_result_is_optional_before_final_receipt(self) -> None:
        self.assertEqual(self.check(result_task_id=None, machine_receipt_task_id=None), [])
        errors = self.check(result_task_id=None, machine_receipt_task_id=None, require_result=True)
        self.assertTrue(any("FORMAL_RESULT_TASK_ID_MISSING" in error for error in errors))

    def test_pull_request_head_branch_is_resolved_from_github_metadata(self) -> None:
        branch = gate.resolve_observed_branch({
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_HEAD_REF": self.contract["expected_task_branch"],
            "GITHUB_REF": "refs/pull/264/merge",
            "GITHUB_REF_NAME": "264/merge",
        })
        self.assertEqual(branch, self.contract["expected_task_branch"])
        self.assertEqual(self.check(observed_branch=branch), [])

    def test_pull_request_without_head_ref_fails_closed(self) -> None:
        branch = gate.resolve_observed_branch({
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REF": "refs/pull/264/merge",
            "GITHUB_REF_NAME": "264/merge",
        })
        self.assertEqual(branch, "")
        errors = self.check(observed_branch=branch)
        self.assertTrue(any(error.startswith("TASK_BRANCH_METADATA_MISMATCH:") for error in errors))

    def test_push_branch_is_resolved_from_github_ref(self) -> None:
        branch = gate.resolve_observed_branch({
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_REF": "refs/heads/codex/r3-forward-20261022",
        })
        self.assertEqual(branch, self.contract["expected_task_branch"])


if __name__ == "__main__":
    unittest.main()
