import json
from pathlib import Path
import tempfile
import unittest

from agent_federation.live_adapters import LiveCodexAdapter
from agent_federation.live_execution import execute_bounded_attempt
from agent_federation.live_pilot import DisposableLiveFixture, LivePilotValidator
from agent_federation.live_transport import LiveProcessResult

from .test_live_orchestration import coordinator, envelope


class FakeCodexTransport:
    def __init__(self, result: dict):
        self.result = result

    def run(self, argv, *, cwd, timeout_seconds, input_text=None, env_overrides=None):
        command = tuple(argv)
        if argv[-1] == "--version":
            return LiveProcessResult(command, str(cwd), 0, "codex-cli 0.144.4\n", "", 5, False, False, True)
        if argv[-2:] == ("exec", "--help"):
            return LiveProcessResult(command, str(cwd), 0, "--json --ephemeral --ignore-user-config --ignore-rules --sandbox --cd\n", "", 5, False, False, True)
        event = {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(self.result, sort_keys=True)}}
        return LiveProcessResult(command, str(cwd), 0, json.dumps(event) + "\n", "", 20, False, False, True)


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
                value = {"nonce": "wrong", "line_count": 1, "field_value": "wrong", "checksum_prefix": "00000000"}
                adapter = LiveCodexAdapter(fixture.root, transport=FakeCodexTransport(value), authentication_observed=True)
                bridge = coordinator(root / "state")
                validator = LivePilotValidator(fixture, task_id="IGNITION-20260823-136", dispatch_id="d-orch", attempt_id="a-orch", executor_id="external.codex")
                result = execute_bounded_attempt(adapter=adapter, envelope=envelope(), coordinator=bridge, fixture=fixture, validator=validator, observed_at="2026-08-24T00:00:00+08:00")
                self.assertFalse(result.success)
                self.assertEqual(result.receipt.state, "VALIDATION_FAILED")
                self.assertEqual(result.durable_record["state"], "FAILED_VALIDATION")
                self.assertEqual(len(result.state_history), 6)


if __name__ == "__main__":
    unittest.main()
