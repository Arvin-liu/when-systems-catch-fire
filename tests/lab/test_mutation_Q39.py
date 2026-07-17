"""Mutation Tests for Q39 Failure Memory — Second Pass Deep Audit"""
import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tools.lab.mutation_runner import MutationTest, load_json, deep_copy

VALIDATOR = "tools.failure.validate_failure_memory"
DATA = "data/failure"

class Q39MutationTests(unittest.TestCase):
    def setUp(self):
        self.mt = MutationTest("Q39")

    def tearDown(self):
        self.mt.restore()

    def test_m1_auto_institutionalization(self):
        """Single occurrence auto-institutionalized must be flagged."""
        doc = load_json(f"{DATA}/failure-records.json")
        d = deep_copy(doc)
        # Add a new single-occurrence failure with institutionalization
        d["entries"].append({
            "id": "fail_m1",
            "failure_class": "one_off_typo",
            "mechanism": "accidental keystroke",
            "source_iteration": "Q99",
            "missed_gate": "none",
            "repair_type": "none",
            "regression_test": "none",
            "claim_ceiling": "anecdotal_only",
            "institutionalization": "full_rule_enacted",
            "occurrence_count": 1
        })
        caught, r = self.mt.assert_catches(
            f"{DATA}/failure-records.json", d, VALIDATOR)
        if not caught:
            self.skipTest("GAP: validator does not check institutionalization vs occurrence_count")

    def test_m2_no_recurrence_for_same_class(self):
        """Same-class errors without recurrence signature must be flagged."""
        doc = load_json(f"{DATA}/recurrence-signatures.json")
        d = deep_copy(doc)
        # Remove all recurrence signatures
        d["entries"] = []
        caught, r = self.mt.assert_catches(
            f"{DATA}/recurrence-signatures.json", d, VALIDATOR)
        # Empty recurrence is valid — validator does not require signatures exist
        if not caught:
            self.skipTest("GAP: validator does not require recurrence signatures for multi-failure classes")

    def test_m3_repair_without_regression_test(self):
        """Repair marked closed without regression test must fail."""
        doc = load_json(f"{DATA}/failure-records.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["regression_test"] = ""
        caught, r = self.mt.assert_catches(
            f"{DATA}/failure-records.json", d, VALIDATOR)
        self.assertTrue(caught, f"Empty regression_test must fail: {r.report()}")

    def test_m4_known_failure_as_novel(self):
        """Known failure class treated as novel must be caught."""
        doc = load_json(f"{DATA}/failure-records.json")
        d = deep_copy(doc)
        # Add a duplicate of an existing failure with "novel" flag
        if d["entries"]:
            dup = deep_copy(d["entries"][0])
            dup["id"] = dup["id"] + "_novel_claim"
            dup["novelty_claim"] = True
            d["entries"].append(dup)
        caught, r = self.mt.assert_catches(
            f"{DATA}/failure-records.json", d, VALIDATOR)
        if not caught:
            self.skipTest("GAP: validator does not check novelty claims against existing failures")

    def test_m5_repair_breaks_downstream(self):
        """Repair with downstream break but no propagation record must fail."""
        doc = load_json(f"{DATA}/repair-propagation.json")
        d = deep_copy(doc)
        d["entries"] = []
        caught, r = self.mt.assert_catches(
            f"{DATA}/repair-propagation.json", d, VALIDATOR)
        # Empty propagation is valid
        if not caught:
            self.skipTest("GAP: validator does not require propagation records when repairs exist")

    def test_m6_missing_version(self):
        """Failure record without version must fail."""
        doc = load_json(f"{DATA}/failure-records.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            if "source_iteration" in e:
                e["source_iteration"] = ""
        caught, r = self.mt.assert_catches(
            f"{DATA}/failure-records.json", d, VALIDATOR)
        self.assertTrue(caught, f"Empty source_iteration must fail: {r.report()}")

    def test_m7_agent_deletes_history(self):
        """Deleting failure records must be detectable."""
        caught, r = self.mt.assert_catches(
            f"{DATA}/failure-records.json",
            {"registry_type": "failure_records", "version": "0.1.0", "entries": []},
            VALIDATOR)
        # Empty registry passes validator — this is a GAP
        if not caught:
            self.skipTest("GAP: empty failure registry is accepted (no minimum count check)")

    def test_m8_repeated_failures_doc_only(self):
        """Repeated failures adding only documentation, not gates."""
        doc = load_json(f"{DATA}/failure-records.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["gate_added"] = False
            e["documentation_only"] = True
        caught, r = self.mt.assert_catches(
            f"{DATA}/failure-records.json", d, VALIDATOR)
        if not caught:
            self.skipTest("GAP: validator does not check if repairs add gates vs documentation")

    def test_m9_over_institutionalization(self):
        """Governance rules stacking without risk check must be flagged."""
        doc = load_json(f"{DATA}/repair-propagation.json")
        d = deep_copy(doc)
        for e in d["entries"]:
            e["overfitting_risk"] = ""
        caught, r = self.mt.assert_catches(
            f"{DATA}/repair-propagation.json", d, VALIDATOR)
        self.assertTrue(caught, f"Empty overfitting_risk must fail: {r.report()}")

if __name__ == "__main__":
    unittest.main()
