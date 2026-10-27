#!/usr/bin/env python3
"""Geometry quality and negative-fixture tests for the sole system map."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import validate_system_map_geometry as geometry  # noqa: E402


class SystemMapGeometryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = geometry.build_report()
        self.baseline = geometry.load_json(geometry.BASELINE_PATH)

    def test_current_geometry_passes_all_quality_thresholds(self) -> None:
        self.assertEqual(self.report["status"], "PASS")
        self.assertGreaterEqual(self.report["metrics"]["blank_area_reduction_vs_baseline"], 0.30)
        self.assertGreaterEqual(self.report["metrics"]["canvas_height_reduction_vs_baseline"], 0.20)
        self.assertLessEqual(self.report["metrics"]["edge_crossing_ratio_vs_baseline"], 1.10)
        self.assertLessEqual(self.report["max_internal_gap"], 200)
        self.assertEqual(self.report["bottom_only_isolated_groups"], [])

    def test_report_is_materialized_deterministically(self) -> None:
        expected = (json.dumps(self.report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        self.assertEqual(geometry.QUALITY_PATH.read_bytes(), expected)

    def test_negative_geometry_fixtures_are_rejected(self) -> None:
        self.assertEqual(geometry.check_fixtures(self.report, self.baseline), [])
        old = geometry.fixture_baseline_candidate(self.baseline)
        old_result = geometry.assess(old, self.baseline)
        self.assertEqual(old_result["status"], "FAIL")
        self.assertIn("blank_area_reduction", old_result["failures"])
        overlap = json.loads(json.dumps(self.report))
        overlap["group_box_overlap_count"] = 1
        self.assertIn("group_box_overlap", geometry.assess(overlap, self.baseline)["failures"])


if __name__ == "__main__":
    unittest.main()
