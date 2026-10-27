"""Regression tests for the Task172 Step07 bounded routing index."""

import unittest
from pathlib import Path

from tools.research.task172_routing import retrieve_candidates
from tools.research.validate_task172_routing_index import validate


ROOT = Path(__file__).resolve().parents[1]


class Task172Step07RoutingTest(unittest.TestCase):
    def test_index_is_complete_deterministic_and_read_only(self) -> None:
        validate(ROOT)

    def test_bounded_facet_query_returns_exact_ids(self) -> None:
        result = retrieve_candidates(
            ROOT,
            {
                "asset_kinds": ["FUNCTION_ASSET", "NONFUNCTION_CLAIM"],
                "unesco_field_codes": ["61"],
                "collision_use": ["EVIDENCE_CHECK"],
            },
            top_k=25,
        )
        self.assertLessEqual(result["selected_count"], 25)
        self.assertEqual(result["invalid_selection_count"], 0)
        self.assertEqual(result["exact_validation_status"], "ALL_SELECTED_EXACT")
        self.assertFalse(result["side_effects"]["repository_mutation"])

    def test_empty_facets_report_explicit_fallback(self) -> None:
        result = retrieve_candidates(ROOT, {"asset_kinds": ["FUNCTION_ASSET"]}, top_k=10)
        self.assertTrue(result["fallback"]["occurred"])
        self.assertEqual(result["fallback"]["reason"], "NO_BOUNDED_FACETS")
        self.assertTrue(result["fallback"]["explicit"])
        self.assertEqual(result["invalid_selection_count"], 0)


if __name__ == "__main__":
    unittest.main()
