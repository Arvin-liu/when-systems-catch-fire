from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_component_comparison as comparison  # noqa: E402


INPUT_SCHEMA = json.loads((IGNITION_ROOT / "schemas/operations/toolbox-component-comparison-input-r0.schema.json").read_text(encoding="utf-8"))
OUTPUT_SCHEMA = json.loads((IGNITION_ROOT / "schemas/operations/toolbox-component-comparison-output-r0.schema.json").read_text(encoding="utf-8"))
REAL_TASK_INPUT = IGNITION_ROOT / "tests/fixtures/toolbox-component-comparison/pr264-actions-tool-scope-r0.json"


def digest(label: str) -> str:
    import hashlib
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def matched_input() -> dict:
    context = {
        "environment_sha256": digest("isolated-python-fixture-environment"),
        "evaluator_sha256": digest("frozen-exact-contract-scorer-v1"),
        "resource_metric_id": "wall_time",
        "resource_metric_unit": "ms",
    }
    use_case = {
        "use_case_id": "bounded-summary",
        "value_basis": "The fixed summary output required by the caller.",
        "input_contract_sha256": digest("input-schema-v1"),
        "output_contract_sha256": digest("output-schema-v1"),
        "evidence_ref": "fixture://matched-case",
    }
    result_old = {"outcome": "PASS", "quality_score": 800, "resource_cost": 12, "permission_rank": 1, "adverse_effect_ids": []}
    result_new = {"outcome": "PASS", "quality_score": 900, "resource_cost": 10, "permission_rank": 1, "adverse_effect_ids": []}
    return {
        "schema_version": "toolbox-component-comparison-input-r0",
        "comparison_id": "matched-improvement-case",
        "incumbent": {"tool_id": "maintenance.old", "version": "1.0.0"},
        "proposed_successor": {"tool_id": "maintenance.new", "version": "1.0.0"},
        "evaluation_context": context,
        "incumbent_use_cases": [use_case],
        "successor_use_cases": [dict(use_case)],
        "paired_results": [{
            "use_case_id": use_case["use_case_id"],
            "input_sha256": digest("exact-input-r0"),
            "output_contract_sha256": use_case["output_contract_sha256"],
            "environment_sha256": context["environment_sha256"],
            "evaluator_sha256": context["evaluator_sha256"],
            "evidence_ref": "fixture://paired-result",
            "incumbent": result_old,
            "proposed_successor": result_new,
        }],
    }


class ToolboxComponentComparisonTests(unittest.TestCase):
    def test_pr264_scope_trial_preserves_coexistence_and_unknown_cost(self) -> None:
        raw = REAL_TASK_INPUT.read_bytes()
        result = comparison.compare(raw)
        self.assertEqual(result["scope_disposition"], "COEXIST_DISTINCT_SCOPE")
        self.assertEqual(result["performance_comparison_status"], "COMPARISON_UNKNOWN")
        self.assertEqual(result["scope"]["incumbent_unique_use_case_ids"], ["detailed_per_step_timeline"])
        self.assertEqual(result["scope"]["successor_unique_use_case_ids"], ["plan_run_artifact_attribution"])
        self.assertEqual(result["paired_result_summary"]["missing_cost_use_case_ids"], ["job_interval_summary"])
        self.assertFalse(result["governance_boundary"]["tool_retired_or_registry_changed"])
        self.assertFalse(result["governance_boundary"]["execution_authorized"])
        Draft202012Validator(INPUT_SCHEMA).validate(json.loads(raw))
        Draft202012Validator(OUTPUT_SCHEMA).validate(result)

    def test_cli_entrypoint_emits_same_result_as_local_function(self) -> None:
        raw = REAL_TASK_INPUT.read_bytes()
        completed = subprocess.run(
            [sys.executable, str(IGNITION_ROOT / "tools/toolbox_component_comparison.py"), "--stdin"],
            input=raw,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(json.loads(completed.stdout), comparison.compare(raw))

    def test_complete_matched_successor_can_be_supported_for_replacement(self) -> None:
        result = comparison.compare(json.dumps(matched_input()).encode())
        self.assertEqual(result["scope_disposition"], "REPLACEMENT_SUPPORTED_AS_DECLARED")
        self.assertEqual(result["performance_comparison_status"], "COMPARABLE_AS_DECLARED")
        self.assertEqual(result["paired_result_summary"]["successor_advantage_use_case_ids"], ["bounded-summary"])
        self.assertFalse(result["governance_boundary"]["tool_retired_or_registry_changed"])

    def test_new_permission_or_adverse_effect_prevents_replacement(self) -> None:
        payload = matched_input()
        payload["paired_results"][0]["proposed_successor"]["permission_rank"] = 2
        payload["paired_results"][0]["proposed_successor"]["adverse_effect_ids"] = ["new-network-access"]
        result = comparison.compare(json.dumps(payload).encode())
        self.assertEqual(result["scope_disposition"], "COEXIST_DISTINCT_SCOPE")
        self.assertEqual(result["paired_result_summary"]["incumbent_advantage_use_case_ids"], ["bounded-summary"])

    def test_missing_pair_preserves_uncertainty(self) -> None:
        payload = matched_input()
        payload["paired_results"] = []
        result = comparison.compare(json.dumps(payload).encode())
        self.assertEqual(result["scope_disposition"], "COMPARISON_UNKNOWN")
        self.assertEqual(result["paired_result_summary"]["missing_pair_use_case_ids"], ["bounded-summary"])
        self.assertIn("matched, low-cost task", result["next_low_cost_comparison"])

    def test_contract_mismatch_is_not_treated_as_coverage(self) -> None:
        payload = matched_input()
        payload["successor_use_cases"][0]["output_contract_sha256"] = digest("different-output")
        payload["paired_results"] = []
        result = comparison.compare(json.dumps(payload).encode())
        self.assertEqual(result["scope_disposition"], "COMPARISON_UNKNOWN")
        self.assertEqual(result["scope"]["same_id_contract_mismatch_use_case_ids"], ["bounded-summary"])

    def test_duplicate_keys_oversized_input_and_unhashable_outcome_fail_closed(self) -> None:
        with self.assertRaises(comparison.ComparisonInputError):
            comparison.compare(b'{"schema_version":"x","schema_version":"y"}')
        with self.assertRaises(comparison.ComparisonInputError):
            comparison.compare(b" " * (comparison.MAX_INPUT_BYTES + 1))
        payload = matched_input()
        payload["paired_results"][0]["incumbent"]["outcome"] = []
        with self.assertRaises(comparison.ComparisonInputError):
            comparison.compare(json.dumps(payload).encode())


if __name__ == "__main__":
    unittest.main()
