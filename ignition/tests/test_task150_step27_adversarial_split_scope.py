import copy
import json
import unittest

from tools.validate_task150_step21_fresh_standalone_evidence import exact_topology_errors
from tools.validate_task150_step27_adversarial_split_scope import (
    ARTIFACT_PATH,
    CANONICAL_PATH,
    FIXTURE_PATH,
    IR_PATH,
    EXPECTED_CASE_IDS,
    apply_topology_mutation,
    evaluate_case,
    load_json,
    validate,
)


class Task150Step27AdversarialSplitScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = load_json(ARTIFACT_PATH)
        cls.fixture = load_json(FIXTURE_PATH)
        cls.architecture = load_json(CANONICAL_PATH)
        cls.ir = load_json(IR_PATH)
        cls.cases = {case["id"]: case for case in cls.fixture["cases"]}

    def test_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_all_required_adversarial_cases_are_present_in_order(self):
        self.assertEqual(tuple(case["id"] for case in self.fixture["cases"]), EXPECTED_CASE_IDS)
        self.assertEqual(self.document["case_results"], self.fixture["cases"])

    def test_standalone_pass_delta_fail_admits_only_base(self):
        result = evaluate_case(self.cases["standalone_pass_delta_fail"], self.architecture, self.ir)
        self.assertEqual(result["base"], "ADMIT_AS_CURRENT_BOUNDED_CANDIDATE")
        self.assertEqual(result["delta"], "DEFER")

    def test_standalone_fail_delta_pass_blocks_base(self):
        result = evaluate_case(self.cases["standalone_fail_delta_pass"], self.architecture, self.ir)
        self.assertEqual(result["base"], "DEFER")
        self.assertEqual(result["delta"], "SEPARATE_ADMISSION_REQUIRED")

    def test_unavailable_provider_fails_closed_without_substitution(self):
        result = evaluate_case(self.cases["archify_unavailable"], self.architecture, self.ir)
        self.assertEqual(result["base"], "PROVIDER_UNAVAILABLE_IN_CURRENT_ENVIRONMENT")
        self.assertEqual(result["result"], "NO_INSTALL_NO_SUBSTITUTION_NO_REPOSITORY_MUTATION")
        self.assertFalse(self.fixture["provider_process_started"])
        self.assertFalse(self.fixture["credentials_or_sessions_accessed"])
        self.assertFalse(self.fixture["system_or_repository_mutation"])

    def test_extra_deleted_and_edge_mutations_are_rejected(self):
        for case_id in (
            "archify_adds_semantic_node",
            "archify_deletes_canonical_node",
            "archify_changes_edge_semantics",
        ):
            mutated = apply_topology_mutation(self.ir, self.cases[case_id]["mutation"])
            self.assertTrue(exact_topology_errors(self.architecture, mutated), case_id)
            self.assertEqual(evaluate_case(self.cases[case_id], self.architecture, self.ir)["base"], "REJECT_ARTIFACT")

    def test_green_validator_does_not_raise_architecture_truth(self):
        result = evaluate_case(self.cases["green_validator_no_architecture_truth"], self.architecture, self.ir)
        self.assertEqual(result["result"], "NO_ARCHITECTURE_TRUTH_ESCALATION")
        self.assertEqual(result["base"], "BOUNDED_RESULT_ONLY")

    def test_aesthetic_endorsement_is_not_required_or_claimed(self):
        result = evaluate_case(self.cases["aesthetic_endorsement_absent"], self.architecture, self.ir)
        self.assertEqual(result["base"], "ADMIT_AS_CURRENT_BOUNDED_CANDIDATE")
        self.assertEqual(result["result"], "FUNCTIONAL_ALLOWED_AESTHETIC_NOT_CLAIMED")
        self.assertEqual(self.document["scope_freeze"]["owner_aesthetic_endorsement"], "NOT_GRANTED_NOT_CLAIMED")

    def test_repaired_delta_requires_separate_admission(self):
        result = evaluate_case(self.cases["delta_wrapper_repaired_no_auto_promotion"], self.architecture, self.ir)
        self.assertEqual(result["delta"], "SEPARATE_ADMISSION_REQUIRED")
        self.assertEqual(result["result"], "NO_AUTOMATIC_DELTA_PROMOTION")

    def test_new_provider_version_requires_compatibility_check(self):
        result = evaluate_case(self.cases["new_provider_version_no_auto_upgrade"], self.architecture, self.ir)
        self.assertEqual(result["base"], "COMPATIBILITY_CHECK_REQUIRED")
        self.assertEqual(result["result"], "NO_AUTOMATIC_PROVIDER_UPGRADE")

    def test_provider_skill_cannot_override_ignition_selection(self):
        result = evaluate_case(self.cases["provider_skill_imperative_no_override"], self.architecture, self.ir)
        self.assertEqual(result["base"], "IGNITION_SELECTION_PREVAILS")
        self.assertEqual(result["result"], "SKILL_CANNOT_OVERRIDE_IGNITION_AUTHORITY")

    def test_scope_and_authority_boundaries_remain_closed(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["architecture_delta"], "EXPERIMENTAL_EXTENSION_DEFERRED")
        self.assertEqual(scope["default_renderer"], "NOT_SELECTED")
        self.assertFalse(scope["architecture_authority"])
        self.assertEqual(scope["agent_reach"], "NO_CHANGE")
        self.assertEqual(scope["authenticated_channel_admission"], "NO_CHANGE")
        self.assertEqual(scope["live_external_invocation"], "OPEN_OWNER_DEFERRED_NOT_RUN")
        self.assertEqual(scope["task151"], "FORBIDDEN")

    def test_tampered_fixture_or_summary_is_rejected(self):
        mutated = copy.deepcopy(self.document)
        mutated["case_results"][0]["expected"]["delta"] = "PASS"
        self.assertTrue(validate(mutated))
        mutated = copy.deepcopy(self.document)
        mutated["validation"]["topology_mutations"] = "PASS_WITH_WARNINGS"
        self.assertTrue(validate(mutated))


if __name__ == "__main__":
    unittest.main()
