#!/usr/bin/env python3
"""P1 (F1 re-adjudication): the jurisdiction registry models applicable legal-regime
scopes, NOT sovereignty or political status.

V18 flagged that JUR-TW was listed as a separate sovereign jurisdiction. The correct
fix is NOT to delete TW's applicable rules nor to mechanically merge them into CN, but
to separate the technical concept of "legal regime scope of application" from any
sovereignty judgment. This test enforces that separation.
"""

import json
import os
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOV_DIR = os.path.join(REPO_ROOT, "data", "governance")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class JurisdictionSovereigntyNeutralTests(unittest.TestCase):
    def setUp(self):
        self.reg = load_json(os.path.join(GOV_DIR, "jurisdiction-rule-registry.json"))

    def test_registry_declares_no_sovereignty(self):
        """The registry must explicitly declare it does not assert sovereignty."""
        self.assertEqual(self.reg.get("sovereignty_position"), "NOT_ASSERTED",
                         "Registry must declare sovereignty_position: NOT_ASSERTED")
        self.assertEqual(self.reg.get("modeling_concept"), "legal_regime_scope_of_application",
                         "Registry must model legal_regime_scope_of_application, not sovereign states")
        self.assertIn("sovereignty", self.reg.get("sovereignty_statement", "").lower(),
                      "Registry must carry a sovereignty_statement")

    def test_every_entry_sovereignty_not_asserted(self):
        """Every jurisdiction/legal-regime entry must carry sovereignty_position: NOT_ASSERTED
        and a non-empty legal_regime_scope + territorial_law_scope."""
        for code, j in self.reg["jurisdictions"].items():
            self.assertEqual(j.get("sovereignty_position"), "NOT_ASSERTED",
                             f"{code} must carry sovereignty_position: NOT_ASSERTED")
            self.assertTrue(j.get("legal_regime_scope", "").strip(),
                            f"{code} missing legal_regime_scope")
            self.assertTrue(j.get("territorial_law_scope", "").strip(),
                            f"{code} missing territorial_law_scope")

    def test_tw_and_cn_are_distinct_legal_regimes(self):
        """TW's applicable rules must be preserved (not merged into CN) and distinguished by
        legal_regime_scope / territorial_law_scope."""
        tw = self.reg["jurisdictions"]["TW"]
        cn = self.reg["jurisdictions"]["CN"]
        self.assertNotEqual(tw["legal_regime_scope"], cn["legal_regime_scope"])
        self.assertNotEqual(tw["territorial_law_scope"], cn["territorial_law_scope"])
        # TW applicable rules preserved
        self.assertIn("exceptions", tw)
        self.assertIn("framework", tw)
        # No sovereignty claim in TW entry
        blob = json.dumps(tw, ensure_ascii=False).lower()
        for forbidden in ["independent sovereign", "sovereign state", "sovereign nation",
                          "country of taiwan", "taiwan is a country", "taiwanese sovereign"]:
            self.assertNotIn(forbidden, blob, f"TW entry appears to assert sovereignty: {forbidden}")

    def test_no_entry_claims_sovereign_recognition(self):
        """No entry may describe itself as a sovereign/independent state."""
        for code, j in self.reg["jurisdictions"].items():
            blob = json.dumps(j, ensure_ascii=False).lower()
            for forbidden in ["independent sovereign state", "sovereign nation state"]:
                self.assertNotIn(forbidden, blob,
                                 f"{code} entry appears to claim sovereign statehood: {forbidden}")


if __name__ == "__main__":
    unittest.main()
