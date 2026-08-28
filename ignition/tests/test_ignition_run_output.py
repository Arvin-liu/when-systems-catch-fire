from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
import plan_ignition_operation_run as planner  # noqa: E402
import validate_ignition_run_output as output_contract  # noqa: E402


class IgnitionRunOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = json.loads(output_contract.FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.base = cls.fixtures["base_output"]

    def test_all_twelve_output_fixtures_pass(self) -> None:
        self.assertEqual(len(self.fixtures["cases"]), 12)
        self.assertEqual(output_contract.validate_fixtures(self.fixtures), [])

    def test_contract_has_exact_semantics_and_guards(self) -> None:
        contract = output_contract.load_json(output_contract.CONTRACT_PATH)
        self.assertEqual(output_contract.validate_contract(contract), [])
        self.assertEqual(
            [(row["semantic_id"], row["json_pointer"]) for row in contract["semantic_fields"]],
            list(output_contract.SEMANTIC_FIELDS),
        )
        self.assertEqual(
            [row["guard_id"] for row in contract["boundary_guards"]],
            list(output_contract.BOUNDARY_GUARDS),
        )

    def test_machine_audit_profile_binds_current_canonical_records(self) -> None:
        self.assertEqual(output_contract.validate_output(copy.deepcopy(self.base)), [])
        matches = {row["canonical_id"]: row for row in self.base["existing_canonical_matches"]}
        self.assertEqual(matches["T2"]["record_sha256"], "d191cec113ac32bd44c05b9c415a6a7fa6d76d0a7d3dcb98735b801433832abe")
        self.assertEqual(matches["CLAIM-T2"]["record_sha256"], "a02e5aa6aff35b60f28ca8cdd0beca0f02a0ea887efef594fec17ce8e6a03136")

    def test_human_default_is_concise_but_points_to_audit_recovery(self) -> None:
        rendered = output_contract.render_human(copy.deepcopy(self.base))
        self.assertIn("Audit recovery", rendered)
        self.assertIn("Claim ceiling", rendered)
        self.assertIn("Stop reason", rendered)
        self.assertNotIn("request_envelope_locator", rendered)
        self.assertNotIn("boundary_attestations", rendered)
        self.assertLess(len(rendered), len(json.dumps(self.base, ensure_ascii=False)))

    def test_input_derived_statement_cannot_be_relabelled_candidate(self) -> None:
        candidate = copy.deepcopy(self.base)
        candidate["candidate_deltas"][0]["statement"] = candidate["input_derived_findings"][0]["statement"]
        errors = output_contract.validate_output(candidate)
        self.assertTrue(any("input-explicit content cannot be relabelled" in error for error in errors))

    def test_candidate_remains_unregistered_and_noncanonical(self) -> None:
        row = self.base["candidate_deltas"][0]
        self.assertEqual(row["asset_status"], "CANDIDATE_NOT_CANONICAL")
        self.assertEqual(row["registry_action"], "NONE")
        self.assertEqual(row["epistemic_status"], "NOT_ESTABLISHED")

    def test_repository_match_has_no_external_truth_effect(self) -> None:
        for row in self.base["existing_canonical_matches"]:
            self.assertEqual(row["repository_identity_effect"], "ESTABLISHES_REPOSITORY_IDENTITY_ONLY")
            self.assertEqual(row["external_truth_status"], "NOT_ESTABLISHED_BY_REPOSITORY_MATCH")

    def test_agent_consensus_is_rejected_as_evidence(self) -> None:
        candidate = copy.deepcopy(self.base)
        candidate["evidence_sources"][0]["source_kind"] = "AGENT_CONSENSUS"
        errors = output_contract.validate_output(candidate)
        self.assertTrue(any("Agent consensus" in error for error in errors))

    def test_implementation_completion_needs_separate_epistemic_authority(self) -> None:
        candidate = copy.deepcopy(self.base)
        candidate["result"]["implementation_status"] = "COMPLETE"
        candidate["result"]["epistemic_status"] = "ACCEPTED_BY_SEPARATE_CURRENT_AUTHORITY"
        errors = output_contract.validate_output(candidate)
        self.assertTrue(any("separately identified Current authority" in error for error in errors))

    def test_historical_material_cannot_be_current_match_authority(self) -> None:
        candidate = copy.deepcopy(self.base)
        candidate["existing_canonical_matches"][0]["authority_path"] = "ignition/data/old_tables/historical.jsonl"
        errors = output_contract.validate_output(candidate)
        self.assertTrue(any("authority_path" in error or "historical" in error for error in errors))

    def test_all_lifecycle_plans_load_global_output_contract(self) -> None:
        request = {"request_envelope": {"user_request": "请核查这个断言。"}, "input_objects": []}
        result = planner.plan_run(request, "knowledge.validate_claim", "refs/heads/main@example-current")
        self.assertEqual(result["output_contract_source"], planner.OUTPUT_CONTRACT_PATH)
        self.assertIn(planner.OUTPUT_CONTRACT_PATH, result["minimal_read_plan"])


if __name__ == "__main__":
    unittest.main()
