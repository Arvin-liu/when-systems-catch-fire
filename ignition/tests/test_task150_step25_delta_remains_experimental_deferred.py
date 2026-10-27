import copy
import json
import unittest

from tools.validate_task150_step25_delta_remains_experimental_deferred import (
    ARTIFACT_PATH,
    EXPECTED_STEP04_SHA,
    EXPECTED_STEP07_SHA,
    EXPECTED_STEP22_SHA,
    validate,
)


class Task150Step25DeltaRemainsExperimentalDeferredTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_retained_delta_deferral_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_historical_receipts_are_hash_pinned(self):
        evidence = self.document["evidence"]
        self.assertEqual(evidence["step04_blocker_receipt"]["sha256"], EXPECTED_STEP04_SHA)
        self.assertEqual(evidence["step07_delta_smoke_receipt"]["sha256"], EXPECTED_STEP07_SHA)
        self.assertEqual(evidence["step22_compatibility_receipt"]["sha256"], EXPECTED_STEP22_SHA)

    def test_semantic_pass_does_not_clear_wrapper_blocker(self):
        gate = self.document["delta_gate"]
        self.assertEqual(gate["semantic_result"], "PASS_28_OF_28_PROVENANCE_ONLY")
        self.assertEqual(gate["visual_result"], "FAIL_UPSTREAM_WRAPPER")
        self.assertEqual(gate["diagnostics"], 3)
        self.assertEqual(gate["blocker"], "UPSTREAM_COMPARE_WRAPPER_VIEWPORT_CONTAINMENT")

    def test_delta_gate_is_independent_and_not_registered(self):
        gate = self.document["delta_gate"]
        self.assertTrue(gate["base_gate_is_independent"])
        self.assertTrue(gate["delta_does_not_block_base"])
        self.assertFalse(gate["delta_operation_registered"])
        self.assertFalse(gate["automatic_promotion"])

    def test_historical_step14_and_step15_are_preserved(self):
        preserved = self.document["preserved_boundaries"]
        self.assertTrue(preserved["step14_defer_preserved"])
        self.assertTrue(preserved["step15_draft_stop_preserved"])
        self.assertTrue(preserved["no_historical_evidence_rewritten"])

    def test_tampered_blocker_or_promotion_is_rejected(self):
        mutated = copy.deepcopy(self.document)
        mutated["delta_gate"]["visual_result"] = "PASS"
        self.assertTrue(validate(mutated))
        mutated = copy.deepcopy(self.document)
        mutated["delta_gate"]["automatic_promotion"] = True
        self.assertTrue(validate(mutated))

    def test_safety_boundaries_remain_closed(self):
        preserved = self.document["preserved_boundaries"]
        self.assertEqual(preserved["default_renderer"], "NOT_SELECTED")
        self.assertFalse(preserved["architecture_authority"])
        self.assertFalse(preserved["provider_authority"])
        self.assertEqual(preserved["agent_reach"], "NO_CHANGE")
        self.assertEqual(preserved["authenticated_channel_admission"], "NO_CHANGE")
        self.assertEqual(preserved["live_external_invocation"], "OPEN_OWNER_DEFERRED_NOT_RUN")
        self.assertEqual(preserved["task151"], "FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
