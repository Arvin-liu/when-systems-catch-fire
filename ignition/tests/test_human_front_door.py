import json
import unittest
from pathlib import Path

from tools.validate_human_front_door import (
    AI_FIRST_USE_HEADING,
    AI_HANDOFF,
    AI_START,
    ARCHITECTURE_PAGES_PRESENTATION_URL,
    ARCHITECTURE_PAGES_URL,
    ARCHITECTURE_INTERACTION_HINT,
    CAPABILITY_REGISTRY_LINK,
    CAPABILITIES,
    CURRENT_STATE,
    GUIDE,
    HUMAN_CURRENT_HEADING,
    HUMAN_IDENTITY_HEADING,
    HUMAN_READING,
    HUMAN_VALUES_HEADING,
    LLMS,
    MINIMAL_INVOCATION,
    OPERATING_METHOD_LINK,
    PROJECT_IDENTITY_TEXT,
    README,
    validate_component_navigation,
    validate_all,
    validate_ai_first_use_section,
    validate_readme_structure,
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
        # The canonical generator materializes every visible registry component;
        # hidden components remain represented in coverage data.
        spec = json.loads((CURRENT_STATE.parent.parent / "data/architecture/interactive-system-map.json").read_text(encoding="utf-8"))
        self.assertEqual(result["system_map_source_link_nodes"], len(spec["nodes"]))

    def test_visible_identity_and_values_blocks_are_first_and_machine_state_is_absent(self):
        validate_texts(self.readme, self.guide, self.current_state, self.human_reading)
        self.assertLess(self.readme.index(HUMAN_IDENTITY_HEADING), self.readme.index(HUMAN_VALUES_HEADING))
        self.assertLess(self.readme.index(HUMAN_VALUES_HEADING), self.readme.index(HUMAN_CURRENT_HEADING))
        self.assertLess(self.readme.index(HUMAN_CURRENT_HEADING), self.readme.index(f"## {AI_FIRST_USE_HEADING}"))
        self.assertIn("<details", self.readme.lower())
        self.assertIn("组件导航：核心控制与状态", self.readme)
        self.assertNotIn("CURRENT-SNAPSHOT", self.readme)
        self.assertNotIn("architecture_counts", self.readme)

    def test_project_identity_is_the_owner_provided_text(self):
        start = self.readme.index(HUMAN_IDENTITY_HEADING) + len(HUMAN_IDENTITY_HEADING)
        end = self.readme.index(HUMAN_VALUES_HEADING)
        identity_block = self.readme[start:end]
        self.assertIn(f"**{PROJECT_IDENTITY_TEXT}**", identity_block)

    def test_identity_applies_self_examination_to_the_whole_system(self):
        start = self.readme.index(HUMAN_IDENTITY_HEADING) + len(HUMAN_IDENTITY_HEADING)
        end = self.readme.index(HUMAN_VALUES_HEADING)
        identity_block = self.readme[start:end]
        for phrase in (
            "点火既是持续认识和改造对象的过程，也是这个过程本身可以被重新认识和改造的对象",
            "点火的整体架构乃至我们对「点火是什么」的表述也如此",
            "它们的价值不取决于新旧、名义或过去投入了多少",
            "新方法确实更好，就可以替换旧方法",
            "旧方法仍有独特作用，就保留其适用位置",
            "证据不足，就承认尚不能判断",
            "我们既不为了变化而变化，也不因为曾经有效就拒绝改变",
        ):
            self.assertIn(phrase, identity_block)

    def test_component_navigation_is_collapsed_and_canonical(self):
        architecture_start = self.readme.index("## 4. 整体架构")
        architecture_end = self.readme.index("## 5. 致谢")
        self.assertGreater(validate_component_navigation(self.readme[architecture_start:architecture_end]), 0)

    def test_ai_first_usage_entry_is_self_sufficient(self):
        validate_ai_first_use_section(self.readme)
        self.assertIn(OPERATING_METHOD_LINK, self.readme)
        self.assertIn(CAPABILITY_REGISTRY_LINK, self.readme)
        self.assertIn(MINIMAL_INVOCATION, self.readme)
        self.assertIn("默认仅作只读处理", self.readme)
        self.assertIn("提供对象不意味着授权修改仓库、联网操作或替你决定目标", self.readme)

    def test_ai_first_usage_static_fixtures_fail_closed(self):
        fixture_path = Path(__file__).parent / "fixtures/ignition-operating-method/homepage-ai-first-r1.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.assertEqual(len(fixture["cases"]), 10)
        for case in fixture["cases"]:
            with self.subTest(case=case["id"]):
                mutated = self.readme
                for replacement in case["replacements"]:
                    self.assertIn(replacement["old"], mutated)
                    mutated = mutated.replace(replacement["old"], replacement["new"], replacement.get("count", 1))
                if case["expected"] == "PASS":
                    validate_ai_first_use_section(mutated)
                else:
                    with self.assertRaises(AssertionError):
                        validate_ai_first_use_section(mutated)

    def test_static_front_door_fixture_has_positive_and_negative_cases(self):
        fixture_path = Path(__file__).parent / "fixtures/human-front-door-r3.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        for case in fixture["cases"]:
            with self.subTest(case=case["id"]):
                mutated = self.readme
                if case["mutation"] == "insert-before-identity":
                    mutated = mutated.replace(HUMAN_IDENTITY_HEADING, f"> 首页导语\n\n{HUMAN_IDENTITY_HEADING}", 1)
                elif case["mutation"] == "duplicate-identity":
                    mutated = mutated.replace(HUMAN_IDENTITY_HEADING, f"{HUMAN_IDENTITY_HEADING}\n\n{HUMAN_IDENTITY_HEADING}", 1)
                elif case["mutation"] == "duplicate-values":
                    mutated = mutated.replace(HUMAN_VALUES_HEADING, f"{HUMAN_VALUES_HEADING}\n\n{HUMAN_VALUES_HEADING}", 1)
                elif case["mutation"] == "insert-snapshot":
                    mutated = mutated.replace(HUMAN_VALUES_HEADING, f"<!-- CURRENT-SNAPSHOT:BEGIN profile=human schema=current-snapshot-r1 -->\nlegacy\n<!-- CURRENT-SNAPSHOT:END -->\n\n{HUMAN_VALUES_HEADING}", 1)
                elif case["mutation"] == "insert-details":
                    mutated = mutated.replace(HUMAN_VALUES_HEADING, f"<details>\n{HUMAN_VALUES_HEADING}\n</details>", 1)
                elif case["mutation"] == "remove-charter-link":
                    mutated = mutated.replace("[《生命共同体价值宪章》](../ignition/docs/governance/life-community-value-charter.md)", "《生命共同体价值宪章》", 1)
                elif case["mutation"] == "insert-machine-count":
                    mutated = mutated.replace(HUMAN_VALUES_HEADING, f"architecture_counts=99\n\n{HUMAN_VALUES_HEADING}", 1)
                elif case["mutation"] == "drift-project-identity":
                    mutated = mutated.replace("点火首先是一种面对未知的精神", "点火首先是一种面对短期的精神", 1)
                elif case["mutation"] == "drift-whole-system-self-examination":
                    mutated = mutated.replace("点火的整体架构乃至我们对「点火是什么」的表述也如此", "点火的整体架构不需要重新审视", 1)
                elif case["mutation"] == "insert-raw-svg-link":
                    entry = f"[全屏打开交互式架构图]({ARCHITECTURE_PAGES_PRESENTATION_URL}) · [阅读模式]({ARCHITECTURE_PAGES_URL}) · {ARCHITECTURE_INTERACTION_HINT}。\n\n"
                    mutated = mutated.replace(entry, "[查看原始 SVG](../ignition/docs/generated/ignition-system-architecture.svg)\n\n" + entry, 1)
                elif case["mutation"] == "insert-machine-architecture-explanation":
                    entry = f"[全屏打开交互式架构图]({ARCHITECTURE_PAGES_PRESENTATION_URL}) · [阅读模式]({ARCHITECTURE_PAGES_URL}) · {ARCHITECTURE_INTERACTION_HINT}。\n\n"
                    mutated = mutated.replace(entry, "SVG href link metadata\n\n" + entry, 1)
                elif case["mutation"] == "open-component-group":
                    mutated = mutated.replace("<details>\n<summary>组件导航：核心控制与状态", "<details open>\n<summary>组件导航：核心控制与状态", 1)
                elif case["mutation"] == "noncanonical-component-link":
                    mutated = mutated.replace("../ignition/docs/architecture/os-control-plane-r2.md", "../ignition/docs/README.md", 1)
                elif case["mutation"] == "duplicate-main-architecture-image":
                    image = "![点火整体架构图](../ignition/docs/generated/ignition-system-architecture.svg)"
                    mutated = mutated.replace(image, image + "\n\n" + image, 1)
                if case["expected"] == "PASS":
                    validate_readme_structure(mutated)
                else:
                    with self.assertRaises(AssertionError):
                        validate_readme_structure(mutated)

    def test_each_capability_has_direct_readme_link(self):
        for name, path in CAPABILITIES.items():
            with self.subTest(name=name):
                self.assertIn(name, self.readme)
                self.assertIn(path, self.readme)

    def test_retired_deployed_reader_is_absent(self):
        self.assertIn("arvin-liu.github.io/when-systems-catch-fire/architecture/", self.readme)
        for token in (".github/workflows/pages.yml", "pages/system-map.html"):
            self.assertNotIn(token, self.readme)
            self.assertNotIn(token, self.human_reading)

    def test_failed_results_and_counterexamples_are_visible(self):
        results = self.readme.split("## 3. 结果与火种", 1)[1].split("## 4. 整体架构", 1)[0]
        self.assertIn("不能复制的结果", results)
        self.assertIn("留下的反例", results)
        self.assertIn("而不是被统一包装成“成功”", results)

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
