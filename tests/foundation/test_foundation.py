import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

class FoundationTests(unittest.TestCase):
    def run_ok(self,*args):
        p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)

    def test_generated_data_is_current(self):
        self.run_ok(sys.executable,"tools/foundation/migrate_legacy.py","--check")

    def test_integrity_validator(self):
        self.run_ok(sys.executable,"tools/foundation/validate_foundation.py")

    def test_benchmarks(self):
        self.run_ok(sys.executable,"tools/foundation/run_benchmarks.py","--check")

    def test_project_state(self):
        state=json.loads((ROOT/"data/foundation/project-state.json").read_text())
        self.assertEqual(state["counts"]["formal_objects"],622)
        self.assertEqual(state["counts"]["formal_cases"],806)

if __name__=="__main__": unittest.main()
