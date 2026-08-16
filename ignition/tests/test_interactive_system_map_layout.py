#!/usr/bin/env python3
"""Deterministic geometry and accessibility gates for the current system map."""

from __future__ import annotations

import json
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
from generate_interactive_system_map import (  # noqa: E402
    DEFAULT_SPEC,
    build_projection,
    render_svg,
)


SVG_NS = "http://www.w3.org/2000/svg"
BASELINE = IGNITION_ROOT / "data/architecture/system-map-geometry-baseline-r1.json"


class InteractiveSystemMapLayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = build_projection()
        self.rendered = render_svg(self.spec, IGNITION_ROOT)
        self.root = ET.fromstring(self.rendered)

    def test_materialized_spec_and_svg_are_deterministic(self) -> None:
        self.assertEqual(self.rendered, render_svg(build_projection(), IGNITION_ROOT))
        self.assertEqual(DEFAULT_SPEC.read_bytes(), (json.dumps(self.spec, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

    def test_compact_independent_column_packing_beats_row_max_baseline(self) -> None:
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        baseline_height = baseline["canvas"]["height"]
        _, _, new_width, new_height = map(float, self.root.attrib["viewBox"].split())
        self.assertEqual(new_width, 1800.0)
        self.assertLess(new_height, baseline_height * 0.8)

        clusters = self.root.findall(f"{{{SVG_NS}}}rect[@class='cluster']")
        self.assertEqual(len(clusters), len(self.spec["groups"]))
        by_column: dict[float, list[tuple[float, float]]] = {}
        group_by_id = {group["id"]: group for group in self.spec["groups"]}
        for cluster in clusters:
            x = float(cluster.attrib["x"])
            y = float(cluster.attrib["y"])
            height = float(cluster.attrib["height"])
            by_column.setdefault(x, []).append((y, height))
            self.assertLessEqual(y + height, new_height)
        for column_clusters in by_column.values():
            ordered = sorted(column_clusters)
            self.assertEqual(len({y for y, _ in ordered}), len(ordered))
            for (previous_y, previous_height), (current_y, _) in zip(ordered, ordered[1:]):
                self.assertGreaterEqual(current_y, previous_y + previous_height + self.spec["layout"]["vertical_gap"])

        # The compact renderer must not reintroduce the old shared row y positions
        # within a column: every group is positioned after its own preceding height.
        declared_rows = {group["row"] for group in group_by_id.values()}
        self.assertGreaterEqual(len(declared_rows), 3)
        self.assertEqual(self.spec["layout"]["packing_algorithm"], "deterministic-scc-ranked-column-packing-r1")

    def test_every_visible_node_remains_clickable_with_solid_background(self) -> None:
        links = self.root.findall(f".//{{{SVG_NS}}}a[@class='node-link']")
        backgrounds = self.root.findall(f"{{{SVG_NS}}}rect[@class='map-bg']")
        self.assertEqual(len(links), len(self.spec["nodes"]))
        self.assertEqual(len(backgrounds), 1)
        self.assertTrue(all(link.attrib.get("href", "").startswith("https://github.com/") for link in links))


if __name__ == "__main__":
    unittest.main()
