from pathlib import Path
import tempfile
import unittest

from agent_federation.live_preflight import run_live_preflight
from agent_federation.live_transport import LiveProcessResult


class FakeProbeTransport:
    def __init__(self, executor: str):
        self.executor = executor

    def run(self, argv, *, cwd, timeout_seconds, input_text=None, env_overrides=None):
        command = tuple(argv)
        if self.executor == "codex":
            if argv[-1] == "--version":
                return LiveProcessResult(command, str(cwd), 0, "codex-cli 0.144.4\n", "", 1, False, False, True)
            if argv[-2:] == ("exec", "--help"):
                return LiveProcessResult(command, str(cwd), 0, "--json --ephemeral --ignore-user-config --ignore-rules --sandbox --cd\n", "", 1, False, False, True)
        if self.executor == "hermes":
            if argv[-1] == "--version":
                return LiveProcessResult(command, str(cwd), 0, "Hermes Agent v0.20.0\n", "", 1, False, False, True)
            if argv[-1] == "--help":
                return LiveProcessResult(command, str(cwd), 0, "-z --safe-mode --ignore-user-config --ignore-rules --no-restore-cwd\n", "", 1, False, False, True)
        if self.executor == "openclaw":
            if argv[-1] == "--version":
                return LiveProcessResult(command, str(cwd), 0, "OpenClaw 2026.7.1-2\n", "", 1, False, False, True)
            return LiveProcessResult(command, str(cwd), 0, "--channel --deliver --message --json --local\n", "", 1, False, False, True)
        raise AssertionError(command)


class LivePreflightTests(unittest.TestCase):
    def test_preflight_is_no_inference_and_selects_only_safe_executor(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace_path = directory
            report = run_live_preflight(
                directory, observed_at="2026-08-24T00:00:00Z", expires_at="2026-08-24T00:05:00Z", ttl_seconds=300,
                authentication_observed={"external.codex": True, "external.hermes": True}, read_only_guard_observed=True,
                transports={"external.codex": FakeProbeTransport("codex"), "external.hermes": FakeProbeTransport("hermes"), "external.openclaw": FakeProbeTransport("openclaw")},
            )
        self.assertEqual(report.selected_executor_id, "external.hermes")
        by_id = {entry.executor_id: entry for entry in report.entries}
        self.assertEqual(by_id["external.codex"].eligibility, "ELIGIBLE_FOR_LIVE_READONLY")
        self.assertEqual(by_id["external.hermes"].eligibility, "ELIGIBLE_FOR_LIVE_READONLY")
        self.assertEqual(by_id["external.openclaw"].eligibility, "SKIPPED_UNSAFE_WORKSPACE_OR_CHANNEL_BOUNDARY")
        self.assertIn("<SYNTHETIC_PROMPT>", by_id["external.hermes"].argv_shape)
        self.assertNotIn(workspace_path, " ".join(by_id["external.hermes"].argv_shape))
        self.assertEqual(by_id["external.hermes"].estimated_initial_invocations, 1)

    def test_auth_or_filesystem_guard_uncertainty_never_becomes_eligible(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run_live_preflight(
                directory, observed_at="2026-08-24T00:00:00Z", expires_at="2026-08-24T00:05:00Z", ttl_seconds=300,
                authentication_observed={"external.codex": False, "external.hermes": True}, read_only_guard_observed=False,
                transports={"external.codex": FakeProbeTransport("codex"), "external.hermes": FakeProbeTransport("hermes"), "external.openclaw": FakeProbeTransport("openclaw")},
            )
        by_id = {entry.executor_id: entry for entry in report.entries}
        self.assertNotEqual(by_id["external.codex"].eligibility, "ELIGIBLE_FOR_LIVE_READONLY")
        self.assertNotEqual(by_id["external.hermes"].eligibility, "ELIGIBLE_FOR_LIVE_READONLY")
        self.assertEqual(report.selected_executor_id, None)


if __name__ == "__main__":
    unittest.main()
