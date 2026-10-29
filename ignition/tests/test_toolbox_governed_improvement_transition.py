from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_governed_improvement_transition as tool  # noqa: E402


FIXTURE = IGNITION_ROOT / "tests/fixtures/toolbox-governed-improvement-transition/valid-input-r0.json"
SCHEMA = IGNITION_ROOT / "schemas/operations/governed-improvement-transition-r0.schema.json"


class GovernedImprovementTransitionTests(unittest.TestCase):
    def packet(self) -> dict:
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def analyze(self, packet: dict) -> dict:
        raw = json.dumps(packet, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return tool.analyze_bytes(raw)

    def codes(self, report: dict) -> set[str]:
        return set(report.get("finding_codes", []))

    def test_synthetic_transition_is_review_only_and_never_claims_acceptance(self) -> None:
        packet = self.packet()
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(packet)), [])

        report = self.analyze(packet)

        self.assertEqual(report["status"], "REVIEW_REQUIRED")
        self.assertEqual(report["finding_codes"], ["NEXT_ROUND_GAIN_NOT_MEASURED"])
        self.assertAlmostEqual(report["quality_deltas"][0]["comparable_directional_delta"], 0.2, places=12)
        self.assertTrue(report["cost_deltas"][0]["within_declared_guardrail"])
        self.assertFalse(report["improvement_accepted"])
        self.assertFalse(report["successor_promoted"])
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(report["source_authenticity"], "NOT_VERIFIED")

    def test_evaluator_or_benchmark_drift_requires_replay_on_predecessor_anchor(self) -> None:
        packet = self.packet()
        packet["evaluation_bindings"]["successor"]["evaluator_sha256"] = "d" * 64
        report = self.analyze(packet)
        self.assertIn("EVALUATION_ANCHOR_CHANGED", self.codes(report))
        self.assertIn("PREDECESSOR_ANCHOR_REPLAY_MISSING", self.codes(report))
        self.assertIsNone(report["quality_deltas"][0]["comparable_directional_delta"])

    def test_gain_disappearing_under_frozen_anchor_is_reported(self) -> None:
        packet = self.packet()
        packet["evaluation_bindings"]["successor"]["evaluator_sha256"] = "d" * 64
        packet["evaluation_bindings"]["successor_on_predecessor_anchor"] = {
            "status": "MEASURED",
            "evaluation_binding": copy.deepcopy(packet["evaluation_bindings"]["predecessor"]),
            "metrics": [{"metric_id": "frozen_experiment_success_rate", "unit": "fraction", "direction": "HIGHER_IS_BETTER", "value": 0.55}],
        }
        report = self.analyze(packet)
        self.assertIn("EVALUATION_ANCHOR_CHANGED", self.codes(report))
        self.assertIn("QUALITY_REGRESSION", self.codes(report))
        self.assertIn("QUALITY_GAIN_NOT_POSITIVE", self.codes(report))
        self.assertEqual(report["quality_deltas"][0]["comparison_basis"], "SUCCESSOR_REPLAYED_ON_PREDECESSOR_ANCHOR")

    def test_replay_claim_on_the_wrong_evaluation_anchor_is_not_comparable(self) -> None:
        packet = self.packet()
        packet["evaluation_bindings"]["successor"]["evaluator_sha256"] = "d" * 64
        packet["evaluation_bindings"]["successor_on_predecessor_anchor"] = {
            "status": "MEASURED",
            "evaluation_binding": copy.deepcopy(packet["evaluation_bindings"]["successor"]),
            "metrics": [{"metric_id": "frozen_experiment_success_rate", "unit": "fraction", "direction": "HIGHER_IS_BETTER", "value": 0.9}],
        }
        report = self.analyze(packet)
        self.assertIn("PREDECESSOR_ANCHOR_REPLAY_BINDING_MISMATCH", self.codes(report))
        self.assertIsNone(report["quality_deltas"][0]["comparable_directional_delta"])
        self.assertEqual(report["quality_deltas"][0]["comparison_basis"], "NOT_COMPARABLE")

    def test_cost_increase_above_declared_guardrail_is_reported(self) -> None:
        packet = self.packet()
        packet["cost_metrics"][0]["successor_value"] = 150
        report = self.analyze(packet)
        self.assertIn("COST_GUARDRAIL_EXCEEDED", self.codes(report))

    def test_failure_increase_above_declared_guardrail_is_reported(self) -> None:
        packet = self.packet()
        packet["failure_deltas"][0]["successor_count"] = 4
        report = self.analyze(packet)
        self.assertIn("FAILURE_GUARDRAIL_EXCEEDED", self.codes(report))

    def test_authority_expansion_is_never_accepted_as_quality_gain(self) -> None:
        packet = self.packet()
        packet["authority_scopes"]["successor"].append("network-access")
        report = self.analyze(packet)
        self.assertIn("AUTHORITY_SCOPE_ADDED", self.codes(report))
        self.assertEqual(report["authority_delta"]["added_scopes"], ["network-access"])
        self.assertFalse(report["improvement_accepted"])

    def test_rollback_must_bind_and_exercise_the_frozen_predecessor(self) -> None:
        packet = self.packet()
        packet["rollback"]["target_system_sha256"] = "f" * 64
        packet["rollback"]["exercise_status"] = "NOT_RUN"
        report = self.analyze(packet)
        self.assertIn("ROLLBACK_TARGET_MISMATCH", self.codes(report))
        self.assertIn("ROLLBACK_NOT_VERIFIED", self.codes(report))

    def test_measured_next_round_gain_is_reported_but_does_not_promote(self) -> None:
        packet = self.packet()
        packet["next_round_rnd_gain"] = {
            "status": "MEASURED",
            "metric": {
                "metric_id": "valid_experiments_per_hour", "unit": "experiments/hour",
                "direction": "HIGHER_IS_BETTER", "predecessor_value": 2, "successor_value": 3,
                "evaluator_sha256": "e" * 64, "benchmark_sha256": "f" * 64,
            },
        }
        report = self.analyze(packet)
        self.assertEqual(report["next_round_rnd_gain"]["directional_delta"], 1)
        self.assertNotIn("NEXT_ROUND_GAIN_NOT_MEASURED", self.codes(report))
        self.assertFalse(report["improvement_accepted"])
        self.assertFalse(report["successor_promoted"])

    def test_nonpositive_next_round_gain_is_not_called_improvement(self) -> None:
        packet = self.packet()
        packet["next_round_rnd_gain"] = {
            "status": "MEASURED",
            "metric": {
                "metric_id": "valid_experiments_per_hour", "unit": "experiments/hour",
                "direction": "HIGHER_IS_BETTER", "predecessor_value": 3, "successor_value": 2,
                "evaluator_sha256": "e" * 64, "benchmark_sha256": "f" * 64,
            },
        }
        self.assertIn("NEXT_ROUND_GAIN_NOT_POSITIVE", self.codes(self.analyze(packet)))

    def test_unknown_keys_duplicate_keys_and_duplicate_metrics_fail_closed(self) -> None:
        packet = self.packet()
        packet["successor_candidate"]["owner_approved"] = True
        self.assertEqual(self.analyze(packet)["status"], "INPUT_INVALID")

        duplicate = b'{"schema_version":"wrong","schema_version":"governed-improvement-transition-r0"}'
        self.assertEqual(tool.analyze_bytes(duplicate)["finding_codes"], ["DUPLICATE_JSON_KEY"])

        packet = self.packet()
        packet["quality_metrics"].append(copy.deepcopy(packet["quality_metrics"][0]))
        self.assertEqual(self.analyze(packet)["finding_codes"], ["DUPLICATE_METRIC_ID"])

    def test_malformed_utf8_nan_bool_number_and_oversized_input_fail_closed(self) -> None:
        self.assertEqual(tool.analyze_bytes(b"\xff")["finding_codes"], ["JSON_INVALID"])
        self.assertEqual(tool.analyze_bytes(b'{"x":NaN}')["finding_codes"], ["NONFINITE_JSON_NUMBER"])
        nested = b"[" * 2000 + b"0" + b"]" * 2000
        self.assertEqual(tool.analyze_bytes(nested)["finding_codes"], ["JSON_INVALID"])

        packet = self.packet()
        packet["quality_metrics"][0]["predecessor_value"] = True
        self.assertEqual(self.analyze(packet)["status"], "INPUT_INVALID")
        self.assertEqual(tool.analyze_bytes(b" " * (tool.MAX_INPUT_BYTES + 1))["finding_codes"], ["INPUT_LIMIT_EXCEEDED"])

        packet = self.packet()
        packet["quality_metrics"][0]["predecessor_value"] = -1e308
        packet["quality_metrics"][0]["successor_value"] = 1e308
        self.assertEqual(self.analyze(packet)["finding_codes"], ["ARITHMETIC_OVERFLOW"])

    def test_replay_metrics_must_match_the_quality_metric_contract(self) -> None:
        packet = self.packet()
        packet["evaluation_bindings"]["successor"]["benchmark_sha256"] = "d" * 64
        packet["evaluation_bindings"]["successor_on_predecessor_anchor"] = {
            "status": "MEASURED",
            "evaluation_binding": copy.deepcopy(packet["evaluation_bindings"]["predecessor"]),
            "metrics": [{"metric_id": "different_metric", "unit": "fraction", "direction": "HIGHER_IS_BETTER", "value": 0.8}],
        }
        self.assertEqual(self.analyze(packet)["finding_codes"], ["PREDECESSOR_ANCHOR_REPLAY_METRICS_MISMATCH"])

    def test_cli_is_repeatable_and_creates_no_files(self) -> None:
        payload = FIXTURE.read_bytes()
        command = [sys.executable, str(IGNITION_ROOT / "tools/toolbox_governed_improvement_transition.py"), "--stdin"]
        with tempfile.TemporaryDirectory() as tmp:
            before = set(Path(tmp).iterdir())
            first = subprocess.run(command, input=payload, capture_output=True, cwd=tmp, check=False)
            second = subprocess.run(command, input=payload, capture_output=True, cwd=tmp, check=False)
            self.assertEqual(set(Path(tmp).iterdir()), before)
        self.assertEqual(first.returncode, 0, first.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(first.stdout, second.stdout)
        result = json.loads(first.stdout)
        self.assertEqual(result["input_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertFalse(result["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
