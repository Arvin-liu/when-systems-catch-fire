from pathlib import Path
import tempfile
import unittest

from agent_federation.live_adapters import LiveCodexAdapter
from agent_federation.live_bridge import LiveDispatchEnvelope, LIVE_DISPATCH_SCHEMA
from agent_federation.live_transport import LiveProcessResult
from agent_federation.contracts import FederationContractError


class FakeTransport:
    def __init__(self, *, complete: bool = True):
        self.calls = []
        self.complete = complete

    def run(self, argv, *, cwd, timeout_seconds, input_text=None, env_overrides=None):
        self.calls.append((tuple(argv), str(cwd), timeout_seconds))
        if argv[-1] == "--version":
            return LiveProcessResult(tuple(argv), str(cwd), 0, "codex-cli 0.144.4\n", "", 1, False, False, True)
        if argv[-2:] == ("exec", "--help"):
            text = "--json --ephemeral --ignore-user-config --ignore-rules --sandbox --cd --output-schema\n" if self.complete else "--json --sandbox\n"
            return LiveProcessResult(tuple(argv), str(cwd), 0, text, "", 1, False, False, True)
        return LiveProcessResult(
            tuple(argv), str(cwd), 0,
            '{"type":"thread.started","thread_id":"private-thread"}\n{"type":"turn.completed","text":"nonce n-001"}\n',
            "", 5, False, False, True,
        )


def envelope(root: Path) -> LiveDispatchEnvelope:
    return LiveDispatchEnvelope(
        schema_version=LIVE_DISPATCH_SCHEMA, task_id="IGNITION-20260823-136", dispatch_id="d-codex", attempt_id="a-codex",
        executor_id="external.codex", adapter_id="codex-live-r2", capability_id="live.readonly.synthetic", capability_lease_ref="lease-codex",
        workspace_ref="DISPOSABLE_FIXTURE_ROOT", workspace_mode="DISPOSABLE_READ_ONLY", permission_ceiling=("repo.read",),
        side_effect_class="READ_ONLY_SYNTHETIC", network_class="INFERENCE_TRANSPORT_ONLY", intent_capsule_ref=None,
        synthetic_input_ref="fixture://136", synthetic_input_digest="a" * 64, success_criteria=("return nonce",),
        output_contract={"format":"json", "required_fields":["nonce"]}, deadline="2026-08-24T00:00:00Z", timeout_seconds=10,
        retry_policy="NO_BLIND_RETRY", reconciliation_policy="REQUIRE_ON_TIMEOUT_OR_UNKNOWN_EFFECT",
        budget_authority="NO_NEW_BILLING_AUTHORITY", provenance={"controller":"pointfire-os"},
    )


class LiveCodexAdapterTests(unittest.TestCase):
    def test_observed_lease_uses_current_public_flags_and_auth_presence(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = LiveCodexAdapter(directory, transport=FakeTransport(), authentication_observed=True)
            lease = adapter.observe_lease(lease_id="lease-codex", observed_at="now", expires_at="later", ttl_seconds=300)
        self.assertEqual(lease.live_eligibility, "ELIGIBLE_FOR_LIVE_READONLY")
        self.assertIn("repo.read", lease.observed_capabilities)
        self.assertNotIn("repo.write", lease.observed_capabilities)

    def test_argv_binds_ephemeral_read_only_explicit_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = LiveCodexAdapter(directory, transport=FakeTransport(), authentication_observed=True)
            argv = adapter.build_argv(envelope(Path(directory)))
            self.assertIn("--ephemeral", argv)
            self.assertIn("--sandbox", argv)
            self.assertIn("read-only", argv)
            self.assertIn("--cd", argv)
            self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", argv)
            self.assertNotIn("--add-dir", argv)
            observation = adapter.dispatch(envelope(Path(directory)))
        self.assertTrue(observation.parsed)
        self.assertEqual(observation.process.returncode, 0)
        self.assertEqual(observation.session_pointer, "opaque:" + __import__("hashlib").sha256(b"private-thread").hexdigest()[:24])

    def test_missing_safe_flags_is_not_eligible(self):
        with tempfile.TemporaryDirectory() as directory:
            lease = LiveCodexAdapter(directory, transport=FakeTransport(complete=False), authentication_observed=True).observe_lease(
                lease_id="lease-codex", observed_at="now", expires_at="later", ttl_seconds=300,
            )
        self.assertNotEqual(lease.live_eligibility, "ELIGIBLE_FOR_LIVE_READONLY")
        self.assertTrue(any(item.startswith("MISSING_PUBLIC_FLAG") for item in lease.eligibility_blockers))

    def test_widened_envelope_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = LiveCodexAdapter(directory, transport=FakeTransport(), authentication_observed=True)
            data = envelope(Path(directory)).to_dict()
            data["permission_ceiling"] = ["repo.read", "structured_progress"]
            with self.assertRaises(FederationContractError):
                adapter.build_argv(LiveDispatchEnvelope.from_dict(data))


if __name__ == "__main__":
    unittest.main()
