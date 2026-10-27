import copy
import json
import unittest

from tools.validate_task149_step15_adversarial_authority_regression import ARTIFACT_PATH, validate


class Task149Step15AuthorityRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_six_adversarial_cases_are_present(self):
        self.assertEqual(len(self.document["fixtures"]), 6)
        self.assertEqual(self.document["external_calls"], 0)
        self.assertTrue(self.document["automated_regression"])

    def test_provider_local_policy_does_not_become_global_policy(self):
        fixture = self.document["fixtures"][0]
        self.assertEqual(fixture["expected_decision"], "PROVIDER_LOCAL_POLICY")
        self.assertTrue(fixture["escalation_blocked"])

    def test_verified_and_health_claims_do_not_escalate(self):
        by_id = {fixture["fixture_id"]: fixture for fixture in self.document["fixtures"]}
        self.assertEqual(by_id["provider-verified-output"]["expected_decision"], "REJECT_UNPROVEN_EXTERNAL_TRUTH")
        self.assertEqual(by_id["provider-health-green"]["expected_decision"], "REJECT_HEALTH_AS_SUCCESS")
        self.assertFalse(by_id["provider-verified-output"]["external_truth_claimed"])

    def test_archify_provenance_and_agent_reach_auth_are_separate(self):
        by_id = {fixture["fixture_id"]: fixture for fixture in self.document["fixtures"]}
        self.assertEqual(by_id["archify-node-without-canonical-provenance"]["expected_decision"], "REJECT_MISSING_CANONICAL_PROVENANCE")
        self.assertEqual(by_id["agent-reach-backend-exists"]["expected_decision"], "AUTH_REQUIRED")

    def test_readme_does_not_promote_current(self):
        fixture = next(f for f in self.document["fixtures"] if f["fixture_id"] == "third-party-readme-production-ready")
        self.assertEqual(fixture["expected_decision"], "REJECT_CLAIM_CEILING")
        self.assertFalse(fixture["current_capability_promoted"])

    def test_all_escalations_and_boundaries_are_closed(self):
        self.assertTrue(all(fixture["escalation_blocked"] for fixture in self.document["fixtures"]))
        invariants = self.document["regression_invariants"]
        self.assertFalse(invariants["provider_local_policy_is_ignition_global_policy"])
        self.assertFalse(invariants["provider_output_is_external_truth"])
        self.assertEqual(invariants["authenticated_channel_admission"], "NO_AUTHENTICATED_CHANNEL_ADMISSION")

    def test_mutated_fixture_fails(self):
        mutated = copy.deepcopy(self.document)
        mutated["fixtures"][0]["escalation_blocked"] = False
        self.assertTrue(validate(mutated))

    def test_no_current_or_production_promotion(self):
        self.assertEqual(self.document["regression_invariants"]["current_integration"], "NOT_CURRENT_INTEGRATION")
        self.assertEqual(self.document["regression_invariants"]["production_readiness"], "NOT_PRODUCTION_READY")


if __name__ == "__main__":
    unittest.main()
