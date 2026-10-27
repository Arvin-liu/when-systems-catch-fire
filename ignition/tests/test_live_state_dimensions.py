from __future__ import annotations

import copy
import unittest

from agent_federation.live_state_dimensions import (
    LiveStateDimensionsError,
    derive_live_state_dimensions,
    validate_live_state_dimensions,
)


class LiveStateDimensionsTests(unittest.TestCase):
    def test_dispatch_process_and_completion_are_independent(self) -> None:
        dimensions = derive_live_state_dimensions(
            {
                "live_dispatch_calls": 1,
                "live_dispatch_started": True,
                "live_process_started": True,
                "live_process_return_code": 1,
            },
            reconciliation_status="NOT_REQUIRED",
            validated_completion=False,
            next_action="RUN_DYNAMIC_EXECUTOR_ADMISSION",
        )
        self.assertEqual(dimensions["live_dispatch_observation_status"], "OBSERVED")
        self.assertEqual(dimensions["live_process_observation_status"], "OBSERVED")
        self.assertEqual(dimensions["inference_observation_status"], "NOT_OBSERVED")
        self.assertEqual(dimensions["validated_completion_status"], "NOT_VALIDATED")
        self.assertEqual(dimensions["reconciliation_blocker_status"], "NONE")

    def test_dispatch_does_not_promote_inference(self) -> None:
        dimensions = derive_live_state_dimensions(
            {"live_dispatch_calls": 1, "live_dispatch_started": True, "live_process_started": True},
            reconciliation_status="NOT_REQUIRED",
            validated_completion=False,
            next_action="RUN_DYNAMIC_EXECUTOR_ADMISSION",
        )
        self.assertEqual(dimensions["inference_observation_status"], "NOT_OBSERVED")

    def test_unknown_and_pre_process_are_explicit(self) -> None:
        unknown = derive_live_state_dimensions(
            {"live_dispatch_calls": None, "live_dispatch_started": None, "live_process_started": None},
            reconciliation_status=None,
            validated_completion=None,
            next_action="UNKNOWN",
        )
        self.assertEqual(unknown["live_dispatch_observation_status"], "UNKNOWN")
        self.assertEqual(unknown["inference_observation_status"], "UNKNOWN")
        self.assertEqual(unknown["validated_completion_status"], "UNKNOWN")
        self.assertEqual(unknown["reconciliation_blocker_status"], "UNKNOWN")

        pre_process = derive_live_state_dimensions(
            {"live_dispatch_calls": 0, "live_dispatch_started": False, "live_process_started": False},
            reconciliation_status="CLOSED_NO_LIVE_DISPATCH",
            validated_completion=False,
            next_action="RUN_DYNAMIC_EXECUTOR_ADMISSION",
        )
        self.assertEqual(pre_process["inference_observation_status"], "NOT_APPLICABLE_PRE_PROCESS")

    def test_invalid_completion_and_observation_combinations_fail(self) -> None:
        dimensions = derive_live_state_dimensions(
            {"live_dispatch_calls": 0, "live_dispatch_started": False, "live_process_started": False},
            reconciliation_status="CLOSED_NO_LIVE_DISPATCH",
            validated_completion=False,
            next_action="RUN_DYNAMIC_EXECUTOR_ADMISSION",
        )
        invalid = copy.deepcopy(dimensions)
        invalid["inference_observation_status"] = "OBSERVED"
        with self.assertRaises(LiveStateDimensionsError):
            validate_live_state_dimensions(invalid)


if __name__ == "__main__":
    unittest.main()
