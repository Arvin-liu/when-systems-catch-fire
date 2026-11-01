from __future__ import annotations

import copy
import hashlib
import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from tools.operations.route_component_validation import MAP_PATH, digest_json, load_json
from tools.operations.run_component_validation_targets import CHECKOUT_ROOT, collect_registered_test_ids
from tools.operations.verify_component_validation_evidence import RoutingBlocked, verify_evidence
from tools.operations.write_final_main_witness import create_witness


class ComponentValidationEvidenceTest(unittest.TestCase):
    base_sha = "1" * 40
    head_sha = "2" * 40
    validation_sha = "3" * 40

    @classmethod
    def setUpClass(cls):
        cls.validation_map = load_json(MAP_PATH)
        cls.validation_sha = subprocess.run(
            ["git", "-C", str(CHECKOUT_ROOT), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    def make_evidence(self):
        target_id = "g_history_remediation_contract"
        target = next(item for item in self.validation_map["targets"] if item["target_id"] == target_id)
        modules = target["modules"]
        previous_tests = {
            name: module for name, module in sys.modules.items()
            if name == "tests" or name.startswith("tests.")
        }
        for name in previous_tests:
            sys.modules.pop(name, None)
        with tempfile.TemporaryDirectory(prefix="component-validation-foreign-tests-") as temporary:
            foreign_root = Path(temporary)
            foreign_tests = foreign_root / "tests"
            foreign_tests.mkdir()
            (foreign_tests / "__init__.py").write_text("\"\"\"Foreign collision fixture.\"\"\"\n", encoding="utf-8")
            (foreign_tests / "test_history_remediation_contract.py").write_text(
                "\"\"\"Wrong-origin test module fixture.\"\"\"\n", encoding="utf-8",
            )
            sys.path.insert(0, str(foreign_root))
            try:
                collision = importlib.import_module("tests")
                if Path(collision.__file__).resolve() != (foreign_tests / "__init__.py").resolve():
                    raise AssertionError("foreign test-package collision fixture did not load")
                test_ids = collect_registered_test_ids(
                    modules, repo_root=CHECKOUT_ROOT, import_roots=target.get("import_roots", []),
                    validation_sha=self.validation_sha,
                )
            finally:
                sys.path.remove(str(foreign_root))
                for name in tuple(sys.modules):
                    if name == "tests" or name.startswith("tests."):
                        sys.modules.pop(name, None)
                sys.modules.update(previous_tests)
        report_lines = [f"{test_id.rsplit('.', 1)[-1]} ({test_id}) ... ok" for test_id in test_ids]
        test_word = "test" if len(test_ids) == 1 else "tests"
        test_report = "\n".join(report_lines) + f"\n\nRan {len(test_ids)} {test_word} in 0.001s\n\nOK\n"
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
                    "modules": modules,
                    "tests_run": len(test_ids),
                    "tests_executed": len(test_ids),
                    "failures": 0,
                    "errors": 0,
                    "skipped": 0,
                    "expected_failures": [],
                    "unexpected_successes": [],
                    "test_outcomes": [{"test": test_id, "status": "passed"} for test_id in test_ids],
                    "test_report": test_report,
                    "test_report_sha256": hashlib.sha256(test_report.encode("utf-8")).hexdigest(),
                    "test_report_bytes": len(test_report.encode("utf-8")),
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

    def test_outcome_must_belong_to_a_selected_registered_module(self):
        plan, receipt = self.make_evidence()
        receipt["target_results"][0]["tests"]["test_outcomes"][0]["test"] = "fixture.test_passes"
        self.rehash_receipt(receipt)
        with self.assertRaisesRegex(RoutingBlocked, "test results are incomplete"):
            verify_evidence(
                plan, receipt, expected_validation_sha=self.validation_sha,
                expected_mode="TARGETED", validation_map=self.validation_map,
            )

    def test_nonexistent_test_id_with_registered_module_prefix_is_rejected(self):
        plan, receipt = self.make_evidence()
        tests = receipt["target_results"][0]["tests"]
        module = tests["modules"][0]
        fake_id = f"{module}.Fixture.test_passes"
        report = f"test_passes ({fake_id}) ... ok\n\nRan 1 test in 0.001s\n\nOK\n"
        tests.update({
            "tests_run": 1,
            "tests_executed": 1,
            "test_outcomes": [{"test": fake_id, "status": "passed"}],
            "test_report": report,
            "test_report_sha256": hashlib.sha256(report.encode("utf-8")).hexdigest(),
            "test_report_bytes": len(report.encode("utf-8")),
        })
        self.rehash_receipt(receipt)
        with self.assertRaisesRegex(RoutingBlocked, "do not match the registered test collection"):
            verify_evidence(
                plan, receipt, expected_validation_sha=self.validation_sha,
                expected_mode="TARGETED", validation_map=self.validation_map,
            )

    def test_duplicate_test_outcomes_are_rejected(self):
        plan, receipt = self.make_evidence()
        tests = receipt["target_results"][0]["tests"]
        tests["tests_run"] = 2
        tests["tests_executed"] = 2
        tests["test_outcomes"] = [tests["test_outcomes"][0], copy.deepcopy(tests["test_outcomes"][0])]
        self.rehash_receipt(receipt)
        with self.assertRaisesRegex(RoutingBlocked, "test results are incomplete"):
            verify_evidence(
                plan, receipt, expected_validation_sha=self.validation_sha,
                expected_mode="TARGETED", validation_map=self.validation_map,
            )

    def test_test_report_must_match_its_recorded_digest_and_length(self):
        plan, receipt = self.make_evidence()
        receipt["target_results"][0]["tests"]["test_report"] += "tampered\n"
        self.rehash_receipt(receipt)
        with self.assertRaisesRegex(RoutingBlocked, "test results are incomplete"):
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
        test_module = repo / "ignition/tests/test_history_remediation_contract.py"
        test_module.parent.mkdir(parents=True)
        (test_module.parent / "__init__.py").write_text("", encoding="utf-8")
        test_module.write_text(
            "import unittest\n"
            "class HistoryRemediationContractTest(unittest.TestCase):\n"
            "    def test_remediation_entries_match_their_schema_without_rewriting_history(self): pass\n"
            "    def test_summary_is_derived_from_remediation_evidence(self): pass\n",
            encoding="utf-8",
        )
        state = repo / "state.txt"
        state.write_text("before\n", encoding="utf-8")
        self._git(repo, "add", ".")
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

    def _full_only_plan(self, before, final_sha, validation_map=None):
        validation_map = validation_map or self.validation_map
        plan = {
            "schema_version": "1.0.0",
            "mode": "FULL",
            "source": {"base_sha": before, "head_sha": final_sha, "validation_sha": final_sha},
            "validation_map_sha256": digest_json(validation_map),
            "selected_target_ids": [],
            "affected_component_closure": ["foundation"],
            "full_regression_reasons": [{
                "kind": "component_requires_full_regression",
                "component_id": "foundation",
            }],
        }
        plan["plan_sha256"] = digest_json(plan)
        return plan

    def test_final_main_witness_binds_full_only_plan_and_successful_regression(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            repo = parent / "repo"
            repo.mkdir()
            before, final_sha = self._two_commit_repository(repo)
            evidence_dir = parent / "evidence"
            evidence_dir.mkdir()
            validation_map = {"components": [{
                "component_id": "foundation", "requires_full_regression": True, "validation_targets": [],
            }]}
            plan = self._full_only_plan(before, final_sha, validation_map)
            plan_path = evidence_dir / "component-validation-plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            output_dir = parent / "out"
            with (
                patch("tools.operations.write_final_main_witness.load_json", return_value=validation_map),
                patch("tools.operations.write_final_main_witness.build_exact_plan", return_value=plan),
            ):
                witness = create_witness(
                    repo_root=repo, evidence_dir=evidence_dir, output_dir=output_dir,
                    expected_sha=final_sha, event_before=before, event_name="push",
                    event_ref="refs/heads/main", mode="FULL", route_result="success",
                    validate_result="success", full_result="success", run_id="14",
                    run_attempt="1", remote_main_sha=final_sha,
                )
            self.assertEqual(witness["validation_evidence"]["mode"], "FULL")
            self.assertEqual(witness["validation_evidence"]["selected_target_ids"], [])
            self.assertIsNone(witness["validation_evidence"]["receipt_sha256"])
            self.assertEqual(witness["validation_evidence"]["plan_sha256"], plan["plan_sha256"])
            self.assertEqual(witness["validation_evidence_files"], ["component-validation-plan.json"])
            self.assertTrue((output_dir / "component-validation-plan.json").is_file())

    def test_final_main_witness_rejects_full_only_plan_without_reviewed_reason(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            repo = parent / "repo"
            repo.mkdir()
            before, final_sha = self._two_commit_repository(repo)
            evidence_dir = parent / "evidence"
            evidence_dir.mkdir()
            validation_map = {"components": [{
                "component_id": "foundation", "requires_full_regression": True, "validation_targets": [],
            }]}
            plan = self._full_only_plan(before, final_sha, validation_map)
            plan["full_regression_reasons"] = []
            plan.pop("plan_sha256")
            plan["plan_sha256"] = digest_json(plan)
            (evidence_dir / "component-validation-plan.json").write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaisesRegex(RoutingBlocked, "reviewed full-regression cause"):
                with (
                    patch("tools.operations.write_final_main_witness.load_json", return_value=validation_map),
                    patch("tools.operations.write_final_main_witness.build_exact_plan", return_value=plan),
                ):
                    create_witness(
                        repo_root=repo, evidence_dir=evidence_dir, output_dir=parent / "out",
                        expected_sha=final_sha, event_before=before, event_name="push",
                        event_ref="refs/heads/main", mode="FULL", route_result="success",
                        validate_result="success", full_result="success", run_id="15",
                        run_attempt="1", remote_main_sha=final_sha,
                    )

    def test_final_main_witness_rejects_full_only_plan_bound_to_another_head(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            repo = parent / "repo"
            repo.mkdir()
            before, final_sha = self._two_commit_repository(repo)
            evidence_dir = parent / "evidence"
            evidence_dir.mkdir()
            validation_map = {"components": [{
                "component_id": "foundation", "requires_full_regression": True, "validation_targets": [],
            }]}
            plan = self._full_only_plan(before, final_sha, validation_map)
            plan["source"]["validation_sha"] = "4" * 40
            plan.pop("plan_sha256")
            plan["plan_sha256"] = digest_json(plan)
            (evidence_dir / "component-validation-plan.json").write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaisesRegex(RoutingBlocked, "reviewed full-regression cause"):
                with (
                    patch("tools.operations.write_final_main_witness.load_json", return_value=validation_map),
                    patch("tools.operations.write_final_main_witness.build_exact_plan", return_value=plan),
                ):
                    create_witness(
                        repo_root=repo, evidence_dir=evidence_dir, output_dir=parent / "out",
                        expected_sha=final_sha, event_before=before, event_name="push",
                        event_ref="refs/heads/main", mode="FULL", route_result="success",
                        validate_result="success", full_result="success", run_id="16",
                        run_attempt="1", remote_main_sha=final_sha,
                    )

    def test_final_main_witness_rejects_full_only_plan_that_omits_affected_targets(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            repo = parent / "repo"
            repo.mkdir()
            before, final_sha = self._two_commit_repository(repo)
            evidence_dir = parent / "evidence"
            evidence_dir.mkdir()
            plan = self._full_only_plan(before, final_sha)
            (evidence_dir / "component-validation-plan.json").write_text(json.dumps(plan), encoding="utf-8")
            expected_plan = copy.deepcopy(plan)
            expected_plan["selected_target_ids"] = ["o_human_result_consumers"]
            with patch("tools.operations.write_final_main_witness.build_exact_plan", return_value=expected_plan):
                with self.assertRaisesRegex(RoutingBlocked, "differs from the exact main-push impact plan"):
                    create_witness(
                        repo_root=repo, evidence_dir=evidence_dir, output_dir=parent / "out",
                        expected_sha=final_sha, event_before=before, event_name="push",
                        event_ref="refs/heads/main", mode="FULL", route_result="success",
                        validate_result="success", full_result="success", run_id="17",
                        run_attempt="1", remote_main_sha=final_sha,
                    )

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
