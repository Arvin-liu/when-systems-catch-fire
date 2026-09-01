import copy
import json
import unittest

from tools.validate_task149_step07_archify_delta import ARTIFACT_PATH, validate


class Task149Step07ArchifyDeltaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_delta_is_authored_facts_only(self):
        delta = self.document["delta_output"]
        self.assertEqual(delta["allowed_change_kinds"], ["added", "removed", "changed", "moved", "rerouted"])
        self.assertEqual(delta["actual_authored_facts"]["change_records"], [])
        self.assertTrue(delta["actual_authored_facts"]["provenance_changed"])
        self.assertEqual(delta["no_inference_fields_emitted"], ["impact", "risk", "safety", "quality_improvement", "correctness", "merge_readiness"])

    def test_context_map_change_is_not_visual_architecture_change(self):
        source_inputs = self.document["source_inputs"]
        self.assertTrue(source_inputs["delta_input"]["byte_identical"])
        self.assertFalse(source_inputs["context_only"][0]["byte_identical"])
        self.assertTrue(source_inputs["context_only"][0]["not_promoted_to_archify_node_or_edge"])

    def test_viewer_residual_is_not_hidden(self):
        visual = self.document["commands"]["visual_check"]
        self.assertEqual(visual["before"]["status"], "PASS")
        self.assertEqual(visual["after"]["status"], "PASS")
        self.assertEqual(visual["delta"]["status"], "FAIL_VIEWPORT_CONTAINMENT")
        self.assertEqual(visual["delta"]["diagnostic_code"], "viewer/viewport-overflow")

    def test_current_and_permission_boundaries_fail_closed(self):
        boundaries = self.document["boundaries"]
        self.assertEqual(boundaries["current_integration"], "NOT_CURRENT_INTEGRATION")
        self.assertEqual(boundaries["production_readiness"], "NOT_PRODUCTION_READY")
        self.assertEqual(boundaries["authenticated_channel_admission"], "NO_AUTHENTICATED_CHANNEL_ADMISSION")
        self.assertFalse(boundaries["provider_permission_granted"])

    def test_mutated_current_claim_fails(self):
        mutated = copy.deepcopy(self.document)
        mutated["boundaries"]["current_integration"] = "CURRENT"
        self.assertTrue(validate(mutated))

    def test_mutated_delta_inference_fails(self):
        mutated = copy.deepcopy(self.document)
        mutated["delta_output"]["actual_authored_facts"]["change_records"] = [{"status": "changed", "impact": "high"}]
        self.assertTrue(validate(mutated))


if __name__ == "__main__":
    unittest.main()
