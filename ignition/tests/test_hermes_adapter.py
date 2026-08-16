from __future__ import annotations

from pathlib import Path
import unittest

from agent_federation.adapters.hermes import HermesAdapter
from agent_federation.contracts import FederatedTaskEnvelope, UnsupportedExecutorOperation
from agent_federation.sdk import CapabilityMismatch, MalformedOutput, SafeProcessResult
from tests.test_federation_core import envelope


FIXTURE = Path(__file__).parent / "fixtures" / "federation" / "hermes-oneshot-final-response.txt"
HERMES_HELP = """
usage: hermes [-z PROMPT] [--safe-mode] [--ignore-user-config] [--ignore-rules]
              [--resume SESSION] [--no-restore-cwd]
  -z PROMPT, --oneshot PROMPT  print ONLY the final response text
  --safe-mode                  disable customizations, memory, plugins and MCP
  --ignore-user-config         ignore user config
  --ignore-rules               skip memory and rules
  --resume SESSION              resume by session pointer
  --no-restore-cwd              keep current working directory
"""


def read_envelope() -> FederatedTaskEnvelope:
    value = envelope().to_dict()
    value["required_capabilities"] = ["repo.read"]
    value["approval_policy"] = {
        **value["approval_policy"],
        "capability_ceiling": ["repo.read"],
    }
    return FederatedTaskEnvelope.from_dict(value)


class CapturedHermesRunner:
    def __init__(self, response: str | None = None) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.response = response if response is not None else FIXTURE.read_text(encoding="utf-8")

    def __call__(self, argv, timeout_seconds: float) -> SafeProcessResult:
        call = tuple(argv)
        self.calls.append(call)
        if call[-1] == "--version":
            return SafeProcessResult(call, 0, "Hermes Agent v0.20.0 (fixture)\n", "", 1.0)
        if call[-1] == "--help":
            return SafeProcessResult(call, 0, HERMES_HELP, "", 1.0)
        self.assert_safe_argv(call)
        return SafeProcessResult(call, 0, self.response, "", 2.0)

    @staticmethod
    def assert_safe_argv(argv: tuple[str, ...]) -> None:
        if "--yolo" in argv or "--accept-hooks" in argv or "--gateway" in argv or "--send" in argv:
            raise AssertionError(f"unsafe Hermes option leaked into adapter argv: {argv}")
        for flag in ("--safe-mode", "--ignore-user-config", "--ignore-rules", "-z"):
            if flag not in argv:
                raise AssertionError(f"required Hermes safety flag missing: {flag}")


class HermesAdapterTests(unittest.TestCase):
    def make_adapter(self, runner: CapturedHermesRunner | None = None, **kwargs):
        runner = runner or CapturedHermesRunner()
        return HermesAdapter("hermes-fixture", runner=runner, **kwargs), runner

    def test_descriptor_marks_text_bridge_degraded_and_read_only(self) -> None:
        adapter, runner = self.make_adapter()
        descriptor = adapter.describe()
        self.assertEqual(descriptor.version, "Hermes Agent v0.20.0 (fixture)")
        self.assertEqual(descriptor.transport_kind, ("CLI_TEXT_ONESHOT",))
        self.assertEqual(descriptor.capability_tokens, ("repo.read",))
        self.assertFalse(descriptor.structured_output_support)
        self.assertFalse(descriptor.progress_support)
        self.assertFalse(descriptor.cancel_support)
        self.assertTrue(any("DEGRADED_TEXT_BRIDGE" in item for item in descriptor.limitations))
        self.assertEqual(len(runner.calls), 2)

    def test_dispatch_uses_literal_read_only_oneshot_argv(self) -> None:
        adapter, runner = self.make_adapter()
        event = adapter.dispatch(read_envelope())
        invocation = runner.calls[-1]
        self.assertEqual(invocation[:4], ("hermes-fixture", "--safe-mode", "--ignore-user-config", "--ignore-rules"))
        self.assertIn("-z", invocation)
        self.assertNotIn("--yolo", invocation)
        self.assertNotIn("--accept-hooks", invocation)
        self.assertNotIn("--gateway", invocation)
        self.assertEqual(event.state, "COMPLETED_UNVALIDATED")
        self.assertIn("Read-only disposable fixture", event.public_summary)

    def test_session_is_pointer_only_and_receipt_requires_reconciliation(self) -> None:
        adapter, _ = self.make_adapter(resume_session="fixture-hermes-session-001")
        event = adapter.dispatch(read_envelope())
        self.assertEqual(event.refs, ("external-session:fixture-hermes-session-001",))
        self.assertEqual(adapter.receipt_from_response("fed-task-001").terminal_state, "REQUIRES_RECONCILIATION")
        self.assertIn("OS_VALIDATION_NOT_PERFORMED", adapter.receipt_from_response("fed-task-001").unresolveds)

    def test_non_read_capability_or_effect_is_denied(self) -> None:
        adapter, _ = self.make_adapter()
        unsafe = FederatedTaskEnvelope.from_dict({
            **envelope().to_dict(),
            "required_capabilities": ["repo.write"],
            "allowed_effects": ["write a fixture"],
        })
        with self.assertRaises(CapabilityMismatch):
            adapter.dispatch(unsafe)

    def test_empty_text_is_malformed_output(self) -> None:
        adapter, _ = self.make_adapter(CapturedHermesRunner("   "))
        with self.assertRaises(MalformedOutput):
            adapter.dispatch(read_envelope())

    def test_cancel_and_synthetic_resume_are_unsupported(self) -> None:
        adapter, _ = self.make_adapter()
        with self.assertRaises(UnsupportedExecutorOperation):
            adapter.cancel("fed-task-001")
        with self.assertRaises(UnsupportedExecutorOperation):
            adapter.resume(None)


if __name__ == "__main__":
    unittest.main()
