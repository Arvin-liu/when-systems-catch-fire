from __future__ import annotations

import unittest

from tools.run_cross_executor_driver_pilot import build_pilot


class CrossExecutorDriverPilotTests(unittest.TestCase):
    def test_bounded_driver_episode_keeps_acceptance_in_ignition(self) -> None:
        result = build_pilot(recorded_at="2026-08-17T00:00:00Z")
        self.assertEqual(result["driver"]["initial_route"]["selected_executor_id"], "external.hermes")
        self.assertEqual(result["driver"]["fallback_route"]["selected_executor_id"], "reference.executor")
        self.assertEqual(result["episode"]["handoff"]["takeover"]["status"], "ACCEPTED")
        self.assertEqual(result["episode"]["os_acceptance"], "COMPLETED_VALIDATED_AFTER_INDEPENDENT_OS_VALIDATION")
        self.assertEqual(result["adversarial"]["validator_outcome"], "REJECTED_FAILED_VALIDATION")
        self.assertEqual(result["adversarial"]["receipt_ingest"]["status"], "UNVERIFIED")
        self.assertEqual(result["convergence"]["bounded_memory_audit"]["entry_count"], 7)


if __name__ == "__main__":
    unittest.main()
