import json
from pathlib import Path
import tempfile
import unittest

from agent_federation.live_adapters import LiveCodexAdapter
from agent_federation.live_execution import execute_bounded_attempt
from agent_federation.live_pilot import DisposableLiveFixture, LivePilotValidator
from agent_federation.live_transport import LiveProcessResult

try:
    from .test_live_orchestration import coordinator, envelope
except ImportError:  # unittest discover -s tests imports this module top-level
    from test_live_orchestration import coordinator, envelope


class FakeCodexTransport:
    def __init__(self, result: dict):
        self.result = result

    def run(self, argv, *, cwd, timeout_seconds, input_text=None, env_overrides=None):
        command = tuple(argv)
        if argv[-1] == "--version":
            return LiveProcessResult(command, str(cwd), 0, "codex-cli 0.144.4\n", "", 5, False, False, True)
        if argv[-2:] == ("exec", "--help"):
            return LiveProcessResult(command, str(cwd), 0, "--json --ephemeral --ignore-user-config --ignore-rules --skip-git-repo-check --sandbox --cd --output-schema\n", "", 5, False, False, True)
        event = {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(self.result, sort_keys=True)}}
        return LiveProcessResult(command, str(cwd), 0, json.dumps(event) + "\n", "", 20, False, False, True)


class FakeTimeoutTransport(FakeCodexTransport):
    def __init__(self):
        super().__init__({})

    def run(self, argv, *, cwd, timeout_seconds, input_text=None, env_overrides=None):
        if argv[-1] not in {"--version", "--help"} and argv[-2:] != ("exec", "--help"):
            return LiveProcessResult(tuple(argv), str(cwd), -15, "", "", 100, True, False, True)
        return super().run(argv, cwd=cwd, timeout_seconds=timeout_seconds, input_text=input_text, env_overrides=env_overrides)


class FakeFailureTransport(FakeCodexTransport):
    def __init__(self, *, stdout: str, returncode: int = 0, timed_out: bool = False):
        super().__init__({})
        self.stdout = stdout
        self.returncode = returncode
        self.timed_out = timed_out

    def run(self, argv, *, cwd, timeout_seconds, input_text=None, env_overrides=None):
        if argv[-1] == "--version" or argv[-2:] == ("exec", "--help"):
            return super().run(argv, cwd=cwd, timeout_seconds=timeout_seconds, input_text=input_text, env_overrides=env_overrides)
        return LiveProcessResult(tuple(argv), str(cwd), self.returncode, self.stdout, "", 20, self.timed_out, False, True)


