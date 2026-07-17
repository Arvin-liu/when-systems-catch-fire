"""LAB-Q37 Analogy Audit Tests"""
import json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.analogy.validate_analogy_audit import validate_all, DATA_DIR

class AnalogyNormalTests(unittest.TestCase):
    def test_n1_all_pass(self):
        r = validate_all()
        self.assertTrue(r.is_pass, r.report())
    def test_n2_all_analogies_have_domains(self):
        doc = json.loads((DATA_DIR / "analogy-candidates.json").read_text())
        for e in doc["entries"]:
            self.assertIn("source_domain", e)
            self.assertIn("target_domain", e)
    def test_n3_residue_exists_for_each(self):
        doc = json.loads((DATA_DIR / "analogy-candidates.json").read_text())
        for e in doc["entries"]:
            self.assertTrue(len(e.get("non_correspondence_residue", [])) > 0)

class AnalogyAttackTests(unittest.TestCase):
    def test_a1_perfect_analogy_is_suspicious(self):
        doc = json.loads((DATA_DIR / "analogy-candidates.json").read_text())
        for e in doc["entries"]:
            self.assertTrue(len(e.get("negative_transfer", [])) > 0, "Every analogy must have negative transfer")
    def test_a2_no_formal_equivalence_claim(self):
        doc = json.loads((DATA_DIR / "analogy-candidates.json").read_text())
        for e in doc["entries"]:
            self.assertNotEqual(e.get("claim_ceiling"), "formal_equivalence")
    def test_a3_hidden_premise_must_be_exposed(self):
        doc = json.loads((DATA_DIR / "analogy-candidates.json").read_text())
        for e in doc["entries"]:
            self.assertTrue(len(e.get("hidden_premise_transfer", [])) > 0)
    def test_a4_main_not_modified(self):
        import subprocess
        r = subprocess.run(["git","-C",str(ROOT),"log","origin/main","--oneline","-1"], capture_output=True, text=True)
        if r.returncode == 0: self.assertIn("d1bedb07", r.stdout)

if __name__ == "__main__":
    unittest.main()
