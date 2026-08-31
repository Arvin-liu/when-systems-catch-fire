import copy
import json
import unittest

from tools.validate_task149_step05_archify_adapter import ARTIFACT_PATH, validate


class Task149Step05ArchifyAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_adapter_receipt_passes(self):
        self.assertEqual(validate(self.document), [])

    def test_external_validation_is_not_claimed_early(self):
        self.assertEqual(self.document["archify_external_validation"]["status"], "PENDING_STEP06")

    def test_canonical_data_remains_authoritative(self):
        boundary = self.document["boundary"]
        self.assertEqual(boundary["current_integration"], "NOT_CURRENT_INTEGRATION")
        self.assertFalse(boundary["permission_granted"])

    def test_source_hash_drift_fails_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["source_inputs"][0]["sha256"] = "0" * 64
        self.assertTrue(any("source hash mismatch" in error for error in validate(mutated)))

    def test_adapter_network_and_auth_are_closed(self):
        mutated = copy.deepcopy(self.document)
        mutated["boundary"]["network_used_by_adapter"] = True
        self.assertTrue(validate(mutated))


if __name__ == "__main__":
    unittest.main()
