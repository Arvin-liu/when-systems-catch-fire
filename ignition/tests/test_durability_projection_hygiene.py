from __future__ import annotations

import json
from pathlib import Path
import unittest

from agent_runtime.pilots.durability_lifecycle_127 import TASK_ID
from tools.validate_durability_projection_hygiene import DATA_PATH, run_check


class DurabilityProjectionHygieneTests(unittest.TestCase):
    def test_step17_projection_and_residual_gates_pass(self) -> None:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        result = run_check(data)
        self.assertEqual(result["task_id"], TASK_ID)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(all(result["checks"].values()))
        self.assertEqual(result["knowledge"]["backflow_count"], 0)
        self.assertEqual(result["human_surface"]["machine_dump_count"], 0)
        self.assertEqual(result["fire_seeds"]["artifact_backflow_count"], 0)
        self.assertEqual(result["historical_propagation"]["status"], "HISTORICAL_RESIDUAL_PRESERVED")

    def test_durability_paths_are_not_knowledge_auto_discovery(self) -> None:
        result = run_check()
        self.assertTrue(all(not item["auto_discovery"] for item in result["new_paths"].values()))
        self.assertEqual(result["function_nonfunction"]["classification"], "DERIVED_RECOMPUTED_FROM_CANONICAL_CLOSURES_NOT_TRUTH_SOURCE")
        self.assertEqual(result["sympy"]["classification"], "ENVIRONMENTAL_RESIDUAL_PRESERVED")


if __name__ == "__main__":
    unittest.main()
