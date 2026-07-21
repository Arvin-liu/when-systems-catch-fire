"""Q36-OBS observation-prediction gate — attack fixture tests.

Each test runs the deterministic validator CLI against a fixture and asserts the
fail-closed exit code. The gate must never PASS by free text; every attack fixture
exercises the real validator end to end.
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
FIXTURES = ROOT / "data" / "observation" / "fixtures"
MAIN_HEAD = "06749dd118df7ade715b53f360e8177b09cdab49"


def run_gate(bundle_path):
    result = subprocess.run(
        [sys.executable, str(GATE), "--bundle", str(bundle_path),
         "--claims", str(CLAIMS), "--q33-rejects", str(Q33_REJECTS),
         "--current-main-head", MAIN_HEAD],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    try:
        report = json.loads(result.stdout)
    except Exception:
        report = {}
    return result.returncode, report


class ObservationPredictionGateFixtureTests(unittest.TestCase):
    def assert_exit(self, name, expected):
        code, report = run_gate(FIXTURES / name)
        if isinstance(expected, tuple):
            ok = code in expected
            exp = f"one of {expected}"
        else:
            ok = code == expected
            exp = str(expected)
        self.assertTrue(ok, f"{name}: expected {exp}, got {code} "
                            f"({report.get('exit_name')}); errors={report.get('errors')}")

    # 1. freeze before reveal + independent outcome -> PASS
    def test_01_frozen_then_independent_outcome(self):
        self.assert_exit("01-frozen-then-independent-outcome.json", 0)

    # 2. outcome visible, prediction back-written -> fail closed
    def test_02_backwritten_prediction(self):
        self.assert_exit("02-backwritten-prediction.json", 3)

    # 3. input snapshot contains future fields -> fail closed
    def test_03_future_input_snapshot(self):
        self.assert_exit("03-future-input-snapshot.json", 3)

    # 4. prediction target != outcome definition -> fail closed
    def test_04_target_definition_mismatch(self):
        self.assert_exit("04-target-definition-mismatch.json", 4)

    # 5. window drift -> fail closed
    def test_05_window_drift(self):
        self.assert_exit("05-window-drift.json", 4)

    # 6. unit/scope mismatch -> fail closed
    def test_06_unit_scope_mismatch(self):
        self.assert_exit("06-unit-scope-mismatch.json", 4)

    # 7. wrong/expired exact head -> fail closed
    def test_07_stale_exact_head(self):
        self.assert_exit("07-stale-exact-head.json", 5)

    # 8. silent post-reveal prediction modification -> fail closed
    def test_08_silent_prediction_rewrite(self):
        self.assert_exit("08-silent-prediction-rewrite.json", 11)

    # 9. delete failed outcomes, keep only successes -> fail closed
    def test_09_selective_outcome_deletion(self):
        self.assert_exit("09-selective-outcome-deletion.json", 12)

    # 10. excluded outcome without reason -> fail closed
    def test_10_exclusion_without_reason(self):
        self.assert_exit("10-exclusion-without-reason.json", 12)

    # 11. model self-generated outcome as sole evidence -> fail closed
    def test_11_self_generated_outcome(self):
        self.assert_exit("11-self-generated-outcome.json", 10)

    # 12. interval inverted -> fail closed
    def test_12_interval_inverted(self):
        self.assert_exit("12-interval-inverted.json", 9)

    # 13. finite-sample accuracy expanded to universal predictability -> fail closed
    def test_13_finite_sample_to_universal(self):
        self.assert_exit("13-finite-sample-to-universal.json", 14)

    # 14. correlation / high fit written as causal mechanism -> fail closed
    def test_14_correlation_as_causation(self):
        self.assert_exit("14-correlation-as-causation.json", 15)

    # 15. uncommitted Q34 hypothesis marked as current prediction claim -> fail closed
    def test_15_uncommitted_q34_claim(self):
        self.assert_exit("15-uncommitted-q34-claim.json", 6)

    # 16. no authorized Q35 subject issued the prediction -> fail closed
    def test_16_missing_q35_authority(self):
        self.assert_exit("16-missing-q35-authority.json", (2, 7))

    # 17. Q33-rights-unknown data published directly -> fail closed
    def test_17_q33_rights_bypass(self):
        self.assert_exit("17-q33-rights-bypass.json", 8)

    # 18. negative result / residual preserved -> PASS, residual record generated
    def test_18_negative_result_preserved(self):
        self.assert_exit("18-negative-result-preserved.json", 0)

    # 19. abstain/defer legally preserved -> PASS, not counted as success, not deleted
    def test_19_abstain_defer_preserved(self):
        self.assert_exit("19-abstain-defer-preserved.json", 0)

    # 20. real retrospective replay pilot -> PASS, honestly marked
    def test_20_retrospective_replay_pilot(self):
        code, report = run_gate(FIXTURES / "20-retrospective-replay-pilot.json")
        self.assertEqual(code, 0, f"retrospective replay must PASS; errors={report.get('errors')}")
        bundle = json.loads((FIXTURES / "20-retrospective-replay-pilot.json").read_text(encoding="utf-8"))
        self.assertIn("RETROSPECTIVE_REPLAY_NOT_LIVE_FORECAST",
                      bundle["predictions"][0]["claim_ceiling"])


if __name__ == "__main__":
    unittest.main()
