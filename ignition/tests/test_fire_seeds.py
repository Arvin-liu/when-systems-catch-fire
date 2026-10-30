#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_fire_seeds", ROOT / "tools/publication/validate_fire_seeds.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class FireSeedsTest(unittest.TestCase):
    def test_human_layer_and_census_are_closed(self) -> None:
        result = MODULE.validate()
        self.assertGreaterEqual(result["entries"], 20)
        self.assertEqual(result["entries"], result["clusters"])

    def test_q1_layered_origin_updates_census_without_creating_seed(self) -> None:
        census = json.loads(MODULE.CENSUS.read_text(encoding="utf-8"))
        layered_rows = [
            line for line in MODULE.LAYERED.read_text(encoding="utf-8").splitlines() if line.strip()
        ]
        self.assertEqual(census["knowledge_experience"]["layered_reading_source_origins"], len(layered_rows))
        self.assertEqual(census["knowledge_experience"]["manifest_counts"]["layered_readings"], len(layered_rows))
        self.assertEqual(census["source_census_summary"]["knowledge_experience_source_origins"], len(layered_rows))
        self.assertEqual(census["candidate_count"], len(census["seeds"]))
        self.assertEqual(census["cluster_count"], len(census["clusters"]))
        reflection_path = "docs/what-is-ignition/2026-10-13-gpt6-participant-reflection.md"
        origin = next(row for row in census["source_census"] if row["source_path"] == reflection_path)
        self.assertEqual(origin["disposition"], "NO_SEED_DELTA")
        self.assertEqual(origin["seed_ids"], [])
        self.assertTrue(all(seed["external_novelty_status"] == "NOT_CHECKED" for seed in census["seeds"]))


if __name__ == "__main__":
    unittest.main()
