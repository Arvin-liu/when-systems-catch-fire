#!/usr/bin/env python3
"""Q42 repair-r2 contract test (RB09-DIRECT-PREDECESSOR-BINDING + inherited engine)."""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools/counterfactual/validate_counterfactual_unrealized_path_gate.py"
PILOT = ROOT / "data/counterfactual/pilot-q42-i1.json"
CORRECT_HEAD = "ea447ed7f6331f8ed5e58526f4c2341d3a41d6a6"

def _run(bundle, tmp):
    p = Path(tmp) / "b.json"
    p.write_text(json.dumps(bundle))
    r = subprocess.run([sys.executable, str(VALIDATOR), "--bundle", str(p)], capture_output=True, text=True)
    return r.returncode, r.stdout

class RepairR2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.pilot = json.loads(PILOT.read_text())
    def test_pilot_bound_to_real_r2_head_passes(self):
        code, out = _run(self.pilot, self.tmp)
        self.assertEqual(code, 0, out)
    def test_wrong_predecessor_head_rejected(self):
        b = json.loads(PILOT.read_text())
        b["parent_binding"]["exact_head"] = "0" * 40
        code, out = _run(b, self.tmp)
        self.assertNotEqual(code, 0)
        self.assertIn("PARENT_BINDING_INVALID", out)
    def test_absolute_path_evidence_rejected(self):
        b = json.loads(PILOT.read_text())
        b["evidence_registry"][0]["repository_relative_path"] = "/etc/passwd"
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

if __name__ == "__main__":
    unittest.main()
