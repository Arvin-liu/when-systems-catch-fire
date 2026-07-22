#!/usr/bin/env python3
"""DECISION-INTEGRITY repair-r2 contract test (RB09-DIRECT-PREDECESSOR-BINDING + inherited engine).

Exercises the wrapper against the fail-closed shared engine:
  * positive pilot (bound to the real SYMBOLIC-SPHERE repair-r2 head) exits 0;
  * wrong predecessor head is rejected (PARENT_BINDING_INVALID);
  * absolute path / '..' / fabricated exact head / missing mandatory git-object
    field / tampered sha256 / caller-asserted bypass are all rejected.
Controlled bundles are written to a repo-external temp dir only.
"""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools/decision/validate_decision_integrity_gate.py"
PILOT = ROOT / "data/decision/pilot-decision-integrity-i1.json"


def _run(bundle, tmp):
    p = Path(tmp) / "b.json"
    p.write_text(json.dumps(bundle))
    r = subprocess.run(
        [sys.executable, str(VALIDATOR), "--bundle", str(p)],
        capture_output=True, text=True,
    )
    return r.returncode, r.stdout


class DecisionIntegrityRepairR2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.pilot = json.loads(PILOT.read_text())

    def test_pilot_bound_to_real_r2_head_passes(self):
        code, out = _run(self.pilot, self.tmp)
        self.assertEqual(code, 0, out)

    def test_wrong_predecessor_head_rejected(self):
        b = json.loads(PILOT.read_text())
        b["parent_binding"]["exact_head"] = "213dced90f1e9b1f1992a148ee10fc0844917490"
        code, out = _run(b, self.tmp)
        self.assertNotEqual(code, 0)
        self.assertIn("PARENT_BINDING_INVALID", out)

    def test_absolute_path_evidence_rejected(self):
        b = json.loads(PILOT.read_text())
        b["evidence_registry"][0]["repository_relative_path"] = "/etc/passwd"
        code, out = _run(b, self.tmp)
        self.assertNotEqual(code, 0)

    def test_dotdot_path_evidence_rejected(self):
        b = json.loads(PILOT.read_text())
        b["evidence_registry"][0]["repository_relative_path"] = "../secrets"
        code, out = _run(b, self.tmp)
        self.assertNotEqual(code, 0)

    def test_fabricated_exact_head_rejected(self):
        b = json.loads(PILOT.read_text())
        b["evidence_registry"][0]["exact_head"] = "deadbeef" * 5
        code, out = _run(b, self.tmp)
        self.assertNotEqual(code, 0)

    def test_missing_mandatory_git_object_field_rejected(self):
        b = json.loads(PILOT.read_text())
        del b["evidence_registry"][0]["blob_sha"]
        code, out = _run(b, self.tmp)
        self.assertNotEqual(code, 0)

    def test_tampered_sha256_rejected(self):
        b = json.loads(PILOT.read_text())
        b["evidence_registry"][0]["sha256"] = "sha256:" + "00" * 32
        code, out = _run(b, self.tmp)
        self.assertNotEqual(code, 0)

    def test_caller_asserted_bypass_rejected(self):
        b = json.loads(PILOT.read_text())
        for a in b["rule_assertions"]:
            a["evidence_refs"] = ["evidence.fake"]
        code, out = _run(b, self.tmp)
        self.assertNotEqual(code, 0)
        self.assertIn("RULE_BLOCKED", out)


if __name__ == "__main__":
    unittest.main()
