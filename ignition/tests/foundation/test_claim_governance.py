import json
import math
import subprocess
import sys
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/foundation"))
import build_function_asset_census
from knowledge_corpus_admission import admission_for_path


class ClaimGovernanceTests(unittest.TestCase):
    def run_ok(self, *args):
        result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator(self):
        self.run_ok(sys.executable, "tools/foundation/validate_claim_governance.py")

    def test_census_is_deterministic(self):
        self.run_ok(sys.executable, "tools/foundation/build_function_asset_census.py", "--check")

    def test_task186_research_report_is_accounted_but_not_a_function_source(self):
        fixture = json.loads((ROOT / "tests/foundation/fixtures/task186_research_surface_isolation.json").read_text(encoding="utf-8"))
        path = fixture["external_research_report_path"]
        admission = admission_for_path(path)
        self.assertEqual(admission.classification, fixture["admission_classification"])
        self.assertTrue(admission.provenance_only)
        self.assertFalse(admission.auto_discovery)

        manifest_path = ROOT / "data/foundation/repository-path-classification/classification-manifest.jsonl"
        manifest = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        row = next((item for item in manifest if item["path"] == "ignition/" + path), None)
        self.assertIsNotNone(row)
        self.assertEqual(row["category"], fixture["path_manifest_category"])

        tracked_path = ("ignition/" + path + "\0").encode("utf-8")
        with mock.patch.object(
            build_function_asset_census.subprocess,
            "check_output",
            return_value=tracked_path,
        ), mock.patch.object(build_function_asset_census, "migration_paths", return_value=[]):
            self.assertNotIn(path, build_function_asset_census.tracked_text_files())

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