class LiveExecutionTests(unittest.TestCase):
    def test_fake_transport_closes_state_receipt_validator_and_durable_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with DisposableLiveFixture.create(root, nonce="0123456789abcdef01234567") as fixture:
                fixture.make_read_only()
                value = {"nonce": fixture.expectation.nonce, "line_count": 3, "field_value": "value-136", "checksum_prefix": fixture.expectation.checksum_prefix}
                adapter = LiveCodexAdapter(fixture.root, transport=FakeCodexTransport(value), authentication_observed=True)
                bridge = coordinator(root / "state")
                validator = LivePilotValidator(fixture, task_id="IGNITION-20260823-136", dispatch_id="d-orch", attempt_id="a-orch", executor_id="external.codex")
                result = execute_bounded_attempt(adapter=adapter, envelope=envelope(), coordinator=bridge, fixture=fixture, validator=validator, observed_at="2026-08-24T00:00:00+08:00")
                self.assertTrue(result.success)
                self.assertEqual(result.receipt.state, "COMPLETED_VALIDATED")
                self.assertEqual(result.validation.status, "PASS")
                self.assertEqual(result.durable_record["state"], "COMPLETED_VALIDATED")
                self.assertEqual(bridge.queue.audit()["state_counts"]["COMPLETED_VALIDATED"], 1)
                self.assertEqual(len(bridge.resources.active(now=100.0)), 0)

    def test_wrong_answer_is_failed_without_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with DisposableLiveFixture.create(root, nonce="0123456789abcdef01234567") as fixture:
                fixture.make_read_only()
                value = {"nonce": "ffffffffffffffffffffffff", "line_count": 1, "field_value": "wrong", "checksum_prefix": "00000000"}
                adapter = LiveCodexAdapter(fixture.root, transport=FakeCodexTransport(value), authentication_observed=True)
                bridge = coordinator(root / "state")
                validator = LivePilotValidator(fixture, task_id="IGNITION-20260823-136", dispatch_id="d-orch", attempt_id="a-orch", executor_id="external.codex")
                result = execute_bounded_attempt(adapter=adapter, envelope=envelope(), coordinator=bridge, fixture=fixture, validator=validator, observed_at="2026-08-24T00:00:00+08:00")
                self.assertFalse(result.success)
                self.assertEqual(result.receipt.state, "VALIDATION_FAILED")
                self.assertEqual(result.durable_record["state"], "FAILED_VALIDATION")
                self.assertEqual(len(result.state_history), 6)

    def test_timeout_is_reconciliation_and_releases_os_resources_without_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with DisposableLiveFixture.create(root, nonce="0123456789abcdef01234567") as fixture:
                fixture.make_read_only()
                adapter = LiveCodexAdapter(fixture.root, transport=FakeTimeoutTransport(), authentication_observed=True)
                bridge = coordinator(root / "state")
                validator = LivePilotValidator(fixture, task_id="IGNITION-20260823-136", dispatch_id="d-orch", attempt_id="a-orch", executor_id="external.codex")
                result = execute_bounded_attempt(adapter=adapter, envelope=envelope(), coordinator=bridge, fixture=fixture, validator=validator, observed_at="2026-08-24T00:00:00+08:00")
                self.assertFalse(result.success)
                self.assertEqual(result.receipt.state, "TIMED_OUT_EFFECT_UNKNOWN")
                self.assertEqual(result.durable_record_state if hasattr(result, "durable_record_state") else result.to_dict()["durable_record_state"], "REQUIRES_RECONCILIATION")
                self.assertEqual(bridge.queue.audit()["state_counts"]["REQUIRES_RECONCILIATION"], 1)
                self.assertEqual(len(bridge.resources.active(now=100.0)), 0)

    def _run_failure(self, transport: FakeFailureTransport):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with DisposableLiveFixture.create(root, nonce="0123456789abcdef01234567") as fixture:
                fixture.make_read_only()
                adapter = LiveCodexAdapter(fixture.root, transport=transport, authentication_observed=True)
                bridge = coordinator(root / "state")
                validator = LivePilotValidator(fixture, task_id="IGNITION-20260823-136", dispatch_id="d-orch", attempt_id="a-orch", executor_id="external.codex")
                return execute_bounded_attempt(adapter=adapter, envelope=envelope(), coordinator=bridge, fixture=fixture, validator=validator, observed_at="2026-08-24T00:00:00+08:00")

    def test_fake_extra_field_is_schema_failure_not_silent_success(self):
        value = {"nonce": "0123456789abcdef01234567", "line_count": 3, "field_value": "value-136", "checksum_prefix": "abcdef01", "extra": "reject"}
        event = {"type": "item.completed", "item": {"text": json.dumps(value)}}
        result = self._run_failure(FakeFailureTransport(stdout=json.dumps(event) + "\n"))
        self.assertEqual(result.receipt.state, "MALFORMED_RESULT")
        self.assertEqual(result.failure_forensics_capsule["diagnostic_class"], "STRUCTURED_RESULT_SCHEMA_FAILURE")

    def test_fake_malformed_json_is_parse_failure(self):
        result = self._run_failure(FakeFailureTransport(stdout="not-json\n"))
        self.assertEqual(result.receipt.state, "MALFORMED_RESULT")
        self.assertEqual(result.failure_forensics_capsule["diagnostic_class"], "STRUCTURED_RESULT_PARSE_FAILURE")

    def test_fake_nonzero_without_result_is_process_failure(self):
        result = self._run_failure(FakeFailureTransport(stdout="", returncode=1))
        self.assertEqual(result.receipt.state, "MALFORMED_RESULT")
        self.assertEqual(result.failure_forensics_capsule["diagnostic_class"], "PROCESS_EXIT_NONZERO_NO_STRUCTURED_RESULT")


if __name__ == "__main__":
    unittest.main()
