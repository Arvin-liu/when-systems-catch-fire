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
)


class HumanFrontDoorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = README.read_text(encoding="utf-8")
        cls.guide = GUIDE.read_text(encoding="utf-8")
        cls.current_state = CURRENT_STATE.read_text(encoding="utf-8")
        cls.pages = PAGES_WORKFLOW.read_text(encoding="utf-8")

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
            "describes the current repository baseline after PR #56",
            "describes the repository after PR #55 was merged",
        )
        with self.assertRaisesRegex(AssertionError, "PR #55"):
            self.validate(current_state=stale)

    def test_pages_must_be_readme_derived(self):
        with self.assertRaisesRegex(AssertionError, "derived from README"):
            self.validate(pages=self.pages.replace("cat README.md", "cat docs/other.md"))


if __name__ == "__main__":
    unittest.main()
