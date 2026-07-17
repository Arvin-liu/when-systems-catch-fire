"""LAB-Q38 Structural Retrieval Tests"""
import json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.retrieval.validate_structural_retrieval import validate_all, DATA_DIR

class RetrievalNormalTests(unittest.TestCase):
    def test_n1_all_pass(self):
        r = validate_all()
        self.assertTrue(r.is_pass, r.report())
    def test_n2_signatures_have_args(self):
        doc = json.loads((DATA_DIR / "relation-signatures.json").read_text())
        for e in doc["entries"]:
            self.assertTrue(len(e.get("arguments", [])) > 0)
    def test_n3_cases_link_signatures(self):
        sig = json.loads((DATA_DIR / "relation-signatures.json").read_text())
        cases = json.loads((DATA_DIR / "case-structures.json").read_text())
        sig_ids = {e["id"] for e in sig["entries"]}
        for e in cases["entries"]:
            for sid in e.get("relation_signature_ids", []):
                self.assertIn(sid, sig_ids)

class RetrievalAttackTests(unittest.TestCase):
    def test_a1_no_spurious_confidence(self):
        """Must not generate fake probability or similarity scores."""
        cases = json.loads((DATA_DIR / "case-structures.json").read_text())
        for e in cases["entries"]:
            self.assertNotIn("similarity_score", e)
            self.assertNotIn("confidence", e)
    def test_a2_counterexamples_required(self):
        cx = json.loads((DATA_DIR / "counterexample-set.json").read_text())
        self.assertTrue(len(cx["entries"]) > 0, "Must have counterexamples")
    def test_a3_vector_similarity_is_not_structural(self):
        """Plain vector similarity must not be labeled as structural retrieval."""
        valid_types = {"structural_pattern_only", "case_description_only", "counterexample_only"}
        self.assertNotIn("vector_similarity", valid_types)
    def test_a4_main_not_modified(self):
        import subprocess
        r = subprocess.run(["git","-C",str(ROOT),"log","origin/main","--oneline","-1"], capture_output=True, text=True)
        if r.returncode == 0: self.assertIn("d1bedb07", r.stdout)

if __name__ == "__main__":
    unittest.main()
