import json
from pathlib import Path
import tempfile
import unittest

from agent_federation.live_adapters import LiveAdapterError, LiveCodexAdapter
from agent_federation.live_bridge import LIVE_DISPATCH_SCHEMA, LiveDispatchEnvelope
from agent_federation.live_child_guard import LIVE_CHILD_DEPTH_ENV, LiveChildContext, LiveChildGuardError, build_synthetic_child_prompt
from agent_federation.live_transport import LiveProcessResult


def envelope() -> LiveDispatchEnvelope:
    return LiveDispatchEnvelope(
        schema_version=LIVE_DISPATCH_SCHEMA, task_id="IGNITION-20260824-137", dispatch_id="d-child", attempt_id="a-child",
        executor_id="external.codex", adapter_id="codex-live-r2", capability_id="live.readonly.synthetic", capability_lease_ref="lease-child",
        workspace_ref="DISPOSABLE_FIXTURE_ROOT", workspace_mode="DISPOSABLE_SYNTHETIC_READ_ONLY", permission_ceiling=("repo.read",),
        side_effect_class="READ_ONLY_SYNTHETIC", network_class="INFERENCE_TRANSPORT_ONLY", intent_capsule_ref=None,
        synthetic_input_ref="fixture://IGNITION-20260824-137", synthetic_input_digest="a" * 64,
        success_criteria=("return the exact fixture result",), output_contract={"format": "json", "required_fields": ["nonce"]},
        deadline="2026-08-24T08:00:00Z", timeout_seconds=10, retry_policy="NO_BLIND_RETRY",
        reconciliation_policy="REQUIRE_ON_TIMEOUT_OR_UNKNOWN_EFFECT", budget_authority="NO_NEW_BILLING_AUTHORITY",
        provenance={"controller": "pointfire-os"},
    )


class CaptureTransport:
    def __init__(self) -> None:
        self.calls = []

    def run(self, argv, *, cwd, timeout_seconds, input_text=None, env_overrides=None):
        self.calls.append((tuple(argv), str(cwd), dict(env_overrides or {})))
        if argv[-1] == "--version":
            return LiveProcessResult(tuple(argv), str(cwd), 0, "codex-cli 0.144.4\n", "", 1, False, False, True)
        if argv[-2:] == ("exec", "--help"):
            return LiveProcessResult(tuple(argv), str(cwd), 0, "--json --ephemeral --ignore-user-config --ignore-rules --skip-git-repo-check --sandbox --cd --output-schema\n", "", 1, False, False, True)
        event = {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps({"nonce": "n"})}}
        return LiveProcessResult(tuple(argv), str(cwd), 0, json.dumps(event) + "\n", "", 1, False, False, True)


class LiveChildGuardTests(unittest.TestCase):
    def test_child_context_is_one_level_and_minimizes_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            child = LiveChildContext.from_environment({}).issue_child(directory)
            env = child.child_environment({
                "PATH": "/bin", "HOME": "/Users/private", "CODEX_HOME": "/Users/private/.codex",
                "OPENAI_API_KEY": "secret", "FORMAL_TASK": "1111 task body",
            })
            self.assertEqual(env[LIVE_CHILD_DEPTH_ENV], "1")
            self.assertEqual(env["HOME"], directory)
            self.assertEqual(env["TMPDIR"], directory)
            self.assertNotIn("OPENAI_API_KEY", env)
            self.assertNotIn("FORMAL_TASK", env)
            with self.assertRaises(LiveChildGuardError):
                child.issue_child(directory)

    def test_synthetic_prompt_has_no_parent_context_input(self):
        prompt = build_synthetic_child_prompt(
            synthetic_input_ref="fixture://IGNITION-20260824-137",
            success_criteria=("return the exact fixture result",),
            output_contract={"format": "json", "required_fields": ["nonce"]},
        )
        self.assertIn("IGNITION_LIVE_CHILD_SYNTHETIC_READONLY_TASK", prompt)
        self.assertIn("fixture://IGNITION-20260824-137", prompt)
        self.assertNotIn("1111 task body", prompt)
        self.assertNotIn("parent formal prompt", prompt)

    def test_depth_one_adapter_refuses_recursive_spawn(self):
        with tempfile.TemporaryDirectory() as directory:
            child = LiveChildContext(depth=1, workspace=Path(directory))
            adapter = LiveCodexAdapter(directory, transport=CaptureTransport(), authentication_observed=True, child_context=child)
            with self.assertRaises(LiveAdapterError):
                adapter.build_argv(envelope())

    def test_adapter_dispatch_marks_child_and_does_not_forward_parent_home(self):
        with tempfile.TemporaryDirectory() as directory:
            transport = CaptureTransport()
            adapter = LiveCodexAdapter(directory, transport=transport, authentication_observed=True, child_context=LiveChildContext(depth=0))
            adapter.dispatch(envelope())
        dispatch_call = next(call for call in transport.calls if call[0][-1].startswith("IGNITION_LIVE_CHILD_SYNTHETIC_READONLY_TASK"))
        env = dispatch_call[2]
        self.assertEqual(env[LIVE_CHILD_DEPTH_ENV], "1")
        self.assertEqual(env["HOME"], directory)
        self.assertNotEqual(env["HOME"], "/Users/private")
        self.assertIn("IGNITION_LIVE_CHILD_SYNTHETIC_READONLY_TASK", dispatch_call[0][-1])


if __name__ == "__main__":
    unittest.main()
