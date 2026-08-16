#!/usr/bin/env python3
"""Unit and negative-boundary tests for CURRENT_STATE_SYNC_INVARIANT."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import validate_current_state_sync as validator  # noqa: E402
import generate_current_facts as facts_generator  # noqa: E402


class CurrentStateSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = validator.load_json(validator.CONTRACT_PATH)
        self.receipt = validator.load_json(
            IGNITION_ROOT / "data/operations/iterations/123/current-state-sync-receipt.json"
        )

    def test_live_contract_and_presentation_receipt_pass(self) -> None:
        self.assertEqual(validator.run_check(check_fixtures=True), [])

    def test_fixture_manifest_has_positive_and_negative_cases(self) -> None:
        fixture = validator.load_json(validator.FIXTURE_PATH)
        kinds = {row["kind"] for row in fixture["fixtures"]}
        self.assertEqual(kinds, {"positive", "negative"})
        self.assertGreaterEqual(len(fixture["fixtures"]), 6)

    def test_architecture_changed_requires_every_surface_to_change(self) -> None:
        receipt = copy.deepcopy(self.receipt)
        receipt["architecture_identity_impact"] = "ARCHITECTURE_CHANGED"
        errors = validator.validate_receipt(self.contract, receipt)
        self.assertTrue(any("requires CHANGE" in error for error in errors))

    def test_presentation_only_rejects_a_changed_surface(self) -> None:
        receipt = copy.deepcopy(self.receipt)
        receipt["surface_decisions"][0]["decision"] = "CHANGE"
        errors = validator.validate_receipt(self.contract, receipt)
        self.assertTrue(any("PRESENTATION_ONLY receipt cannot mark" in error for error in errors))

    def test_contract_rejects_a_self_referential_sha_field(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["current_architecture_identity"]["current_commit_sha"] = "a" * 40
        errors, _ = validator.validate_contract(contract)
        self.assertTrue(any("self-referential commit SHA" in error for error in errors))

    def test_fixture_manifest_is_json_serializable_and_task_scoped(self) -> None:
        fixture = json.loads(validator.FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(fixture["task_id"], "IGNITION-20260816-123")
        self.assertTrue(all(row["expected_status"] in {"PASS", "FAIL"} for row in fixture["fixtures"]))

    def test_current_facts_two_generations_are_byte_identical(self) -> None:
        first = facts_generator.build_projection(self.contract)
        second = facts_generator.build_projection(self.contract)
        self.assertEqual(facts_generator.render_json(first), facts_generator.render_json(second))
        self.assertEqual(facts_generator.render_markdown(first), facts_generator.render_markdown(second))


if __name__ == "__main__":
    unittest.main()
