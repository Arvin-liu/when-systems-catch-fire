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
                self.assertIn(self.snapshot["map"]["current_version"], block)
                self.assertIn(compiler.BLOCK_END, block)

    def test_render_is_byte_deterministic(self) -> None:
        self.assertEqual(compiler.render_block(self.snapshot, "human"), compiler.render_block(self.snapshot, "human"))

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


if __name__ == "__main__":
    unittest.main()
