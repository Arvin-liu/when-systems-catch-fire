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
        self.run_ok(sys.executable,"tools/foundation/adjudicate_core.py","--check")
        self.run_ok(sys.executable,"tools/foundation/migrate_legacy.py","--check")

    def test_integrity_validator(self):
        self.run_ok(sys.executable,"tools/foundation/validate_foundation.py")

    def test_benchmarks(self):
        self.run_ok(sys.executable,"tools/foundation/run_benchmarks.py","--check")

    def test_core_claims(self):
        self.run_ok(sys.executable,"tools/foundation/verify_core_claims.py","--check")

    def test_project_state(self):
        state=json.loads((ROOT/"data/foundation/project-state.json").read_text())
        self.assertEqual(state["counts"]["formal_objects"],622)
        self.assertEqual(state["counts"]["formal_cases"],806)
        self.assertEqual(state["semantic_adjudication_counts"],{"adjudicated":621,"provisional":1,"total":622})
        self.assertEqual(state["migration_coverage"],"complete")
        self.assertEqual(
            state["semantic_adjudication"],
            "registry_closed_by_identity_or_explicit_quarantine; content proofs and empirical obligations remain independently open",
        )
        self.assertTrue(state["counts"]["function_asset_deep_adjudication"]["registry_closed"])

    def test_migration_does_not_override_adjudication(self):
        objects={row["id"]:row for row in map(json.loads,(ROOT/"data/foundation/formal-objects/objects.jsonl").read_text().splitlines())}
        overrides={row["stable_id"]:row for row in map(json.loads,(ROOT/"data/foundation/adjudications/classification-overrides.jsonl").read_text().splitlines())}
        self.assertEqual(len(overrides),621)
        for object_id,override in overrides.items():
            self.assertEqual(objects[object_id]["classification_status"],"ADJUDICATED")
            self.assertEqual(objects[object_id]["formal_object_type"],override["formal_object_type"])

    def test_lean_proof_has_no_placeholder(self):
        proof=(ROOT/"formal/lean/Foundation.lean").read_text()
        self.assertIn("theorem T2_mul_zero_factor",proof)
        self.assertNotIn("sorry",proof.lower())

if __name__=="__main__": unittest.main()
