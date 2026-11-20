from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.markdown_document import markdown_headings, strip_fenced_code  # noqa: E402
from tools.validate_human_front_door import validate_readme_structure  # noqa: E402


class ReadmeFrontDoorLocalTests(unittest.TestCase):
    def test_readme_front_door_structure_and_identity(self):
        readme = (REPO_ROOT / ".github/README.md").read_text(encoding="utf-8")
        validate_readme_structure(strip_fenced_code(readme))

    def test_entire_first_module_inside_collapsed_details_is_not_visible(self):
        readme = self.readme()
        headings = [item for item in markdown_headings(readme) if item["level"] == 2]
        lines = readme.splitlines(keepends=True)
        line_offsets = [0]
        for line in lines:
            line_offsets.append(line_offsets[-1] + len(line))
        start = line_offsets[int(headings[0]["line"])]
        end = line_offsets[int(headings[1]["line"])]
        module = readme[start:end]
        wrapped = readme[:start] + "<details>\n" + module + "\n</details>\n" + readme[end:]
        with self.assertRaisesRegex(AssertionError, "essential H2 sections must remain visible"):
            validate_readme_structure(strip_fenced_code(wrapped))

    def test_h2_inside_collapsed_details_with_open_word_in_attribute_is_not_visible(self):
        hidden = self.readme().replace(
            "## 4. 整体架构",
            '<details title="closed but open inside ">\n'
            "<summary>更多</summary>\n\n"
            "## 4. 整体架构\n\n</details>",
            1,
        )
        with self.assertRaisesRegex(AssertionError, "essential H2 sections must remain visible"):
            validate_readme_structure(strip_fenced_code(hidden))

    def test_h2_inside_collapsed_details_after_script_close_text_is_not_visible(self):
        for element in ("script", "style"):
            with self.subTest(element=element):
                hidden = self.readme().replace(
                    "## 4. 整体架构",
                    "<details>\n<summary>更多</summary>\n\n"
                    f"<{element}>\n</details>\n</{element}>\n\n"
                    "## 4. 整体架构\n\n</details>",
                    1,
                )
                with self.assertRaisesRegex(AssertionError, "essential H2 sections must remain visible"):
                    validate_readme_structure(strip_fenced_code(hidden))

    def test_entire_readme_inside_non_ascii_open_attribute_details_is_not_visible(self):
        wrapped = (
            '<details title="More"\u00a0open>\n\n'
            + self.readme()
            + "\n</details>\n"
        )
        with self.assertRaisesRegex(AssertionError, "essential H2 sections must remain visible"):
            validate_readme_structure(strip_fenced_code(wrapped))

    def test_entire_first_module_inside_html_comment_is_not_visible(self):
        readme = self.readme()
        headings = [item for item in markdown_headings(readme) if item["level"] == 2]
        lines = readme.splitlines(keepends=True)
        line_offsets = [0]
        for line in lines:
            line_offsets.append(line_offsets[-1] + len(line))
        start = line_offsets[int(headings[0]["line"])]
        end = line_offsets[int(headings[1]["line"])]
        module = readme[start:end]
        wrapped = readme[:start] + "<!--\n" + module + "\n-->\n" + readme[end:]
        with self.assertRaisesRegex(AssertionError, "essential H2 sections must remain visible"):
            validate_readme_structure(strip_fenced_code(wrapped))

    def test_h2_inside_raw_html_block_is_not_visible(self):
        readme = self.readme().replace(
            "## 4. 整体架构",
            "<div>\n## 4. 整体架构\n</div>",
            1,
        )
        with self.assertRaisesRegex(AssertionError, "essential H2 sections must remain visible"):
            validate_readme_structure(strip_fenced_code(readme))

    def test_h2_inside_list_item_raw_html_block_is_not_visible(self):
        readme = self.readme().replace(
            "## 4. 整体架构",
            "- <div>\n  ## 4. 整体架构\n  </div>",
            1,
        )
        with self.assertRaisesRegex(AssertionError, "essential H2 sections must remain visible"):
            validate_readme_structure(strip_fenced_code(readme))

    def test_h2_inside_list_item_fenced_code_is_not_visible(self):
        readme = self.readme().replace(
            "## 4. 整体架构",
            "- ```markdown\n  ## 4. 整体架构\n  ```",
            1,
        )
        with self.assertRaisesRegex(AssertionError, "essential H2 sections must remain visible|README is missing section"):
            validate_readme_structure(strip_fenced_code(readme))

    def test_raw_html_block_types_do_not_contribute_headings(self):
        fixtures = (
            "<script>\n## 隐藏脚本标题\n</script>\n## 可见标题\n",
            "<script\n## 隐藏不完整脚本标题\n</script>\n## 可见标题\n",
            "<div\n## 隐藏不完整区块标题\n\n## 可见标题\n",
            "<![CDATA[\n## 隐藏 CDATA 标题\n]]>\n## 可见标题\n",
            "<?php\n## 隐藏处理指令标题\n?>\n## 可见标题\n",
            "<!DOCTYPE html\n## 隐藏声明标题\n>\n## 可见标题\n",
        )
        for markdown in fixtures:
            titles = [item["title"] for item in markdown_headings(markdown)]
            self.assertEqual(titles, ["可见标题"])

    def test_custom_html_block_only_starts_where_gfm_allows_it(self):
        block = "## 父标题\n<custom-tag>\n## 隐藏标题\n\n## 可见标题\n"
        paragraph = "普通段落\n<a>\n## 仍可见标题\n"
        indented_heading = "  ## 父标题\n<custom-tag>\n## 隐藏标题\n\n## 可见标题\n"
        setext_heading = "父标题\n===\n<custom-tag>\n## 隐藏标题\n\n## 可见标题\n"
        table = "| 列 |\n| --- |\n<custom-tag>\n## 表格后隐藏标题\n</custom-tag>\n\n## 可见标题\n"
        indented_code = "    代码块\n<custom-tag>\n## 代码后隐藏标题\n</custom-tag>\n\n## 可见标题\n"
        list_code = "- ```markdown\n  ## 列表代码标题\n  ```\n\n## 可见标题\n"
        self.assertEqual([item["title"] for item in markdown_headings(block)], ["父标题", "可见标题"])
        self.assertEqual([item["title"] for item in markdown_headings(paragraph)], ["仍可见标题"])
        self.assertEqual(
            [item["title"] for item in markdown_headings(indented_heading)],
            ["父标题", "可见标题"],
        )
        self.assertEqual([item["title"] for item in markdown_headings(setext_heading)], ["可见标题"])
        self.assertEqual([item["title"] for item in markdown_headings(table)], ["可见标题"])
        self.assertEqual([item["title"] for item in markdown_headings(indented_code)], ["可见标题"])
        self.assertEqual([item["title"] for item in markdown_headings(list_code)], ["可见标题"])

    @staticmethod
    def readme() -> str:
        return (REPO_ROOT / ".github/README.md").read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
