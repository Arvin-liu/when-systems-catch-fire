from __future__ import annotations

import json
from pathlib import Path
import unittest

from agent_federation.adapters.openclaw import OpenClawAdapter
from agent_federation.contracts import UnsupportedExecutorOperation
from agent_federation.sdk import SafeProcessResult
from tests.test_federation_core import envelope


FIXTURE = Path(__file__).parent / "fixtures" / "federation" / "openclaw-agent-json-response.json"
OPENCLAW_HELP = """
Usage: openclaw agent [options]
  --json                 emit a JSON result
  --message-file <path>  read the task message from a UTF-8 file
  --agent <id>           select an agent
  --session-key <key>    use a stable session key
  --session-id <id>      use an existing session
  --timeout <seconds>    bound agent execution
"""


class CapturedRunner:
    def __init__(self, response: str | None = None, *, version: str = "OpenClaw 2026.7.1-2 (fixture)") -> None:
        self.calls: list[tuple[str, ...]] = []
        self.envelopes: list[dict[str, object]] = []
        self.response = response if response is not None else FIXTURE.read_text(encoding="utf-8")
        self.version = version

    def __call__(self, argv, timeout_seconds: float) -> SafeProcessResult:
        call = tuple(argv)
        self.calls.append(call)
        if call[-1] == "--version":
            return SafeProcessResult(call, 0, self.version + "\n", "", 1.0)
        if call[-2:] == ("agent", "--help"):
            return SafeProcessResult(call, 0, OPENCLAW_HELP, "", 1.0)
        message_path = Path(call[call.index("--message-file") + 1])
        self.envelopes.append(json.loads(message_path.read_text(encoding="utf-8")))
        self.assert_safe_argv(call)
        return SafeProcessResult(call, 0, self.response, "", 2.0)

    @staticmethod
    def assert_safe_argv(argv: tuple[str, ...]) -> None:
        if "--deliver" in argv or "--channel" in argv or "--gateway" in argv:
            raise AssertionError(f"channel/gateway flag leaked into adapter argv: {argv}")


class OpenClawAdapterTests(unittest.TestCase):
    def make_adapter(self, runner: CapturedRunner | None = None, **kwargs):
        runner = runner or CapturedRunner()
        return OpenClawAdapter("openclaw-fixture", runner=runner, **kwargs), runner

    def test_descriptor_is_built_from_observed_version_and_help(self) -> None:
        adapter, runner = self.make_adapter()
        descriptor = adapter.describe()
        self.assertEqual(descriptor.version, runner.version)
        self.assertEqual(descriptor.family, "OpenClaw")
        self.assertEqual(descriptor.capability_tokens, ("long_task",))
        self.assertTrue(descriptor.structured_output_support)
        self.assertFalse(descriptor.progress_support)
        self.assertFalse(descriptor.cancel_support)
        self.assertFalse(descriptor.native_resume_support)
        self.assertIn("openclaw-session-key", descriptor.external_session_refs)
        self.assertEqual(len(runner.calls), 2)

    def test_dispatch_uses_disposable_envelope_file_and_public_json(self) -> None:
        adapter, runner = self.make_adapter(agent_id="fixture-agent", session_key="fixture-session")
        event = adapter.dispatch(envelope())
        invocation = runner.calls[-1]
        self.assertEqual(invocation[:4], ("openclaw-fixture", "agent", "--json", "--agent"))
        self.assertIn("--message-file", invocation)
        self.assertIn("--timeout", invocation)
        self.assertNotIn("--deliver", invocation)
        self.assertEqual(runner.envelopes[0]["federation_task_id"], "fed-task-001")
        self.assertEqual(event.state, "COMPLETED_UNVALIDATED")
        self.assertIn("fixture response", event.public_summary)
        self.assertIn("external-session:fixture-openclaw-session-001", event.refs)
        self.assertEqual(adapter.status("fed-task-001"), event)

    def test_response_redaction_and_receipt_keep_validation_at_os_boundary(self) -> None:
        response = json.dumps({
            "status": "completed",
            "summary": "safe result",
            "prompt": "must not be surfaced",
            "api_key": "fixture-not-a-credential",
            "result": {"reasoning": "hidden", "observed": "yes"},
        })
        adapter, _ = self.make_adapter(CapturedRunner(response))
        event = adapter.dispatch(envelope())
        self.assertNotIn("must not", event.public_summary)
        self.assertNotIn("fixture-not-a-credential", event.public_summary)
        receipt = adapter.receipt_from_response("fed-task-001")
        self.assertEqual(receipt.terminal_state, "REQUIRES_RECONCILIATION")
        self.assertIn("OS_VALIDATION_NOT_PERFORMED", receipt.unresolveds)
        self.assertFalse(receipt.handoff_eligibility.eligible)

    def test_cancel_and_resume_are_typed_unsupported_operations(self) -> None:
        adapter, _ = self.make_adapter()
        with self.assertRaises(UnsupportedExecutorOperation):
            adapter.cancel("fed-task-001")
        with self.assertRaises(UnsupportedExecutorOperation):
            adapter.resume(None)

    def test_malformed_json_is_not_silently_promoted(self) -> None:
        adapter, _ = self.make_adapter(CapturedRunner("not-json"))
        with self.assertRaises(Exception) as raised:
            adapter.dispatch(envelope())
        self.assertIn("JSON", str(raised.exception))

    def test_missing_public_json_surface_is_degraded_and_denied(self) -> None:
        runner = CapturedRunner()

        def text_only(argv, timeout_seconds):
            call = tuple(argv)
            runner.calls.append(call)
            if call[-1] == "--version":
                return SafeProcessResult(call, 0, "OpenClaw fixture\n", "", 1.0)
            return SafeProcessResult(call, 0, "Usage: openclaw agent\n--message <text>\n", "", 1.0)

        adapter = OpenClawAdapter("openclaw-fixture", runner=text_only)
        descriptor = adapter.describe()
        self.assertFalse(descriptor.structured_output_support)
        with self.assertRaises(UnsupportedExecutorOperation):
            adapter.dispatch(envelope())


if __name__ == "__main__":
    unittest.main()
