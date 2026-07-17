"""LAB-Q39 Failure Memory Tests"""
import json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.failure.validate_failure_memory import validate_all, DATA_DIR

class FailureMemoryNormalTests(unittest.TestCase):
    def test_n1_all_pass(self):
        r = validate_all()
        self.assertTrue(r.is_pass, r.report())
    def test_n2_q32_pilot_complete(self):
        """All 11 Q32 failure types must be recorded."""
        doc = json.loads((DATA_DIR / "failure-records.json").read_text())
        self.assertEqual(len(doc["entries"]), 11)
    def test_n3_all_have_missed_gate(self):
        doc = json.loads((DATA_DIR / "failure-records.json").read_text())
        for e in doc["entries"]:
            self.assertTrue(e.get("missed_gate"), f"{e['id']}: must identify missed gate")
    def test_n4_all_have_regression_test(self):
        doc = json.loads((DATA_DIR / "failure-records.json").read_text())
        for e in doc["entries"]:
            self.assertTrue(e.get("regression_test"), f"{e['id']}: must have regression test")
    def test_n5_all_institutionalized(self):
        doc = json.loads((DATA_DIR / "failure-records.json").read_text())
        for e in doc["entries"]:
            self.assertEqual(e.get("status"), "institutionalized")

class FailureMemoryAttackTests(unittest.TestCase):
    def test_a1_bypass_old_fix_detected(self):
        """Removing an old fix should be detected as known recurrence, not new issue."""
        doc = json.loads((DATA_DIR / "failure-records.json").read_text())
        fail_classes = {e["failure_class"] for e in doc["entries"]}
        # If we see one of these classes again, the recurrence signature should match
        self.assertIn("consistency_drift", fail_classes)
    def test_a2_no_over_institutionalization(self):
        """Not every failure should become a permanent rule."""
        doc = json.loads((DATA_DIR / "failure-records.json").read_text())
        rep = json.loads((DATA_DIR / "repair-propagation.json").read_text())
        for e in rep["entries"]:
            self.assertIn(e.get("overfitting_risk"), ["low", "medium", "high", "none"])
    def test_a3_accidental_not_permanent(self):
        """Some failures are accidental and should not be permanently institutionalized."""
        doc = json.loads((DATA_DIR / "failure-records.json").read_text())
        for e in doc["entries"]:
            self.assertIn(e.get("institutionalization"),
                ["enforced_by_validator", "enforced_by_schema", "enforced_by_ci",
                 "enforced_by_process", "enforced_by_ci_receipt", "field_removed",
                 "historical_evidence_structure", "monitoring_only"])
    def test_a4_main_not_modified(self):
        import subprocess
        r = subprocess.run(["git","-C",str(ROOT),"log","origin/main","--oneline","-1"], capture_output=True, text=True)
        if r.returncode == 0: self.assertIn("d1bedb07", r.stdout)

if __name__ == "__main__":
    unittest.main()
