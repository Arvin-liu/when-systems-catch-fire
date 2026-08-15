from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from agent_runtime.memory import OperationalMemoryStore
from agent_runtime.pilots.r2_repository_maintenance import run_pilot, validate_receipts


class R2RepositoryMaintenancePilotTests(unittest.TestCase):
    def test_offline_multi_run_episode_and_adversarial_episode(self) -> None:
        with tempfile.TemporaryDirectory(prefix="r2-repository-maintenance-test-") as temp:
            output = Path(temp)
            receipt = run_pilot(output)
            validation = validate_receipts(output)

            self.assertEqual(validation["status"], "PASS")
            self.assertEqual(receipt["episode"]["terminal"]["state"], "EPISODE_COMPLETED_VALIDATED")
            self.assertEqual(receipt["episode"]["checkpoint_count"], 1)
            self.assertEqual(
                {child["run_id"] for child in receipt["episode"]["children"]},
                {"audit", "repair", "validate"},
            )
            self.assertTrue(all(child["status"] == "COMPLETED_VALIDATED" for child in receipt["episode"]["children"]))
            self.assertEqual(receipt["fresh_clone"]["head_match"], True)
            self.assertFalse(receipt["fresh_clone"]["network_allowed"])
            self.assertFalse(receipt["fresh_clone"]["remote_mutation"])
            self.assertFalse(receipt["fresh_clone"]["git_push_invoked"])
            self.assertTrue(receipt["fresh_clone"]["private_paths_in_receipt"] is False)
            self.assertEqual(receipt["claim_ceiling"], "OFFLINE_REPOSITORY_PILOT_OBSERVED_ONLY_NOT_GENERAL_INTELLIGENCE")

            memory = OperationalMemoryStore(output / "durable-memory.jsonl")
            self.assertEqual(memory.audit()["status"], "PASS")
            self.assertEqual(len(memory.query(memory_type="FAILURE")), 1)
            self.assertEqual(len(memory.query(memory_type="EPISODIC")), 1)
            capsule = json.loads((output / "memory-capsule.json").read_text(encoding="utf-8"))
            self.assertTrue(capsule["bounded"])
            self.assertIn("not knowledge truth", capsule["claim_ceiling"])

            adversarial = json.loads((output / "adversarial-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(adversarial["terminal_state"], "EPISODE_COMPLETED_WITH_INDEPENDENT_FAILURES")
            self.assertEqual(set(adversarial["gateway_denials"]), {"permission_expansion", "forged_completion"})
            self.assertFalse(adversarial["network_allowed"])
            self.assertFalse(adversarial["remote_mutation"])
            self.assertTrue(adversarial["protected_file_preserved"])


if __name__ == "__main__":
    unittest.main()
