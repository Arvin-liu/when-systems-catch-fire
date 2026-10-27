#!/usr/bin/env python3
"""Regression tests for the stable Task150-derived homepage projection."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.build_architecture_pages_site import EXPECTED_PUBLIC_URL, build
from tools.validate_homepage_architecture_projection import (
    ARCHITECTURE_PAGES_URL,
    ARCHITECTURE_PAGES_PRESENTATION_URL,
    PUBLISHED_SVG_SHA256,
    README_PATH,
    TASK150_HTML_SHA256,
    TASK150_SVG_SHA256,
    ROOT,
    _standalone_svg_bytes,
    sha256_bytes,
    validate,
)


LATEST_PATH = ROOT / "RESULTS/LATEST.md"


class HomepageArchitectureProjectionTests(unittest.TestCase):
    def test_stable_homepage_projection_is_current_and_displayed(self) -> None:
        result = validate(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["source_unchanged_from_formal_main"])
        self.assertTrue(result["homepage_display_verified"])
        self.assertEqual(result["default_renderer"], "NOT_SELECTED")
        self.assertEqual(result["agent_reach"], "NO_CHANGE")
        self.assertEqual(result["svg"]["nodes"], result["html"]["nodes"])
        self.assertEqual(result["svg"]["edges"], result["html"]["edges"])
        self.assertEqual(result["public_delivery"]["url"], ARCHITECTURE_PAGES_URL)
        self.assertEqual(result["public_delivery"]["status"], "AWAITING_PAGES_DEPLOYMENT_OBSERVATION")

    def test_published_svg_is_a_bounded_packaging_of_the_task150_svg(self) -> None:
        source = (ROOT / "data/operations/iterations/150/derived-artifacts/task150-current-architecture.svg").read_bytes()
        published = (ROOT / "docs/generated/ignition-system-architecture.svg").read_bytes()
        html = (ROOT / "docs/generated/ignition-system-architecture.html").read_bytes()
        self.assertEqual(sha256_bytes(source), TASK150_SVG_SHA256)
        self.assertEqual(sha256_bytes(published), PUBLISHED_SVG_SHA256)
        self.assertEqual(sha256_bytes(html), TASK150_HTML_SHA256)
        self.assertEqual(_standalone_svg_bytes(source), published)
        self.assertNotIn(b"iterations/150/", published)
        self.assertNotIn(b"iterations/150/", html)

    def test_pages_payload_is_an_exact_copy_of_stable_html(self) -> None:
        with TemporaryDirectory() as directory:
            result = build(Path(directory))
            payload = Path(directory) / "architecture" / "index.html"
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["public_url"], EXPECTED_PUBLIC_URL)
            self.assertEqual(payload.read_bytes(), (ROOT / "docs/generated/ignition-system-architecture.html").read_bytes())
            self.assertEqual(result["payload"]["sha256"], TASK150_HTML_SHA256)
            self.assertEqual(result["payload"]["bytes"], payload.stat().st_size)
            self.assertTrue((Path(directory) / "index.html").is_file())
            self.assertTrue((Path(directory) / ".nojekyll").is_file())

    def test_task169_readme_results_entry_is_exact(self) -> None:
        readme = README_PATH.read_text(encoding="utf-8")
        start = readme.index("## 3. 结果与火种")
        end = readme.index("## 4. 整体架构")
        self.assertEqual(
            readme[start:end],
            """## 3. 结果与火种

先看[《火种：点火跑出来的发现、问题与写作种子》](../ignition/PUBLICATIONS/pointfire-results-book/12-火种：点火跑出来的发现、问题与写作种子.md)：现有成果、失败、边界和仍值得继续追踪的问题都从这里进入；最近一轮关于表征/基底变化、状态转换与跨线程认知碰撞的研究仍保持研究候选或负结果，不升级为系统能力或认识论结论。详见[下一步认识论能力评估](../ignition/docs/governance/next-epistemic-capability-assessment-2026-09-08.md)。

随后按目的进入唯一[点火成果册](../ignition/PUBLICATIONS/pointfire-results-book/README.md)、[当前结果](../ignition/RESULTS/LATEST.md)、[开放问题](../ignition/RESULTS/OPEN-QUESTIONS.md)、[函数资产](../ignition/docs/human/function-assets/README.md)或[非函数资产](../ignition/docs/human/nonfunction-assets/README.md)。机器闭合只表示状态已记录，不表示证明、外部证据、复制或现实真值已经完成。

""",
        )

    def test_task169_readme_architecture_entries_are_exact(self) -> None:
        readme = README_PATH.read_text(encoding="utf-8")
        start = readme.index("## 4. 整体架构")
        end = readme.index("<details>", start)
        self.assertEqual(
            readme[start:end],
            """## 4. 整体架构

[![点火整体架构图](../ignition/docs/generated/ignition-system-architecture.svg)](https://arvin-liu.github.io/when-systems-catch-fire/architecture/?present=1)

[全屏打开交互式架构图](https://arvin-liu.github.io/when-systems-catch-fire/architecture/?present=1) · [阅读模式](https://arvin-liu.github.io/when-systems-catch-fire/architecture/) · 滚轮缩放 · 拖动画布 · 点击节点查看关系 · 搜索组件。

""",
        )
        self.assertEqual(readme.count(ARCHITECTURE_PAGES_PRESENTATION_URL), 2)
        self.assertEqual(readme.count(ARCHITECTURE_PAGES_URL), 3)

    def test_task169_latest_is_thin_and_routes_to_current_facts(self) -> None:
        latest = LATEST_PATH.read_text(encoding="utf-8")
        self.assertIn("[Current Facts](../docs/architecture/current-facts.md)", latest)
        self.assertIn("[下一步认识论能力评估](../docs/governance/next-epistemic-capability-assessment-2026-09-08.md)", latest)
        self.assertNotIn("0.8.0", latest)
        self.assertNotIn("2026-07-30", latest)
        self.assertNotIn("## 任务 ", latest)
        self.assertNotIn("|问题|当前结果|", latest)


if __name__ == "__main__":
    unittest.main()
