import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class FunctionAssetClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_module("tools/foundation/build_function_asset_census.py", "task99_census")
        cls.adjudicator = load_module("tools/foundation/adjudicate_function_assets.py", "task99_adjudicator")

    def run_ok(self, *args):
        result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_closure_validator(self):
        self.run_ok(sys.executable, "tools/foundation/validate_function_asset_closure.py")

    def test_generators_are_deterministic(self):
        self.run_ok(sys.executable, "tools/foundation/build_function_asset_census.py", "--check")
        self.run_ok(sys.executable, "tools/foundation/adjudicate_function_assets.py", "--check")

    def test_discovery_v2_sentinels(self):
        self.assertTrue(self.builder.implicit_candidate("fixture.py", "def bounded_transform(value: int) -> int:"))
        self.assertTrue(self.builder.implicit_candidate("fixture.md", "# Force equation candidate"))
        self.assertTrue(self.builder.implicit_candidate("fixture.md", "Φ(x) = x / (1 + x)"))
        self.assertFalse(self.builder.implicit_candidate("fixture.md", "ordinary prose"))

    def test_task99_identity_examples_cover_twelve(self):
        path = ROOT / "tests/foundation/fixtures/function_asset_identity_task99.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(rows), 12)
        self.assertEqual(len({row["primary_identity"] for row in rows}), 12)

    def test_semantic_rebound_normalization_ignores_renaming_adjectives(self):
        left = self.adjudicator.semantic_text("physical grand unification proved impossible")
        right = self.adjudicator.semantic_text("structural grand unification proved impossible")
        self.assertEqual(left, right)


if __name__ == "__main__":
    unittest.main()
