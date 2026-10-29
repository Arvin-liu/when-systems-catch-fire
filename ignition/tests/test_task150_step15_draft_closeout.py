import copy
import json
import unittest

from tools.validate_task150_step15_draft_closeout import ARTIFACT_PATH, validate


class Task150Step15DraftCloseoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_draft_closeout_passes(self):
        self.assertEqual(validate(self.document), [])
        self.assertEqual(self.document["status"], "AWAIT_OWNER_ARCHIFY_BOUNDED_ADMISSION_REVIEW")

    def test_pr_is_open_draft_and_unmerged(self):
        pr = self.document["pull_request"]
        self.assertEqual(pr["number"], 200)
        self.assertTrue(pr["is_draft"])
        self.assertEqual(pr["state"], "OPEN")
        self.assertFalse(pr["merged"])
        self.assertIsNone(pr["merge_commit"])

    def test_pr_state_escalation_is_rejected(self):
        mutated = copy.deepcopy(self.document)
        mutated["pull_request"]["is_draft"] = False
        self.assertTrue(validate(mutated))
        mutated = copy.deepcopy(self.document)
        mutated["pull_request"]["merged"] = True
        self.assertTrue(validate(mutated))

    def test_queued_checks_are_not_overclaimed(self):
        self.assertEqual(self.document["pull_request"]["checks_at_creation"], "QUEUED_NOT_TREATED_AS_PASS")
        mutated = copy.deepcopy(self.document)
        mutated["pull_request"]["checks_at_creation"] = "PASS"
        self.assertTrue(validate(mutated))

    def test_closeout_is_defer_and_owner_review_only(self):
        closeout = self.document["closeout"]
        self.assertEqual(closeout["decision"], "DEFER")
        self.assertEqual(closeout["stop_state"], "AWAIT_OWNER_ARCHIFY_BOUNDED_ADMISSION_REVIEW")
        self.assertEqual(closeout["next_action"], "OWNER_REVIEW_ONLY")
        self.assertEqual(closeout["owner_review_state"], "PENDING")

    def test_registry_current_and_renderer_stay_closed(self):
        closeout = self.document["closeout"]
        self.assertFalse(closeout["registry_write"])
        self.assertFalse(closeout["current_capability"])
        self.assertFalse(closeout["default_renderer"])
        mutated = copy.deepcopy(self.document)
        mutated["closeout"]["current_capability"] = True
        self.assertTrue(validate(mutated))

    def test_non_intent_is_exact(self):
        self.assertEqual(self.document["explicit_non_intent"], ["DO_NOT_ACTIVATE_PROVIDER", "DO_NOT_ADD_CURRENT_PROVIDER_CAPABILITY", "DO_NOT_ENABLE_AUTHENTICATED_CHANNELS", "DO_NOT_CHANGE_LIVE_EXTERNAL_INVOCATION", "MERGE_EXPERIMENTAL_EVIDENCE_AND_PROVIDER_NEUTRAL_CONTRACT_ONLY"])

    def test_auth_and_live_invocation_remain_closed(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["authenticated_channels"], "NO_AUTHENTICATED_ADMISSION")
        self.assertEqual(scope["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")
        self.assertEqual(scope["agent_reach_authenticated"], "DEFER")

    def test_no_successor_task_or_homepage_claim(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["task151"], "FORBIDDEN")
        self.assertEqual(scope["successor_task"], "NOT_CREATED")
        self.assertEqual(scope["provider_homepage"], "NO_CLAIM")


if __name__ == "__main__":
    unittest.main()
