from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import evaluate_object_collision_run as collision  # noqa: E402
import plan_ignition_operation_run as planner  # noqa: E402


class IgnitionObjectCollisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = json.loads(collision.FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.base = cls.fixtures["base_run"]

    def test_all_twelve_collision_fixtures_pass(self) -> None:
        self.assertEqual(len(self.fixtures["cases"]), 12)
        self.assertEqual(collision.validate_fixtures(self.fixtures), [])

    def test_report_binds_both_current_canonical_registries(self) -> None:
        result = collision.render_run(copy.deepcopy(self.base))
        matches = {row["canonical_id"]: row for row in result["existing_canonical_matches"]}
        self.assertEqual(set(matches), {"T2", "CLAIM-T2"})
        self.assertEqual(matches["T2"]["record_sha256"], "e8aca6e6451d0669f262f840a1ddbb2f83c9420be3ba45fd662f200ac77e470d")
        self.assertEqual(matches["CLAIM-T2"]["record_sha256"], "a02e5aa6aff35b60f28ca8cdd0beca0f02a0ea887efef594fec17ce8e6a03136")
        self.assertEqual(matches["T2"]["claim_ceiling"], matches["CLAIM-T2"]["claim_ceiling"])

    def test_source_explicit_viewpoint_is_not_an_increment(self) -> None:
        result = collision.render_run(copy.deepcopy(self.base))
        self.assertEqual([row["finding_id"] for row in result["input_derived_findings"]], ["F1"])
        self.assertEqual([row["finding_id"] for row in result["ignition_increments"]], ["F2"])

    def test_candidate_new_requires_actual_matches_and_never_writes_registry(self) -> None:
        case = next(row for row in self.fixtures["cases"] if row["case_id"] == "valid_candidate_new_requires_actual_nearest_matches")
        run = collision.apply_fixture_mutations(self.base, case["mutations"])
        result = collision.render_run(run)
        self.assertEqual(result["candidate_new"][0]["nearest_canonical_match_ids"], ["M1", "M2"])
        self.assertEqual(result["candidate_registry_action"], "NONE")
        self.assertFalse(result["side_effects_authorized"])

    def test_input_viewpoint_cannot_be_relabelled_candidate_new(self) -> None:
        run = copy.deepcopy(self.base)
        run["candidate_new"] = [{
            "candidate_id": "CANDIDATE-COPIED",
            "statement": run["normalized_units"][0]["text"],
            "relationship": "CANDIDATE_NEW",
            "derived_from_unit_ids": ["U1"],
            "nearest_canonical_match_ids": ["M1"],
            "collision_delta": "A copied statement is not a delta.",
            "not_verbatim_from_input": True,
            "source_explicit_overlap_review": {
                "reviewed_unit_ids": ["U1"],
                "decision": "NOT_SOURCE_EXPLICIT",
                "method": "Exact comparison",
                "rationale": "Synthetic false assertion for fail-closed testing.",
            },
            "registry_action": "NONE",
        }]
        errors = collision.validate_run(run)
        self.assertTrue(any("source-explicit input cannot be relabelled CANDIDATE_NEW" in error for error in errors))

    def test_candidate_overlap_review_must_cover_derived_units(self) -> None:
        case = next(row for row in self.fixtures["cases"] if row["case_id"] == "valid_candidate_new_requires_actual_nearest_matches")
        run = collision.apply_fixture_mutations(self.base, case["mutations"])
        run["candidate_new"][0]["source_explicit_overlap_review"]["reviewed_unit_ids"] = ["U1"]
        errors = collision.validate_run(run)
        self.assertTrue(any("overlap review must cover every derived source unit" in error for error in errors))

    def test_undefined_pseudo_quantification_is_rejected(self) -> None:
        run = copy.deepcopy(self.base)
        run["quantitative_assessments"] = [{
            "metric_id": "UNDEFINED",
            "metric_name": "同构度",
            "metric_value": 75,
        }]
        errors = collision.validate_run(run)
        self.assertTrue(any("metric_definition" in error for error in errors))

    def test_unknown_current_asset_fails_closed(self) -> None:
        run = copy.deepcopy(self.base)
        run["canonical_search"]["matches"][0]["canonical_id"] = "D999999"
        errors = collision.validate_run(run)
        self.assertTrue(any("canonical ID not present" in error for error in errors))

    def test_read_only_contract_rejects_every_side_effect(self) -> None:
        for key in ("repository_mutation", "external_action", "registry_write"):
            run = copy.deepcopy(self.base)
            run["side_effects"][key] = True
            errors = collision.validate_run(run)
            self.assertTrue(any(key in error for error in errors))

    def test_user_note_routes_registered_collision_operation_read_only(self) -> None:
        request = {
            "request_envelope": {"user_request": "用最新的点火跑一遍这篇笔记，我要看你的输出。"},
            "input_objects": [{"object_type": "MARKDOWN", "content": "fixture note"}],
        }
        plan = planner.plan_run(request, "knowledge.collide_object", "refs/heads/main@example-current")
        self.assertEqual(plan["run_mode"], "READ_ONLY_RUN")
        self.assertEqual(plan["operation_status"], "CURRENT_BOUNDED")
        self.assertEqual(plan["decision"], "PROCEED_BOUNDED")
        self.assertIn(collision.FUNCTION_AUTHORITY, plan["minimal_read_plan"])
        self.assertIn(collision.NONFUNCTION_AUTHORITY, plan["minimal_read_plan"])
        self.assertFalse(plan["side_effects_authorized_by_plan"])


if __name__ == "__main__":
    unittest.main()
