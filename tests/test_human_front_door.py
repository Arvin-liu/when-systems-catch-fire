import unittest
from pathlib import Path

from tools.validate_human_front_door import (
    CAPABILITIES,
    PAGES_WORKFLOW,
    README,
    GUIDE,
    CURRENT_STATE,
    validate_all,
    validate_texts,
    validate_version_front_doors,
    AI_START,
    AI_HANDOFF,
    LLMS,
)


class HumanFrontDoorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = README.read_text(encoding="utf-8")
        cls.guide = GUIDE.read_text(encoding="utf-8")
        cls.current_state = CURRENT_STATE.read_text(encoding="utf-8")
        cls.pages = PAGES_WORKFLOW.read_text(encoding="utf-8")
        cls.ai_start = AI_START.read_text(encoding="utf-8")
        cls.ai_handoff = AI_HANDOFF.read_text(encoding="utf-8")
        cls.llms = LLMS.read_text(encoding="utf-8")

    def validate(self, readme=None, guide=None, current_state=None, pages=None):
        validate_texts(
            self.readme if readme is None else readme,
            self.guide if guide is None else guide,
            self.current_state if current_state is None else current_state,
            self.pages if pages is None else pages,
        )

    def test_repository_front_doors_validate(self):
        self.assertEqual(validate_all()["status"], "PASS")

    def test_each_capability_is_required_in_readme(self):
        for name, path in CAPABILITIES.items():
            with self.subTest(name=name), self.assertRaisesRegex(AssertionError, name):
                self.validate(readme=self.readme.replace(path, f"missing/{name.lower()}.md"))

    def test_each_capability_is_required_in_expanded_guide(self):
        for name, path in CAPABILITIES.items():
            with self.subTest(name=name), self.assertRaisesRegex(AssertionError, name):
                self.validate(guide=self.guide.replace(path, f"missing/{name.lower()}.md"))

    def test_visible_summary_cannot_omit_mcf_psd_arn_or_iteration(self):
        prefix, remainder = self.readme.split("## 项目现状", 1)
        visible, suffix = remainder.split("## 生命共同体价值宪章", 1)
        for name in CAPABILITIES:
            with self.subTest(name=name), self.assertRaisesRegex(AssertionError, name):
                self.validate(readme=prefix + "## 项目现状" + visible.replace(name, "REMOVED") + "## 生命共同体价值宪章" + suffix)

    def test_prompt_divergence_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "prompts diverge"):
            self.validate(guide=self.guide.replace("真正必要的问题", "必要的问题", 1))

    def test_stale_pr55_scope_is_rejected(self):
        stale = self.current_state.replace(
            "describes the current repository baseline after PR #57",
            "describes the repository after PR #55 was merged",
        )
        with self.assertRaisesRegex(AssertionError, "PR #55"):
            self.validate(current_state=stale)

    def test_pages_must_be_readme_derived(self):
        with self.assertRaisesRegex(AssertionError, "derived from README"):
            self.validate(pages=self.pages.replace("cat README.md", "cat docs/other.md"))

    def test_readme_has_one_current_state_and_expected_top_order(self):
        self.assertEqual(self.readme.count("## 项目现状"), 1)
        headings = ["## 项目现状", "## 之元写作法成果", "## 生命共同体价值宪章", "## 完整可点击系统图", "## 使用指南"]
        positions = [self.readme.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))

    def test_ai_prompt_and_current_details_are_folded(self):
        self.assertIn("<summary>展开：当前能力、限制与完整项目现状</summary>", self.readme)
        self.assertIn("<summary>展开：完整 AI 首次阅读提示词</summary>", self.readme)

    def test_complete_system_map_is_between_charter_and_usage(self):
        charter = self.readme.index("## 生命共同体价值宪章")
        system_map = self.readme.index("## 完整可点击系统图")
        usage = self.readme.index("## 使用指南")
        self.assertLess(charter, system_map)
        self.assertLess(system_map, usage)
        self.assertIn("<object data=\"./generated/ignition-system-map.svg\"", self.readme)

    def test_system_map_has_all_clickable_nodes_and_no_l7_layer(self):
        result = validate_all()
        # 63 = 41 original declared nodes + 7 Q33 governance nodes
        # + 3 Q34 discovery_commitment governance nodes
        # + 3 Q35 agent_responsibility governance nodes
        # + 3 Q36-OBS observation_prediction governance nodes
        # + 3 Q36-INT intervention_failure governance nodes
        # + 3 Q37 analogy_audit governance nodes; the materialized
        # map must cover the full current node set.
        self.assertEqual(result["interactive_system_map_nodes"], 66)

    def test_pages_artifact_carries_typed_propagation_evidence(self):
        self.assertIn("typed-change-propagation.md", self.pages)
        self.assertIn("121Q32-change-propagation-impact.md", self.pages)
        self.assertIn("site/data/operations/project-components.json", self.pages)
        self.assertIn("site/data/operations/change-propagation-topology.json", self.pages)

    def test_three_ai_front_doors_share_version_truth(self):
        validate_version_front_doors(self.ai_start, self.ai_handoff, self.llms)

    def test_stale_current_method_is_rejected_in_each_ai_front_door(self):
        stale = "Current method 1.2.0; Current map 0.2.0; method 1.3.0 and map 0.3.0 are not Current. Historical 1.1.0."
        for index in range(3):
            texts = [self.ai_start, self.ai_handoff, self.llms]
            texts[index] = stale
            with self.subTest(index=index), self.assertRaises(AssertionError):
                validate_version_front_doors(*texts)

    def test_rollback_typo_is_rejected(self):
        typo = "roll" + "bar"
        with self.assertRaisesRegex(AssertionError, "rollback"):
            validate_version_front_doors(self.ai_start + "\n" + typo + "回", self.ai_handoff, self.llms)


if __name__ == "__main__":
    unittest.main()
