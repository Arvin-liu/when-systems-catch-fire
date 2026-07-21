"""Q34 discovery-commitment gate — attack fixture tests.

Each test runs the deterministic validator CLI against a fixture and asserts the
fail-closed exit code. The gate must never PASS by free text; it must return a
stable, machine-readable exit code.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
GATE = ROOT / "tools" / "discovery" / "validate_commitment_gate.py"
REGISTRY = ROOT / "data" / "discovery" / "evidence-resolvable-registry.json"
FIXTURES = ROOT / "data" / "discovery" / "fixtures"
CLAIMS = ROOT / "data" / "discovery" / "claims"
MAIN_HEAD = "81edff4039619b8343a82cb1b84785c8a9f6a990"


def run_gate(claim_path):
    result = subprocess.run(
        [sys.executable, str(GATE), "--claim", str(claim_path),
         "--registry", str(REGISTRY), "--current-main-head", MAIN_HEAD],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    try:
        report = json.loads(result.stdout)
    except Exception:
        report = {}
    return result.returncode, report


class CommitmentGateFixtureTests(unittest.TestCase):
    def assert_exit(self, path, expected_code):
        code, report = run_gate(path)
        self.assertEqual(
            code, expected_code,
            f"{path.name}: expected exit {expected_code}, got {code}; errors={report.get('errors')}")

    def test_01_allow_commit_positive(self):
        self.assert_exit(FIXTURES / "01-allow-commit-positive.json", 0)

    def test_02_premature_no_evidence(self):
        self.assert_exit(FIXTURES / "02-premature-no-evidence.json", 5)

    def test_03_circular_self_proof(self):
        self.assert_exit(FIXTURES / "03-circular-self-proof.json", 4)

    def test_04_claim_ceiling_breach(self):
        self.assert_exit(FIXTURES / "04-claim-ceiling-breach.json", 6)

    def test_05_analogy_as_mechanism(self):
        self.assert_exit(FIXTURES / "05-analogy-as-mechanism.json", 7)

    def test_06_stale_exact_head(self):
        self.assert_exit(FIXTURES / "06-stale-exact-head.json", 8)

    def test_07_selective_reporting(self):
        self.assert_exit(FIXTURES / "07-selective-reporting.json", 9)

    def test_08_retraction_new_positive(self):
        self.assert_exit(FIXTURES / "08-retraction-new-positive.json", 0)

    def test_09_uncommitted_path_deferred(self):
        self.assert_exit(FIXTURES / "09-uncommitted-path-deferred.json", 0)

    def test_10_q33_global_compliance_breach(self):
        self.assert_exit(FIXTURES / "10-q33-global-compliance-breach.json", 6)

    def test_11_external_world_no_attestation(self):
        self.assert_exit(FIXTURES / "11-external-world-no-attestation.json", 12)

    def test_q33_seven_components_pilot_committable(self):
        code, report = run_gate(CLAIMS / "q33-seven-governance-components-current.json")
        self.assertEqual(code, 0, f"pilot claim must pass; errors={report.get('errors')}")
        self.assertEqual(report.get("decision"), "COMMIT")


class CommitmentGateContractTests(unittest.TestCase):
    def test_gate_emits_machine_readable_report(self):
        code, report = run_gate(FIXTURES / "01-allow-commit-positive.json")
        for key in ("gate", "exit_code", "exit_name", "decision", "errors"):
            self.assertIn(key, report)
        self.assertEqual(report["gate"], "q34_commitment_gate")

    def test_gate_is_fail_closed_on_malformed_json(self):
        bad = FIXTURES / "_malformed_tmp.json"
        bad.write_text("{ not valid json ")
        try:
            code, _ = run_gate(bad)
            self.assertEqual(code, 2)
        finally:
            bad.unlink()

    def test_committed_state_requires_independent_reviewer(self):
        # verifier == discovered_by actor must be rejected (self-approval)
        import copy, tempfile
        claim = json.loads((FIXTURES / "01-allow-commit-positive.json").read_text())
        claim["verifier"] = dict(claim["discovered_by"])
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, dir=str(FIXTURES)) as tf:
            json.dump(claim, tf)
            tmp = Path(tf.name)
        try:
            code, _ = run_gate(tmp)
            self.assertEqual(code, 13)
        finally:
            tmp.unlink()


if __name__ == "__main__":
    unittest.main()
