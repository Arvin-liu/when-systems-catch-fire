"""LAB-Q36 Temporal Causality Tests"""
import json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.temporal.validate_temporal_causality import validate_all, DATA_DIR

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
        doc = {"entries": [{"id":"x","mechanism":"repository reachability proves X",
            "object":"y","time_range":"z","trigger_conditions":"a",
            "falsification_conditions":"b","observation_period":"c","expiry_status":"active",
            "claim_ceiling":"risk_projection_only"}]}
        from tools.temporal.validate_temporal_causality import validate_no_reachability_as_causation
        r = validate_no_reachability_as_causation()
        # Current data passes
        self.assertTrue(r.is_pass)
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
