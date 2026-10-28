from pathlib import Path
import tempfile
import unittest

from agent_federation.live_adapters import LiveHermesAdapter
from agent_federation.live_bridge import LiveDispatchEnvelope, LIVE_DISPATCH_SCHEMA
from agent_federation.live_transport import LiveProcessResult
from agent_federation.contracts import FederationContractError


class FakeHermesTransport:
    def __init__(self, *, complete: bool = True, response: str = '{"nonce":"n-001"}'):
        self.calls = []
        self.complete = complete
        self.response = response

    def run(self, argv, *, cwd, timeout_seconds, input_text=None, env_overrides=None):
        self.calls.append((tuple(argv), str(cwd), timeout_seconds))
        if argv[-1] == "--version":
            return LiveProcessResult(tuple(argv), str(cwd), 0, "Hermes Agent v0.20.0 (2026.8.3)\n", "", 1, False, False, True)
        if argv[-1] == "--help":
            text = "-z --safe-mode --ignore-user-config --ignore-rules --no-restore-cwd --resume\n" if self.complete else "-z --safe-mode\n"
            return LiveProcessResult(tuple(argv), str(cwd), 0, text, "", 1, False, False, True)
        return LiveProcessResult(tuple(argv), str(cwd), 0, self.response, "", 5, False, False, True)


def envelope() -> LiveDispatchEnvelope:
    return LiveDispatchEnvelope(
        schema_version=LIVE_DISPATCH_SCHEMA, task_id="IGNITION-20260823-136", dispatch_id="d-hermes", attempt_id="a-hermes",
        executor_id="external.hermes", adapter_id="hermes-live-r2", capability_id="live.readonly.synthetic", capability_lease_ref="lease-hermes",
        workspace_ref="DISPOSABLE_FIXTURE_ROOT", workspace_mode="DISPOSABLE_READ_ONLY", permission_ceiling=("repo.read",),
        side_effect_class="READ_ONLY_SYNTHETIC", network_class="INFERENCE_TRANSPORT_ONLY", intent_capsule_ref=None,
        synthetic_input_ref="fixture://136", synthetic_input_digest="a" * 64, success_criteria=("return nonce",),
        output_contract={"format":"json", "required_fields":["nonce"]}, deadline="2026-08-24T00:00:00Z", timeout_seconds=10,
        retry_policy="NO_BLIND_RETRY", reconciliation_policy="REQUIRE_ON_TIMEOUT_OR_UNKNOWN_EFFECT",
        budget_authority="NO_NEW_BILLING_AUTHORITY", provenance={"controller":"pointfire-os"},
    )


class LiveHermesAdapterTests(unittest.TestCase):
    def test_lease_requires_auth_and_filesystem_guard_without_reading_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = LiveHermesAdapter(directory, transport=FakeHermesTransport(), authentication_observed=True, read_only_guard_observed=True)
            lease = adapter.observe_lease(lease_id="lease-hermes", observed_at="now", expires_at="later", ttl_seconds=300)
        self.assertEqual(lease.live_eligibility, "ELIGIBLE_FOR_LIVE_READONLY")
        self.assertEqual(lease.observed_capabilities, ("repo.read",))
        self.assertFalse(lease.cancel_supported is False)

    def test_argv_is_safe_one_shot_and_never_uses_gateway_or_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = LiveHermesAdapter(directory, transport=FakeHermesTransport(), authentication_observed=True, read_only_guard_observed=True)
            argv = adapter.build_argv(envelope())
            self.assertIn("-z", argv)
            self.assertIn("--safe-mode", argv)
            self.assertIn("--no-restore-cwd", argv)
            self.assertNotIn("--resume", argv)
            self.assertNotIn("--worktree", argv)
            observation = adapter.dispatch(envelope())
        self.assertTrue(observation.parsed)
        self.assertEqual(observation.parsed_events[0]["nonce"], "n-001")

    def test_text_parser_is_strict_and_never_guesses_success(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = LiveHermesAdapter(directory, transport=FakeHermesTransport(response="looks successful"), authentication_observed=True, read_only_guard_observed=True)
            observation = adapter.dispatch(envelope())
        self.assertFalse(observation.parsed)
        self.assertIn("exact JSON contract", observation.parse_error)

    def test_missing_guard_or_public_flags_is_not_eligible(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = LiveHermesAdapter(directory, transport=FakeHermesTransport(complete=False), authentication_observed=True)
            lease = adapter.observe_lease(lease_id="lease-hermes", observed_at="now", expires_at="later", ttl_seconds=300)
        self.assertNotEqual(lease.live_eligibility, "ELIGIBLE_FOR_LIVE_READONLY")
        self.assertTrue(lease.eligibility_blockers)

    def test_widened_envelope_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = LiveHermesAdapter(directory, transport=FakeHermesTransport(), authentication_observed=True, read_only_guard_observed=True)
            data = envelope().to_dict()
            data["permission_ceiling"] = ["repo.read", "structured_progress"]
            with self.assertRaises(FederationContractError):
                adapter.build_argv(LiveDispatchEnvelope.from_dict(data))


if __name__ == "__main__":
    unittest.main()
