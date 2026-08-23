import os
from pathlib import Path
import sys
import tempfile
import unittest

from agent_federation.live_transport import LiveProcessTransport, LiveTransportError, parse_bounded_jsonl


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
