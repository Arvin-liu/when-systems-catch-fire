from __future__ import annotations

import sys
import unittest

from process_supervisor import run_fixture


class ProcessSupervisorTests(unittest.TestCase):
    def test_timeout_terminates_parent_and_descendant_process_group(self):
        child = (
            "import subprocess,sys,time; "
            "subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
            "time.sleep(30)"
        )
        result = run_fixture([sys.executable, "-c", child], timeout_seconds=0.4)
        self.assertTrue(result.timed_out)
        self.assertTrue(result.term_sent)
        self.assertTrue(result.cleanup_proven)
        self.assertEqual(result.surviving_process_group_pids, ())
        self.assertEqual(result.surviving_observed_pids, ())
        self.assertGreaterEqual(len(result.observed_descendant_pids), 1)

    def test_timeout_reaps_observed_descendant_that_changes_process_group(self):
        child = (
            "import subprocess,sys,time; "
            "subprocess.Popen([sys.executable,'-c','import os,time; os.setsid(); time.sleep(30)']); "
            "time.sleep(30)"
        )
        result = run_fixture([sys.executable, "-c", child], timeout_seconds=0.4)
        self.assertTrue(result.timed_out)
        self.assertTrue(result.cleanup_proven)
        self.assertGreaterEqual(len(result.observed_descendant_pids), 1)

    def test_short_process_has_no_surviving_group(self):
        result = run_fixture([sys.executable, "-c", "pass"], timeout_seconds=5)
        self.assertFalse(result.timed_out)
        self.assertTrue(result.cleanup_proven)
        self.assertEqual(result.surviving_process_group_pids, ())


if __name__ == "__main__":
    unittest.main()
