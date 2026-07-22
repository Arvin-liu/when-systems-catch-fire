#!/usr/bin/env python3
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools/symbolic/validate_symbolic_power_perspective_gate.py"
BUILDER = ROOT / "tools/symbolic/build_symbolic-sphere-i1_fixtures.py"
FIXTURES = ROOT / "data/symbolic/fixtures"
PILOT = ROOT / "data/symbolic/pilot-symbolic-sphere-i1.json"
REQUIRED_REFERENCE_FIELDS = {
    "repository_relative_path", "commit_sha", "blob_sha", "sha256",
    "record_type", "declared_role",
}


def run_validator(path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--bundle", str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


class SymbolicPowerPerspectiveGateTests(unittest.TestCase):
    def test_real_cli_matrix_uses_stable_data_integrity_names(self):
        paths = sorted(FIXTURES.glob("[0-9][0-9]-*.json"))
        self.assertEqual(len(paths), 20)
        for path in paths:
            expected = int(re.search(r"-exit(\d+)\.json$", path.name).group(1))
            completed = run_validator(path)
            payload = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, expected, f"{path.name}: {completed.stdout} {completed.stderr}")
            self.assertEqual(payload["exit_code"], expected, path.name)
            self.assertNotEqual(payload["exit_name"], "RULE_BLOCKED", path.name)

    def test_pilot_passes(self):
        completed = run_validator(PILOT)
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(json.loads(completed.stdout)["exit_name"], "GATE_PASS")

    def test_builder_outputs_are_current(self):
        completed = subprocess.run(
            [sys.executable, str(BUILDER), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_every_repository_reference_has_required_integrity_fields(self):
        bundle = json.loads(PILOT.read_text())
        for reference in bundle["reference_records"]:
            self.assertTrue(REQUIRED_REFERENCE_FIELDS.issubset(reference))
            path = PurePosixPath(reference["repository_relative_path"])
            self.assertFalse(path.is_absolute())
            self.assertNotIn("..", path.parts)
            self.assertRegex(reference["commit_sha"], r"^[0-9a-f]{40}$")
            self.assertRegex(reference["blob_sha"], r"^[0-9a-f]{40}$")
            self.assertRegex(reference["sha256"], r"^sha256:[0-9a-f]{64}$")

    def test_task_semantics_are_structured_not_boolean_assertions(self):
        bundle = json.loads(PILOT.read_text())
        self.assertNotIn("facts", bundle)
        self.assertNotIn("rule_assertions", bundle)
        self.assertEqual(
            {record["record_type"] for record in bundle["records"]},
            {"COMMUNITY_FOOTBALL_FIELD", "SCHOOL_DATA_POLICY"},
        )
        modalities = {
            power["modality"]
            for record in bundle["records"]
            for power in record["power_modalities"]
        }
        self.assertTrue({"OWNERSHIP", "POPULARITY", "NAMING_AUTHORITY"}.issubset(modalities))
        self.assertEqual(bundle["conclusion"]["truth_status"], "NOT_ESTABLISHED")
        self.assertEqual(bundle["conclusion"]["causal_status"], "NOT_ESTABLISHED")

    def test_counter_readings_bind_distinct_evidence(self):
        bundle = json.loads(PILOT.read_text())
        for record in bundle["records"]:
            projections = {item["projection_id"]: item for item in record["meaning_projections"]}
            for counter in record["counter_readings"]:
                target = projections[counter["target_projection_id"]]
                self.assertTrue(counter["evidence_refs"])
                self.assertTrue(set(counter["evidence_refs"]).isdisjoint(target["evidence_refs"]))


if __name__ == "__main__":
    unittest.main()
