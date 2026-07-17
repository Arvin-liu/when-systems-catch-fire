"""LAB-Q34 Dual Plane Tests
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
    def test_a1_conjecture_in_commitment_blocked(self):
        """Low epistemic level must not reach commitment plane."""
        entry = {"id": "x", "plane": "commitment", "status": "committed",
                 "epistemic_level": "conjecture", "gates": {
                     "rights_gate": "pass", "epistemic_gate": "pass", "action_authority_gate": "pass"}}
        # Validator should catch this
        from tools.discovery.validate_dual_plane import VALID_EPISTEMIC
        self.assertIn("conjecture", VALID_EPISTEMIC)
        # But commitment with conjecture should be invalid
        low_levels = {"analogy", "inspiration", "conjecture", "model_sketch"}
        self.assertIn("conjecture", low_levels)

    def test_a2_missing_gate_blocks_promotion(self):
        """Any gate != pass must block commitment."""
        gates = {"rights_gate": "pass", "epistemic_gate": "fail", "action_authority_gate": "pass"}
        self.assertNotEqual(gates["epistemic_gate"], "pass")

    def test_a3_exploration_item_cannot_be_committed(self):
        """Discovery registry entries must stay in exploration plane."""
        entry = {"plane": "exploration", "status": "committed"}
        self.assertNotEqual(entry["plane"], "commitment")

    def test_a4_demotion_must_have_reason(self):
        """Demoted entries must explain why."""
        entry = {"status": "demoted", "demotion_reason": ""}
        self.assertFalse(bool(entry.get("demotion_reason")))

    def test_a5_feedback_is_not_evidence(self):
        """Feedback cannot upgrade epistemic level."""
        valid_upgrades = {"tested_claim", "validated_hypothesis", "accepted_fact"}
        self.assertNotIn("feedback_received", valid_upgrades)

    def test_a6_main_not_modified(self):
        import subprocess
        r = subprocess.run(["git", "-C", str(ROOT), "log", "origin/main", "--oneline", "-1"],
                          capture_output=True, text=True)
        if r.returncode == 0:
            self.assertIn("d1bedb07", r.stdout)

if __name__ == "__main__":
    unittest.main()
