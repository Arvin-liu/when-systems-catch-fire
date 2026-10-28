import copy
import json
import unittest

from tools.validate_soft_context_exposure import DEFAULT_CONTRACT, DEFAULT_SCHEMA, validate


class SoftContextExposureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
        cls.schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))

    def test_contract_is_advisory_and_non_authoritative(self):
        self.assertEqual([], validate(self.contract, self.schema))
        self.assertEqual("ADVISORY_ONLY", self.contract["status"])
        self.assertEqual("NONE", self.contract["handoff_capsule"]["permission_delta"])

    def test_permission_promotion_is_rejected(self):
        contract = copy.deepcopy(self.contract)
        contract["handoff_capsule"]["permission_delta"] = "GRANTED"
        self.assertTrue(validate(contract, self.schema))

    def test_private_session_field_is_not_permitted(self):
        contract = copy.deepcopy(self.contract)
        contract["exposure_event"]["prohibited_fields"].remove("vendor_session_state")
        self.assertTrue(validate(contract, self.schema))


if __name__ == "__main__":
    unittest.main()
