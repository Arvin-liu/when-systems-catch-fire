from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.markdown_document import markdown_headings  # noqa: E402
from tools.governance.validate_human_visibility import (  # noqa: E402
    file_for,
    local_links,
    markdown_anchor_exists,
    validate_visible_readme_sections,
)


class ReadmeVisibilityLocalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = (REPO_ROOT / ".github/README.md").read_text(encoding="utf-8")

    def test_required_readme_sections_are_visible_outside_code_fences(self):
        validate_visible_readme_sections(self.readme)

    def test_readme_local_links_resolve(self):
        missing = sorted(target for target in local_links("README.md") if not file_for(target).exists())
        self.assertEqual(missing, [])

    def test_readme_component_anchor_is_present(self):
        registry_path = ROOT / "data/operations/project-components.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        component = next(row for row in registry["components"] if row["component_id"] == "owner_human")
        path, separator, fragment = component["canonical_target"].partition("#")
        self.assertTrue(separator)
        self.assertEqual(path, ".github/README.md")
        self.assertTrue(markdown_anchor_exists(file_for(path).read_text(encoding="utf-8"), fragment))

    def test_code_fenced_h2_does_not_replace_visible_section(self):
        hidden = self.readme.replace("## 3. 结果与火种", "### 3. 结果与火种", 1)
        hidden += "\n~~~markdown\n## 3. 结果与火种\n~~~\n"
        with self.assertRaisesRegex(AssertionError, "结果与火种"):
            validate_visible_readme_sections(hidden)

    def test_code_fenced_h3_does_not_replace_visible_identity_section(self):
        hidden = self.readme.replace(
            "### 点火是什么",
            "```markdown\n### 点火是什么\n```",
            1,
        )
        with self.assertRaisesRegex(AssertionError, "点火是什么"):
            validate_visible_readme_sections(hidden)

    def test_h2_inside_collapsed_details_does_not_satisfy_required_section(self):
        hidden = self.readme.replace(
            "## 3. 结果与火种",
            "<details>\n<summary>更多</summary>\n## 3. 结果与火种\n</details>",
            1,
        )
        with self.assertRaisesRegex(AssertionError, "结果与火种"):
            validate_visible_readme_sections(hidden)

    def test_h2_inside_collapsed_details_after_raw_text_close_text_is_not_visible(self):
        for element in ("script", "style"):
            with self.subTest(element=element):
                hidden = self.readme.replace(
                    "## 3. 结果与火种",
                    "<details>\n<summary>更多</summary>\n\n"
                    f"<{element}>\n</details>\n</{element}>\n\n"
                    "## 3. 结果与火种\n\n</details>",
                    1,
                )
                with self.assertRaisesRegex(AssertionError, "结果与火种"):
                    validate_visible_readme_sections(hidden)

    def test_h3_inside_collapsed_details_does_not_satisfy_identity_section(self):
        hidden = self.readme.replace(
            "### 点火是什么",
            "<details>\n<summary>身份</summary>\n### 点火是什么\n</details>",
            1,
        )
        with self.assertRaisesRegex(AssertionError, "must visibly contain"):
            validate_visible_readme_sections(hidden)

    def test_h2_inside_html_comment_does_not_satisfy_required_section(self):
        hidden = self.readme.replace(
            "## 3. 结果与火种",
            "<!--\n## 3. 结果与火种\n-->",
            1,
        )
        with self.assertRaisesRegex(AssertionError, "结果与火种"):
            validate_visible_readme_sections(hidden)

    def test_h2_inside_raw_html_block_does_not_satisfy_required_section(self):
        hidden = self.readme.replace(
            "## 3. 结果与火种",
            "<div>\n## 3. 结果与火种\n</div>",
            1,
        )
        with self.assertRaisesRegex(AssertionError, "结果与火种"):
            validate_visible_readme_sections(hidden)

    def test_h2_inside_list_item_raw_html_block_does_not_satisfy_required_section(self):
        hidden = self.readme.replace(
            "## 3. 结果与火种",
            "- <div>\n  ## 3. 结果与火种\n  </div>",
            1,
        )
        with self.assertRaisesRegex(AssertionError, "结果与火种"):
            validate_visible_readme_sections(hidden)

    def test_h2_inside_list_item_fenced_code_does_not_satisfy_required_section(self):
        hidden = self.readme.replace(
            "## 3. 结果与火种",
            "- ```markdown\n  ## 3. 结果与火种\n  ```",
            1,
        )
        with self.assertRaisesRegex(AssertionError, "结果与火种"):
            validate_visible_readme_sections(hidden)

    def test_h3_inside_html_comment_does_not_satisfy_identity_section(self):
        hidden = self.readme.replace(
            "### 点火是什么",
            "<!--\n### 点火是什么\n-->",
            1,
        )
        with self.assertRaisesRegex(AssertionError, "must visibly contain"):
            validate_visible_readme_sections(hidden)

    def test_h3_inside_raw_html_block_does_not_satisfy_identity_section(self):
        hidden = self.readme.replace(
            "### 点火是什么",
            "<div>\n### 点火是什么\n</div>",
            1,
        )
        with self.assertRaisesRegex(AssertionError, "must visibly contain"):
            validate_visible_readme_sections(hidden)

    def test_open_word_inside_collapsed_details_attribute_does_not_expose_headings_or_anchors(self):
        collapsed = (
            '<details title="closed but open inside > still closed">\n'
            "<summary>More</summary>\n\n"
            "## Hidden Section\n\n</details>\n"
            "## Visible Section\n"
        )
        self.assertEqual(
            [item["title"] for item in markdown_headings(collapsed)],
            ["Visible Section"],
        )
        self.assertFalse(markdown_anchor_exists(collapsed, "Hidden Section"))
        self.assertTrue(markdown_anchor_exists(collapsed, "Visible Section"))
        self.assertFalse(markdown_anchor_exists("<details/open>\n\n## Hidden\n", "Hidden"))

        expanded = (
            '<details title="closed but open inside " open>\n'
            "<summary>More</summary>\n\n"
            "## Expanded Section\n\n</details>\n"
        )
        self.assertTrue(markdown_anchor_exists(expanded, "Expanded Section"))

    def test_details_close_text_inside_raw_text_elements_does_not_expose_headings_or_anchors(self):
        for element in ("script", "style"):
            with self.subTest(element=element):
                collapsed = (
                    "<details>\n<summary>More</summary>\n\n"
                    f"<{element}>\n</details>\n</{element}>\n\n"
                    "## Hidden Section\n\n</details>\n\n"
                    "## Visible Section\n"
                )
                self.assertEqual(
                    [item["title"] for item in markdown_headings(collapsed)],
                    ["Visible Section"],
                )
                self.assertFalse(markdown_anchor_exists(collapsed, "Hidden Section"))
                self.assertTrue(markdown_anchor_exists(collapsed, "Visible Section"))

                raw_text_heading = (
                    f"<{element}>\n## Not A Markdown Heading\n</{element}>\n"
                    "## Visible Section\n"
                )
                self.assertEqual(
                    [item["title"] for item in markdown_headings(raw_text_heading)],
                    ["Visible Section"],
                )
                self.assertEqual(
                    markdown_headings(f"<{element}>\n## Hidden Without A Close\n"),
                    [],
                )

    def test_details_close_text_inside_a_quoted_tag_attribute_does_not_end_the_block(self):
        collapsed = (
            "<details>\n<summary>More</summary>\n\n"
            '<div title="</details>">\n\n'
            "## Hidden Section\n\n</details>\n\n"
            "## Visible Section\n"
        )
        self.assertEqual(
            [item["title"] for item in markdown_headings(collapsed)],
            ["Visible Section"],
        )
        self.assertFalse(markdown_anchor_exists(collapsed, "Hidden Section"))
        self.assertTrue(markdown_anchor_exists(collapsed, "Visible Section"))

    def test_anchor_lookup_ignores_collapsed_details_and_html_comments(self):
        collapsed = "<details>\n## 仅折叠锚点\n</details>\n"
        expanded = "<details open>\n\n<summary>展开内容</summary>\n\n## 展开锚点\n\n</details>\n"
        unseparated_expanded = "<details open>\n## 不应计入\n</details>\n"
        commented = "<!--\n## 仅注释锚点\n-->\n"
        raw_html = "<div>\n## 仅原始 HTML 锚点\n</div>\n"
        list_raw_html = "- <div>\n  ## 仅列表原始 HTML 锚点\n  </div>\n"
        list_fenced_code = "- ```markdown\n  ## 仅列表围栏锚点\n  ```\n"
        self.assertFalse(markdown_anchor_exists(collapsed, "仅折叠锚点"))
        self.assertTrue(markdown_anchor_exists(expanded, "展开锚点"))
        self.assertFalse(markdown_anchor_exists(unseparated_expanded, "不应计入"))
        self.assertFalse(markdown_anchor_exists(commented, "仅注释锚点"))
        self.assertFalse(markdown_anchor_exists(raw_html, "仅原始 HTML 锚点"))
        self.assertFalse(markdown_anchor_exists(list_raw_html, "仅列表原始 HTML 锚点"))
        self.assertFalse(markdown_anchor_exists(list_fenced_code, "仅列表围栏锚点"))

    def test_markdown_after_raw_html_blank_line_remains_visible(self):
        markdown = "<div>\nraw HTML\n\n## 可见标题\n\n</div>\n"
        self.assertTrue(markdown_anchor_exists(markdown, "可见标题"))

    def test_unclosed_hidden_markup_fails_closed_for_anchor_lookup(self):
        self.assertFalse(markdown_anchor_exists("<details>\n## 未闭合折叠锚点\n", "未闭合折叠锚点"))
        self.assertFalse(markdown_anchor_exists("<details open>\n## 未闭合展开锚点\n", "未闭合展开锚点"))
        self.assertFalse(markdown_anchor_exists("<!--\n## 未闭合注释锚点\n", "未闭合注释锚点"))


if __name__ == "__main__":
    unittest.main()
