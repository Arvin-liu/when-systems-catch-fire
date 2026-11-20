from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.markdown_document import markdown_headings, strip_fenced_code  # noqa: E402
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

    def test_entire_readme_inside_non_ascii_open_attribute_details_is_not_visible(self):
        wrapped = '<details title="More"\u00a0open>\n\n' + self.readme + "\n</details>\n"
        with self.assertRaisesRegex(AssertionError, "README lacks visible section"):
            validate_visible_readme_sections(wrapped)

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

    def test_nbsp_only_line_does_not_end_raw_html_block(self):
        hidden = self.readme.replace(
            "## 3. 结果与火种",
            "<div>\n\u00a0\n## 3. 结果与火种",
            1,
        )
        with self.assertRaisesRegex(AssertionError, "结果与火种"):
            validate_visible_readme_sections(hidden)

        list_raw_html = (
            "- <div>\n  \u00a0\n  ## Hidden List Heading\n  </div>\n\n"
            "## Visible Heading\n"
        )
        self.assertEqual(
            [item["title"] for item in markdown_headings(list_raw_html)],
            ["Visible Heading"],
        )

    def test_unicode_line_separator_does_not_create_a_heading_or_anchor(self):
        markdown = "说明\u2028## 伪造标题\n"
        self.assertEqual(markdown_headings(markdown), [])
        self.assertFalse(markdown_anchor_exists(markdown, "伪造标题"))

        hidden = self.readme.replace(
            "## 3. 结果与火种",
            "当前状态：旧\u2028## 3. 结果与火种",
            1,
        )
        with self.assertRaisesRegex(AssertionError, "结果与火种"):
            validate_visible_readme_sections(hidden)

    def test_unicode_line_separator_does_not_end_a_fenced_code_block(self):
        markdown = (
            "```text\n正文\u2028```\n## 隐藏代码标题\n```\n## 可见标题\n"
        )
        self.assertEqual(
            [item["title"] for item in markdown_headings(markdown)],
            ["可见标题"],
        )

    def test_bare_cr_fenced_code_preserves_following_heading_line_number(self):
        markdown = "```text\r## 隐藏标题\r```\r## 可见标题\r"
        self.assertEqual(
            strip_fenced_code(markdown),
            "\r\r\r## 可见标题\r",
        )
        self.assertEqual(
            markdown_headings(markdown),
            [{"level": 2, "title": "可见标题", "line": 3}],
        )

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

    def test_non_ascii_space_does_not_create_an_open_attribute_or_close_details(self):
        collapsed = (
            '<details title="More"\u00a0open>\n<summary>More</summary>\n\n'
            "## Hidden Section\n\n</detaıls>\n"
            "## Still Hidden Section\n\n</details>\n\n"
            "## Visible Section\n"
        )
        self.assertEqual(
            [item["title"] for item in markdown_headings(collapsed)],
            ["Visible Section"],
        )
        self.assertFalse(markdown_anchor_exists(collapsed, "Hidden Section"))
        self.assertFalse(markdown_anchor_exists(collapsed, "Still Hidden Section"))
        self.assertTrue(markdown_anchor_exists(collapsed, "Visible Section"))

    def test_non_ascii_space_and_unicode_lookalike_do_not_close_raw_text(self):
        for element, fake_close in (
            ("script", "</script\u00a0>"),
            ("script", "</scrıpt>"),
            ("textarea", "</textarea\u00a0>"),
        ):
            with self.subTest(element=element, fake_close=fake_close):
                markdown = f"<{element}>\n{fake_close}\n## Hidden Without An ASCII Close\n"
                self.assertEqual(markdown_headings(markdown), [])

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
