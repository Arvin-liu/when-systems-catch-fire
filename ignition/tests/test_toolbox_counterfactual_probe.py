from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:  # Runtime CLI is stdlib-only; this is an optional test dependency.
    Draft202012Validator = None


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_counterfactual_probe as TOOL  # noqa: E402
import toolbox_function_os_evaluator as FUNCTION_OS  # noqa: E402


TOOL_PATH = IGNITION_ROOT / "tools/toolbox_counterfactual_probe.py"
INPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-counterfactual-probe-input-r0.schema.json"
OUTPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-counterfactual-probe-output-r0.schema.json"


def request() -> dict:
    function_spec = {
        "function_id": "FN-20261026-0001",
        "spec_version": "1.0.0",
        "name": "threshold_decision",
        "domain": "symbolic",
        "inputs": {"benefit": "integer", "cost": "integer"},
        "outputs": {"conclusion": "boolean"},
        "preconditions": [{"expression": "benefit >= 0", "message": "benefit is nonnegative"}],
        "postconditions": [{"expression": "conclusion == (benefit >= cost)", "message": "declared threshold decision"}],
        "effects_declared": ["pure"],
        "created_at": "2026-10-26T00:00:00Z",
    }
    return {
        "schema_version": "toolbox-counterfactual-probe-input-r0",
        "target_conclusion": {
            "conclusion_id": "decision-ready",
            "statement": "Declared benefit is at least the declared cost.",
        },
        "function_spec": function_spec,
        "baseline_inputs": {"benefit": 12, "cost": 10},
        "assumptions": [
            {"assumption_id": "benefit-estimate", "statement": "Benefit is caller declared.", "input_names": ["benefit"]},
            {"assumption_id": "cost-estimate", "statement": "Cost is caller declared.", "input_names": ["cost"]},
        ],
        "probes": [
            {
                "probe_id": "lower-benefit",
                "assumption_id": "benefit-estimate",
                "input_name": "benefit",
                "replacement_value": 8,
                "expected_direction": "TRUE_TO_FALSE",
                "admissibility_note": "Declared admissible for this bounded model only.",
            }
        ],
    }


