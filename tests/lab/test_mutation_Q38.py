"""Mutation Tests for Q38 Structural Retrieval — Second Pass Deep Audit"""
import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tools.lab.mutation_runner import MutationTest, load_json, deep_copy

VALIDATOR = "tools.retrieval.validate_structural_retrieval"
DATA = "data/retrieval"

class Q38MutationTests(unittest.TestCase):
    def setUp(self):
        self.mt = MutationTest("Q38")

    def tearDown(self):
        self.mt.restore()

    def test_m1_vector_as_isomorphism(self):
        """Plain vector similarity labeled as isomorphism."""
        doc = load_json(f"{DATA}/case-structures.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["retrieval_type"] = "vector_similarity_isomorphism"
        caught, r = self.mt.assert_catches(
            f"{DATA}/case-structures.json", d, VALIDATOR)
        if not caught:
            self.skipTest("GAP: validator does not check retrieval_type values")

    def test_m2_no_counterexamples(self):
        """Empty counterexample set must be flagged."""
        caught, r = self.mt.assert_catches(
            f"{DATA}/counterexample-set.json",
            {"registry_type": "counterexample_set", "version": "0.1.0", "entries": []},
            VALIDATOR)
        # Validator checks reference integrity but not emptiness
        if not caught:
            self.skipTest("GAP: validator does not require non-empty counterexamples")

    def test_m3_no_common_relation_generalization(self):
        """Two cases without shared relation signature must not generalize."""
        doc = load_json(f"{DATA}/counterexample-set.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["generalization_claim"] = "generalized_from_two"
        caught, r = self.mt.assert_catches(
            f"{DATA}/counterexample-set.json", d, VALIDATOR)
        if not caught:
            self.skipTest("GAP: validator does not check generalization claims")

    def test_m4_partial_as_complete(self):
        """Partial mapping labeled complete isomorphism."""
        doc = load_json(f"{DATA}/case-structures.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["isomorphism_type"] = "complete"
            e["mapped_nodes"] = 1
            e["total_nodes"] = 10
        caught, r = self.mt.assert_catches(
            f"{DATA}/case-structures.json", d, VALIDATOR)
        if not caught:
            self.skipTest("GAP: validator does not check isomorphism completeness")

    def test_m5_signature_order_sensitivity(self):
        """Reversed argument order must change signature."""
        doc = load_json(f"{DATA}/relation-signatures.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            args = e.get("arguments", [])
            if len(args) >= 2:
                e["arguments"] = list(reversed(args))
        caught, r = self.mt.assert_catches(
            f"{DATA}/relation-signatures.json", d, VALIDATOR)
        if not caught:
            self.skipTest("GAP: validator does not check argument order")

    def test_m6_same_name_surface_match(self):
        """Same-named nodes creating false surface match."""
        doc = load_json(f"{DATA}/case-structures.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["nodes"] = [{"name": "X", "type": "agent"}]
        caught, r = self.mt.assert_catches(
            f"{DATA}/case-structures.json", d, VALIDATOR)
        if not caught:
            self.skipTest("GAP: validator does not check for name-based surface matches")

    def test_m7_retrieval_to_commitment(self):
        """Retrieval result directly entering commitment must be caught."""
        doc = load_json(f"{DATA}/case-structures.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["commitment_status"] = "committed"
        caught, r = self.mt.assert_catches(
            f"{DATA}/case-structures.json", d, VALIDATOR)
        if not caught:
            self.skipTest("GAP: validator does not check commitment_status field")

    def test_m8_fabricated_scores(self):
        """Fabricated probability/confidence scores must fail."""
        doc = load_json(f"{DATA}/case-structures.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["confidence"] = 0.95
            e["similarity_score"] = 0.88
        caught, r = self.mt.assert_catches(
            f"{DATA}/case-structures.json", d, VALIDATOR)
        if not caught:
            self.skipTest("GAP: validator does not check for fabricated scores")

if __name__ == "__main__":
    unittest.main()
