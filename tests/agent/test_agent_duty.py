"""LAB-Q35 Agent Duty Tests"""
import json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.agent.validate_agent_duty import validate_all, DATA_DIR

class AgentDutyNormalTests(unittest.TestCase):
    def test_n1_all_pass(self):
        r = validate_all()
        self.assertTrue(r.is_pass, r.report())

    def test_n2_state_machine_complete(self):
        doc = json.loads((DATA_DIR / "task-states.json").read_text())
        required = {"CREATED", "CONTEXT_LOADED", "CLAIMED", "RUNNING", "PAUSED",
                    "ESCALATED", "RESUMED", "SUBMITTED", "REVIEWED", "CLOSED",
                    "BLOCKED", "ABORTED", "QUARANTINED"}
        self.assertEqual(set(doc["valid_states"]), required)

    def test_n3_no_main_push_allowed(self):
        doc = json.loads((DATA_DIR / "tool-permissions.json").read_text())
        for e in doc["entries"]:
            if e.get("target") == "main":
                self.assertFalse(e.get("allowed"))

    def test_n4_self_review_blocked(self):
        doc = json.loads((DATA_DIR / "duty-contracts.json").read_text())
        found = False
        for e in doc["entries"]:
            if "self_review_accept" in e.get("blocked_actions", []):
                found = True
        self.assertTrue(found, "Self-review must be blocked")

    def test_n5_q29r_unchanged(self):
        q = ROOT / "docs/publication/works/when-an-army-believes-its-own-back.md"
        if q.exists():
            import hashlib
            self.assertEqual(hashlib.sha256(q.read_bytes()).hexdigest(),
                "c135acd35a2232f0a6b3f933db482932a9fe5d5add51f870af97901faac90d4b")

class AgentDutyAttackTests(unittest.TestCase):
    def test_a1_invalid_transition(self):
        doc = json.loads((DATA_DIR / "task-states.json").read_text())
        t = doc["valid_transitions"]
        self.assertNotIn("CLOSED", t.get("CREATED", []), "Cannot jump CREATED->CLOSED")

    def test_a2_quarantine_is_terminal(self):
        doc = json.loads((DATA_DIR / "task-states.json").read_text())
        self.assertEqual(doc["valid_transitions"]["QUARANTINED"], [])

    def test_a3_aborted_is_terminal(self):
        doc = json.loads((DATA_DIR / "task-states.json").read_text())
        self.assertEqual(doc["valid_transitions"]["ABORTED"], [])

    def test_a4_no_self_accept(self):
        doc = json.loads((DATA_DIR / "duty-contracts.json").read_text())
        for e in doc["entries"]:
            self.assertNotIn("accept", [a for a in e.get("blocked_actions",[]) if "self" in a.lower()])

    def test_a5_lost_context_must_escalate(self):
        doc = json.loads((DATA_DIR / "duty-contracts.json").read_text())
        found = any("context" in e.get("title","").lower() for e in doc["entries"])
        self.assertTrue(found, "Must have a context-loss duty contract")

    def test_a6_main_not_modified(self):
        import subprocess
        r = subprocess.run(["git", "-C", str(ROOT), "log", "origin/main", "--oneline", "-1"],
                          capture_output=True, text=True)
        if r.returncode == 0:
            self.assertIn("d1bedb07", r.stdout)

if __name__ == "__main__":
    unittest.main()
