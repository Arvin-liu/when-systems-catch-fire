#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import copy
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/overall-architecture-derived-expectation-r1.json"
SPEC = importlib.util.spec_from_file_location("generate_overall_architecture", ROOT / "tools/generate_overall_architecture.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class OverallArchitectureTest(unittest.TestCase):
    def assert_canonical_projection(self, spec: dict, svg: str, expected: dict) -> None:
        MODULE.validate_spec(spec)
        registry_count = expected["component_coverage"]["registry_components"]
        visible_nodes = len(expected["nodes"])
        hidden_count = expected["component_coverage"]["hidden_components"]
        visible_edges = len(expected["edges"])

        self.assertEqual(spec["nodes"], expected["nodes"])
        self.assertEqual(spec["edges"], expected["edges"])
        self.assertEqual(spec["groups"], expected["groups"])
        self.assertEqual(spec["layout"], expected["layout"])
        self.assertEqual(spec["component_coverage"], expected["component_coverage"])
        self.assertEqual(spec["component_coverage"]["registry_components"], registry_count)
        self.assertEqual(spec["component_coverage"]["visible_nodes"], visible_nodes)
        self.assertEqual(spec["component_coverage"]["hidden_components"], hidden_count)
        self.assertEqual(registry_count, visible_nodes + hidden_count)
        self.assertEqual(len(spec["edges"]), visible_edges)
        self.assertEqual(svg.count('class="node-link"'), visible_nodes)
        self.assertEqual(spec["component_coverage"]["orphan_components"], [])

        geometry = spec["layout"]
        self.assertGreaterEqual(geometry["columns"], 1)
        self.assertGreaterEqual(geometry["group_width"], 1)
        self.assertGreaterEqual(geometry["group_header_height"], 1)
        self.assertGreaterEqual(geometry["node_height"], 1)
        self.assertGreaterEqual(geometry["node_gap"], 0)
        self.assertGreaterEqual(geometry["vertical_gap"], 0)
        node_ids = {node["id"] for node in spec["nodes"]}
        self.assertTrue(all(edge["source"] in node_ids and edge["target"] in node_ids for edge in spec["edges"]))

    def test_conceptual_map_is_transparent_source_linked_and_bounded(self) -> None:
        spec = MODULE.json.loads(MODULE.SPEC_PATH.read_text(encoding="utf-8"))
        expected = MODULE.build_projection()
        svg = MODULE.OUT.read_text(encoding="utf-8")
        self.assertEqual(spec["title"], "点火唯一完整总架构图")
        self.assertIn("map-bg", svg)
        # The graph contract is derived from the canonical component registry,
        # propagation topology, and layout overlay.  No Current node/edge
        # count is duplicated as a test magic number.
        self.assert_canonical_projection(spec, svg, expected)

    def test_unsynchronized_projection_fixture_fails_closed(self) -> None:
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(fixture["schema_version"], "overall-architecture-derived-expectation-r1")
        self.assertEqual(fixture["synchronized_case"]["expected"], "PASS")
        self.assertEqual(fixture["unsynchronized_case"]["expected"], "FAIL")

        spec = MODULE.json.loads(MODULE.SPEC_PATH.read_text(encoding="utf-8"))
        expected = MODULE.build_projection()
        synchronized = copy.deepcopy(expected)
        self.assert_canonical_projection(synchronized, MODULE.OUT.read_text(encoding="utf-8"), expected)

        stale = copy.deepcopy(spec)
        mutation = fixture["unsynchronized_case"]["mutation"]
        if mutation == "remove_last_visible_node_without_updating_coverage":
            stale["nodes"].pop()
        else:
            self.fail(f"unknown fixture mutation: {mutation}")
        with self.assertRaises((AssertionError, ValueError)):
            self.assert_canonical_projection(stale, MODULE.OUT.read_text(encoding="utf-8"), expected)


if __name__ == "__main__":
    unittest.main()
