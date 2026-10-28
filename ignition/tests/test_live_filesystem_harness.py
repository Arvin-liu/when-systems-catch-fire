from pathlib import Path
import tempfile
import unittest

from agent_federation.live_filesystem_harness import (
    run_parent_environment_allowlist_probe,
    run_reproduction_matrix,
)


class LiveFilesystemHarnessTests(unittest.TestCase):
    def test_matrix_reproduces_permission_root_cause_and_repair(self):
        observations = run_reproduction_matrix()
        by_id = {item.case_id: item for item in observations}
        self.assertEqual(len(observations), 6)
        self.assertEqual(by_id["readonly_home_and_tmpdir"].failure_stage, "PRE_INFERENCE_STARTUP")
        self.assertFalse(by_id["readonly_home_and_tmpdir"].structured_result)
        self.assertEqual(by_id["isolated_writable_runtime_scratch"].returncode, 0)
        self.assertTrue(by_id["isolated_writable_runtime_scratch"].structured_result)
        self.assertTrue(by_id["isolated_writable_runtime_scratch"].workspace_unchanged)
        self.assertTrue(by_id["isolated_writable_runtime_scratch"].scratch_changed)
        self.assertTrue(all(item.scratch_cleanup for item in observations))
        self.assertEqual(by_id["codex_home_workspace_collision"].failure_stage, "PRE_INFERENCE_STARTUP")
        self.assertEqual(by_id["tmpdir_workspace_collision"].failure_stage, "PRE_INFERENCE_STARTUP")
        self.assertEqual(by_id["runtime_scratch_permission_mismatch"].failure_stage, "PRE_INFERENCE_STARTUP")

    def test_parent_agent_environment_marker_is_not_forwarded(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_parent_environment_allowlist_probe(Path(directory))
        self.assertTrue(result["probe_completed"])
        self.assertFalse(result["parent_marker_present"])


if __name__ == "__main__":
    unittest.main()
