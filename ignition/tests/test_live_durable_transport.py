from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from agent_federation.live_capture import LiveCaptureWriter
from agent_federation.live_transport import LiveProcessTransport


PYTHON = sys.executable


class LiveDurableTransportTests(unittest.TestCase):
    def writer(self, parent: str | Path) -> LiveCaptureWriter:
        return LiveCaptureWriter.create(
            capture_id="capture-transport-1",
            task_id="IGNITION-20260825-139",
            dispatch_id="dispatch-transport-1",
            attempt_id="attempt-transport-1",
            executor_id="external.synthetic",
            adapter_id="synthetic-live-r1",
            parent=parent,
        )

    def transport(self) -> LiveProcessTransport:
        return LiveProcessTransport(executable_allowlist=(PYTHON,), output_cap_bytes=128)

    def test_context_sized_output_is_bounded_but_durable_capture_continues(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = self.writer(directory)
            code = (
                "import json, sys; "
                "print(json.dumps({'type':'progress','step':1}), flush=True); "
                "sys.stdout.write('x' * (1024 * 1024)); sys.stdout.flush()"
            )
            result = self.transport().run(
                (PYTHON, "-c", code), cwd=directory, timeout_seconds=3, capture=writer,
            )
            self.assertEqual(result.returncode, 0)
            self.assertFalse(result.output_truncated)
            self.assertTrue(result.context_truncated)
            self.assertEqual(len(result.captured_events), 1)
            self.assertEqual(result.captured_events[0]["step"], 1)
            self.assertEqual(result.capture_capsule["stdout"]["byte_count"], 1024 * 1024 + len(json.dumps({"type": "progress", "step": 1}) .encode("utf-8")) + 1)
            self.assertEqual(result.capture_capsule["capture_completeness"], "COMPLETE")
            self.assertTrue(writer.spool_path.exists())
            writer.cleanup_spool()
            self.assertFalse(writer.spool_path.exists())

    def test_timeout_keeps_capture_receipt_even_when_external_outcome_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            writer = self.writer(directory)
            result = self.transport().run(
                (PYTHON, "-c", "import time; print('started', flush=True); time.sleep(2)"),
                cwd=directory, timeout_seconds=0.05, capture=writer,
            )
            self.assertTrue(result.timed_out)
            self.assertIsNotNone(result.capture_capsule)
            self.assertEqual(result.capture_capsule["process_observation"]["process_group_status"], "CONFIRMED_GONE")
            self.assertEqual(result.capture_capsule["capture_completeness"], "COMPLETE")
            self.assertEqual(result.capture_capsule["spool_cleanup_status"], "PENDING")
            writer.cleanup_spool()


if __name__ == "__main__":
    unittest.main()
