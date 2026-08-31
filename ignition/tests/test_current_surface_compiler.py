from __future__ import annotations

import unittest

from tools import current_surface_compiler as compiler


class CurrentSurfaceCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = compiler.build_snapshot()
        cls.contract = compiler.load_json(compiler.CONTRACT_PATH)

    def test_all_profiles_share_snapshot_identity_and_task(self) -> None:
        for profile in ("human", "ai", "machine"):
            with self.subTest(profile=profile):
                block = compiler.render_block(self.snapshot, profile)
                self.assertIn(self.snapshot["identity"]["epoch"], block)
                self.assertIn(self.snapshot["current_task"]["task_id"], block)
                self.assertIn(str(self.snapshot["iteration_identity"]["current_formal_task_ordinal"]), block)
                self.assertIn(str(self.snapshot["iteration_identity"]["latest_architecture_task_ordinal"]), block)
                self.assertIn(str(self.snapshot["iteration_identity"]["current_iteration_boundary"]), block)
                if profile == "machine":
                    self.assertIn(self.snapshot["iteration_identity"]["current_iteration_boundary_semantics"], block)
                else:
                    self.assertIn("deprecated compatibility alias", block)
                self.assertIn(self.snapshot["map"]["current_version"], block)
                self.assertIn(self.snapshot["current_operating_method"]["identity"], block)
                self.assertIn(self.snapshot["current_operating_method"]["version"], block)
                self.assertIn(self.snapshot["current_method_version"], block)
                self.assertIn("REMOTE_REF_OBSERVATION", block)
                self.assertIn(compiler.BLOCK_END, block)

    def test_publication_is_projected_as_authority_not_static_state(self) -> None:
        for profile in ("human", "ai", "machine"):
            with self.subTest(profile=profile):
                block = compiler.render_block(self.snapshot, profile)
                self.assertNotIn("NOT_PUBLISHED", block)
                self.assertNotIn("release_publication_state", block)
                self.assertNotIn("release_task_branch_projection", block)
                self.assertIn("REMOTE_REF_OBSERVATION", block)
                self.assertIn("NONE", block)

    def test_render_is_byte_deterministic(self) -> None:
        self.assertEqual(compiler.render_block(self.snapshot, "human"), compiler.render_block(self.snapshot, "human"))

    def test_iteration_and_operating_method_versions_are_not_overwritten(self) -> None:
        self.assertEqual(self.snapshot["current_method_version"], "1.4.0")
        self.assertEqual(self.snapshot["current_operating_method"]["version"], "1.0.0")
        self.assertEqual(self.snapshot["current_operating_method"]["identity"], "IGNITION_OPERATING_METHOD_R1")

    def test_upsert_replaces_existing_block_without_duplicate(self) -> None:
        surface = {"surface_id": "test", "profile": "human", "insert_after": "## 1."}
        first = compiler.compile_surface("# H\n## 1. 项目与价值\n", surface, self.snapshot)
        second = compiler.compile_surface(first, surface, self.snapshot)
        self.assertEqual(first, second)
        self.assertEqual(second.count("CURRENT-SNAPSHOT:BEGIN"), 1)

    def test_homepage_block_does_not_add_heading(self) -> None:
        surface = {"surface_id": "test", "profile": "human", "insert_after": "## 1."}
        text = compiler.compile_surface("# H\n## 1. 项目与价值\n", surface, self.snapshot)
        self.assertEqual(text.count("## "), 1)

    def test_homepage_is_explicitly_non_generated_surface(self) -> None:
        surface = next(row for row in self.contract["non_generated_surfaces"] if row["surface_id"] == "homepage-identity")
        source = "# H\n## 1. 项目与价值\n### 项目现状\n### 价值宪章\n"
        self.assertEqual(compiler.compile_surface(source, surface, self.snapshot), source)
        self.assertNotIn("CURRENT-SNAPSHOT", compiler.compile_surface(source, surface, self.snapshot))

    def test_homepage_legacy_surface_never_injects(self) -> None:
        legacy_surface = {"surface_id": "homepage-identity", "path": ".github/README.md", "profile": "human", "insert_after": "### 项目现状"}
        source = "# H\n## 1. 项目与价值\n### 项目现状\n### 价值宪章\n"
        self.assertEqual(compiler.compile_surface(source, legacy_surface, self.snapshot), source)

    def test_homepage_identity_and_component_navigation_survive_current_compiler(self) -> None:
        source = (compiler.REPO_ROOT / compiler.HOMEPAGE_PATH).read_text(encoding="utf-8")
        surface = next(row for row in self.contract["non_generated_surfaces"] if row["surface_id"] == "homepage-identity")
        compiled = compiler.compile_surface(source, surface, self.snapshot)
        self.assertEqual(compiled, source)
        self.assertIn("点火是一个面向长期研究、判断与创作的认知—行动工作系统", compiled)
        self.assertIn("组件导航：核心控制与状态", compiled)


if __name__ == "__main__":
    unittest.main()
