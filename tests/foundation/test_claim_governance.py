import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ClaimGovernanceTests(unittest.TestCase):
    def run_ok(self, *args):
        result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator(self):
        self.run_ok(sys.executable, "tools/foundation/validate_claim_governance.py")

    def test_census_is_deterministic(self):
        self.run_ok(sys.executable, "tools/foundation/build_function_asset_census.py", "--check")

    def test_identity_examples_cover_ten_types(self):
        rows = [json.loads(line) for line in (ROOT / "tests/foundation/fixtures/function_identity_examples.jsonl").read_text().splitlines() if line.strip()]
        self.assertEqual(len(rows), 10)
        self.assertEqual(len({row["identity"] for row in rows}), 10)

    def test_d183_term_count_counterexample(self):
        mu, lambda_a, lambda_b, lambda_ab = 10.0, 1.0, 1.0, 9.0
        phi_before = 1 / math.log(mu / lambda_a) + 1 / math.log(mu / lambda_b)
        phi_after = 1 / math.log(mu / lambda_ab)
        self.assertGreater(phi_after, phi_before)
        self.assertLess(math.exp(-phi_after), math.exp(-phi_before))

    def test_d260_math_and_interpretation_split(self):
        score = lambda p: p / (1 - p)
        self.assertEqual(score(0.5), 1.0)
        self.assertGreater(score(0.9), score(0.5))
        self.assertGreater(1 / (1 - 0.9) ** 2, 0)

    def test_zero_product_converse_fails_with_zero_divisors(self):
        self.assertEqual((2 * 3) % 6, 0)
        self.assertNotEqual(2 % 6, 0)
        self.assertNotEqual(3 % 6, 0)


if __name__ == "__main__":
    unittest.main()
