from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_function_os_evaluator.py"
PACKAGE_ROOT = IGNITION_ROOT / "function-os-candidate/v0.2"
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
sys.path.insert(0, str(PACKAGE_ROOT))
import toolbox_function_os_evaluator as TOOL  # noqa: E402


def request(*, x: int = 3, expression: str = "result == x + y") -> tuple[dict, dict]:
    spec = {
        "function_id": "FN-20261025-0001",
        "spec_version": "1.0.0",
        "name": "add",
        "domain": "symbolic",
        "inputs": {"x": "integer", "y": "integer"},
        "outputs": {"result": "integer"},
        "preconditions": [{"expression": "x >= 0", "message": "x is nonnegative"}],
        "postconditions": [{"expression": expression, "message": "result is the declared expression"}],
        "effects_declared": ["pure"],
        "created_at": "2026-10-25T00:00:00Z",
    }
    return spec, {"x": x, "y": 7}


@unittest.skipUnless(sys.version_info >= (3, 10), "Function OS v0.2 requires Python >=3.10")
class FunctionOSEvaluatorTests(unittest.TestCase):
    def test_executes_one_bounded_pure_spec_and_validates_trace(self) -> None:
        spec, inputs = request()
        result = TOOL.build_evaluation_result(spec, inputs)
        self.assertEqual(result["execution_status"], "OK")
        self.assertEqual(result["policy_status"], "OK")
        self.assertEqual(result["outputs"], {"result": 10})
        self.assertEqual(result["n7_validation"]["status"], "PASS")
        self.assertTrue(result["artifact_integrity"]["valid"])
        self.assertEqual(result["pipeline_nodes"], ["N1", "N2", "N3", "N4", "N5", "N6", "N7"])
        self.assertEqual(result["registry_write"], "NOT_REQUESTED_N9_NOT_INVOKED")
        self.assertNotIn("truth", result["claim_ceiling"].lower())

    def test_precondition_failure_is_preserved_without_registry_write(self) -> None:
        spec, inputs = request(x=-1)
        result = TOOL.build_evaluation_result(spec, inputs)
        self.assertEqual(result["execution_status"], "PRECONDITION_FAILED")
        self.assertEqual(result["outputs"], {})
        self.assertEqual(result["registry_write"], "NOT_REQUESTED_N9_NOT_INVOKED")

    def test_rejects_calls_attributes_exponents_and_multiple_outputs(self) -> None:
        for expression in (
            "result == __import__('os')",
            "result == x.__class__",
            "result == x ** 1000000",
        ):
            with self.subTest(expression=expression):
                spec, inputs = request(expression=expression)
                with self.assertRaises(TOOL.FunctionOSRunError):
                    TOOL.build_evaluation_result(spec, inputs)
        spec, inputs = request()
        spec["outputs"] = {"first": "integer", "second": "integer"}
        with self.assertRaisesRegex(TOOL.FunctionOSRunError, "exactly one output"):
            TOOL.build_evaluation_result(spec, inputs)

    def test_rejects_unbounded_inputs_and_nonpure_effects(self) -> None:
        spec, inputs = request(x=10**13)
        with self.assertRaisesRegex(TOOL.FunctionOSRunError, "magnitude limit"):
            TOOL.build_evaluation_result(spec, inputs)
        spec, inputs = request()
        spec["effects_declared"] = ["io"]
        with self.assertRaisesRegex(TOOL.FunctionOSRunError, "pure"):
            TOOL.build_evaluation_result(spec, inputs)

    def test_rejects_oversized_intermediates_and_division_by_zero_before_pipeline(self) -> None:
        spec, inputs = request(x=10**12, expression="result == x*x*x*x*x*x*x*x*x")
        with self.assertRaisesRegex(TOOL.FunctionOSRunError, "oversized intermediate"):
            TOOL.build_evaluation_result(spec, inputs)
        spec, inputs = request(expression="result == x / y")
        inputs["y"] = 0
        with self.assertRaisesRegex(TOOL.FunctionOSRunError, "bounded arithmetic contract"):
            TOOL.build_evaluation_result(spec, inputs)

    def test_cli_rejects_duplicate_json_keys_without_partial_stdout(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input='{"function_spec":{},"function_spec":{},"inputs":{}}',
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("duplicate JSON key", completed.stderr)

    def test_cli_rejects_oversized_request_without_partial_stdout(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=" " * (TOOL.MAX_REQUEST_BYTES + 1),
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("exceeds 16 KiB", completed.stderr)


if __name__ == "__main__":
    unittest.main()
