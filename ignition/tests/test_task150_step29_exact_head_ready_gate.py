import copy
import unittest

from tools.validate_task150_step29_exact_head_ready_gate import (
    ARTIFACT_PATH,
    EXPECTED_CANDIDATE_HEAD,
    EXPECTED_STEP14_SHA,
    EXPECTED_STEP15_SHA,
    STEP14_PATH,
    STEP15_PATH,
    load_json,
    sha256,
    validate,
)


class Task150Step29ExactHeadReadyGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = load_json(ARTIFACT_PATH)

    def test_exact_head_ready_gate_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_candidate_head_is_the_exact_step28_parent(self):
        self.assertEqual(self.document["formal_previous_commit"], EXPECTED_CANDIDATE_HEAD)
        self.assertEqual(self.document["candidate_head_sha"], EXPECTED_CANDIDATE_HEAD)
        self.assertEqual(self.document["full_regression"]["head_sha"], EXPECTED_CANDIDATE_HEAD)
        self.assertEqual(self.document["remote_observation"]["pull_request"]["head_sha"], EXPECTED_CANDIDATE_HEAD)

    def test_historical_defer_and_draft_stop_are_hash_pinned(self):
        self.assertEqual(sha256(STEP14_PATH), EXPECTED_STEP14_SHA)
        self.assertEqual(sha256(STEP15_PATH), EXPECTED_STEP15_SHA)
        timeline = self.document["historical_lineage"]
        self.assertEqual(timeline["step14_status"], "DEFER")
        self.assertEqual(timeline["step15_status"], "AWAIT_OWNER_ARCHIFY_BOUNDED_ADMISSION_REVIEW")
        self.assertTrue(timeline["historical_files_unchanged"])
        self.assertTrue(timeline["no_evidence_rewritten"])

    def test_base_and_delta_have_independent_gate_outcomes(self):
        self.assertEqual(self.document["standalone_evidence"]["operation_status"], "CURRENT_BOUNDED_CANDIDATE")
        self.assertEqual(self.document["standalone_evidence"]["topology"]["standalone_containment_failures"], 0)
        self.assertEqual(self.document["standalone_evidence"]["compatibility"]["status"], "PASS_BASE_ONLY_DELTA_DEFERRED")
        self.assertEqual(self.document["standalone_evidence"]["compatibility"]["delta_visual_residuals"], 3)
        self.assertEqual(self.document["scope_freeze"]["architecture_delta"], "EXPERIMENTAL_EXTENSION_DEFERRED")

    def test_aesthetic_provider_renderer_and_live_boundaries_remain_closed(self):
        scope = self.document["scope_freeze"]
        self.assertFalse(scope["aesthetic_endorsement_required_for_functional_admission"])
        self.assertEqual(scope["owner_aesthetic_endorsement"], "NOT_GRANTED_NOT_CLAIMED")
        self.assertFalse(scope["archify_architecture_authority"])
        self.assertEqual(scope["default_renderer"], "NOT_SELECTED")
        self.assertEqual(scope["agent_reach"], "NO_CHANGE")
        self.assertEqual(scope["authenticated_channel_admission"], "NO_CHANGE")
        self.assertEqual(scope["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")
        self.assertEqual(scope["task151"], "FORBIDDEN")

    def test_ready_is_authorized_but_not_performed(self):
        lifecycle = self.document["lifecycle_boundary"]
        self.assertTrue(lifecycle["ready_transition_authorized_by_step29"])
        self.assertFalse(lifecycle["formal_ready"])
        self.assertTrue(lifecycle["pr_is_draft"])
        self.assertFalse(lifecycle["merged_to_main"])
        self.assertFalse(lifecycle["current_on_main"])

    def test_tampered_head_or_regression_is_rejected(self):
        mutated = copy.deepcopy(self.document)
        mutated["candidate_head_sha"] = "0" * 40
        self.assertTrue(validate(mutated))
        mutated = copy.deepcopy(self.document)
        mutated["full_regression"]["failures"] = 1
        self.assertTrue(validate(mutated))


if __name__ == "__main__":
    unittest.main()
