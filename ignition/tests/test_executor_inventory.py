from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from tools.validate_executor_inventory import InventoryValidationError, validate_inventory, validate_path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "data/agent-federation/executor-inventory-r1.json"


class ExecutorInventoryTests(unittest.TestCase):
    def test_checked_in_inventory_is_strict_and_safe(self) -> None:
        summary = validate_path(INVENTORY)
        self.assertTrue(summary["safe"])
        self.assertEqual(summary["executor_count"], 3)
        self.assertEqual(summary["available_executors"], ["external.codex", "external.hermes", "external.openclaw"])

    def test_inventory_rejects_live_smoke_or_secret_read(self) -> None:
        data = json.loads(INVENTORY.read_text(encoding="utf-8"))
        changed = copy.deepcopy(data)
        changed["safety_notes"]["secret_content_read"] = True
        with self.assertRaises(InventoryValidationError):
            validate_inventory(changed)

        changed = copy.deepcopy(data)
        changed["executors"][0]["live_smoke"]["status"] = "PASS"
        with self.assertRaises(InventoryValidationError):
            validate_inventory(changed)

    def test_inventory_requires_canonical_baseline(self) -> None:
        data = json.loads(INVENTORY.read_text(encoding="utf-8"))
        data["formal_baseline"]["origin_main_sha"] = "0" * 40
        with self.assertRaises(InventoryValidationError):
            validate_inventory(data)


if __name__ == "__main__":
    unittest.main()
