"""Q35 responsibility-authority-action-trace gate — attack fixture tests.

Each test runs the deterministic validator CLI against a fixture and asserts the
fail-closed exit code. The gate must never PASS by free text.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
GATE = ROOT / "tools" / "agent" / "validate_responsibility_gate.py"
CLAIMS = ROOT / "data" / "agent" / "q34-claims-registry.json"
Q33_REJECTS = ROOT / "data" / "agent" / "q33-publication-rejects.json"
FIXTURES = ROOT / "data" / "agent" / "fixtures"
MAIN_HEAD = "06749dd118df7ade715b53f360e8177b09cdab49"
NOW = "2026-07-21T00:00:00Z"


def run_gate(bundle_path):
    result = subprocess.run(
        [sys.executable, str(GATE), "--bundle", str(bundle_path),
         "--claims", str(CLAIMS), "--q33-rejects", str(Q33_REJECTS),
         "--current-main-head", MAIN_HEAD, "--now", NOW],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    try:
        report = json.loads(result.stdout)
    except Exception:
        report = {}
    return result.returncode, report


class ResponsibilityGateFixtureTests(unittest.TestCase):
    def assert_exit(self, name, expected):
        code, report = run_gate(FIXTURES / name)
        self.assertEqual(code, expected,
                         f"{name}: expected {expected}, got {code}; errors={report.get('errors')}")

    def test_01_legal_low_risk(self):
        self.assert_exit("01-legal-low-risk.json", 0)

    def test_02_self_grant(self):
        self.assert_exit("02-self-grant.json", 7)

    def test_03_model_name_as_authority(self):
        self.assert_exit("03-model-name-as-authority.json", 8)

    def test_04_expired_grant(self):
        self.assert_exit("04-expired-grant.json", 5)

    def test_05_revoked_grant(self):
        self.assert_exit("05-revoked-grant.json", 5)

    def test_06_scope_breach(self):
        self.assert_exit("06-scope-breach.json", 6)

    def test_07_broken_delegation(self):
        self.assert_exit("07-broken-delegation.json", 9)

    def test_08_self_all_roles_high_risk(self):
        self.assert_exit("08-self-all-roles-high-risk.json", 12)

    def test_09_stale_exact_head(self):
        self.assert_exit("09-stale-exact-head.json", 13)

    def test_10_claim_ceiling_breach(self):
        self.assert_exit("10-claim-ceiling-breach.json", 11)

    def test_11_uncommitted_hypothesis_action(self):
        self.assert_exit("11-uncommitted-hypothesis-action.json", 10)

    def test_12_trajectory_tamper(self):
        self.assert_exit("12-trajectory-tamper.json", 14)

    def test_13_trajectory_chain_break(self):
        self.assert_exit("13-trajectory-chain-break.json", 14)

    def test_14_silent_rollback_rewrite(self):
        self.assert_exit("14-silent-rollback-rewrite.json", 16)

    def test_15_many_hands_forced_owner(self):
        self.assert_exit("15-many-hands-forced-owner.json", 17)

    def test_16_q33_gate_bypass(self):
        self.assert_exit("16-q33-gate-bypass.json", 15)


class ResponsibilityGateContractTests(unittest.TestCase):
    def test_gate_emits_machine_readable_report(self):
        code, report = run_gate(FIXTURES / "01-legal-low-risk.json")
        for key in ("gate", "exit_code", "exit_name", "decision", "errors"):
            self.assertIn(key, report)
        self.assertEqual(report["gate"], "q35_responsibility_gate")

    def test_gate_fail_closed_on_malformed_json(self):
        bad = FIXTURES / "_malformed_tmp.json"
        bad.write_text("{ not json ")
        try:
            code, _ = run_gate(bad)
            self.assertEqual(code, 2)
        finally:
            bad.unlink()

    def test_legal_bundle_decision_authorize(self):
        code, report = run_gate(FIXTURES / "01-legal-low-risk.json")
        self.assertEqual(code, 0)
        self.assertEqual(report.get("decision"), "AUTHORIZE")


if __name__ == "__main__":
    unittest.main()
