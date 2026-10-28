from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools import run_full_regression as runner


ROOT = Path(__file__).resolve().parents[1]


class FullRegressionRunnerContractTests(unittest.TestCase):
    def test_contract_document_matches_code_summary(self) -> None:
        document = json.loads((ROOT / "data/operations/full-regression-runner-r1.json").read_text(encoding="utf-8"))
        self.assertEqual(document, runner.contract_summary())

    def test_repository_root_is_script_derived(self) -> None:
        repo_root, app_root = runner.discover_repository_root(ROOT.parent)
        self.assertEqual(repo_root, ROOT.parent.resolve())
        self.assertEqual(app_root, ROOT)

    def test_canonical_discovery_is_app_root_relative(self) -> None:
        self.assertEqual(runner.TEST_DISCOVERY_ARGS, ("-m", "unittest", "discover", "-s", "tests", "-p", "test*.py"))
        self.assertEqual(runner.contract_summary()["canonical_working_directory"], "ignition")

    def test_dependency_preflight_is_read_only_and_explicit(self) -> None:
        result = runner.dependency_preflight()
        self.assertEqual(result["requirements_file"], "ignition/requirements-foundation.txt")
        self.assertFalse(result["install_performed"])
        self.assertTrue(result["isolated_environment_required"])
        self.assertEqual([row["name"] for row in result["requirements"]], ["sympy", "z3-solver", "jsonschema"])

    def test_unittest_summary_pass_fail_and_skip_semantics(self) -> None:
        passed = runner.parse_unittest_result("\nRan 4 tests in 0.100s\n\nOK\n", "", 0)
        self.assertEqual((passed["status"], passed["tests_run"], passed["failures"], passed["errors"], passed["skipped"]), ("PASS", 4, 0, 0, 0))
        failed = runner.parse_unittest_result("\nRan 4 tests in 0.100s\n\nFAILED (failures=1, errors=2)\n", "", 1)
        self.assertEqual((failed["status"], failed["failures"], failed["errors"]), ("FAIL", 1, 2))
        skipped = runner.parse_unittest_result("\nRan 4 tests in 0.100s\n\nOK (skipped=1)\n", "", 0)
        self.assertEqual((skipped["status"], skipped["skipped"]), ("FAIL", 1))


if __name__ == "__main__":
    unittest.main()
