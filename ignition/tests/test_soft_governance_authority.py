import copy
import json
import unittest
from pathlib import Path

from tools.validate_soft_governance_authority import (
    DEFAULT_CONTRACT,
    DEFAULT_FIXTURES,
    DEFAULT_SCHEMA,
    evaluate_attempt,
    scan_runtime_sources,
    validate_contract,
)


class SoftGovernanceAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
        cls.schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))

    def test_contract_is_machine_enforced_and_runtime_is_uncoupled(self):
        self.assertEqual([], validate_contract(self.contract, self.schema))
        self.assertEqual([], scan_runtime_sources())

    def test_all_negative_fixtures_fail_closed(self):
        fixtures = sorted(DEFAULT_FIXTURES.glob("*.json"))
        self.assertGreaterEqual(len(fixtures), 3)
        for path in fixtures:
            fixture = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("REJECT_SOFT_AUTHORITY_ESCALATION", evaluate_attempt(self.contract, fixture))

    def test_unknown_authority_effect_is_rejected(self):
        fixture = {"soft_input": {"esi_score": 1.0}, "requested_effect": "NEW_AUTHORITY"}
        self.assertEqual("REJECT_UNKNOWN_EFFECT", evaluate_attempt(self.contract, fixture))

    def test_allowed_advisory_effect_remains_bounded(self):
        fixture = {"soft_input": {"esi_score": 0.5}, "requested_effect": "ADVISORY_CONTEXT"}
        self.assertEqual("ALLOW_BOUNDED_SOFT_EFFECT", evaluate_attempt(self.contract, fixture))


if __name__ == "__main__":
    unittest.main()
