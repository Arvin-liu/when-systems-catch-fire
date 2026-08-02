import re
import unittest

from tools.validate_human_front_door import (
    AI_HANDOFF,
    AI_START,
    CAPABILITIES,
    CURRENT_STATE,
    GUIDE,
    HUMAN_READING,
    LLMS,
    README,
    validate_all,
    validate_texts,
    validate_version_front_doors,
)


class HumanFrontDoorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = README.read_text(encoding="utf-8")
        cls.guide = GUIDE.read_text(encoding="utf-8")
        cls.current_state = CURRENT_STATE.read_text(encoding="utf-8")
        cls.human_reading = HUMAN_READING.read_text(encoding="utf-8")
        cls.ai_start = AI_START.read_text(encoding="utf-8")
        cls.ai_handoff = AI_HANDOFF.read_text(encoding="utf-8")
        cls.llms = LLMS.read_text(encoding="utf-8")

    def test_repository_front_doors_validate(self):
        result = validate_all()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["interactive_system_map_nodes"], 50)

    def test_visible_result_sections_are_ordered_and_unfolded(self):
        validate_texts(self.readme, self.guide, self.current_state, self.human_reading)
        self.assertNotIn("<details", self.readme.lower())

    def test_each_capability_has_direct_readme_link(self):
        for name, path in CAPABILITIES.items():
            with self.subTest(name=name):
                self.assertIn(name, self.readme)
                self.assertIn(path, self.readme)

    def test_retired_deployed_reader_is_absent(self):
        for token in ("arvin-liu.github.io/when-systems-catch-fire", ".github/workflows/pages.yml", "pages/system-map.html"):
            self.assertNotIn(token, self.readme)
            self.assertNotIn(token, self.human_reading)

    def test_physics_correction_is_visible(self):
        self.assertRegex(self.readme, r"没有证明.{0,20}大一统普遍不可能|撤回.{0,40}大一统")

    def test_three_ai_front_doors_share_version_truth(self):
        validate_version_front_doors(self.ai_start, self.ai_handoff, self.llms)

    def test_stale_current_method_is_rejected(self):
        stale = "Current method 1.3.0; 1.4.0 Historical; map 0.4.0 Current; 0.3.0 and 0.2.0 Historical; method 1.2.0 Historical."
        with self.assertRaises(AssertionError):
            validate_version_front_doors(stale, self.ai_handoff, self.llms)

    def test_nonimpact_proof_only_exempts_named_surface(self):
        stale = "Current method 1.3.0"
        with self.assertRaises(AssertionError):
            validate_version_front_doors(self.ai_start, self.ai_handoff, self.llms, readme=stale)
        validate_version_front_doors(self.ai_start, self.ai_handoff, self.llms, readme=stale, nonimpact_proofs={"human.readme"})


if __name__ == "__main__":
    unittest.main()
