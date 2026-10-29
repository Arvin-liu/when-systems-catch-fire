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
        registry = _load_json(ROOT / "data/operations/generator-registry.json")
        registered = registry["generators"]
        for item in self.authority["generated_outputs"]:
            if "historical_sealed_record" in item:
                continue
            if "generator_id" in item:
                self.assertIn(item["generator_id"], registered)
                cmd = registered[item["generator_id"]]["canonical_tool"]
            else:
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
            if "producer_id" in item:
                authority_id = ("producer_command", item["producer_id"])
            elif "generator_id" in item:
                authority_id = ("registered_generator", item["generator_id"])
            else:
                authority_id = ("historical_sealed_record", item.get("historical_sealed_record"))
            key = (authority_id, tuple(sorted(item["input_authorities"])), item["output_type"])
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
        from tools.operations.era_resolver import resolve_era
        era = resolve_era(ROOT, "121Q32I")
        self.assertIsNotNone(era)
        self.assertIsNotNone(era["era_ref"])
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/operations/compute_change_propagation.py"),
             "--request", str(ROOT / "data/operations/propagation/121Q32I-request.json"),
             "--output", str(ROOT / "data/operations/propagation/121Q32I-closure.json"),
             "--report", str(ROOT / "reports/operations/121Q32I-change-propagation-impact.md"),
             "--map-delta", str(ROOT / "data/operations/propagation/121Q32I-system-map-delta.json"),
             "--residue", str(ROOT / "data/operations/propagation/121Q32I-residue.json"),
             "--era-ref", era["era_ref"],
             "--check"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        self.assertEqual(result.returncode, 0, f"Propagation --check failed: {result.stderr}")
        output = json.loads(result.stdout.strip().split("\n")[-1])
        self.assertEqual(output["status"], "PASS")

    def test_seed_generated_disjoint(self):
        request = _load_json(ROOT / "data/operations/propagation/121Q32I-request.json")
        seeds = set(request["changed_paths"])
        generated = {item["path"] for item in self.authority["generated_outputs"]}
        self.assertFalse(seeds & generated, "Seeds and generated overlap")


if __name__ == "__main__":
    unittest.main()
