import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("human_visibility", ROOT / "tools/governance/validate_human_visibility.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class HumanVisibilityGateTests(unittest.TestCase):
    def test_current_surfaces_are_visible_paired_and_reachable(self):
        result = MODULE.validate()
        self.assertGreaterEqual(result["human_surfaces"], 10)
        self.assertGreaterEqual(result["machine_human_pairs"], 8)
        self.assertGreaterEqual(result["two_click_destinations"], 8)


if __name__ == "__main__":
    unittest.main()
