import hashlib
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest

from agent_federation.live_transport import LiveProcessResult, LiveProcessTransport, LiveTransportError, parse_bounded_jsonl


PYTHON = sys.executable


class LiveTransportTests(unittest.TestCase):
    def transport(self, **kwargs):
        return LiveProcessTransport(executable_allowlist=(PYTHON,), env_allowlist=("PATH",), **kwargs)

    def test_literal_argv_explicit_cwd_and_allowlisted_env(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.transport().run(
                (PYTHON, "-c", "import os, pathlib; print(pathlib.Path.cwd()); print('SECRET=' + str(os.getenv('LIVE_TEST_SECRET'))); print('{\\\"type\\\":\\\"done\\\"}')"),
                cwd=directory, timeout_seconds=2,
            )
        self.assertEqual(result.returncode, 0)
        self.assertIn(str(Path(directory)), result.stdout)
        self.assertIn("SECRET=None", result.stdout)
        self.assertFalse(result.output_truncated)

    def test_shell_syntax_and_env_widening_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(LiveTransportError):
                self.transport().run((PYTHON, "-c", "print(1)", ";"), cwd=directory, timeout_seconds=2)
            with self.assertRaises(LiveTransportError):
                self.transport().run((PYTHON, "-c", "print(1)"), cwd=directory, timeout_seconds=2, env_overrides={"LIVE_TEST_SECRET": "x"})

    def test_timeout_kills_process_group_and_bounds_output(self):
        with tempfile.TemporaryDirectory() as directory:
            timeout = self.transport().run((PYTHON, "-c", "import time; time.sleep(2)"), cwd=directory, timeout_seconds=0.05)
            huge = self.transport(output_cap_bytes=128).run((PYTHON, "-c", "print('x' * 10000)"), cwd=directory, timeout_seconds=2)
        self.assertTrue(timeout.timed_out)
        self.assertTrue(timeout.process_group_cleaned)
        self.assertTrue(huge.output_truncated)
        self.assertTrue(huge.process_group_cleaned)

    def test_slow_start_valid_records_monotonic_elapsed_and_first_public_event(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.transport().run(
                (PYTHON, "-c", "import time; time.sleep(0.08); print('ready', flush=True)"),
                cwd=directory, timeout_seconds=2,
            )
        self.assertFalse(result.timed_out)
        self.assertEqual(result.wall_clock_order, "ORDERED")
        self.assertIsNotNone(result.first_public_event_latency_ms)
        self.assertGreaterEqual(result.first_public_event_latency_ms, 40)
        self.assertGreaterEqual(result.monotonic_elapsed_ms, result.first_public_event_latency_ms)
        self.assertEqual(result.stdout_bytes, len("ready\n"))
        self.assertEqual(result.stdout_digest, hashlib.sha256(b"ready\n").hexdigest())
        self.assertEqual(result.process_group_status, "CONFIRMED_GONE")

    def test_hard_timeout_records_requested_termination_and_sigterm(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.transport().run(
                (PYTHON, "-c", "import time; time.sleep(2)"), cwd=directory, timeout_seconds=0.05,
            )
        self.assertTrue(result.timed_out)
        self.assertTrue(result.timeout_requested)
        self.assertTrue(result.termination_requested)
        self.assertIn("SIGTERM", result.signals_sent)
        self.assertGreaterEqual(result.monotonic_elapsed_ms, 40)
        self.assertEqual(result.process_group_status, "CONFIRMED_GONE")

    def test_sigterm_to_sigkill_escalation_is_observable(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.transport().run(
                (PYTHON, "-c", "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(2)"),
                cwd=directory, timeout_seconds=0.05,
            )
        self.assertTrue(result.timed_out)
        self.assertEqual(result.signals_sent, ("SIGTERM", "SIGKILL"))
        self.assertEqual(result.process_group_status, "CONFIRMED_GONE")

    def test_child_left_behind_is_fail_closed_when_leader_exits_outside_group(self):
        child_pid = None
        try:
            with tempfile.TemporaryDirectory() as directory:
                code = (
                    "import subprocess, sys, time, os; "
                    "child=subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(2)'], start_new_session=True); "
                    "print(child.pid, flush=True); time.sleep(0.01)"
                )
                result = self.transport().run((PYTHON, "-c", code), cwd=directory, timeout_seconds=0.05)
                child_pid = int(result.stdout.strip().splitlines()[0])
            self.assertTrue(result.timed_out)
            self.assertEqual(result.process_group_status, "CHILD_LEFT_BEHIND")
            self.assertFalse(result.process_group_cleaned)
        finally:
            if child_pid is not None:
                try:
                    os.kill(child_pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass

    def test_timestamp_drift_does_not_change_monotonic_evidence(self):
        drifted = LiveProcessResult(
            (PYTHON,), "/tmp/disposable", 0, "", "", 1234.0, False, False, True,
            started_at="2026-08-24T00:00:02+00:00", ended_at="2026-08-24T00:00:01+00:00",
            timeout_seconds=10.0, monotonic_elapsed_ms=1234.0, wall_clock_order="DRIFTED",
        )
        self.assertEqual(drifted.wall_clock_order, "DRIFTED")
        self.assertEqual(drifted.monotonic_elapsed_ms, 1234.0)

    def test_process_death_and_malformed_utf8_are_observable(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.transport().run((PYTHON, "-c", "import os, sys; os.write(1, b'\\xff'); sys.exit(7)"), cwd=directory, timeout_seconds=2)
        self.assertEqual(result.returncode, 7)
        self.assertIn("�", result.stdout)

    def test_jsonl_parser_rejects_partial_or_overlarge_public_events(self):
        self.assertEqual(parse_bounded_jsonl('{"type":"a"}\n{"type":"b"}')[1]["type"], "b")
        with self.assertRaises(LiveTransportError):
            parse_bounded_jsonl('{"type":"a"}\nnot-json')
        with self.assertRaises(LiveTransportError):
            parse_bounded_jsonl('{"x":"' + ('a' * 100) + '"}', max_line_bytes=20)


if __name__ == "__main__":
    unittest.main()
