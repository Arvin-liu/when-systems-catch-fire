import json
from pathlib import Path
import stat
import tempfile
import unittest

from agent_federation.live_admission import LiveCapabilityAdmission
from agent_federation.live_adapters import LiveCodexAdapter
from agent_federation.live_bridge import LiveCapabilityLease
from agent_federation.live_task137 import (
    TASK137_ID,
    build_task137_coordinator,
    build_task137_envelope,
    build_task137_steering,
    execute_task137_attempt,
)
from agent_federation.live_pilot import DisposableLiveCompletionFixture
from agent_federation.live_transport import LiveProcessResult


OBSERVED_AT = "2026-08-24T00:00:00+00:00"


class FakeCodexTransport:
    def __init__(self, result: dict):
        self.result = result
        self.calls = []

    def run(self, argv, *, cwd, timeout_seconds, input_text=None, env_overrides=None):
        command = tuple(argv)
        self.calls.append(command)
        if argv[-1] == "--version":
            return LiveProcessResult(command, str(cwd), 0, "codex-cli 0.144.4\n", "", 5, False, False, True)
        if argv[-2:] == ("exec", "--help"):
            return LiveProcessResult(command, str(cwd), 0, "--json --ephemeral --ignore-user-config --ignore-rules --skip-git-repo-check --sandbox --cd --output-schema\n", "", 5, False, False, True)
        event = {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(self.result, sort_keys=True)}}
        return LiveProcessResult(command, str(cwd), 0, json.dumps(event) + "\n", "", 20, False, False, True)


def _lease(adapter: LiveCodexAdapter) -> LiveCapabilityLease:
    return adapter.observe_lease(
        lease_id="live-codex-137-attempt-lease",
        observed_at=OBSERVED_AT,
        expires_at="2026-08-24T00:15:00+00:00",
        ttl_seconds=900,
    )


class LiveTask137Tests(unittest.TestCase):
    def test_dry_run_contract_builds_without_dispatching_process(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture_root = root / "fixture"
            fixture_root.mkdir()
            schema = root / "schema.json"
            schema.write_text('{"type":"object","additionalProperties":false}', encoding="utf-8")
            schema.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            fixture = DisposableLiveCompletionFixture.create(fixture_root, nonce="0123456789abcdef01234567")
            try:
                fixture.make_read_only()
                adapter = LiveCodexAdapter(fixture.root, transport=FakeCodexTransport({}), authentication_observed=True)
                lease = _lease(adapter)
                envelope = build_task137_envelope(schema_path=schema, observed_at=OBSERVED_AT)
                steering = build_task137_steering(OBSERVED_AT)
                admission = LiveCapabilityAdmission().admit(
                    envelope,
                    lease,
                    os_granted=lease.observed_capabilities,
                    executor_declared=lease.observed_capabilities,
                    now_observed=OBSERVED_AT,
                    current_binary_digest=lease.binary_digest,
                    current_interface_digest=lease.interface_digest,
                )
                self.assertEqual(admission.status, "ADMITTED")
                bridge = build_task137_coordinator(root / "state", envelope=envelope, steering=steering, admission=admission, now_epoch=0.0)
                argv = adapter.build_argv(envelope)
                self.assertIn("--output-schema", argv)
                self.assertTrue(all(value == 0 for value in bridge.queue.audit()["state_counts"].values()))
                self.assertEqual(len(adapter.transport.calls), 2)
                self.assertTrue(all(call[-1] in {"--version", "--help"} or call[-2:] == ("exec", "--help") for call in adapter.transport.calls))
            finally:
                fixture.cleanup()

    def test_one_fake_task137_attempt_requires_unvalidated_then_independent_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture_root = root / "fixture"
            fixture_root.mkdir()
            schema = root / "schema.json"
            schema.write_text('{"type":"object","additionalProperties":false}', encoding="utf-8")
            schema.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            with DisposableLiveCompletionFixture.create(fixture_root, nonce="0123456789abcdef01234567") as fixture:
                fixture.make_read_only()
                result = {
                    "nonce": fixture.expectation.nonce,
                    "selected_ids": list(fixture.expectation.selected_ids),
                    "count": fixture.expectation.count,
                    "workspace_digest_claim": fixture.before_digest,
                }
                transport = FakeCodexTransport(result)
                adapter = LiveCodexAdapter(fixture.root, transport=transport, authentication_observed=True)
                lease = _lease(adapter)
                envelope = build_task137_envelope(schema_path=schema, observed_at=OBSERVED_AT)
                steering = build_task137_steering(OBSERVED_AT)
                admission = LiveCapabilityAdmission().admit(
                    envelope,
                    lease,
                    os_granted=lease.observed_capabilities,
                    executor_declared=lease.observed_capabilities,
                    now_observed=OBSERVED_AT,
                    current_binary_digest=lease.binary_digest,
                    current_interface_digest=lease.interface_digest,
                )
                bridge = build_task137_coordinator(root / "state", envelope=envelope, steering=steering, admission=admission, now_epoch=0.0)
                attempt = execute_task137_attempt(
                    adapter=adapter,
                    envelope=envelope,
                    coordinator=bridge,
                    fixture=fixture,
                    lease=lease,
                    observed_at=OBSERVED_AT,
                )
                self.assertTrue(attempt.success)
                self.assertEqual(attempt.executor_receipt.state, "COMPLETED_VALIDATED")
                self.assertEqual(attempt.unvalidated_receipt.state, "RETURNED_UNVALIDATED")
                self.assertEqual(attempt.validation_receipt.status, "PASS")
                self.assertEqual(attempt.durable_record["state"], "COMPLETED_VALIDATED")
                self.assertEqual([item["to_state"] for item in attempt.state_history][-2:], ["VALIDATING", "COMPLETED_VALIDATED"])
                self.assertEqual(bridge.queue.audit()["state_counts"]["COMPLETED_VALIDATED"], 1)
                self.assertEqual(len(transport.calls), 3)
                self.assertEqual(TASK137_ID, attempt.executor_receipt.task_id)


if __name__ == "__main__":
    unittest.main()
