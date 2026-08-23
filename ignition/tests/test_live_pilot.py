from pathlib import Path
import tempfile
import unittest

from agent_federation.live_pilot import DisposableLiveFixture, LivePilotValidator, tree_digest


class LivePilotTests(unittest.TestCase):
    def test_fixture_and_validator_are_deterministic_and_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            with DisposableLiveFixture.create(Path(directory), nonce="0123456789abcdef01234567") as fixture:
                fixture.make_read_only()
                self.assertTrue(fixture.read_only_guard_observed())
                validator = LivePilotValidator(fixture, task_id="IGNITION-20260823-136", dispatch_id="dispatch-136", attempt_id="attempt-136", executor_id="external.hermes")
                before = fixture.current_digest()
                report = validator.validate(
                    {"nonce": fixture.expectation.nonce, "line_count": 3, "field_value": "value-136", "checksum_prefix": fixture.expectation.checksum_prefix},
                    before_digest=before, after_digest=fixture.current_digest(),
                )
                self.assertEqual(report.status, "PASS")
                self.assertEqual(report.failure_codes, ())

    def test_workspace_mutation_and_untracked_file_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            with DisposableLiveFixture.create(Path(directory), nonce="0123456789abcdef01234567") as fixture:
                fixture.make_read_only()
                before = fixture.current_digest()
                fixture.root.chmod(0o755)
                (fixture.root / "unexpected.txt").write_text("mutation", encoding="utf-8")
                validator = LivePilotValidator(fixture, task_id="IGNITION-20260823-136", dispatch_id="dispatch-136", attempt_id="attempt-136", executor_id="external.codex")
                report = validator.validate(
                    {"nonce": fixture.expectation.nonce, "line_count": 3, "field_value": "value-136", "checksum_prefix": fixture.expectation.checksum_prefix},
                    before_digest=before, after_digest=fixture.current_digest(), side_effect_observation="FORBIDDEN_EFFECT_OBSERVED",
                )
                self.assertEqual(report.status, "FAIL")
                self.assertIn("FIXTURE_FILES_EXACT", report.failure_codes)
                self.assertIn("SIDE_EFFECT_FREE", report.failure_codes)

    def test_wrong_result_and_wrong_binding_never_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            with DisposableLiveFixture.create(Path(directory), nonce="0123456789abcdef01234567") as fixture:
                fixture.make_read_only()
                digest = fixture.current_digest()
                validator = LivePilotValidator(fixture, task_id="IGNITION-20260823-136", dispatch_id="dispatch-136", attempt_id="attempt-136", executor_id="external.codex")
                report = validator.validate(
                    {"nonce": "wrong", "line_count": 2, "field_value": "wrong", "checksum_prefix": "00000000"},
                    before_digest=digest, after_digest=digest, result_task_id="wrong-task", result_executor_id="external.hermes",
                )
                self.assertEqual(report.status, "FAIL")
                self.assertIn("NONCE_EXACT", report.failure_codes)
                self.assertIn("TASK_BINDING", report.failure_codes)
                self.assertIn("EXECUTOR_BINDING", report.failure_codes)

    def test_tree_digest_excludes_absolute_workspace_path(self):
        with tempfile.TemporaryDirectory() as directory:
            with DisposableLiveFixture.create(Path(directory), nonce="0123456789abcdef01234567") as fixture:
                self.assertEqual(tree_digest(fixture.root), fixture.before_digest)
                self.assertNotIn(str(fixture.root), fixture.before_digest)


if __name__ == "__main__":
    unittest.main()
