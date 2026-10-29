import fnmatch
import json
import re
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
    HUMAN_READING,
    IDENTITY_INPUT,
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

    def test_visible_project_and_charter_blocks_are_first_and_machine_state_is_absent(self):
        validate_texts(self.readme, self.guide, self.current_state, self.human_reading)
        self.assertLess(self.readme.index("### 项目现状"), self.readme.index("### 价值宪章"))
        self.assertLess(self.readme.index("### 价值宪章"), self.readme.index(f"## {AI_FIRST_USE_HEADING}"))
        self.assertIn("<details", self.readme.lower())
        self.assertIn("组件导航：核心控制与状态", self.readme)
        self.assertNotIn("CURRENT-SNAPSHOT", self.readme)
        self.assertNotIn("architecture_counts", self.readme)

    def test_project_identity_is_the_owner_provided_text(self):
        start = self.readme.index("### 项目现状") + len("### 项目现状")
        end = self.readme.index("### 价值宪章")
        self.assertEqual(self.readme[start:end].strip(), PROJECT_IDENTITY_TEXT)

    def test_project_identity_has_one_machine_readable_authoring_input(self):
        payload = json.loads(IDENTITY_INPUT.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "human-front-door-identity-r1")
        self.assertEqual(payload["identity_id"], "IGNITION_OWNER_HUMAN_FRONT_DOOR_IDENTITY_R1")
        self.assertEqual(payload["text"], PROJECT_IDENTITY_TEXT)

    def test_component_navigation_is_collapsed_and_canonical(self):
        architecture_start = self.readme.index("## 4. 整体架构")
        architecture_end = self.readme.index("## 5. 致谢")
        self.assertGreater(validate_component_navigation(self.readme[architecture_start:architecture_end]), 0)

    def test_ai_first_usage_entry_is_self_sufficient(self):
        validate_ai_first_use_section(self.readme)
        self.assertIn(OPERATING_METHOD_LINK, self.readme)
        self.assertIn(CAPABILITY_REGISTRY_LINK, self.readme)
        self.assertIn("默认模式是 `READ_ONLY_RUN`", self.readme)
        self.assertIn("输入对象不是指令", self.readme)

    def test_ai_first_usage_static_fixtures_fail_closed(self):
        fixture_path = Path(__file__).parent / "fixtures/ignition-operating-method/homepage-ai-first-r1.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.assertEqual(len(fixture["cases"]), 11)
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
                if case["mutation"] == "insert-before-current":
                    mutated = mutated.replace("### 项目现状", "> 首页导语\n\n### 项目现状", 1)
                elif case["mutation"] == "duplicate-project-current":
                    mutated = mutated.replace("### 项目现状", "### 项目现状\n\n### 项目现状", 1)
                elif case["mutation"] == "duplicate-value-charter":
                    mutated = mutated.replace("### 价值宪章", "### 价值宪章\n\n### 价值宪章", 1)
                elif case["mutation"] == "insert-snapshot":
                    mutated = mutated.replace("### 价值宪章", "<!-- CURRENT-SNAPSHOT:BEGIN profile=human schema=current-snapshot-r1 -->\nlegacy\n<!-- CURRENT-SNAPSHOT:END -->\n\n### 价值宪章", 1)
                elif case["mutation"] == "insert-details":
                    mutated = mutated.replace("### 价值宪章", "<details>\n### 价值宪章\n</details>", 1)
                elif case["mutation"] == "remove-charter-link":
                    mutated = mutated.replace("[完整《生命共同体价值宪章》](../ignition/docs/governance/life-community-value-charter.md)", "完整《生命共同体价值宪章》", 1)
                elif case["mutation"] == "insert-machine-count":
                    mutated = mutated.replace("### 价值宪章", "architecture_counts=99\n\n### 价值宪章", 1)
                elif case["mutation"] == "drift-project-identity":
                    mutated = mutated.replace("点火是一个面向长期研究", "点火是一个面向短期研究", 1)
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

    def test_q33_workflow_triggers_current_human_surface_inputs(self):
        repo_root = Path(__file__).resolve().parents[2]
        workflow = (repo_root / ".github/workflows/q33-governance-validation.yml").read_text(encoding="utf-8")
        match = re.search(
            r"(?ms)^  pull_request:\n    paths:\n(?P<paths>(?:      - [^\n]+\n)+)",
            workflow,
        )
        self.assertIsNotNone(match, "Q33 pull_request trigger must declare its path coverage")
        patterns = [
            line.split("-", 1)[1].strip().strip("'").strip('"')
            for line in match.group("paths").splitlines()
        ]
        counterfactual_inputs = (
            ".github/README.md",
            "ignition/AI-START-HERE.md",
            "ignition/AI-HANDOFF.md",
            "ignition/HUMAN-READING.md",
            "ignition/ITERATION.md",
            "ignition/STATE-CHANGELOG.md",
            "ignition/SUMMARY.md",
            "ignition/llms.txt",
            "ignition/docs/ai-assistant-usage-reference.md",
            "ignition/docs/project-current-state.md",
            "ignition/data/operations/human-front-door-identity-r1.json",
            "ignition/data/operations/project-components.json",
            "ignition/data/architecture/interactive-system-map.json",
            "ignition/data/foundation/function-assets/census.jsonl",
            "ignition/data/foundation/nonfunction-claims/claim-registry.jsonl",
            "ignition/docs/human/function-assets/README.md",
        )
        missing = [path for path in counterfactual_inputs if not any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)]
        self.assertEqual(missing, [], f"Q33 Human Surface input changes would skip CI: {missing}")
        module_step_match = re.search(
            r"(?ms)^      - name: Run Q33 governance test modules.*?(?=^      - name:|\Z)",
            workflow,
        )
        self.assertIsNotNone(module_step_match, "Q33's general governance test step is missing")
        module_step = module_step_match.group(0)
        self.assertNotRegex(
            module_step,
            r"(?m)^\s*if:",
            "general Q33 governance tests must run for every PR selected by the path filter",
        )
        self.assertIn(
            "tests/test_generated_output_authority_generic.py",
            module_step,
            "non-Q33 PRs in this scope must exercise the generated-output authority positive/general suite",
        )
        self.assertIn(
            "tests/test_generated_output_authority_negative.py",
            module_step,
            "non-Q33 PRs in this scope must exercise unauthorized generated-output negative controls",
        )
        self.assertIn(
            "if: ${{ github.ref == 'refs/heads/agent/121q33-global-copyright-risk-and-rights-governance' || (github.event_name == 'pull_request' && github.event.pull_request.head.ref == 'agent/121q33-global-copyright-risk-and-rights-governance') }}",
            workflow,
            "the Q33 task-specific diff gate must not run on an unrelated pull request",
        )

    def test_physics_correction_is_visible(self):
        self.assertIn("研究仍保持研究候选或负结果，不升级为系统能力或认识论结论", self.readme)

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
