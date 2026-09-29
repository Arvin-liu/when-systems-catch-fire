import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
TASK228 = ROOT / "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0"
TASK227 = ROOT / "ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0"
PACKET = Path("/tmp/ignition-227-component-isolation-r0/FINAL-OWNER-PACKET")
VALIDATOR = TASK227 / "tools/validate_policy.py"
TAXONOMY = TASK228 / "validator-failure-taxonomy.json"


class DiagnosticCrossCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(TAXONOMY.read_text(encoding="utf-8"))

    def test_exactly_six_original_policy_hashes_are_bound(self):
        self.assertEqual(self.data["policy_count"], 6)
        self.assertEqual(self.data["all_policy_bytes_unchanged"], True)
        for result in self.data["results"]:
            path = PACKET / "reference-m1" / f'{result["ref_id"]}.json'
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(digest, result["policy_sha256"])
            self.assertEqual(digest, result["policy_sha256_after"])

    def test_official_pass_fail_and_first_failure_match(self):
        families = {
            "REF-01": "FAMILY01", "REF-02": "FAMILY01",
            "REF-03": "FAMILY02", "REF-04": "FAMILY02",
            "REF-05": "FAMILY03", "REF-06": "FAMILY03",
        }
        for result in self.data["results"]:
            policy = PACKET / "reference-m1" / f'{result["ref_id"]}.json'
            proc = subprocess.run(
                [sys.executable, str(VALIDATOR), "--family", families[result["ref_id"]], str(policy)],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            combined = proc.stdout + "\n" + proc.stderr
            match = re.search(r"TASK227_POLICY_INVALID: (.+)", combined)
            official_failure = match.group(1).strip() if match else None
            diagnostic_failure = result["failures"][0]["detail"] if result["failures"] else None
            self.assertEqual(official_failure, result["official_first_failure"])
            self.assertEqual(diagnostic_failure, official_failure)
            self.assertEqual(proc.returncode == 0, result["diagnostic_pass"])
            self.assertEqual(proc.returncode == 0, result["validator_pass"])
            self.assertTrue(result["pass_fail_matches_official"])

    def test_all_first_failure_checks_are_true(self):
        self.assertTrue(self.data["first_failure_crosscheck_all_match"])
        self.assertTrue(self.data["pass_fail_crosscheck_all_match"])
        self.assertTrue(all(r["first_failure_matches_official"] for r in self.data["results"]))


if __name__ == "__main__":
    unittest.main()
