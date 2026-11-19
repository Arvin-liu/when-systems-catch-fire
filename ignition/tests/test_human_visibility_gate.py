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
        self.assertGreaterEqual(result["human_surfaces"], 20)
        self.assertGreaterEqual(result["machine_human_pairs"], 14)
        self.assertGreaterEqual(result["two_click_destinations"], 16)

    def test_visibility_gate_does_not_pin_the_owner_h2_title(self):
        readme = MODULE.file_for("README.md").read_text(encoding="utf-8")
        renamed = readme.replace(
            "## 1. 项目与价值",
            "## 1. 丹无定形，火有法度，炼无终局，化有来路。",
            1,
        )
        self.assertNotEqual(readme, renamed)
        MODULE.validate_visible_readme_sections(renamed)
        self.assertTrue(MODULE.markdown_anchor_exists(renamed, "点火是什么"))
        self.assertFalse(MODULE.markdown_anchor_exists(renamed, "1. 项目与价值"))

    def test_visibility_gate_still_rejects_a_missing_required_section(self):
        readme = MODULE.file_for("README.md").read_text(encoding="utf-8")
        missing = readme.replace("## 3. 结果与火种", "### 3. 结果与火种", 1)
        with self.assertRaises(AssertionError):
            MODULE.validate_visible_readme_sections(missing)


if __name__ == "__main__":
    unittest.main()
