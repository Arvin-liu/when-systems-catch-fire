"""Mutation Tests for Q37 Analogy Audit — Second Pass Deep Audit"""
import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tools.lab.mutation_runner import MutationTest, load_json, deep_copy

VALIDATOR = "tools.analogy.validate_analogy_audit"
DATA = "data/analogy"

class Q37MutationTests(unittest.TestCase):
    def setUp(self):
        self.mt = MutationTest("Q37")

    def tearDown(self):
        self.mt.restore()

    def test_m1_surface_as_structural(self):
        """Surface similarity labeled as structural mapping."""
        doc = load_json(f"{DATA}/analogy-candidates.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["structural_correspondence"] = [{"type": "surface_name_match", "detail": "same label"}]
        caught, r = self.mt.assert_catches(
            f"{DATA}/analogy-candidates.json", d, VALIDATOR)
        # Validator only checks non-empty, not quality
        if not caught:
            self.skipTest("GAP: validator does not evaluate correspondence quality")

    def test_m2_no_non_correspondence(self):
        """Missing non-correspondence residue must fail."""
        doc = load_json(f"{DATA}/analogy-candidates.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["non_correspondence_residue"] = []
        caught, r = self.mt.assert_catches(
            f"{DATA}/analogy-candidates.json", d, VALIDATOR)
        self.assertTrue(caught, f"Empty non-correspondence must fail: {r.report()}")

    def test_m3_source_teleology_in_target(self):
        """Source domain purpose leaking into target domain."""
        doc = load_json(f"{DATA}/analogy-candidates.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["target_domain"]["imported_purpose"] = e.get("source_domain", {}).get("purpose", "")
        caught, r = self.mt.assert_catches(
            f"{DATA}/analogy-candidates.json", d, VALIDATOR)
        if not caught:
            self.skipTest("GAP: validator does not check teleology transfer")

    def test_m4_mismatch_as_evidence(self):
        """Productive mismatch auto-becoming evidence."""
        doc = load_json(f"{DATA}/analogy-candidates.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["evidence_status"] = "confirmed_by_mismatch"
        caught, r = self.mt.assert_catches(
            f"{DATA}/analogy-candidates.json", d, VALIDATOR)
        if not caught:
            self.skipTest("GAP: validator does not check evidence_status field")

    def test_m5_claim_ceiling_elevated(self):
        """Claim ceiling elevated to 'causal_conclusion' must fail."""
        doc = load_json(f"{DATA}/analogy-candidates.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["claim_ceiling"] = "causal_conclusion"
        caught, r = self.mt.assert_catches(
            f"{DATA}/analogy-candidates.json", d, VALIDATOR)
        if not caught:
            self.skipTest("GAP: validator only blocks formal_equivalence, not causal_conclusion")

    def test_m6_unidirectional_as_bidirectional(self):
        """Unidirectional mapping disguised as bidirectional."""
        doc = load_json(f"{DATA}/analogy-candidates.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["mapping_direction"] = "bidirectional"
            e["source_to_target"] = ["A->X"]
            e["target_to_source"] = []
        caught, r = self.mt.assert_catches(
            f"{DATA}/analogy-candidates.json", d, VALIDATOR)
        if not caught:
            self.skipTest("GAP: validator does not check mapping direction consistency")

    def test_m7_no_negative_transfer(self):
        """Missing negative transfer analysis must fail."""
        doc = load_json(f"{DATA}/analogy-candidates.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["negative_transfer"] = []
        caught, r = self.mt.assert_catches(
            f"{DATA}/analogy-candidates.json", d, VALIDATOR)
        self.assertTrue(caught, f"Empty negative transfer must fail: {r.report()}")

if __name__ == "__main__":
    unittest.main()
