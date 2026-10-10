"""Synthetic, source-independent acceptance controls for V1 G1 preflight."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_runtime.steering import GoalRecord
from research_os_v1.g1_goal_intake.preflight import (
    REQUEST_SCHEMA,
    _allowlisted_input,
    _new_report_dir,
    evaluate_request,
)


IGNITION = Path(__file__).resolve().parents[1]
FIXTURE = IGNITION / "research_os_v1/g1_goal_intake/fixtures/structurally-valid-proposal.json"


def _base() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _evaluate(payload: dict) -> dict:
    return evaluate_request(_bytes(payload))


def _codes(report: dict) -> set[str]:
    return {item["code"] for item in report["findings"]}


class GoalIntakeSyntheticControls(unittest.TestCase):
    def test_01_valid_fixture_is_proposal_candidate_and_still_requires_owner(self) -> None:
        self.assertEqual(REQUEST_SCHEMA, _base()["schema"])
        report = evaluate_request(FIXTURE.read_bytes())
        self.assertEqual("REQUIRES_OWNER_AUTHORITY", report["preflight_status"])
        self.assertEqual("CANDIDATE_STRUCTURALLY_VALID_PROPOSAL_ONLY", report["structural_outcome"])
        self.assertEqual("UNKNOWN", report["authority"]["trust_roots"])
        self.assertEqual("UNVERIFIED_OFFLINE", report["authority"]["source_currentness"])

    def test_02_exact_raw_bytes_are_hashed_including_whitespace(self) -> None:
        first = FIXTURE.read_bytes()
        second = first + b" "
        self.assertNotEqual(evaluate_request(first)["raw_request_sha256"], evaluate_request(second)["raw_request_sha256"])
        self.assertEqual(hashlib.sha256(first).hexdigest(), evaluate_request(first)["raw_request_sha256"])

    def test_03_forged_owner_origin_is_a_claim_not_authentication(self) -> None:
        payload = _base()
        payload["request"]["declared_origin"] = "OWNER_DECLARED"
        report = _evaluate(payload)
        self.assertEqual("REQUIRES_OWNER_AUTHORITY", report["preflight_status"])
        self.assertEqual("NOT_AUTHENTICATED", report["authority"]["owner_identity"])
        self.assertIn("owner_claim_unverified", _codes(report))
        self.assertIn("request_declares_owner_origin", report["authority"]["claims_observed"])

    def test_04_forged_authorized_owner_provenance_is_not_trusted(self) -> None:
        payload = _base()
        for record in (payload["snapshots"]["intent"], payload["snapshots"]["goal"]):
            record["provenance"].update(source_type="OWNER_DECLARED", authorized=True)
        report = _evaluate(payload)
        self.assertEqual("REQUIRES_OWNER_AUTHORITY", report["preflight_status"])
        self.assertIn("goal_snapshot_claims_owner_authority", report["authority"]["claims_observed"])
        self.assertEqual(False, report["effects"]["canonical_records_written"])

    def test_05_unknown_envelope_schema_is_invalid(self) -> None:
        payload = _base()
        payload["schema"] = "other.v9"
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("unsupported_request_schema", _codes(report))

    def test_06_malformed_json_is_invalid(self) -> None:
        report = evaluate_request(b"{not-json")
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("malformed_json", _codes(report))

    def test_07_duplicate_json_keys_are_rejected(self) -> None:
        report = evaluate_request(b'{"schema":"a","schema":"b"}')
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("duplicate_json_key", _codes(report))

    def test_08_invalid_utf8_is_rejected(self) -> None:
        report = evaluate_request(b"\xff")
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("malformed_json", _codes(report))

    def test_09_oversized_input_is_rejected(self) -> None:
        report = evaluate_request(b" " * 1_000_001)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("input_exceeds_size_limit", _codes(report))

    def test_10_missing_intent_binding_is_unbound(self) -> None:
        payload = _base()
        del payload["bindings"]["intent_id"]
        report = _evaluate(payload)
        self.assertEqual("BLOCKED_STALE_OR_UNBOUND", report["preflight_status"])
        self.assertIn("stable_identifier_missing_or_invalid", _codes(report))

    def test_11_mismatched_intent_id_is_unbound(self) -> None:
        payload = _base()
        payload["bindings"]["intent_id"] = "intent:other"
        report = _evaluate(payload)
        self.assertEqual("BLOCKED_STALE_OR_UNBOUND", report["preflight_status"])
        self.assertIn("intent_id_mismatch", _codes(report))

    def test_12_stale_goal_version_is_unbound(self) -> None:
        payload = _base()
        payload["bindings"]["goal_version"] = 2
        report = _evaluate(payload)
        self.assertEqual("BLOCKED_STALE_OR_UNBOUND", report["preflight_status"])
        self.assertIn("goal_version_mismatch", _codes(report))

    def test_13_conflicting_declared_objective_digest_is_unbound(self) -> None:
        payload = _base()
        payload["bindings"]["objective_digest"] = "0" * 64
        report = _evaluate(payload)
        self.assertEqual("BLOCKED_STALE_OR_UNBOUND", report["preflight_status"])
        self.assertIn("objective_digest_mismatch", _codes(report))

    def test_14_malformed_objective_digest_is_invalid(self) -> None:
        payload = _base()
        payload["bindings"]["objective_digest"] = "sha256:bad"
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("objective_digest_malformed", _codes(report))

    def test_15_goal_snapshot_digest_must_match_existing_digest_semantics(self) -> None:
        payload = _base()
        payload["snapshots"]["goal"]["objective_digest"] = "0" * 64
        report = _evaluate(payload)
        self.assertEqual("BLOCKED_STALE_OR_UNBOUND", report["preflight_status"])
        self.assertIn("objective_digest_mismatch", _codes(report))

    def test_16_research_question_must_match_bound_goal_statement(self) -> None:
        payload = _base()
        payload["request"]["research_question"] = "A different question"
        report = _evaluate(payload)
        self.assertEqual("BLOCKED_STALE_OR_UNBOUND", report["preflight_status"])
        self.assertIn("research_question_objective_mismatch", _codes(report))

    def test_17_superseded_intent_is_blocked(self) -> None:
        payload = _base()
        payload["snapshots"]["intent"]["supersedes_intent_id"] = "intent:old"
        report = _evaluate(payload)
        self.assertEqual("BLOCKED_STALE_OR_UNBOUND", report["preflight_status"])
        self.assertIn("intent_superseded_lineage_requires_reconciliation", _codes(report))

    def test_18_superseded_goal_is_blocked(self) -> None:
        payload = _base()
        payload["snapshots"]["goal"]["supersedes_goal_id"] = "goal:old"
        report = _evaluate(payload)
        self.assertEqual("BLOCKED_STALE_OR_UNBOUND", report["preflight_status"])
        self.assertIn("goal_superseded_lineage_requires_reconciliation", _codes(report))

    def test_19_missing_completion_contract_is_unbound_not_crash(self) -> None:
        payload = _base()
        payload["snapshots"]["completion_contract"] = None
        report = _evaluate(payload)
        self.assertEqual("BLOCKED_STALE_OR_UNBOUND", report["preflight_status"])
        self.assertIn("completion_contract_missing", _codes(report))

    def test_20_missing_lineage_snapshot_is_unbound_not_generated(self) -> None:
        payload = _base()
        payload["snapshots"]["goal"] = None
        report = _evaluate(payload)
        self.assertEqual("BLOCKED_STALE_OR_UNBOUND", report["preflight_status"])
        self.assertIn("lineage_snapshot_missing", _codes(report))

    def test_21_missing_proposal_run_binding_is_unbound(self) -> None:
        payload = _base()
        del payload["bindings"]["proposal_run_ids"]
        report = _evaluate(payload)
        self.assertEqual("BLOCKED_STALE_OR_UNBOUND", report["preflight_status"])
        self.assertIn("binding_missing", _codes(report))

    def test_22_parent_binding_without_snapshot_is_unbound(self) -> None:
        payload = _base()
        payload["snapshots"]["goal"]["parent_goal_id"] = "goal:parent"
        payload["bindings"]["parent_goal_id"] = "goal:parent"
        payload["bindings"]["parent_goal_version"] = 1
        report = _evaluate(payload)
        self.assertEqual("BLOCKED_STALE_OR_UNBOUND", report["preflight_status"])
        self.assertIn("parent_goal_unbound", _codes(report))

    def test_23_parent_id_mismatch_is_blocked(self) -> None:
        payload = _base()
        parent = copy.deepcopy(payload["snapshots"]["goal"])
        parent.update(goal_id="goal:parent", parent_goal_id=None, supersedes_goal_id=None)
        parent["objective_digest"] = GoalRecord.from_dict(parent).objective_digest()
        payload["snapshots"]["goal"]["parent_goal_id"] = "goal:parent"
        payload["bindings"].update(parent_goal_id="goal:wrong", parent_goal_version=1)
        payload["snapshots"]["parent_goal"] = parent
        report = _evaluate(payload)
        self.assertEqual("BLOCKED_STALE_OR_UNBOUND", report["preflight_status"])
        self.assertIn("parent_goal_id_mismatch", _codes(report))

    def test_24_parent_ancestor_chain_is_blocked_until_bound(self) -> None:
        payload = _base()
        parent = copy.deepcopy(payload["snapshots"]["goal"])
        parent.update(goal_id="goal:parent", parent_goal_id="goal:grandparent", supersedes_goal_id=None)
        parent["objective_digest"] = GoalRecord.from_dict(parent).objective_digest()
        payload["snapshots"]["goal"]["parent_goal_id"] = "goal:parent"
        payload["bindings"].update(parent_goal_id="goal:parent", parent_goal_version=1)
        payload["snapshots"]["parent_goal"] = parent
        report = _evaluate(payload)
        self.assertEqual("BLOCKED_STALE_OR_UNBOUND", report["preflight_status"])
        self.assertIn("parent_ancestor_lineage_unbound", _codes(report))

    def test_25_deliverable_policy_expansion_is_invalid(self) -> None:
        payload = _base()
        payload["request"]["deliverables"] = ["preflight-report.md", "canonical-goal.json"]
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("deliverable_policy_expansion", _codes(report))

    def test_26_source_kind_policy_expansion_is_invalid(self) -> None:
        payload = _base()
        payload["request"]["allowed_source_kinds"].append("NETWORK_PROVIDER")
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("allowed_source_kinds_policy_expansion", _codes(report))

    def test_27_executor_outside_allowlist_is_invalid(self) -> None:
        payload = _base()
        payload["request"]["allowed_executors"] = ["remote-provider"]
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("allowed_executors_policy_expansion", _codes(report))

    def test_28_branch_budget_expansion_is_invalid(self) -> None:
        payload = _base()
        payload["request"]["budget_envelopes"]["branches"] = 4
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("budget_envelope_expansion", _codes(report))

    def test_29_boolean_budget_is_not_an_integer_budget(self) -> None:
        payload = _base()
        payload["request"]["budget_envelopes"]["reviews"] = True
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("positive_integer_required", _codes(report))

    def test_30_claim_ceiling_expansion_is_invalid(self) -> None:
        payload = _base()
        payload["request"]["claim_ceiling"] = "SCIENTIFIC_FINDING"
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("claim_ceiling_expansion_or_mismatch", _codes(report))

    def test_31_weakened_stop_condition_is_invalid(self) -> None:
        payload = _base()
        payload["request"]["stop_conditions"]["stale_or_unbound"] = "OWNER_REVIEW"
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("stop_condition_weakens_inherited_rule", _codes(report))

    def test_32_unknown_stop_condition_is_invalid(self) -> None:
        payload = _base()
        payload["request"]["stop_conditions"]["executor_unavailable"] = "CONTINUE"
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("contradictory_or_unknown_stop_condition", _codes(report))

    def test_33_completion_predicate_loss_is_invalid(self) -> None:
        payload = _base()
        payload["request"]["success_predicates"].pop()
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("completion_predicate_policy_expansion_or_loss", _codes(report))

    def test_34_run_pass_cannot_satisfy_goal_completion(self) -> None:
        payload = _base()
        predicate = "RUN_PASS -> GOAL_COMPLETE"
        payload["request"]["success_predicates"] = [predicate]
        payload["snapshots"]["completion_contract"]["acceptance_predicates"] = [predicate]
        payload["snapshots"]["completion_contract"]["forbidden_shortcuts"] = ["RUN_PASS"]
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("run_pass_cannot_infer_goal_completion", _codes(report))
        self.assertFalse(report["effects"]["completion_decision_evaluated"])

    def test_35_unknown_snapshot_fields_are_invalid(self) -> None:
        payload = _base()
        payload["snapshots"]["goal"]["owner_token"] = "secret"
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("unknown_field", _codes(report))

    def test_36_duplicate_policy_values_are_invalid(self) -> None:
        payload = _base()
        payload["request"]["allowed_executors"].append("local-python")
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("duplicate_list_value", _codes(report))

    def test_37_supplied_drift_projection_reports_objective_mismatch(self) -> None:
        payload = _base()
        payload["request"]["success_predicates"] = ["new_predicate"]
        report = _evaluate(payload)
        self.assertTrue(report["drift_guard"]["evaluated"])
        self.assertEqual("PAUSE_RECONCILE", report["drift_guard"]["outcome"])
        self.assertIn("acceptance_criteria_lost", report["drift_guard"]["reason_codes"])
        self.assertFalse(report["drift_guard"]["memory_conflict_checked"])

    def test_38_binder_projection_is_explicitly_noncanonical(self) -> None:
        report = _evaluate(_base())
        projection = report["episode_binding_projection"]
        self.assertTrue(projection["created"])
        self.assertTrue(projection["projection_only"])
        self.assertFalse(projection["canonical_binding_created"])
        self.assertFalse(report["effects"]["goal_lifecycle_mutated"])

    def test_39_active_owner_goal_is_not_an_adapter_activation(self) -> None:
        payload = _base()
        goal = payload["snapshots"]["goal"]
        goal["provenance"].update(source_type="OWNER_DECLARED", authorized=True)
        goal["status"] = "ACTIVE"
        report = _evaluate(payload)
        self.assertEqual("BLOCKED_STALE_OR_UNBOUND", report["preflight_status"])
        self.assertIn("snapshot_not_proposal_only", _codes(report))
        self.assertEqual("NOT_AUTHENTICATED", report["authority"]["owner_identity"])
        self.assertFalse(report["episode_binding_projection"]["created"])
        self.assertFalse(report["effects"]["goal_lifecycle_mutated"])

    def test_40_missing_schema_in_record_is_invalid(self) -> None:
        payload = _base()
        payload["snapshots"]["intent"]["schema"] = None
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("steering_snapshot_schema_mismatch", _codes(report))

    def test_41_malformed_contract_predicates_are_invalid(self) -> None:
        payload = _base()
        payload["snapshots"]["completion_contract"]["acceptance_predicates"] = "objective_digest_matches"
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("bounded_string_list_required", _codes(report))

    def test_42_report_is_deterministic_for_identical_bytes(self) -> None:
        raw = FIXTURE.read_bytes()
        self.assertEqual(evaluate_request(raw), evaluate_request(raw))

    def test_43_input_path_allowlist_rejects_external_file(self) -> None:
        with tempfile.NamedTemporaryFile() as handle:
            with self.assertRaises(ValueError):
                _allowlisted_input(handle.name)

    def test_44_input_path_allowlist_rejects_fixture_symlink(self) -> None:
        fixture_dir = FIXTURE.parent
        with tempfile.TemporaryDirectory(dir=str(fixture_dir)) as temp_dir:
            link = Path(temp_dir) / "linked.json"
            link.symlink_to(FIXTURE)
            with self.assertRaises(ValueError):
                _allowlisted_input(str(link))

    def test_45_cli_emits_both_reports_from_the_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_dir = Path(temp_dir) / "reports"
            env = dict(os.environ)
            env["PYTHONPATH"] = str(IGNITION)
            result = subprocess.run(
                [sys.executable, "-m", "research_os_v1.g1_goal_intake", "--input", str(FIXTURE), "--report-dir", str(report_dir)],
                cwd=str(IGNITION), env=env, text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            report_bytes = (report_dir / "admission-report.json").read_bytes()
            markdown_bytes = (report_dir / "summary.md").read_bytes()
            report = json.loads(report_bytes.decode("utf-8"))
            self.assertEqual("REQUIRES_OWNER_AUTHORITY", report["preflight_status"])
            self.assertTrue(markdown_bytes.startswith(b"# Offline Goal intake preflight\n"))

    def test_46_matching_parent_snapshot_remains_proposal_only(self) -> None:
        payload = _base()
        parent = copy.deepcopy(payload["snapshots"]["goal"])
        parent.update(goal_id="goal:parent", parent_goal_id=None, supersedes_goal_id=None)
        parent["objective_digest"] = GoalRecord.from_dict(parent).objective_digest()
        payload["snapshots"]["goal"]["parent_goal_id"] = "goal:parent"
        payload["bindings"].update(parent_goal_id="goal:parent", parent_goal_version=1)
        payload["snapshots"]["parent_goal"] = parent
        report = _evaluate(payload)
        self.assertEqual("REQUIRES_OWNER_AUTHORITY", report["preflight_status"])
        self.assertEqual("CANDIDATE_STRUCTURALLY_VALID_PROPOSAL_ONLY", report["structural_outcome"])
        self.assertEqual("goal:parent", report["bindings"]["parent_goal_id_snapshot"])

    def test_47_unhashable_origin_json_value_fails_closed(self) -> None:
        payload = _base()
        payload["request"]["declared_origin"] = ["OWNER_DECLARED"]
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("unknown_declared_origin", _codes(report))
        self.assertNotIn("OWNER_DECLARED", json.dumps(report))

    def test_48_unhashable_stop_value_fails_closed(self) -> None:
        payload = _base()
        payload["request"]["stop_conditions"]["stale_or_unbound"] = {"continue": True}
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("contradictory_or_unknown_stop_condition", _codes(report))

    def test_49_nested_nontext_deliverable_fails_closed(self) -> None:
        payload = _base()
        payload["request"]["deliverables"] = [{"path": "canonical.json"}]
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("bounded_text_required", _codes(report))

    def test_50_prohibited_private_marker_is_not_echoed(self) -> None:
        payload = _base()
        payload["request"]["claim_ceiling"] = "client_secret=synthetic-value"
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertNotIn("client_secret=synthetic-value", json.dumps(report))

    def test_51_report_directory_outside_temp_roots_is_rejected_before_write(self) -> None:
        with self.assertRaises(ValueError):
            _new_report_dir(str(IGNITION / "agent_runtime"))

    def test_52_report_directory_symlink_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            link = Path(temp_dir) / "outside-link"
            link.symlink_to(IGNITION / "agent_runtime", target_is_directory=True)
            with self.assertRaises(ValueError):
                _new_report_dir(str(link / "new-report"))

    def test_53_case_and_separator_variants_of_forbidden_shortcut_fail_closed(self) -> None:
        payload = _base()
        payload["request"]["success_predicates"] = ["run_pass"]
        payload["snapshots"]["completion_contract"]["acceptance_predicates"] = ["run_pass"]
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("forbidden_completion_shortcut", _codes(report))

    def test_54_spaced_and_compact_run_pass_goal_complete_inferences_fail_closed(self) -> None:
        for predicate in ("Run pass -> goal complete", "RUNPASS -> GOAL_COMPLETE"):
            with self.subTest(predicate=predicate):
                payload = _base()
                payload["request"]["success_predicates"] = [predicate]
                payload["snapshots"]["completion_contract"]["acceptance_predicates"] = [predicate]
                report = _evaluate(payload)
                self.assertEqual("INVALID_INPUT", report["preflight_status"])
                self.assertIn("run_pass_cannot_infer_goal_completion", _codes(report))

    def test_55_synchronized_untrusted_contract_cannot_remove_run_pass_invariant(self) -> None:
        payload = _base()
        predicates = ["RUN_PASS", "GOAL_COMPLETE"]
        payload["request"]["success_predicates"] = predicates
        payload["snapshots"]["completion_contract"]["acceptance_predicates"] = predicates
        payload["snapshots"]["completion_contract"]["forbidden_shortcuts"] = ["NEVER_SHORTCUT"]
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("forbidden_completion_shortcut", _codes(report))
        self.assertIn("run_pass_cannot_infer_goal_completion", _codes(report))

    def test_56_run_pass_alone_is_not_a_completion_predicate_without_shortcut_metadata(self) -> None:
        payload = _base()
        payload["request"]["success_predicates"] = ["RUN_PASS"]
        payload["snapshots"]["completion_contract"]["acceptance_predicates"] = ["RUN_PASS"]
        payload["snapshots"]["completion_contract"]["forbidden_shortcuts"] = ["NEVER_SHORTCUT"]
        report = _evaluate(payload)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("forbidden_completion_shortcut", _codes(report))

    def test_57_deeply_nested_json_fails_closed_without_traceback(self) -> None:
        raw = b"[" * 5000 + b"0" + b"]" * 5000
        report = evaluate_request(raw)
        self.assertEqual("INVALID_INPUT", report["preflight_status"])
        self.assertIn("malformed_json", _codes(report))

    def test_58_unicode_confusable_policy_tokens_are_rejected(self) -> None:
        for predicate in ("RUN_P\u0410SS -> GOAL_COMPLETE", "RUN_\uff30\uff21\uff33\uff33 -> GOAL_COMPLETE"):
            with self.subTest(predicate=predicate):
                payload = _base()
                payload["request"]["success_predicates"] = [predicate]
                payload["snapshots"]["completion_contract"]["acceptance_predicates"] = [predicate]
                payload["snapshots"]["completion_contract"]["forbidden_shortcuts"] = ["NEVER_SHORTCUT"]
                report = _evaluate(payload)
                self.assertEqual("INVALID_INPUT", report["preflight_status"])
                self.assertIn("ascii_policy_token_required", _codes(report))


if __name__ == "__main__":
    unittest.main()
