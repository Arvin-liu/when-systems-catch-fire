"""Focused checks for the Task180 evaluation evidence and frozen boundaries."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPORT_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "validate_task180_evaluation",
    REPORT_DIR / "validate_task180_evaluation.py",
)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class Task180EvaluationTests(unittest.TestCase):
    def test_report_bundle_is_complete_and_consistent(self) -> None:
        result = VALIDATOR.validate_artifacts()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["frozen_metrics_checked"], 11)
        self.assertEqual(result["negative_controls_checked"], 8)

    def test_continuations_preserve_non_equivalence_boundaries(self) -> None:
        content = VALIDATOR.read_json("continuation-content.json")
        engineering = VALIDATOR.read_json("continuation-engineering.json")
        self.assertEqual(content["faster_than_A"]["decision"], "NO")
        self.assertEqual(content["capability_or_external_truth"]["decision"], "NO")
        self.assertEqual(engineering["current_reverification"]["can_claim_current_7_of_7"], "NO")
        self.assertTrue(engineering["forbidden_inferences"])

    def test_blind_checkpoint_precedes_unblind(self) -> None:
        log = VALIDATOR.read_json("blind-evaluation-log.json")
        comparison = VALIDATOR.read_json("unblind-comparison.json")
        self.assertFalse(log["sequence"]["unblind_material_read_before_checkpoint"])
        self.assertTrue(comparison["blind_checkpoint"]["remote_push_verified"])
        self.assertEqual(
            comparison["blind_checkpoint"]["commit"],
            "cf37d6d33707870514c3e62249ac3b8cbebf2526",
        )

    def test_frozen_criteria_and_contamination_are_retained(self) -> None:
        verdict = VALIDATOR.read_json("verdict.json")
        criterion_ids = {record["criterion_id"] for record in verdict["frozen_criterion_dispositions"]}
        self.assertEqual(criterion_ids, VALIDATOR.CRITERIA)
        self.assertEqual(verdict["blinding_contamination"]["status"], "BLINDING_CONTAMINATION")
        self.assertTrue(verdict["conversation_independence_declaration"]["builder_narrative_exposed_after_e2"])
        self.assertEqual(verdict["owner_gpt_adjudication"], "NOT_YET_RUN")

    def test_post_e2_exposure_is_disclosed_without_rewriting_checkpoint(self) -> None:
        addendum = VALIDATOR.read_json("post-e2-contamination-addendum.json")
        self.assertFalse(addendum["event"]["e1_blind_checkpoint_changed"])
        self.assertFalse(addendum["event"]["body_claims_used_to_resolve_unknowns"])
        self.assertTrue(addendum["execution_correction"]["corrected_via_base_update"])


if __name__ == "__main__":
    unittest.main()
