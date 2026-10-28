import copy
import json
import unittest

from tools.validate_task149_step01_remote_truth import (
    AUDIT_PATH,
    CONTRACT_PATH,
    validate,
)


class Task149Step01RemoteTruthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_step01_receipt_passes(self):
        self.assertEqual(validate(self.audit, self.contract), [])

    def test_provider_records_are_empty_at_step01(self):
        mutated = copy.deepcopy(self.contract)
        mutated["provider_records"] = [{"provider_id": "vendor"}]
        self.assertTrue(any("provider records" in error for error in validate(self.audit, mutated)))

    def test_authority_boundary_cannot_be_removed(self):
        mutated = copy.deepcopy(self.audit)
        mutated["authority_boundaries"] = mutated["authority_boundaries"][:-1]
        self.assertTrue(any("boundaries" in error for error in validate(mutated, self.contract)))

    def test_baseline_is_exact(self):
        mutated = copy.deepcopy(self.audit)
        mutated["formal_remote_observation"]["observed_sha"] = "0" * 40
        self.assertTrue(any("baseline" in error for error in validate(mutated, self.contract)))


if __name__ == "__main__":
    unittest.main()
