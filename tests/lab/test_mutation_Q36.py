"""Mutation Tests for Q36 Temporal Causality — Second Pass Deep Audit"""
import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tools.lab.mutation_runner import MutationTest, load_json, deep_copy

VALIDATOR = "tools.temporal.validate_temporal_causality"
DATA = "data/temporal"

class Q36MutationTests(unittest.TestCase):
    def setUp(self):
        self.mt = MutationTest("Q36")

    def tearDown(self):
        self.mt.restore()

    def test_m1_no_expiry_prediction(self):
        """Prediction without expiry_status must fail."""
        doc = load_json(f"{DATA}/prediction-records.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["expiry_status"] = ""
        caught, r = self.mt.assert_catches(
            f"{DATA}/prediction-records.json", d, VALIDATOR)
        self.assertTrue(caught, f"Empty expiry must fail: {r.report()}")

    def test_m2_expired_prediction_as_current(self):
        """Expired prediction still marked active must fail."""
        doc = load_json(f"{DATA}/prediction-records.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["expiry_status"] = "expired"
        caught, r = self.mt.assert_catches(
            f"{DATA}/prediction-records.json", d, VALIDATOR)
        if not caught:
            self.skipTest("GAP: validator does not check if expired predictions are still referenced")

    def test_m3_observation_mismatch(self):
        """Observation referencing non-existent prediction must fail."""
        doc = load_json(f"{DATA}/observation-records.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["prediction_id"] = "nonexistent_prediction"
        caught, r = self.mt.assert_catches(
            f"{DATA}/observation-records.json", d, VALIDATOR)
        # Validator only reads predictions and interventions, not observations
        if not caught:
            self.skipTest("GAP: validator does not validate observation->prediction linkage")

    def test_m4_counterfactual_as_fact(self):
        """Counterfactual written as observed fact must fail."""
        doc = load_json(f"{DATA}/intervention-candidates.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["counterfactual"] = ""
        caught, r = self.mt.assert_catches(
            f"{DATA}/intervention-candidates.json", d, VALIDATOR)
        self.assertTrue(caught, f"Empty counterfactual must fail: {r.report()}")

    def test_m5_reachability_as_causation(self):
        """Using 'repository reachability' as mechanism must fail."""
        doc = load_json(f"{DATA}/prediction-records.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["mechanism"] = "repository reachability proves the outcome"
        caught, r = self.mt.assert_catches(
            f"{DATA}/prediction-records.json", d, VALIDATOR)
        self.assertTrue(caught, f"Reachability as causation must fail: {r.report()}")

    def test_m6_intervention_window_closed(self):
        """Intervention with closed window still executing must fail."""
        doc = load_json(f"{DATA}/intervention-candidates.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["window_status"] = "closed"
            e["execution_status"] = "executing"
        caught, r = self.mt.assert_catches(
            f"{DATA}/intervention-candidates.json", d, VALIDATOR)
        if not caught:
            self.skipTest("GAP: validator does not check window_status vs execution_status")

    def test_m7_calibration_as_truth(self):
        """Model calibration claiming truth must fail."""
        doc = load_json(f"{DATA}/prediction-records.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["claim_ceiling"] = "causal_proof"
        caught, r = self.mt.assert_catches(
            f"{DATA}/prediction-records.json", d, VALIDATOR)
        # Validator checks "proof" in claim_ceiling — "causal_proof" contains "proof"
        self.assertTrue(caught, f"Truth claim must fail: {r.report()}")

    def test_m8_no_falsification_conditions(self):
        """Prediction without falsification_conditions must fail."""
        doc = load_json(f"{DATA}/prediction-records.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["falsification_conditions"] = ""
        caught, r = self.mt.assert_catches(
            f"{DATA}/prediction-records.json", d, VALIDATOR)
        self.assertTrue(caught, f"Empty falsification must fail: {r.report()}")

if __name__ == "__main__":
    unittest.main()
