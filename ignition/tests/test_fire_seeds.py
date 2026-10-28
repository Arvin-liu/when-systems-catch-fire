#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
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


if __name__ == "__main__":
    unittest.main()
