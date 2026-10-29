#!/usr/bin/env python3
"""Q38 fixtures drive the real validator CLI and assert stable exits."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools/retrieval/validate_evidence_retrieval_gate.py"
FIXTURES = ROOT / "data/retrieval/fixtures"
PILOT = ROOT / "data/retrieval/pilot-q38-repository-evidence-retrieval.json"


def run(path):
    return subprocess.run([sys.executable, str(VALIDATOR), "--bundle", str(path)], capture_output=True, text=True)


def matrix():
    expected = {
        1: 0, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8,
        9: 9, 10: 10, 11: 11, 12: 12, 13: 13, 14: 14, 15: 15,
        16: 16, 17: 17, 18: 18, 19: 19, 20: 20, 21: 21,
        22: 7, 23: 2, 24: 10, 25: 15, 26: 15, 27: 15,
        28: 15, 29: 15, 30: 15
    }
    rows = []
    for path in sorted(FIXTURES.glob("*.json")):
        number = int(path.name.split("-", 1)[0])
        rows.append((path, expected[number]))
    return rows


class EvidenceRetrievalGateTests(unittest.TestCase):
    def test_fixture_matrix_has_at_least_twenty_real_cli_cases(self):
        self.assertGreaterEqual(len(matrix()), 20)
        for path, expected in matrix():
            result = run(path)
            self.assertEqual(result.returncode, expected, f"{path.name}: expected {expected}, got {result.returncode}\n{result.stdout}\n{result.stderr}")

    def test_pilot_passes_real_gate(self):
        result = run(PILOT)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_every_required_evidence_kind_is_present(self):
        data = json.loads(PILOT.read_text())
        self.assertEqual({i["kind"] for i in data["evidence_items"]}, {"SUPPORT", "COUNTEREXAMPLE", "BOUNDARY_CASE", "NEGATIVE_RESULT", "FAILED_RETRIEVAL"})

    def test_negative_and_failed_items_export_to_q39(self):
        data = json.loads(PILOT.read_text())
        expected = {i["evidence_id"] for i in data["evidence_items"] if i["kind"] in {"COUNTEREXAMPLE", "NEGATIVE_RESULT", "FAILED_RETRIEVAL"}}
        actual = {e["evidence_id"] for e in data["q39_failure_exports"]}
        self.assertEqual(expected, actual)

    def test_successful_evidence_binds_actual_repository_bytes(self):
        data = json.loads(PILOT.read_text())
        retrieved = [i for i in data["evidence_items"] if i["kind"] != "FAILED_RETRIEVAL"]
        self.assertTrue(retrieved)
        for item in retrieved:
            self.assertEqual(item["retrieval_status"], "RETRIEVED_REPOSITORY_BYTES")
            self.assertEqual(item["source_locator"], item["source_binding"]["path"])
            self.assertEqual(item["source_digest"], item["source_binding"]["sha256"])
            self.assertEqual(item["exact_head"], item["source_binding"]["exact_commit"])

    def test_unperformed_retrieval_does_not_invent_content_evidence(self):
        data = json.loads(PILOT.read_text())
        failed = next(i for i in data["evidence_items"] if i["kind"] == "FAILED_RETRIEVAL")
        self.assertEqual(failed["retrieval_status"], "FAILED_UNPERFORMED")
        self.assertIsNone(failed["source_binding"])
        self.assertIsNone(failed["source_digest"])


if __name__ == "__main__":
    unittest.main()
