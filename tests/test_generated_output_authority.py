"""Generated-output authority validation tests.

Ensures the generated-output authority is consistent:
- Schema validation passes
- All declared outputs exist
- Producer scripts exist
- Propagation freshness check passes
- No inconsistent duplicate authorities
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATH = ROOT / "data/operations/generated-output-authority.json"
SCHEMA_PATH = ROOT / "schemas/operations/generated-output-authority.schema.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class GeneratedOutputAuthorityTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.authority = _load_json(AUTHORITY_PATH)

    def test_schema_valid(self):
        from jsonschema import Draft202012Validator
        schema = _load_json(SCHEMA_PATH)
        errors = list(Draft202012Validator(schema).iter_errors(self.authority))
        self.assertEqual(errors, [], f"Schema errors: {[e.message for e in errors]}")

    def test_all_outputs_exist(self):
        for item in self.authority["generated_outputs"]:
            self.assertTrue(
                (ROOT / item["path"]).exists(),
                f"Generated output missing: {item['path']}",
            )

    def test_producer_scripts_exist(self):
        checked = set()
        for item in self.authority["generated_outputs"]:
            cmd = item["producer_command"]
            if cmd in checked:
                continue
            checked.add(cmd)
            for part in cmd.split():
                if part.endswith(".py") or part.endswith(".sh"):
                    self.assertTrue(
                        (ROOT / part).exists(),
                        f"Producer script missing: {part}",
                    )

    def test_input_authorities_exist(self):
        all_inputs = set()
        for item in self.authority["generated_outputs"]:
            all_inputs.update(item["input_authorities"])
        for inp in sorted(all_inputs):
            self.assertTrue(
                (ROOT / inp).exists(),
                f"Input authority missing: {inp}",
            )

    def test_no_inconsistent_duplicates(self):
        from collections import defaultdict
        groups = defaultdict(list)
        for item in self.authority["generated_outputs"]:
            key = (item["producer_id"], tuple(sorted(item["input_authorities"])), item["output_type"])
            groups[key].append(item["path"])
        for key, paths in groups.items():
            if len(paths) <= 1:
                continue
            contents = []
            for p in paths:
                fp = ROOT / p
                if fp.exists():
                    contents.append(fp.read_bytes())
            if len(set(contents)) > 1:
                self.fail(f"Inconsistent duplicate outputs for {key}: {paths}")

    def test_propagation_freshness(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/operations/compute_change_propagation.py"),
             "--request", str(ROOT / "data/operations/propagation/121Q32-request.json"),
             "--output", str(ROOT / "data/operations/propagation/121Q32-closure.json"),
             "--report", str(ROOT / "reports/operations/121Q32-change-propagation-impact.md"),
             "--map-delta", str(ROOT / "data/operations/propagation/121Q32-system-map-delta.json"),
             "--residue", str(ROOT / "data/operations/propagation/121Q32-residue.json"),
             "--check"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        self.assertEqual(result.returncode, 0, f"Propagation --check failed: {result.stderr}")
        output = json.loads(result.stdout.strip().split("\n")[-1])
        self.assertEqual(output["status"], "PASS")

    def test_seed_generated_disjoint(self):
        request = _load_json(ROOT / "data/operations/propagation/121Q32-request.json")
        seeds = set(request["changed_paths"])
        generated = {item["path"] for item in self.authority["generated_outputs"]}
        self.assertFalse(seeds & generated, "Seeds and generated overlap")


if __name__ == "__main__":
    unittest.main()
