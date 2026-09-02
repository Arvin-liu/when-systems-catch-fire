import copy
import unittest

from tools.validate_task150_step28_owner_adjudication_scope_split import (
    ARTIFACT_PATH,
    EXPECTED_STEP14_SHA,
    EXPECTED_STEP15_SHA,
    STEP14_PATH,
    STEP15_PATH,
    load_json,
    sha256,
    validate,
)


class Task150Step28OwnerAdjudicationScopeSplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = load_json(ARTIFACT_PATH)

    def test_post_review_adjudication_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_historical_step14_and_step15_are_hash_pinned(self):
        timeline = self.document["historical_timeline"]
        self.assertEqual(sha256(STEP14_PATH), EXPECTED_STEP14_SHA)
        self.assertEqual(sha256(STEP15_PATH), EXPECTED_STEP15_SHA)
        self.assertEqual(timeline["step14_sha256"], EXPECTED_STEP14_SHA)
        self.assertEqual(timeline["step15_sha256"], EXPECTED_STEP15_SHA)

    def test_step14_defer_is_preserved_as_valid_under_old_combined_scope(self):
        timeline = self.document["historical_timeline"]
        self.assertEqual(timeline["step14_status"], "DEFER")
        self.assertEqual(timeline["step14_basis"], "STEP14_DEFER_WAS_VALID_UNDER_COMBINED_SCOPE")
        self.assertTrue(timeline["historical_files_unchanged"])
        self.assertTrue(timeline["no_evidence_rewritten"])

    def test_scope_split_occurs_after_step15(self):
        timeline = self.document["historical_timeline"]
        self.assertEqual(timeline["step15_stop_state"], "TASK150_STEP15_DRAFT_PR_OWNER_REVIEW_STOP")
        self.assertEqual(timeline["owner_scope_split_timing"], "OWNER_SCOPE_SPLIT_OCCURRED_AFTER_STEP15")

    def test_base_is_candidate_and_delta_is_separately_deferred(self):
        adjudication = self.document["adjudication"]
        base = adjudication["base_standalone"]
        delta = adjudication["architecture_delta"]
        self.assertEqual(base["decision"], "ADMIT_AS_CURRENT_BOUNDED_CANDIDATE")
        self.assertFalse(base["delta_is_required"])
        self.assertEqual(delta["decision"], "DEFER")
        self.assertEqual(delta["status"], "EXPERIMENTAL_EXTENSION_DEFERRED")
        self.assertTrue(delta["independent_admission_required"])
        self.assertFalse(delta["base_pass_promotes_delta"])

    def test_aesthetic_endorsement_is_not_required_and_not_claimed(self):
        aesthetic = self.document["adjudication"]["aesthetic_endorsement"]
        self.assertEqual(aesthetic["decision"], "NOT_CLAIMED")
        self.assertFalse(aesthetic["required_for_functional_admission"])
        self.assertEqual(aesthetic["homepage_or_brand_claim"], "FORBIDDEN")

    def test_archify_is_not_authority_and_default_renderer_is_unselected(self):
        adjudication = self.document["adjudication"]
        self.assertFalse(adjudication["archify_architecture_authority"])
        self.assertEqual(adjudication["architecture_authority_source"], "IGNITION_CANONICAL_SOURCE")
        self.assertEqual(adjudication["default_renderer"], "NOT_SELECTED")

    def test_any_base_gate_failure_falls_back_to_defer(self):
        self.assertEqual(self.document["adjudication"]["base_gate_failure_fallback"], "OVERALL_DEFER")

    def test_ready_merge_and_current_on_main_remain_closed(self):
        lifecycle = self.document["lifecycle_boundary"]
        self.assertEqual(lifecycle["registry_entry_status"], "CURRENT_BOUNDED_CANDIDATE")
        self.assertFalse(lifecycle["formal_ready"])
        self.assertFalse(lifecycle["merged_to_main"])
        self.assertFalse(lifecycle["current_on_main"])
        self.assertTrue(lifecycle["pr_is_draft"])
        self.assertFalse(lifecycle["ready_transition_authorized_by_step28"])

    def test_auth_live_and_successor_boundaries_remain_closed(self):
        adjudication = self.document["adjudication"]
        self.assertEqual(adjudication["agent_reach"], "NO_CHANGE")
        self.assertEqual(adjudication["authenticated_channel_admission"], "NO_CHANGE")
        self.assertEqual(adjudication["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")
        self.assertEqual(adjudication["task151"], "FORBIDDEN")

    def test_tampered_adjudication_is_rejected(self):
        mutated = copy.deepcopy(self.document)
        mutated["adjudication"]["architecture_delta"]["base_pass_promotes_delta"] = True
        self.assertTrue(validate(mutated))
        mutated = copy.deepcopy(self.document)
        mutated["historical_timeline"]["step14_basis"] = "STEP14_WAS_WRONG"
        self.assertTrue(validate(mutated))


if __name__ == "__main__":
    unittest.main()
