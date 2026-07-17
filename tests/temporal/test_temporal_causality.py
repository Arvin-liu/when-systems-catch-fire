"""LAB-Q36 Temporal Causality Tests — V2 Deep Audit (broken mutation repaired)"""
import json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.temporal.validate_temporal_causality import validate_all, DATA_DIR, validate_no_reachability_as_causation

class TemporalNormalTests(unittest.TestCase):
    def test_n1_all_pass(self):
        r = validate_all()
        self.assertTrue(r.is_pass, r.report())
    def test_n2_predictions_have_all_fields(self):
        doc = json.loads((DATA_DIR / "prediction-records.json").read_text())
        for e in doc["entries"]:
            for f in ["object","mechanism","time_range","trigger_conditions","falsification_conditions","observation_period","expiry_status"]:
                self.assertIn(f, e)
    def test_n3_observations_link_predictions(self):
        preds = json.loads((DATA_DIR / "prediction-records.json").read_text())
        obs = json.loads((DATA_DIR / "observation-records.json").read_text())
        pred_ids = {e["id"] for e in preds["entries"]}
        for e in obs["entries"]:
            self.assertIn(e.get("prediction_id"), pred_ids)

class TemporalAttackTests(unittest.TestCase):
    def test_a1_reachability_not_causation(self):
        """Reachability used as mechanism must fail — REPAIRED: uses real mutation."""
        from tools.lab.mutation_runner import MutationTest, load_json, deep_copy
        mt = MutationTest("Q36_atk")
        doc = load_json("data/temporal/prediction-records.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["mechanism"] = "repository reachability proves the outcome"
        try:
            mt.mutate_file("data/temporal/prediction-records.json", d)
            r = validate_all()
            self.assertFalse(r.is_pass, f"Reachability as causation must fail: {r.report()}")
        finally:
            mt.restore()

    def test_a2_no_causal_proof_ceiling(self):
        doc = json.loads((DATA_DIR / "prediction-records.json").read_text())
        for e in doc["entries"]:
            self.assertNotIn("proof", e.get("claim_ceiling",""))

    def test_a3_main_not_modified(self):
        import subprocess
        r = subprocess.run(["git","-C",str(ROOT),"log","origin/main","--oneline","-1"], capture_output=True, text=True)
        if r.returncode == 0: self.assertIn("d1bedb07", r.stdout)

if __name__ == "__main__":
    unittest.main()
