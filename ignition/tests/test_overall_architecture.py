#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generate_overall_architecture", ROOT / "tools/generate_overall_architecture.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class OverallArchitectureTest(unittest.TestCase):
    def test_conceptual_map_is_transparent_clickable_and_bounded(self) -> None:
        spec = MODULE.json.loads(MODULE.SPEC_PATH.read_text(encoding="utf-8"))
        MODULE.validate_spec(spec)
        svg = MODULE.OUT.read_text(encoding="utf-8")
        self.assertEqual(spec["title"], "点火唯一完整可点击总架构图")
        self.assertEqual(len(spec["nodes"]), 64)
        self.assertIn("map-bg", svg)
        self.assertEqual(svg.count('class="node-link"'), 64)
        self.assertEqual(spec["component_coverage"]["registry_components"], 75)
        self.assertEqual(spec["component_coverage"]["visible_nodes"], 64)


if __name__ == "__main__":
    unittest.main()
