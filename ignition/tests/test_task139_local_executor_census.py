from __future__ import annotations

import unittest
from pathlib import Path

from agent_federation.local_executor_census import validate_path


class Task139LocalExecutorCensusTests(unittest.TestCase):
    def test_fresh_census_selects_only_the_re_attested_codex_candidate(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data/operations/iterations/139/local-executor-census-r1.json"
        summary = validate_path(path, expected_task_id="IGNITION-20260825-139", expected_step="09")
        self.assertTrue(summary["safe"])
        self.assertEqual(summary["candidate_count"], 14)
        self.assertEqual(summary["agentic_executor_count"], 5)
        self.assertEqual(summary["admitted_executor_count"], 1)
        self.assertEqual(summary["selected_executor_id"], "external.codex")


if __name__ == "__main__":
    unittest.main()
