from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_federation.live_capture import LiveCaptureError, LiveCaptureWriter, validate_capsule


class LiveCaptureTests(unittest.TestCase):
    def make_writer(self, parent: str | Path) -> LiveCaptureWriter:
        return LiveCaptureWriter.create(
            capture_id="capture-test-1",
            task_id="IGNITION-20260825-139",
            dispatch_id="dispatch-test-1",
            attempt_id="attempt-test-1",
            executor_id="external.synthetic",
            adapter_id="synthetic-live-r1",
            parent=parent,
        )

    def test_streaming_capsule_has_digests_counts_sequences_and_redacted_process(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = self.make_writer(directory)
            writer.write_stdout(b"one\n")
            writer.write_stdout(b"two\n")
            writer.write_stderr(b"diagnostic\n")
            self.assertEqual(writer.record_public_event({"type": "progress", "step": 1}), 0)
            self.assertEqual(writer.record_public_event({"type": "completed", "ok": True}), 1)
            result_ref = writer.record_structured_result({"answer": "bounded"})
            capsule = writer.finalize(return_code=0, context_summary="bounded summary")
            self.assertEqual(capsule["stdout"]["byte_count"], 8)
            self.assertEqual(capsule["stderr"]["byte_count"], 11)
            self.assertEqual(capsule["public_events"]["count"], 2)
            self.assertEqual(capsule["public_events"]["sequence_end"], 1)
            self.assertEqual(capsule["structured_result"]["ref"], result_ref)
            self.assertEqual(capsule["process_observation"]["pid_ref"], "REDACTED")
            self.assertNotIn("spool_path", capsule)
            self.assertFalse(writer.spool_path.exists())
            self.assertEqual(validate_capsule(capsule)["capture_completeness"], "COMPLETE")

    def test_large_output_is_counted_without_context_sized_buffer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = self.make_writer(directory)
            payload = b"x" * (1024 * 1024)
            writer.write_stdout(payload)
            capsule = writer.finalize(return_code=0, capture_completeness="COMPLETE")
            self.assertEqual(capsule["stdout"]["byte_count"], len(payload))
            self.assertEqual(capsule["output_truncated"], False)

    def test_private_marker_fails_closed_and_never_reaches_public_capsule(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = self.make_writer(directory)
            with self.assertRaises(LiveCaptureError):
                writer.write_stdout(b"secret=must-not-be-persisted")
            capsule = writer.finalize(return_code=1, capture_completeness="INCOMPLETE", secret_scan_status="FAIL")
            self.assertEqual(capsule["secret_scan_status"], "FAIL")
            self.assertEqual(capsule["capture_completeness"], "INCOMPLETE")
            self.assertFalse(writer.spool_path.exists())

    def test_context_summary_is_pointer_and_digest_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = self.make_writer(directory)
            capsule = writer.finalize(return_code=None, capture_completeness="INCOMPLETE", cleanup=False, context_summary="bounded")
            self.assertNotIn("bounded summary", str(capsule))
            self.assertIsNotNone(capsule["context_projection"]["summary_digest"])
            self.assertEqual(capsule["spool_cleanup_status"], "PENDING")
            writer.finalize(return_code=None, capture_completeness="INCOMPLETE", cleanup=True)

    def test_capsule_rejects_truncated_complete_projection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = self.make_writer(directory)
            capsule = writer.finalize(return_code=0, capture_completeness="INCOMPLETE", output_truncated=True)
            invalid = dict(capsule)
            invalid["capture_completeness"] = "COMPLETE"
            with self.assertRaises(LiveCaptureError):
                validate_capsule(invalid)


if __name__ == "__main__":
    unittest.main()
