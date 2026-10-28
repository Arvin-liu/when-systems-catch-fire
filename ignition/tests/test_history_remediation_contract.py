from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = ROOT / "data/governance/history-remediation-register.json"
ENTRY_SCHEMA_PATH = ROOT / "schemas/governance/history-remediation-entry.schema.json"


class HistoryRemediationContractTest(unittest.TestCase):
    def setUp(self):
        self.register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
        self.schema = json.loads(ENTRY_SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_remediation_entries_match_their_schema_without_rewriting_history(self):
        entries = self.register["entries"]
        entry_ids = [entry["entry_id"] for entry in entries]
        self.assertEqual(len(entry_ids), len(set(entry_ids)), "history entry IDs must be unique")
        remediation_entries = [entry for entry in entries if "remediation_status" in entry]
        self.assertTrue(remediation_entries, "register must contain remediation evidence")
        validator = Draft7Validator(self.schema)
        for entry in remediation_entries:
            with self.subTest(entry_id=entry["entry_id"]):
                validator.validate(entry)

    def test_summary_is_derived_from_remediation_evidence(self):
        remediation_entries = [entry for entry in self.register["entries"] if "remediation_status" in entry]
        counts = Counter(entry["remediation_status"] for entry in remediation_entries)
        summary = self.register["summary"]
        self.assertEqual(summary["total_entries"], len(remediation_entries))
        self.assertEqual(summary["completed"], counts["COMPLETED"])
        self.assertEqual(summary["in_progress"], counts["IN_PROGRESS"])
        self.assertEqual(summary["pending"], counts["PENDING"])
        self.assertEqual(summary["not_applicable"], counts["NOT_APPLICABLE"])


if __name__ == "__main__":
    unittest.main()
