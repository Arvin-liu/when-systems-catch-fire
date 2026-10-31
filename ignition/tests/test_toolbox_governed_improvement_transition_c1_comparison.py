from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import toolbox_execution_pareto_frontier as pareto
import toolbox_governed_improvement_transition as transition


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/toolbox-governed-improvement-transition"
DATA = ROOT / "data/operations"


class GovernedTransitionC1ComparisonTests(unittest.TestCase):
    def test_matched_synthetic_outputs_are_complementary_and_non_authoritative(self) -> None:
        transition_inputs = {
            "variant_b": FIXTURES / "c1-transition-variant-b-r0.json",
            "variant_c": FIXTURES / "c1-transition-variant-c-r0.json",
        }
        results = {
            key: transition.analyze_bytes(path.read_bytes())
            for key, path in transition_inputs.items()
        }
        pareto_path = FIXTURES / "c1-pareto-input-r0.json"
        frontier = pareto.analyze(pareto_path.read_bytes())

        self.assertEqual(frontier["frontier_candidate_ids"], ["variant-b", "variant-c"])
        self.assertEqual(frontier["quality_floor_pass_rate_fraction"], "2/3")
        self.assertEqual(
            {row["candidate_id"]: row["pass_rate_fraction"] for row in frontier["candidates"]},
            {"predecessor-a": "2/3", "variant-b": "2/3", "variant-c": "1/1"},
        )
        self.assertFalse(frontier["execution_authorized"])

        self.assertEqual(results["variant_b"]["status"], "REVIEW_REQUIRED")
        self.assertEqual(results["variant_c"]["status"], "REVIEW_REQUIRED")
        self.assertEqual(results["variant_b"]["quality_deltas"][0]["primary_directional_delta"], 0)
        self.assertEqual(results["variant_c"]["quality_deltas"][0]["primary_directional_delta"], 1)
        for result in results.values():
            self.assertFalse(result["improvement_accepted"])
            self.assertFalse(result["successor_promoted"])
            self.assertFalse(result["execution_authorized"])
            self.assertEqual(result["authority_delta"]["added_scopes"], [])
            self.assertTrue(result["rollback"]["target_matches_predecessor"])
            self.assertEqual(result["next_round_rnd_gain"]["status"], "NOT_MEASURED")

        receipt_path = DATA / "toolbox-governed-improvement-transition-c1-matched-comparison-r0.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["interpretation"]["comparison_status"], "COMPARISON_UNKNOWN")
        self.assertEqual(receipt["interpretation"]["replacement_or_retirement"].split(".")[0], "No replacement or retirement is supported")
        self.assertEqual(receipt["operator_steps_per_multi_successor_task"], {
            "transition_preflight": 2,
            "pareto_summary": 1,
            "combined": 3,
        })
        receipt_inputs = {
            "transition_variant_b": transition_inputs["variant_b"],
            "transition_variant_c": transition_inputs["variant_c"],
            "pareto_all_successors": pareto_path,
        }
        for key, path in receipt_inputs.items():
            self.assertEqual(
                receipt["runs"][key]["input_sha256"],
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )

        c1 = json.loads((DATA / "toolbox-governed-improvement-transition-c1-evidence-r0.json").read_text(encoding="utf-8"))
        self.assertEqual(c1["same_task_trials"]["status"], "COMPLETED_SYNTHETIC_ONLY")
        self.assertEqual(c1["decision"]["comparison_status"], "COMPARISON_UNKNOWN")
        self.assertEqual(c1["decision"]["replacement_candidates"], [])


if __name__ == "__main__":
    unittest.main()
