import tempfile
import unittest

from agent_federation.live_adapters import LiveAdapterError, LiveOpenClawAdapter
from agent_federation.live_transport import LiveProcessResult
from agent_federation.live_bridge import LiveDispatchEnvelope


class FakeOpenClawTransport:
    def __init__(self):
        self.calls = []

    def run(self, argv, *, cwd, timeout_seconds, input_text=None, env_overrides=None):
        self.calls.append(tuple(argv))
        if argv[-1] == "--version":
            return LiveProcessResult(tuple(argv), str(cwd), 0, "OpenClaw 2026.7.1-2 (0790d9f)\n", "", 1, False, False, True)
        return LiveProcessResult(tuple(argv), str(cwd), 0, "--channel --deliver --message --message-file --json --local --timeout --session-key --session-id\n", "", 1, False, False, True)


class LiveOpenClawAdapterTests(unittest.TestCase):
    def test_current_public_surface_is_machine_readable_but_unsafe_for_live_bridge(self):
        transport = FakeOpenClawTransport()
        with tempfile.TemporaryDirectory() as directory:
            lease = LiveOpenClawAdapter(directory, transport=transport).observe_lease(
                lease_id="lease-openclaw", observed_at="now", expires_at="later", ttl_seconds=300,
            )
        self.assertEqual(lease.live_eligibility, "SKIPPED_UNSAFE_WORKSPACE_OR_CHANNEL_BOUNDARY")
        self.assertIn("MISSING_PUBLIC_DISPOSABLE_WORKSPACE_BINDING", lease.eligibility_blockers)
        self.assertEqual(len(transport.calls), 2)
        self.assertTrue(all("agent" not in call or "--help" in call for call in transport.calls))

    def test_no_dispatch_is_constructible_under_an_unsafe_lease(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = LiveOpenClawAdapter(directory, transport=FakeOpenClawTransport())
            with self.assertRaises(LiveAdapterError):
                adapter.dispatch(object())
            with self.assertRaises(LiveAdapterError):
                adapter.build_argv(object())


if __name__ == "__main__":
    unittest.main()
