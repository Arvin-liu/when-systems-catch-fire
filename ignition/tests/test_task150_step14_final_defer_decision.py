import copy
import json
import unittest

from tools.validate_task150_step14_final_defer_decision import ARTIFACT_PATH, validate


class Task150Step14FinalDeferDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_final_decision_is_defer(self):
        self.assertEqual(validate(self.document), [])
        self.assertEqual(self.document["status"], "DEFER")
        self.assertEqual(self.document["decision"]["candidate_status"], "EXPERIMENTAL_CANDIDATE_NOT_REGISTERED")

    def test_archify_and_public_agent_reach_context(self):
        archify = self.document["owner_decision_context"]["archify"]
        public = self.document["owner_decision_context"]["agent_reach_public"]
        self.assertEqual(archify["fit"], "FIT_WITH_LIMITS")
        self.assertEqual(archify["continuation"], "CONTINUE_EXPERIMENT")
        self.assertEqual(public["fit"], "FIT_WITH_LIMITS")
        self.assertEqual(public["continuation"], "CONTINUE_EXPERIMENT")
        self.assertEqual(public["task150_change"], "NO_CHANGE")

    def test_authenticated_agent_reach_remains_deferred(self):
        auth = self.document["owner_decision_context"]["agent_reach_authenticated"]
        self.assertEqual(auth["decision"], "DEFER")
        self.assertEqual(auth["authenticated_channel_admission"], "NO_AUTHENTICATED_ADMISSION")
        self.assertEqual(auth["task150_change"], "NO_CHANGE")

    def test_failed_and_pending_gates_force_defer(self):
        gates = self.document["gate_summary"]
        self.assertEqual(gates["delta_viewport_containment_zero_failure"], "FAIL")
        self.assertEqual(gates["owner_visual_acceptance"], "PENDING")
        mutated = copy.deepcopy(self.document)
        mutated["gate_summary"]["delta_viewport_containment_zero_failure"] = "PASS"
        self.assertTrue(validate(mutated))

    def test_registry_current_and_renderer_boundaries_are_closed(self):
        decision = self.document["decision"]
        self.assertFalse(decision["current_capability"])
        self.assertFalse(decision["default_renderer"])
        self.assertFalse(decision["registry_write"])
        self.assertFalse(decision["ready_or_merge_authorization"])
        mutated = copy.deepcopy(self.document)
        mutated["decision"]["registry_write"] = True
        self.assertTrue(validate(mutated))

    def test_blocking_evidence_retains_semantic_pass_and_visual_failure(self):
        evidence = self.document["blocking_evidence"]
        self.assertEqual(evidence["delta_diagnostics"], 3)
        self.assertEqual(evidence["standalone_containment"], "PASS")
        self.assertEqual(evidence["delta_semantic_compare"], "PASS_28_OF_28")
        self.assertEqual(evidence["owner_aesthetic_acceptance"], "PENDING")

    def test_live_and_authenticated_boundaries_remain_closed(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["authenticated_channels"], "NO_AUTHENTICATED_ADMISSION")
        self.assertEqual(scope["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")

    def test_no_successor_task_is_created(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["task151"], "FORBIDDEN")
        self.assertEqual(scope["successor_task"], "NOT_CREATED")


if __name__ == "__main__":
    unittest.main()
