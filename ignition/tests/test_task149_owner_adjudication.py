import copy
import json
import unittest

from tools.validate_task149_owner_adjudication import ARTIFACT_PATH, validate


class Task149OwnerAdjudicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_adjudication_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_owner_decisions_are_exact(self):
        decisions = self.document["owner_decision"]
        self.assertEqual(decisions["archify"], {"fit": "FIT_WITH_LIMITS", "decision": "CONTINUE_EXPERIMENT"})
        self.assertEqual(decisions["agent_reach_public"], {"fit": "FIT_WITH_LIMITS", "decision": "CONTINUE_EXPERIMENT"})
        self.assertEqual(decisions["agent_reach_authenticated"], {"decision": "DEFER"})

    def test_merge_intent_and_non_intent_are_closed(self):
        self.assertEqual(self.document["merge_intent"], "MERGE_EXPERIMENTAL_EVIDENCE_AND_PROVIDER_NEUTRAL_CONTRACT_ONLY")
        self.assertEqual(len(self.document["explicit_non_intent"]), 4)
        self.assertIn("DO_NOT_CHANGE_LIVE_EXTERNAL_INVOCATION", self.document["explicit_non_intent"])

    def test_all_residuals_are_retained(self):
        evidence = self.document["retained_evidence_and_residuals"]
        self.assertEqual(evidence["archify"]["validation"], "PASS 9/9")
        self.assertEqual(len(evidence["archify"]["residuals"]), 4)
        self.assertEqual(len(evidence["agent_reach_public"]["residuals"]), 6)
        self.assertEqual(evidence["agent_reach_authenticated"]["authenticated_calls"], 0)

    def test_ready_is_conditional_and_task150_is_blocked(self):
        lifecycle = self.document["lifecycle_boundary"]
        self.assertFalse(lifecycle["ready_authorized_by_this_record"])
        self.assertEqual(lifecycle["ready_transition"], "CONDITIONAL_ON_A6_ALL_GATES_PASS")
        self.assertEqual(lifecycle["task150_creation"], "BLOCKED_UNTIL_A8_FRESH_MAIN_CLOSEOUT")
        self.assertEqual(lifecycle["task150_scope_if_a8_passes"], "ARCHIFY_ONLY")

    def test_mutated_authenticated_decision_fails(self):
        mutated = copy.deepcopy(self.document)
        mutated["owner_decision"]["agent_reach_authenticated"]["decision"] = "CONTINUE_EXPERIMENT"
        self.assertTrue(validate(mutated))

    def test_mutated_merge_intent_fails(self):
        mutated = copy.deepcopy(self.document)
        mutated["merge_intent"] = "MERGE_PROVIDER_RUNTIME"
        self.assertTrue(validate(mutated))


if __name__ == "__main__":
    unittest.main()
