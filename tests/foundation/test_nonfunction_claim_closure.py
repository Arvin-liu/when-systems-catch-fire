import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class NonFunctionClaimClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adjudicator = load_module("tools/foundation/adjudicate_nonfunction_claims.py", "task100_adjudicator")
        cls.fixtures = [json.loads(line) for line in (ROOT / "tests/foundation/fixtures/nonfunction_claim_gate_cases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]

    def run_ok(self, *args):
        result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_closure_validator(self):
        self.run_ok(sys.executable, "tools/foundation/validate_nonfunction_claim_closure.py")

    def test_generator_is_deterministic(self):
        self.run_ok(sys.executable, "tools/foundation/adjudicate_nonfunction_claims.py", "--check")

    def test_regression_gate_cases(self):
        for row in self.fixtures:
            claim_class = self.adjudicator.classify(row["text"])
            kind = self.adjudicator.assertion_type(claim_class)
            disposition = self.adjudicator.disposition_for(claim_class, "CURRENT_REPOSITORY_RECORD", row["text"], None, None)
            audits = self.adjudicator.audits_for(claim_class, kind, row["text"], disposition, "CURRENT_REPOSITORY_RECORD")
            self.assertEqual(audits[row["expected_gate"]], row["expected_result"], row["case_id"])
            self.assertEqual(disposition, row["expected_disposition"], row["case_id"])

    def test_rebound_normalization_removes_renaming_adjectives(self):
        left = self.adjudicator.semantic_rebound_text("Physical grand unification proved impossible")
        right = self.adjudicator.semantic_rebound_text("Structural grand unification proved impossible")
        self.assertEqual(left, right)

    def test_candidate_discovery_is_conservative_but_multilingual(self):
        self.assertTrue(self.adjudicator.candidate("This theorem proves a universal result."))
        self.assertTrue(self.adjudicator.candidate("该机制导致普遍结果。"))
        self.assertFalse(self.adjudicator.candidate("ordinary navigation entry"))


if __name__ == "__main__":
    unittest.main()
