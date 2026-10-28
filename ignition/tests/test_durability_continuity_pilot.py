from __future__ import annotations

import json
from pathlib import Path
import unittest

from agent_runtime.pilots.durability_lifecycle_127 import run_pilot
from tools.run_durability_lifecycle_pilot import validate_result


ROOT = Path(__file__).resolve().parents[1]


class DurabilityContinuityPilotTests(unittest.TestCase):
    def test_cross_lifecycle_disposable_episode_reaches_pass(self) -> None:
        data = json.loads((ROOT / "data/operations/durability/continuity-pilot-r1.json").read_text(encoding="utf-8"))
        result = run_pilot(recorded_at=data["recorded_at"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(validate_result(data, result), [])
        self.assertTrue(all(result["checks"].values()))
        self.assertEqual(result["scenario"]["external_invocation"], "NOT_RUN")
        self.assertEqual(result["dispatch"]["state"], "REQUIRES_RECONCILIATION")
        self.assertEqual(result["soft_governance"]["restored_status"], "ADVISORY_ONLY")

    def test_pack_pin_and_namespace_boundaries_survive_recovery(self) -> None:
        result = run_pilot()
        self.assertEqual(result["pack"]["old_run_pin"], "1.0.0")
        self.assertEqual(result["pack"]["new_run_pin"], "1.1.0")
        self.assertEqual(result["pack"]["final_active"], "1.1.0")
        self.assertEqual(result["namespace"]["default_deny"], True)
        self.assertEqual(result["disaster_recovery"]["component_matches"]["pack"], True)
        self.assertEqual(result["disaster_recovery"]["component_matches"]["namespace"], True)


if __name__ == "__main__":
    unittest.main()
