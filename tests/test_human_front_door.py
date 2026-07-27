import re
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

    def test_homepage_must_mention_each_capability(self):
        # Each capability acronym must appear somewhere on the homepage. Removing
        # every occurrence (including inside the AI prompt) from both the homepage
        # and the guide keeps the prompt/guide divergence guard quiet, so the only
        # guard that can fire is the "README must mention capability" check. The
        # replacement token must not itself contain the capability name.
        for name in CAPABILITIES:
            with self.subTest(name=name), self.assertRaisesRegex(AssertionError, name):
                self.validate(
                    readme=re.sub(re.escape(name), "WITHDRAWN", self.readme),
                    guide=re.sub(re.escape(name), "WITHDRAWN", self.guide),
                )

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
        self.assertEqual(self.readme.count("## 项目阶段性更新"), 0)
        self.assertEqual(self.readme.count("## 项目宣言"), 1)
        headings = [
            "## 项目现状",
            "## 项目宣言",
            "## 使用说明",
            "## 之元写作法成果",
            "## 宪章体系",
            "## 完整可点击系统图",
            "## 项目内容入口",
        ]
        positions = [self.readme.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))
        # 项目宣言 must sit between 项目现状 and 首要入口.
        self.assertLess(self.readme.index("## 项目宣言"), self.readme.index("**首要入口：**"))

    def test_ai_prompt_is_expanded(self):
        # The stage-snapshot homepage module and its fold were removed; the AI
        # first-read prompt is now shown expanded directly (no <details> fold).
        self.assertNotIn("<summary>展开：当前能力、限制与完整项目现状</summary>", self.readme)
        self.assertNotIn("<summary>展开：完整 AI 首次阅读提示词</summary>", self.readme)
        self.assertIn("```text\n请阅读并分析点火项目：", self.readme)

    def test_complete_system_map_is_between_charter_and_usage(self):
        charter = self.readme.index("## 宪章体系")
        system_map = self.readme.index("## 完整可点击系统图")
        usage = self.readme.index("## 项目内容入口")
        self.assertLess(charter, system_map)
        self.assertLess(system_map, usage)
        self.assertIn("<object data=\"./generated/ignition-system-map.svg\"", self.readme)

    def test_system_map_has_all_clickable_nodes_and_no_l7_layer(self):
        result = validate_all()
        # 49 = 41 original declared nodes + 7 Q33 draft_candidate governance
        # nodes + 1 Charter System R1 governance node; the materialized map must
        # cover the full current node set.
        self.assertEqual(result["interactive_system_map_nodes"], 49)

    def test_pages_artifact_carries_typed_propagation_evidence(self):
        self.assertIn("typed-change-propagation.md", self.pages)
        self.assertIn("121Q32-change-propagation-impact.md", self.pages)
        self.assertIn("site/data/operations/project-components.json", self.pages)
        self.assertIn("site/data/operations/change-propagation-topology.json", self.pages)

    def test_stage_snapshot_registry_stays_in_pages_not_homepage(self):
        # The stage snapshot system/registry/history stays; only the homepage
        # display module is removed. The README must not expose 正在炼化 and the
        # Pages artifact must still carry the registry and its staleness gate.
        self.assertNotIn("正在炼化", self.readme)
        self.assertIn("data/operations/stage-snapshots.json", self.pages)
        self.assertIn("validate_stage_snapshots.py --check", self.pages)

    def test_project_declaration_poem_is_verbatim_and_separated(self):
        decl = self.readme.split("## 项目宣言", 1)[1].split("## 使用说明", 1)[0]
        self.assertIn("丹无定形，火有法度；\n炼无终局，化有来路。", decl)
        # 项目宣言 is an independent module: after 项目现状 and before 价值宪章,
        # clearly separated from both the status narrative and the value charter.
        self.assertLess(self.readme.index("## 项目现状"), self.readme.index("## 项目宣言"))
        self.assertLess(self.readme.index("## 项目宣言"), self.readme.index("## 宪章体系"))

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

    def test_stale_current_method_is_rejected_in_readme(self):
        stale = (
            "method 1.4.0 is Candidate only.\n"
            "method 1.3.0 is Current now.\n"
            "map 0.3.0 Current; map 0.2.0 Historical; map 0.1.0 earlier Historical; method 1.2.0 Historical."
        )
        with self.assertRaises(AssertionError):
            validate_version_front_doors(self.ai_start, self.ai_handoff, self.llms, readme=stale)

    def test_stale_current_method_is_rejected_in_current_state(self):
        stale = (
            "method 1.4.0 is Candidate only.\n"
            "method 1.3.0 is Current now.\n"
            "map 0.3.0 Current; map 0.2.0 Historical; map 0.1.0 earlier Historical; method 1.2.0 Historical."
        )
        with self.assertRaises(AssertionError):
            validate_version_front_doors(self.ai_start, self.ai_handoff, self.llms, current_state=stale)

    def test_charter_r1_name_required_in_front_doors(self):
        no_name = self.readme.replace("宪章系统 R1", "Charter System X").replace("Charter System R1", "Charter System X")
        with self.assertRaises(AssertionError):
            validate_texts(no_name, self.guide, self.current_state, self.pages)

    def test_charter_r1_boundary_required_in_front_doors(self):
        no_boundary = self.readme.replace("activated=false", "activated=true")
        with self.assertRaises(AssertionError):
            validate_texts(no_boundary, self.guide, self.current_state, self.pages)

    def test_charter_r1_boundary_required_in_current_state(self):
        no_boundary = self.current_state.replace("activated=false", "activated=true")
        with self.assertRaises(AssertionError):
            validate_texts(self.readme, self.guide, no_boundary, self.pages)

    def test_nonimpact_proof_exempts_front_door_surface(self):
        # A legitimate NonImpactProof must let a surface skip the staleness check.
        stale = (
            "method 1.4.0 is Candidate only.\n"
            "method 1.3.0 is Current now.\n"
            "map 0.3.0 Current; map 0.2.0 Historical; map 0.1.0 earlier Historical; method 1.2.0 Historical."
        )
        with self.assertRaises(AssertionError):
            validate_version_front_doors(self.ai_start, self.ai_handoff, self.llms, readme=stale)
        # Exempting human.readme via a valid NonImpactProof skips the stale check for that surface only.
        validate_version_front_doors(
            self.ai_start, self.ai_handoff, self.llms, readme=stale, nonimpact_proofs={"human.readme"}
        )
        # Exempting the wrong surface does not rescue the stale README.
        with self.assertRaises(AssertionError):
            validate_version_front_doors(
                self.ai_start, self.ai_handoff, self.llms, readme=stale, nonimpact_proofs={"human.current_state"}
            )


if __name__ == "__main__":
    unittest.main()
