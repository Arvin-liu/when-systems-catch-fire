import copy
import json
import unittest

from tools.validate_task149_step06_archify_validation import ARTIFACT_PATH, validate


class Task149Step06ArchifyValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_provider_bound_passes_are_not_current_claims(self):
        self.assertEqual(self.document["status"], "VALIDATED_WITHIN_RECORDED_ENVIRONMENT")
        boundaries = self.document["boundaries"]
        self.assertEqual(boundaries["current_integration"], "NOT_CURRENT_INTEGRATION")
        self.assertEqual(boundaries["production_readiness"], "NOT_PRODUCTION_READY")
        self.assertEqual(boundaries["authenticated_channel_admission"], "NO_AUTHENTICATED_CHANNEL_ADMISSION")
        self.assertFalse(boundaries["provider_permission_granted"])

    def test_visual_check_retains_light_and_dark_evidence(self):
        visual = self.document["commands"]["visual_check"]
        self.assertEqual(len(visual["light_containment_viewports"]), 4)
        self.assertEqual(len(visual["dark_capture_viewports"]), 2)
        self.assertEqual(len(visual["screenshots"]), 4)
        self.assertEqual(visual["upstream_visual_review_field"], "pending")
        self.assertEqual(visual["local_screenshot_inspection"], "PERFORMED")

    def test_source_and_artifact_hashes_are_bound(self):
        self.assertEqual(self.document["commands"]["deliver"]["specification_sha256"], self.document["typed_ir"]["sha256"])
        self.assertEqual(self.document["commands"]["deliver"]["artifact_sha256"], self.document["artifact"]["sha256"])
        self.assertFalse(self.document["upstream"]["source_copied_or_vendored"])
        self.assertFalse(self.document["artifact"]["source_copied_or_vendored"])

    def test_current_integration_mutation_fails_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["boundaries"]["current_integration"] = "CURRENT"
        self.assertTrue(validate(mutated))

    def test_artifact_mutation_fails_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["artifact"]["status"] = "COMMITTED"
        self.assertTrue(validate(mutated))

    def test_source_hash_mutation_fails_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["source_inputs"][0]["sha256"] = "0" * 64
        self.assertTrue(any("source hash mismatch" in error for error in validate(mutated)))


if __name__ == "__main__":
    unittest.main()