class CounterfactualProbeTests(unittest.TestCase):
    def test_targeted_assumption_edit_flips_only_the_declared_model(self) -> None:
        result = TOOL.probe_counterfactual_fragility(request())
        probe = result["probes"][0]
        self.assertEqual(result["status"], "COUNTERFACTUAL_PROBE_REPORTED")
        self.assertEqual(result["baseline"]["output_value"], True)
        self.assertEqual(probe["observed_or_simulated_result"]["output_value"], False)
        self.assertEqual(probe["assumption_id"], "benefit-estimate")
        self.assertEqual(probe["conclusion_stability"], "FRAGILE_WITHIN_DECLARED_MODEL")
        self.assertEqual(probe["disconfirmation_status"], "EXPECTED_DIRECTION_OBSERVED_NOT_CONFIRMATORY")
        self.assertEqual(probe["admissibility"]["status"], "CALLER_DECLARED_NOT_VERIFIED")
        self.assertFalse(result["counterfactual_edit_is_actual_world_evidence"])
        self.assertFalse(result["source_evidence_mutated"])
        self.assertFalse(result["external_action_taken"])
        self.assertTrue(all(result["baseline"][key] for key in ("evaluable", "artifact_integrity_valid")))
        self.assertEqual(result["baseline"]["n7_status"], "PASS")

    def test_each_probe_starts_from_baseline_not_the_previous_edit(self) -> None:
        data = request()
        data["probes"] = [
            {
                "probe_id": "raise-cost",
                "assumption_id": "cost-estimate",
                "input_name": "cost",
                "replacement_value": 20,
                "expected_direction": "TRUE_TO_FALSE",
                "admissibility_note": "Declared admissible for this bounded model only.",
            },
            {
                "probe_id": "lower-benefit-but-still-above-baseline-cost",
                "assumption_id": "benefit-estimate",
                "input_name": "benefit",
                "replacement_value": 11,
                "expected_direction": "NO_CHANGE",
                "admissibility_note": "Declared admissible for this bounded model only.",
            },
        ]
        result = TOOL.probe_counterfactual_fragility(data)
        self.assertEqual(result["baseline"]["output_value"], True)
        self.assertEqual(result["probes"][0]["observed_or_simulated_result"]["output_value"], False)
        self.assertEqual(result["probes"][1]["observed_or_simulated_result"]["output_value"], True)
        self.assertEqual(result["probes"][1]["conclusion_stability"], "STABLE_WITHIN_DECLARED_MODEL")

    def test_direction_mismatch_is_preserved_as_disconfirming_not_filtered(self) -> None:
        data = request()
        data["probes"][0]["expected_direction"] = "FALSE_TO_TRUE"
        result = TOOL.probe_counterfactual_fragility(data)
        self.assertEqual(result["probes"][0]["observed_direction"], "TRUE_TO_FALSE")
        self.assertFalse(result["probes"][0]["expected_direction_match"])
        self.assertEqual(
            result["probes"][0]["disconfirmation_status"],
            "EXPECTED_DIRECTION_NOT_OBSERVED_PRESERVE_AS_DISCONFIRMING_RESULT",
        )

    def test_failed_probe_is_retained_without_rewriting_baseline_or_source(self) -> None:
        data = request()
        data["probes"][0]["replacement_value"] = -1
        result = TOOL.probe_counterfactual_fragility(data)
        probe = result["probes"][0]
        self.assertEqual(result["status"], "COUNTERFACTUAL_PROBE_WITH_FAILURES_RETAINED")
        self.assertEqual(result["baseline"]["output_value"], True)
        self.assertFalse(probe["observed_or_simulated_result"]["evaluable"])
        self.assertEqual(probe["observed_or_simulated_result"]["execution_status"], "PRECONDITION_FAILED")
        self.assertEqual(probe["conclusion_stability"], "NOT_ASSESSABLE")
        self.assertEqual(probe["disconfirmation_status"], "NOT_ASSESSABLE_FAILURE_PRESERVED")
        self.assertFalse(result["source_evidence_mutated"])

    def test_probe_must_bind_to_the_declared_load_bearing_assumption(self) -> None:
        data = request()
        data["probes"][0]["assumption_id"] = "cost-estimate"
        with self.assertRaisesRegex(TOOL.CounterfactualProbeError, "must bind the declared assumption"):
            TOOL.probe_counterfactual_fragility(data)

    def test_noop_edit_unknown_field_and_duplicate_probe_id_are_rejected(self) -> None:
        data = request()
        data["probes"][0]["replacement_value"] = 12
        with self.assertRaisesRegex(TOOL.CounterfactualProbeError, "must differ from the baseline"):
            TOOL.probe_counterfactual_fragility(data)
        data = request()
        data["extra"] = "not accepted"
        with self.assertRaisesRegex(TOOL.CounterfactualProbeError, "fields mismatch"):
            TOOL.probe_counterfactual_fragility(data)
        data = request()
        data["probes"].append(copy.deepcopy(data["probes"][0]))
        with self.assertRaisesRegex(TOOL.CounterfactualProbeError, "probe_id values must be unique"):
            TOOL.probe_counterfactual_fragility(data)

    @unittest.skipIf(Draft202012Validator is None, "jsonschema is an optional test dependency")
    def test_schema_contracts_validate_request_and_output(self) -> None:
        input_schema = json.loads(INPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
        output_schema = json.loads(OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(input_schema)
        Draft202012Validator.check_schema(output_schema)
        data = request()
        self.assertEqual(list(Draft202012Validator(input_schema).iter_errors(data)), [])
        result = TOOL.probe_counterfactual_fragility(data)
        self.assertEqual(list(Draft202012Validator(output_schema).iter_errors(result)), [])

    def test_results_match_repeated_single_function_os_evaluations(self) -> None:
        data = request()
        combined = TOOL.probe_counterfactual_fragility(data)
        baseline = FUNCTION_OS.build_evaluation_result(data["function_spec"], data["baseline_inputs"])
        edited = dict(data["baseline_inputs"])
        edited["benefit"] = 8
        probe = FUNCTION_OS.build_evaluation_result(data["function_spec"], edited)
        self.assertEqual(combined["baseline"]["output_value"], baseline["outputs"]["conclusion"])
        self.assertEqual(combined["probes"][0]["observed_or_simulated_result"]["output_value"], probe["outputs"]["conclusion"])
        self.assertEqual(combined["baseline"]["n7_status"], baseline["n7_validation"]["status"])
        self.assertRegex(combined["probes"][0]["observed_or_simulated_result"]["trace_sha256"], r"^[0-9a-f]{64}$")

    @unittest.skipIf(sys.version_info < (3, 10), "Function OS CLI requires Python >=3.10")
    def test_cli_returns_one_report_and_duplicate_json_keys_fail_without_partial_stdout(self) -> None:
        request_text = json.dumps(request(), ensure_ascii=False)
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=request_text,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["status"], "COUNTERFACTUAL_PROBE_REPORTED")
        duplicate = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input='{"schema_version":"x","schema_version":"y"}',
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(duplicate.returncode, 2)
        self.assertEqual(duplicate.stdout, "")
        self.assertIn("duplicate JSON key", duplicate.stderr)


if __name__ == "__main__":
    unittest.main()
