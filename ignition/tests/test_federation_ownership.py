from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from tools.validate_federation_ownership import (
    OwnershipValidationError,
    check_reference_freeze_fixtures,
    validate_contracts,
)


ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict:
    return json.loads((ROOT / "data/agent-federation" / name).read_text(encoding="utf-8"))


class FederationOwnershipTests(unittest.TestCase):
    def test_canonical_contracts_freeze_reference_executor(self) -> None:
        result = validate_contracts()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["reference_executor_components"], 1)

    def test_protected_new_runtime_path_fails_closed_without_exception(self) -> None:
        with self.assertRaises(OwnershipValidationError):
            validate_contracts(changed_paths=["agent_runtime/browser_driver.py"])
        with self.assertRaises(OwnershipValidationError):
            validate_contracts(changed_paths=["agent_runtime/model.py"])
        result = validate_contracts(changed_paths=["agent_federation/adapters/openclaw.py"])
        self.assertEqual(result["protected_path_violations"], 0)

    def test_task_identity_model_is_not_an_external_runtime_layer(self) -> None:
        result = validate_contracts(changed_paths=["data/operations/task-identity-model-r1.json"])
        self.assertEqual(result["protected_path_violations"], 0)

    def test_incomplete_exception_is_rejected(self) -> None:
        ownership = load("os-executor-ownership-r1.json")
        policy = load("build-vs-integrate-policy-r1.json")
        registry = load("executor-component-ownership-r1.json")
        changed = copy.deepcopy(policy)
        changed["exceptions"] = [{"exception_id": "incomplete"}]
        with self.assertRaises(OwnershipValidationError):
            validate_contracts(ownership, changed, registry)

    def test_task149_exception_is_removable_evidence_classification(self) -> None:
        policy = load("build-vs-integrate-policy-r1.json")
        exceptions = policy["exceptions"]
        self.assertEqual(len(exceptions), 2)
        exception = exceptions[0]
        self.assertEqual(exception["exception_id"], "HISTORICAL_OR_EXPERIMENTAL_PROVIDER_EVIDENCE_NO_RUNTIME_AUTHORITY")
        self.assertEqual(exception["decision"], "ALLOW_HISTORICAL_OR_EXPERIMENTAL_PROVIDER_EVIDENCE_NO_RUNTIME_AUTHORITY")
        self.assertIn("no provider runtime", exception["capability_scope"])
        self.assertIn("separate formally reviewed task", exception["sunset_or_review_condition"])
        self.assertIn("generic runtime bypass", exception["sunset_or_review_condition"])
        validate_contracts(changed_paths=["data/operations/iterations/149/provider-adapter-contract-r0.json"])

    def test_task150_exception_is_narrow_evidence_only_and_removable(self) -> None:
        policy = load("build-vs-integrate-policy-r1.json")
        exception = next(item for item in policy["exceptions"] if item["exception_id"] == "TASK150_ARCHIFY_EXPERIMENTAL_EVIDENCE_NO_RUNTIME_AUTHORITY")
        self.assertEqual(exception["decision"], "ALLOW_TASK150_ARCHIFY_EXPERIMENTAL_EVIDENCE_NO_RUNTIME_AUTHORITY")
        self.assertIn("Task150 Step08", exception["capability_scope"])
        self.assertIn("no runtime", exception["capability_scope"])
        self.assertIn("exactly four", exception["threshold_or_boundary"])
        self.assertIn("generic runtime bypass", exception["sunset_or_review_condition"])
        self.assertEqual(len(exception["protected_paths"]), 4)
        validate_contracts(changed_paths=["data/operations/iterations/150/step08-provider-failure-fallback.json"])

    def test_expired_task149_draft_exception_is_rejected(self) -> None:
        ownership = load("os-executor-ownership-r1.json")
        policy = load("build-vs-integrate-policy-r1.json")
        registry = load("executor-component-ownership-r1.json")
        changed = copy.deepcopy(policy)
        changed["exceptions"][0]["exception_id"] = "IGNITION-149-PROVIDER-ADAPTER-SPIKE"
        with self.assertRaises(OwnershipValidationError):
            validate_contracts(ownership, changed, registry)

    def test_reference_freeze_negative_fixtures_are_rejected(self) -> None:
        result = check_reference_freeze_fixtures()
        self.assertEqual(result["status"], "PASS")
        self.assertGreaterEqual(result["negative_fixtures"], 3)


if __name__ == "__main__":
    unittest.main()
