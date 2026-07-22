"""Q36-OBS observation-prediction gate — core freeze/bind/calibration tests.

Covers the P1 core semantics: freeze-before-reveal, outcome binding, deterministic
metric legality, immutability and failure preservation. Attack-surface fixtures
(P2) live in test_observation_prediction_gate.py.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
GATE = ROOT / "tools" / "observation" / "validate_observation_prediction_gate.py"
CLAIMS = ROOT / "data" / "agent" / "q34-claims-registry.json"
Q33_REJECTS = ROOT / "data" / "agent" / "q33-publication-rejects.json"
PILOT = ROOT / "data" / "observation" / "pilot-q34-closure-drift-prediction.json"
MAIN_HEAD = "06749dd118df7ade715b53f360e8177b09cdab49"


def run_gate(bundle_path, head=MAIN_HEAD):
    result = subprocess.run(
        [sys.executable, str(GATE), "--bundle", str(bundle_path),
         "--claims", str(CLAIMS), "--q33-rejects", str(Q33_REJECTS),
         "--current-main-head", head],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    try:
        report = json.loads(result.stdout)
    except Exception:
        report = {}
    return result.returncode, report


def _load_pilot():
    return json.loads(PILOT.read_text(encoding="utf-8"))


def _write_tmp(bundle, name):
    path = ROOT / ".cache" / "fulltest" / "q36-obs" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


class PilotPositiveTests(unittest.TestCase):
    def test_pilot_passes(self):
        code, report = run_gate(PILOT)
        self.assertEqual(code, 0, f"pilot must PASS; errors={report.get('errors')}")
        self.assertEqual(report.get("exit_name"), "GATE_PASS")
        self.assertEqual(report.get("decision", {}).get("verdict"), "ADMISSIBLE_WITHIN_DECLARED_SCOPE")


class FreezeBeforeRevealTests(unittest.TestCase):
    def test_prediction_issued_after_outcome_fails(self):
        b = _load_pilot()
        b["predictions"][0]["issued_at"] = "2026-07-21T07:00:00Z"  # after outcome available 06:00
        path = _write_tmp(b, "tmp-core-issued-after-outcome.json")
        code, report = run_gate(path)
        self.assertEqual(code, 3, f"expected TEMPORAL_LEAK; errors={report.get('errors')}")

    def test_input_cutoff_after_outcome_available_fails(self):
        b = _load_pilot()
        b["predictions"][0]["input_cutoff_time"] = "2026-07-21T07:00:00Z"
        path = _write_tmp(b, "tmp-core-cutoff-after-outcome.json")
        code, report = run_gate(path)
        self.assertEqual(code, 3, f"expected TEMPORAL_LEAK; errors={report.get('errors')}")

    def test_input_cutoff_before_outcome_passes(self):
        b = _load_pilot()
        # The positive pilot already has a cutoff before outcome availability and
        # its freeze record byte-binds that exact value. Mutating the cutoff while
        # reusing the old freeze record must not be treated as a legal positive.
        self.assertLess(
            b["predictions"][0]["input_cutoff_time"],
            b["observations"][0]["available_at"],
        )
        code, report = run_gate(PILOT)
        self.assertEqual(code, 0, f"legal cutoff must PASS; errors={report.get('errors')}")


class DeterministicMetricTests(unittest.TestCase):
    def test_interval_inversion_fails(self):
        b = _load_pilot()
        b["predictions"][0]["prediction_value"]["interval_lower"] = 5
        b["predictions"][0]["prediction_value"]["interval_upper"] = 2
        path = _write_tmp(b, "tmp-core-interval-inverted.json")
        code, report = run_gate(path)
        self.assertEqual(code, 9, f"expected ILLEGAL_PROBABILITY; errors={report.get('errors')}")

    def test_class_probability_out_of_range_fails(self):
        b = _load_pilot()
        b["predictions"][0]["prediction_type"] = "class"
        b["predictions"][0]["prediction_value"] = {
            "kind": "class", "class_label": "drift", "class_probability": 1.5}
        path = _write_tmp(b, "tmp-core-prob-out-of-range.json")
        code, report = run_gate(path)
        # schema (maximum: 1) fails closed first, or the legality check catches it
        self.assertIn(code, (2, 9), f"expected SCHEMA_ERROR or ILLEGAL_PROBABILITY; errors={report.get('errors')}")

    def test_metric_out_of_range_fails(self):
        b = _load_pilot()
        b["evaluations"][0]["metrics"]["brier_score"] = 1.7
        path = _write_tmp(b, "tmp-core-metric-out-of-range.json")
        code, report = run_gate(path)
        self.assertIn(code, (2, 9), f"expected SCHEMA_ERROR or ILLEGAL_PROBABILITY; errors={report.get('errors')}")


class CalibrationBindingTests(unittest.TestCase):
    def test_missing_sample_size_fails(self):
        b = _load_pilot()
        del b["evaluations"][0]["sample_size"]
        path = _write_tmp(b, "tmp-core-no-sample-size.json")
        code, report = run_gate(path)
        self.assertIn(code, (2, 16), f"expected SCHEMA_ERROR or CALIBRATION_UNBOUND; errors={report.get('errors')}")

    def test_missing_baseline_fails(self):
        b = _load_pilot()
        del b["evaluations"][0]["baseline_comparison"]
        path = _write_tmp(b, "tmp-core-no-baseline.json")
        code, report = run_gate(path)
        self.assertIn(code, (2, 16), f"expected SCHEMA_ERROR or CALIBRATION_UNBOUND; errors={report.get('errors')}")


class FailurePreservationTests(unittest.TestCase):
    def test_zero_accuracy_without_residual_fails(self):
        b = _load_pilot()
        b["evaluations"][0]["metrics"] = {"accuracy": 0}
        path = _write_tmp(b, "tmp-core-dropped-failure.json")
        code, report = run_gate(path)
        self.assertEqual(code, 17, f"expected FAILURE_DROPPED; errors={report.get('errors')}")

    def test_zero_accuracy_with_residual_passes(self):
        b = _load_pilot()
        b["evaluations"][0]["metrics"] = {"accuracy": 0}
        b["residuals"].append({
            "residual_id": "res-q34-closure-drift-001",
            "prediction_id": "pred-q34-closure-drift-001",
            "binding_id": "bind-q34-closure-drift-001",
            "residual_type": "missed_class",
            "magnitude": 1,
            "direction": "not_applicable",
            "expected_status": "unexpected",
            "unresolved_anomaly": True,
            "escalation_target": "q39_failure_memory",
            "claim_ceiling": "repository scope only; residual record, no causal inference",
            "do_not_infer_cause": True,
            "exact_head": MAIN_HEAD,
        })
        path = _write_tmp(b, "tmp-core-preserved-failure.json")
        code, report = run_gate(path)
        self.assertEqual(code, 0, f"preserved failure must PASS; errors={report.get('errors')}")


class ImmutabilityTests(unittest.TestCase):
    def test_superseded_without_link_fails(self):
        b = _load_pilot()
        b["predictions"][0]["status"] = "superseded"
        path = _write_tmp(b, "tmp-core-superseded-no-link.json")
        code, report = run_gate(path)
        self.assertEqual(code, 11, f"expected SILENT_PREDICTION_REWRITE; errors={report.get('errors')}")


if __name__ == "__main__":
    unittest.main()
