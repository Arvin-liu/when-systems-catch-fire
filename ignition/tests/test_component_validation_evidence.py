from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.operations.route_component_validation import MAP_PATH, digest_json, load_json
from tools.operations.verify_component_validation_evidence import RoutingBlocked, verify_evidence
from tools.operations.write_final_main_witness import create_witness


class ComponentValidationEvidenceTest(unittest.TestCase):
    base_sha = "1" * 40
    head_sha = "2" * 40
    validation_sha = "3" * 40

    @classmethod
    def setUpClass(cls):
        cls.validation_map = load_json(MAP_PATH)

    def make_evidence(self):
        target_id = "g_history_remediation_contract"
        plan = {
            "schema_version": "1.0.0",
            "mode": "TARGETED",
            "source": {
                "base_sha": self.base_sha,
                "head_sha": self.head_sha,
                "validation_sha": self.validation_sha,
            },
            "validation_map_sha256": digest_json(self.validation_map),
            "selected_target_ids": [target_id],
        }
        plan["plan_sha256"] = digest_json(plan)
        receipt = {
            "schema_version": "1.0.0",
            "head_sha": self.head_sha,
            "base_sha": self.base_sha,
            "validation_sha": self.validation_sha,
            "python_version": "3.12.0",
            "plan_sha256": plan["plan_sha256"],
            "validation_map_sha256": plan["validation_map_sha256"],
            "target_results": [{
                "target_id": target_id,
                "domain": "G",
                "successful": True,
                "tests": {
                    "modules": self.validation_map["targets"][
                        next(i for i, item in enumerate(self.validation_map["targets"]) if item["target_id"] == target_id)
                    ]["modules"],
                    "tests_run": 1,
                    "tests_executed": 1,
                    "failures": 0,
                    "errors": 0,
                    "skipped": 0,
                    "expected_failures": [],
                    "unexpected_successes": [],
                    "test_outcomes": [{"test": "fixture.test_passes", "status": "passed"}],
                    "test_report_sha256": "a" * 64,
                    "test_report_bytes": 1,
                    "successful": True,
                    "status": "PASSED",
                },
                "commands": [],
            }],
            "claim_ceiling": "test fixture",
        }
        receipt["receipt_sha256"] = digest_json(receipt)
        return plan, receipt

    def rehash_receipt(self, receipt):
        receipt.pop("receipt_sha256", None)
        receipt["receipt_sha256"] = digest_json(receipt)

    def test_complete_plan_and_receipt_are_accepted(self):
        plan, receipt = self.make_evidence()
        summary = verify_evidence(
            plan, receipt, expected_validation_sha=self.validation_sha,
            expected_mode="TARGETED", validation_map=self.validation_map,
        )
        self.assertEqual(summary["selected_target_ids"], ["g_history_remediation_contract"])
        self.assertEqual(summary["validation_sha"], self.validation_sha)

    def test_validation_sha_must_match_workflow_commit(self):
        plan, receipt = self.make_evidence()
        with self.assertRaisesRegex(RoutingBlocked, "plan validation SHA"):
            verify_evidence(
                plan, receipt, expected_validation_sha="4" * 40,
                expected_mode="TARGETED", validation_map=self.validation_map,
            )

    def test_tampered_receipt_without_new_digest_is_rejected(self):
        plan, receipt = self.make_evidence()
        receipt["target_results"][0]["successful"] = False
        with self.assertRaisesRegex(RoutingBlocked, "receipt digest"):
            verify_evidence(
                plan, receipt, expected_validation_sha=self.validation_sha,
                expected_mode="TARGETED", validation_map=self.validation_map,
            )

    def test_missing_target_cannot_be_hidden_by_rehashing_receipt(self):
        plan, receipt = self.make_evidence()
        receipt["target_results"] = []
        self.rehash_receipt(receipt)
        with self.assertRaisesRegex(RoutingBlocked, "do not exactly match"):
            verify_evidence(
                plan, receipt, expected_validation_sha=self.validation_sha,
                expected_mode="TARGETED", validation_map=self.validation_map,
            )

    def test_recorded_skip_cannot_be_hidden_by_rehashing_receipt(self):
        plan, receipt = self.make_evidence()
        tests = receipt["target_results"][0]["tests"]
        tests.update({
            "tests_run": 2,
            "tests_executed": 1,
            "skipped": 1,
            "test_outcomes": [
                {"test": "fixture.test_passes", "status": "passed"},
                {"test": "fixture.test_skips", "status": "skipped"},
            ],
        })
        self.rehash_receipt(receipt)
        with self.assertRaisesRegex(RoutingBlocked, "incomplete, skipped"):
            verify_evidence(
                plan, receipt, expected_validation_sha=self.validation_sha,
                expected_mode="TARGETED", validation_map=self.validation_map,
            )

    def test_targeted_success_flag_does_not_override_recorded_test_failure(self):
        plan, receipt = self.make_evidence()
        tests = receipt["target_results"][0]["tests"]
        tests["failures"] = 1
        self.rehash_receipt(receipt)
        with self.assertRaisesRegex(RoutingBlocked, "incomplete, skipped"):
            verify_evidence(
                plan, receipt, expected_validation_sha=self.validation_sha,
                expected_mode="TARGETED", validation_map=self.validation_map,
            )

    def _git(self, repo, *args):
        return subprocess.run(
            ["git", "-C", str(repo), *args], check=True,
            capture_output=True, text=True,
        ).stdout.strip()

    def _two_commit_repository(self, repo):
        self._git(repo, "init", "-q", "-b", "main")
        self._git(repo, "config", "user.name", "Witness Fixture")
        self._git(repo, "config", "user.email", "witness@example.invalid")
        state = repo / "state.txt"
        state.write_text("before\n", encoding="utf-8")
        self._git(repo, "add", "state.txt")
        self._git(repo, "commit", "-m", "before")
        before = self._git(repo, "rev-parse", "HEAD")
        state.write_text("final\n", encoding="utf-8")
        self._git(repo, "commit", "-am", "final")
        return before, self._git(repo, "rev-parse", "HEAD")

    def test_final_main_witness_binds_receipt_and_remote_sha(self):
        plan, receipt = self.make_evidence()
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            repo = parent / "repo"
            repo.mkdir()
            before, final_sha = self._two_commit_repository(repo)
            plan["source"] = {
                "base_sha": before,
                "head_sha": final_sha,
                "validation_sha": final_sha,
            }
            plan.pop("plan_sha256")
            plan["plan_sha256"] = digest_json(plan)
            receipt["base_sha"] = before
            receipt["head_sha"] = final_sha
            receipt["validation_sha"] = final_sha
            receipt["plan_sha256"] = plan["plan_sha256"]
            self.rehash_receipt(receipt)
            evidence_dir = parent / "evidence"
            evidence_dir.mkdir()
            (evidence_dir / "component-validation-plan.json").write_text(json.dumps(plan), encoding="utf-8")
            (evidence_dir / "component-validation-receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
            output_dir = parent / "out"
            witness = create_witness(
                repo_root=repo, evidence_dir=evidence_dir, output_dir=output_dir,
                expected_sha=final_sha, event_before=before, event_name="push",
                event_ref="refs/heads/main", mode="TARGETED", route_result="success",
                validate_result="success", full_result="skipped", run_id="11",
                run_attempt="1", remote_main_sha=final_sha,
            )
            self.assertEqual(witness["final_main_sha"], final_sha)
            self.assertEqual(witness["validation_evidence"]["receipt_sha256"], receipt["receipt_sha256"])
            self.assertTrue((output_dir / "final-main-witness.json").is_file())

    def test_final_main_witness_rejects_remote_ref_moved_to_another_sha(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            before, final_sha = self._two_commit_repository(repo)
            with self.assertRaisesRegex(RoutingBlocked, "remote refs/heads/main moved"):
                create_witness(
                    repo_root=repo, evidence_dir=repo / "missing", output_dir=repo / "out",
                    expected_sha=final_sha, event_before=before, event_name="push",
                    event_ref="refs/heads/main", mode="FULL", route_result="success",
                    validate_result="success", full_result="success", run_id="12",
                    run_attempt="1", remote_main_sha="4" * 40,
                )

    def test_final_main_witness_rejects_non_main_event(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            _, final_sha = self._two_commit_repository(repo)
            with self.assertRaisesRegex(RoutingBlocked, "limited to a push event"):
                create_witness(
                    repo_root=repo, evidence_dir=repo / "missing", output_dir=repo / "out",
                    expected_sha=final_sha, event_before="0" * 40, event_name="pull_request",
                    event_ref="refs/heads/main", mode="FULL", route_result="success",
                    validate_result="success", full_result="success", run_id="13",
                    run_attempt="1", remote_main_sha=final_sha,
                )


if __name__ == "__main__":
    unittest.main()
