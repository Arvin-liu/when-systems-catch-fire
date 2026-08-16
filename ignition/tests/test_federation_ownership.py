from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from tools.validate_federation_ownership import OwnershipValidationError, validate_contracts


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
        result = validate_contracts(changed_paths=["agent_federation/adapters/openclaw.py"])
        self.assertEqual(result["protected_path_violations"], 0)

    def test_incomplete_exception_is_rejected(self) -> None:
        ownership = load("os-executor-ownership-r1.json")
        policy = load("build-vs-integrate-policy-r1.json")
        registry = load("executor-component-ownership-r1.json")
        changed = copy.deepcopy(policy)
        changed["exceptions"] = [{"exception_id": "incomplete"}]
        with self.assertRaises(OwnershipValidationError):
            validate_contracts(ownership, changed, registry)


if __name__ == "__main__":
    unittest.main()
