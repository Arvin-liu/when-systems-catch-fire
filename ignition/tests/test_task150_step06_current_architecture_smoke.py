import copy
import json
import unittest

from tools.validate_task150_step06_current_architecture_smoke import ARTIFACT_PATH, validate


class Task150Step06CurrentArchitectureSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_receipt_and_committed_outputs_pass(self):
        self.assertEqual(validate(self.document), [])

    def test_fresh_source_is_exact_clean_nonshallow_commit(self):
        source = self.document["fresh_source"]
        self.assertEqual(source["revision"], "d7372c27abe456b5b8c058675630d8038f91b448")
        self.assertEqual(source["checkout"], "DETACHED_EXACT_COMMIT")
        self.assertEqual(source["worktree"], "CLEAN")
        self.assertTrue(source["non_shallow"])

    def test_two_runs_are_bound_to_same_outputs(self):
        self.assertEqual(len(self.document["runs"]), 2)
        self.assertEqual(self.document["runs"][0]["ir_sha256"], self.document["runs"][1]["ir_sha256"])
        self.assertEqual(self.document["runs"][0]["html_sha256"], self.document["runs"][1]["html_sha256"])
        self.assertEqual(self.document["runs"][0]["svg_sha256"], self.document["runs"][1]["svg_sha256"])

    def test_future_stability_is_not_overclaimed(self):
        self.assertEqual(self.document["stability"]["observed_scope"], "TWO_RUNS_SAME_INPUT_SAME_PROVIDER_REVISION")
        self.assertEqual(self.document["stability"]["future_nondeterminism_claim"], "NOT_CLAIMED")
        mutated = copy.deepcopy(self.document)
        mutated["stability"]["future_nondeterminism_claim"] = "GUARANTEED"
        self.assertTrue(validate(mutated))

    def test_topology_and_provider_authority_remain_bounded(self):
        self.assertEqual(self.document["adapter"]["topology"], {"nodes":24,"edges":24,"semantic_relationships_unchanged":True})
        self.assertEqual(self.document["provider"]["role"], "DERIVED_ARTIFACT_PROVIDER_NOT_AUTHORITY")

    def test_step04_delta_blocker_is_not_erased_by_standalone_pass(self):
        self.assertEqual(self.document["scope_freeze"]["delta_blocker"], "INHERITED_STEP04_UPSTREAM_WRAPPER_BLOCKER")
        mutated = copy.deepcopy(self.document)
        mutated["scope_freeze"]["delta_blocker"] = "RESOLVED"
        self.assertTrue(validate(mutated))

    def test_current_auth_and_live_boundaries_remain_closed(self):
        scope = self.document["scope_freeze"]
        self.assertEqual(scope["current_admission"], "NOT_ADMITTED")
        self.assertEqual(scope["authenticated_channels"], "NO_AUTHENTICATED_ADMISSION")
        self.assertEqual(scope["live_external_invocation"], "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN")
        self.assertEqual(scope["agent_reach"], "NO_CHANGE")


if __name__ == "__main__":
    unittest.main()
