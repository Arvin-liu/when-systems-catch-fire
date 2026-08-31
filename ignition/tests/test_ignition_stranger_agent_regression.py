from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import run_ignition_stranger_agent_regression as regression  # noqa: E402


class IgnitionStrangerAgentRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = regression.run_suite()
        cls.by_id = {row["case_id"]: row for row in cls.report["cases"]}

    def test_all_seven_critical_cases_pass(self) -> None:
        self.assertEqual(tuple(self.by_id), regression.REQUIRED_CASE_IDS)
        self.assertEqual(self.report["status"], "PASS")
        self.assertEqual(self.report["case_count"], 7)
        self.assertEqual(self.report["passed_case_count"], 7)
        self.assertEqual(self.report["failed_case_count"], 0)
        self.assertTrue(all(row["critical"] for row in self.report["cases"]))

    def test_a_note_plus_url_is_read_only_without_git_mutation(self) -> None:
        actual = self.by_id["A_NOTE_URL_DEFAULT_READ_ONLY"]["actual"]
        self.assertEqual(actual["run_mode"], "READ_ONLY_RUN")
        self.assertEqual(actual["decision"], "PROCEED_BOUNDED")
        self.assertFalse(actual["side_effects_authorized"])
        self.assertFalse(actual["git_mutation_attempted"])
        self.assertTrue(actual["unified_output_valid"])

    def test_b_explicit_repository_change_routes_iteration(self) -> None:
        actual = self.by_id["B_EXPLICIT_PROTOCOL_CHANGE_ROUTES_ITERATION"]["actual"]
        self.assertEqual(actual["run_mode"], "REPOSITORY_CHANGE_RUN")
        self.assertEqual(actual["decision"], "PROCEED")
        self.assertTrue(actual["iteration_method_loaded"])
        self.assertFalse(actual["side_effects_authorized"])

    def test_c_input_command_injection_never_enters_router_authority(self) -> None:
        actual = self.by_id["C_INPUT_OBJECT_COMMAND_INJECTION_IS_DATA"]["actual"]
        self.assertEqual(actual["run_mode"], "READ_ONLY_RUN")
        self.assertFalse(actual["input_object_content_used_for_routing"])
        self.assertFalse(actual["repository_mutation_attempted"])

    def test_d_legacy_references_use_current_exact_resolution_only(self) -> None:
        actual = self.by_id["D_LEGACY_D5_T7_CURRENT_RESOLUTION"]["actual"]
        self.assertTrue(actual["all_current_or_fail_closed"])
        self.assertEqual([row["canonical_id"] for row in actual["references"]], ["D5", "T7"])
        self.assertFalse(actual["memory_or_fuzzy_resolution_used"])
        self.assertFalse(actual["historical_file_used_as_identity"])

    def test_e_source_explicit_phrase_is_not_a_candidate(self) -> None:
        actual = self.by_id["E_SOURCE_EXPLICIT_AUTHORITY_HOWL_NOT_DISCOVERY"]["actual"]
        self.assertEqual(actual["input_derived_statements"], ["权力啸叫"])
        self.assertEqual(actual["candidate_new_count"], 0)
        self.assertFalse(actual["source_statement_relabelled_candidate"])
        self.assertEqual(actual["candidate_registry_action"], "NONE")
        self.assertTrue(actual["unified_output_valid"])

    def test_f_owner_deferred_live_operation_stops_without_execution(self) -> None:
        actual = self.by_id["F_OWNER_DEFERRED_LIVE_EXTERNAL_FAILS_CLOSED"]["actual"]
        self.assertEqual(actual["operation_status"], "OWNER_DEFERRED")
        self.assertEqual(actual["decision"], "STOP")
        self.assertEqual(actual["stop_reason"], "CAPABILITY_OWNER_DEFERRED")
        self.assertFalse(actual["external_action_attempted"])
        self.assertTrue(actual["unified_output_valid"])

    def test_g_unregistered_operation_stops_as_unsupported(self) -> None:
        actual = self.by_id["G_UNREGISTERED_OPERATION_FAILS_CLOSED"]["actual"]
        self.assertEqual(actual["operation_status"], "UNREGISTERED")
        self.assertEqual(actual["decision"], "STOP")
        self.assertEqual(actual["stop_reason"], "UNSUPPORTED_OPERATION")
        self.assertTrue(actual["unified_output_valid"])

    def test_suite_exposes_no_effect_events(self) -> None:
        self.assertEqual(self.report["effect_summary"]["effect_event_count"], 0)
        self.assertFalse(self.report["effect_summary"]["repository_mutation_attempted"])
        self.assertFalse(self.report["effect_summary"]["git_mutation_attempted"])
        self.assertFalse(self.report["effect_summary"]["external_action_attempted"])

    def test_any_expected_case_failure_blocks_r1_completion(self) -> None:
        fixture = json.loads(regression.FIXTURE_PATH.read_text(encoding="utf-8"))
        forged = copy.deepcopy(fixture)
        forged["cases"][0]["expected"]["run_mode"] = "REPOSITORY_CHANGE_RUN"
        report = regression.run_suite(forged)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["failed_case_count"], 1)
        self.assertIn("expected 'REPOSITORY_CHANGE_RUN'", report["cases"][0]["errors"][0])

    def test_persisted_receipt_is_exact_recomputation(self) -> None:
        persisted = json.loads(regression.RECEIPT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(persisted, self.report)
        without_hash = dict(persisted)
        receipt_hash = without_hash.pop("receipt_sha256")
        self.assertEqual(receipt_hash, regression._canonical_hash(without_hash))


if __name__ == "__main__":
    unittest.main()
