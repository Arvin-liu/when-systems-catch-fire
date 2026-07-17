"""LAB-Q34 Dual Plane Tests — V2 Deep Audit (pseudo-tests repaired)
LAB / SPECULATIVE / NON-AUTHORITATIVE / NOT CURRENT / NOT MERGE-AUTHORIZED
"""
import json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.discovery.validate_dual_plane import validate_all, Result, DATA_DIR

class DualPlaneNormalTests(unittest.TestCase):
    def test_n1_all_pass(self):
        r = validate_all()
        self.assertTrue(r.is_pass, r.report())

    def test_n2_no_exploration_in_commitment_registry(self):
        for f in sorted(DATA_DIR.glob("*.json")):
            doc = json.loads(f.read_text())
            if doc["plane_type"] == "commitment_candidate":
                for e in doc.get("entries", []):
                    self.assertEqual(e["plane"], "commitment")

    def test_n3_committed_items_have_all_gates_pass(self):
        for f in sorted(DATA_DIR.glob("*.json")):
            doc = json.loads(f.read_text())
            for e in doc.get("entries", []):
                if e.get("status") == "committed":
                    g = e.get("gates", {})
                    self.assertEqual(g.get("rights_gate"), "pass")
                    self.assertEqual(g.get("epistemic_gate"), "pass")
                    self.assertEqual(g.get("action_authority_gate"), "pass")

    def test_n4_residue_has_blocked_reasons(self):
        for f in sorted(DATA_DIR.glob("*.json")):
            doc = json.loads(f.read_text())
            for e in doc.get("entries", []):
                if e.get("status") == "residue":
                    self.assertTrue(len(e.get("promotion_blocked_reasons", [])) > 0)

    def test_n5_q29r_unchanged(self):
        q = ROOT / "docs/publication/works/when-an-army-believes-its-own-back.md"
        if q.exists():
            import hashlib
            self.assertEqual(hashlib.sha256(q.read_bytes()).hexdigest(),
                "c135acd35a2232f0a6b3f933db482932a9fe5d5add51f870af97901faac90d4b")

class DualPlaneAttackTests(unittest.TestCase):
    """Attack tests — REPAIRED in deep audit V2. All now call real validator."""

    def test_a1_conjecture_in_commitment_blocked(self):
        """Low epistemic level must not reach commitment plane — real mutation."""
        from tools.lab.mutation_runner import MutationTest, load_json, deep_copy
        mt = MutationTest("Q34_atk")
        doc = load_json("data/discovery/commitment-candidates.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["epistemic_level"] = "conjecture"
            e["plane"] = "commitment"
            e["status"] = "committed"
            if "gates" not in e:
                e["gates"] = {"rights_gate": "pass", "epistemic_gate": "pass", "action_authority_gate": "pass"}
        try:
            mt.mutate_file("data/discovery/commitment-candidates.json", d)
            r = validate_all()
            self.assertFalse(r.is_pass, f"Conjecture in commitment must fail: {r.report()}")
        finally:
            mt.restore()

    def test_a2_missing_gate_blocks_promotion(self):
        """Any gate != pass must block commitment — real mutation."""
        from tools.lab.mutation_runner import MutationTest, load_json, deep_copy
        mt = MutationTest("Q34_atk")
        doc = load_json("data/discovery/commitment-candidates.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            if e.get("status") == "committed":
                if "gates" not in e:
                    e["gates"] = {}
                e["gates"]["epistemic_gate"] = "fail"
        try:
            mt.mutate_file("data/discovery/commitment-candidates.json", d)
            r = validate_all()
            self.assertFalse(r.is_pass, f"Failed gate must block commitment: {r.report()}")
        finally:
            mt.restore()

    def test_a3_exploration_item_cannot_be_committed(self):
        """Discovery registry entries must stay in exploration plane — real mutation."""
        from tools.lab.mutation_runner import MutationTest, load_json, deep_copy
        mt = MutationTest("Q34_atk")
        doc = load_json("data/discovery/discovery-registry.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["plane"] = "commitment"
            e["status"] = "committed"
        try:
            mt.mutate_file("data/discovery/discovery-registry.json", d)
            r = validate_all()
            self.assertFalse(r.is_pass, f"Exploration->commitment must fail: {r.report()}")
        finally:
            mt.restore()

    def test_a4_residue_without_blocked_reasons(self):
        """Residue without blocked reasons must fail — real mutation."""
        from tools.lab.mutation_runner import MutationTest, load_json, deep_copy
        mt = MutationTest("Q34_atk")
        doc = load_json("data/discovery/residue-records.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            if e.get("status") == "residue":
                e["promotion_blocked_reasons"] = []
        try:
            mt.mutate_file("data/discovery/residue-records.json", d)
            r = validate_all()
            self.assertFalse(r.is_pass, f"Residue without reasons must fail: {r.report()}")
        finally:
            mt.restore()

    def test_a5_analogy_epistemic_blocked(self):
        """Analogy-level epistemic cannot enter commitment — real mutation."""
        from tools.lab.mutation_runner import MutationTest, load_json, deep_copy
        mt = MutationTest("Q34_atk")
        doc = load_json("data/discovery/commitment-candidates.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["epistemic_level"] = "analogy"
            e["plane"] = "commitment"
            e["status"] = "committed"
            if "gates" not in e:
                e["gates"] = {"rights_gate": "pass", "epistemic_gate": "pass", "action_authority_gate": "pass"}
        try:
            mt.mutate_file("data/discovery/commitment-candidates.json", d)
            r = validate_all()
            self.assertFalse(r.is_pass, f"Analogy in commitment must fail: {r.report()}")
        finally:
            mt.restore()

    def test_a6_main_not_modified(self):
        import subprocess
        r = subprocess.run(["git", "-C", str(ROOT), "log", "origin/main", "--oneline", "-1"],
                          capture_output=True, text=True)
        if r.returncode == 0:
            self.assertIn("d1bedb07", r.stdout)

if __name__ == "__main__":
    unittest.main()
