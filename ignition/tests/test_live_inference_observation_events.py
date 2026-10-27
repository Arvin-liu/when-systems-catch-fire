from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_federation.live_inference_observation_events import (
    InferenceObservationEventError,
    LiveInferenceObservationEventLedger,
    validate_inference_observation_event,
)


class LiveInferenceObservationEventTests(unittest.TestCase):
    def _event(self, *, status: str = "NOT_OBSERVED", marker: bool = False) -> dict[str, object]:
        return {
            "task_id": "IGNITION-20260826-140",
            "dispatch_id": "dispatch-140-live-01",
            "attempt_id": "attempt-140-live-01",
            "prior_record_hash": "a" * 64,
            "inference_observation_status": status,
            "marker_observed": marker,
            "marker_source": "PUBLIC_CAPTURE_NO_INFERENCE_MARKER",
            "evidence_scope": "PUBLIC_MACHINE_OBSERVATION_ONLY",
            "claim_ceiling": "No private inference or completion claim is made.",
        }

    def test_append_binds_and_hashes_an_independent_inference_observation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inference.jsonl"
            event = LiveInferenceObservationEventLedger(path).append(
                self._event(), expected_task_id="IGNITION-20260826-140", expected_attempt_id="attempt-140-live-01"
            )
            self.assertEqual(event["sequence"], 0)
            self.assertEqual(event["inference_observation_status"], "NOT_OBSERVED")
            ledger = LiveInferenceObservationEventLedger(path)
            self.assertEqual(ledger.audit()["record_count"], 1)
            self.assertEqual(ledger.records()[0]["previous_event_hash"], "0" * 64)

    def test_dispatch_or_process_does_not_authorize_inference_observed(self) -> None:
        event = self._event(status="OBSERVED", marker=False)
        with self.assertRaises(InferenceObservationEventError):
            validate_inference_observation_event({
                **event,
                "schema_version": "live-inference-observation-event-r1",
                "sequence": 0,
                "event_type": "INFERENCE_OBSERVATION_CORRECTION_RECORDED",
                "previous_event_hash": "0" * 64,
                "event_hash": "b" * 64,
            }, check_hash=False)

    def test_rendered_event_is_machine_readable_and_no_raw_output_field_exists(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inference.jsonl"
            LiveInferenceObservationEventLedger(path).append(self._event())
            value = json.loads(path.read_text(encoding="utf-8"))
        self.assertNotIn("stdout", value)
        self.assertNotIn("stderr", value)
        self.assertNotIn("prompt", value)
        self.assertEqual(validate_inference_observation_event(value)["event_type"], "INFERENCE_OBSERVATION_CORRECTION_RECORDED")


if __name__ == "__main__":
    unittest.main()
