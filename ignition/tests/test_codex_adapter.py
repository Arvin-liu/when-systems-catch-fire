from __future__ import annotations

import json
from pathlib import Path
import unittest

from agent_federation.adapters.codex import CodexAdapter
from agent_federation.contracts import FederatedTaskEnvelope, UnsupportedExecutorOperation
from agent_federation.sdk import CapabilityMismatch, MalformedOutput, SafeProcessResult
from tests.test_federation_core import envelope


FIXTURE = Path(__file__).parent / "fixtures" / "federation" / "codex-exec-jsonl-response.jsonl"
CODEX_HELP = """
Usage: codex exec [OPTIONS] [PROMPT]
  --json                         Print events to stdout as JSONL
  --ephemeral                    Run without persisting session files
  --ignore-user-config           Do not load config.toml
  --ignore-rules                 Do not load execpolicy rules
  --sandbox <SANDBOX_MODE>       read-only, workspace-write, danger-full-access
  --cd <DIR>                     working root
  --dangerously-bypass-approvals-and-sandbox  EXTREMELY DANGEROUS
Commands: resume  Resume a previous session by id
"""


def read_envelope() -> FederatedTaskEnvelope:
    value = envelope().to_dict()
    value["required_capabilities"] = ["repo.read"]
    value["approval_policy"] = {
        **value["approval_policy"],
        "capability_ceiling": ["repo.read"],
    }
    return FederatedTaskEnvelope.from_dict(value)


class CapturedCodexRunner:
    def __init__(self, response: str | None = None) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.prompts: list[dict[str, object]] = []
        self.response = response if response is not None else FIXTURE.read_text(encoding="utf-8")

    def __call__(self, argv, timeout_seconds: float) -> SafeProcessResult:
        call = tuple(argv)
        self.calls.append(call)
        if call[-1] == "--version":
            return SafeProcessResult(call, 0, "codex-cli 0.144.4 (fixture)\n", "", 1.0)
        if call[-2:] == ("exec", "--help"):
            return SafeProcessResult(call, 0, CODEX_HELP, "", 1.0)
        self.assert_safe_argv(call)
        self.prompts.append(json.loads(call[-1].split("\n", 1)[1]))
        return SafeProcessResult(call, 0, self.response, "", 2.0)

    @staticmethod
    def assert_safe_argv(argv: tuple[str, ...]) -> None:
        if "--dangerously-bypass-approvals-and-sandbox" in argv or "--dangerously-bypass-hook-trust" in argv:
            raise AssertionError(f"dangerous Codex bypass leaked into adapter argv: {argv}")
        if "--json" not in argv or "--ephemeral" not in argv or "--sandbox" not in argv or "read-only" not in argv:
            raise AssertionError(f"safe Codex JSON argv incomplete: {argv}")


class CodexAdapterTests(unittest.TestCase):
    def make_adapter(self, runner: CapturedCodexRunner | None = None, **kwargs):
        runner = runner or CapturedCodexRunner()
        return CodexAdapter("codex-fixture", runner=runner, **kwargs), runner

    def test_descriptor_uses_jsonl_and_explicit_sandbox_intersection(self) -> None:
        adapter, runner = self.make_adapter()
        descriptor = adapter.describe()
        self.assertEqual(descriptor.version, "codex-cli 0.144.4 (fixture)")
        self.assertEqual(descriptor.transport_kind, ("CLI_JSONL",))
        self.assertEqual(descriptor.capability_tokens, ("repo.read", "structured_progress"))
        self.assertTrue(descriptor.structured_output_support)
        self.assertTrue(descriptor.progress_support)
        self.assertFalse(descriptor.cancel_support)
        self.assertFalse(descriptor.native_resume_support)
        self.assertIn("codex-thread-id", descriptor.external_session_refs)
        self.assertEqual(len(runner.calls), 2)

    def test_dispatch_parses_public_jsonl_and_keeps_thread_as_pointer(self) -> None:
        adapter, runner = self.make_adapter(workspace="/tmp/codex-fixture")
        event = adapter.dispatch(read_envelope())
        invocation = runner.calls[-1]
        self.assertEqual(invocation[:3], ("codex-fixture", "exec", "--json"))
        self.assertIn("--ephemeral", invocation)
        self.assertIn("--ignore-user-config", invocation)
        self.assertIn("--ignore-rules", invocation)
        self.assertIn("--cd", invocation)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", invocation)
        self.assertEqual(runner.prompts[0]["federation_task_id"], "fed-task-001")
        self.assertEqual(event.state, "COMPLETED_UNVALIDATED")
        self.assertEqual(event.progress_fraction, 0.75)
        self.assertEqual(event.refs, ("external-session:fixture-codex-thread-001",))
        self.assertIn("Read-only disposable", event.public_summary)

    def test_receipt_does_not_promote_codex_completion_to_validation(self) -> None:
        adapter, _ = self.make_adapter()
        adapter.dispatch(read_envelope())
        receipt = adapter.receipt_from_response("fed-task-001")
        self.assertEqual(receipt.terminal_state, "REQUIRES_RECONCILIATION")
        self.assertIn("OS_VALIDATION_NOT_PERFORMED", receipt.unresolveds)
        self.assertFalse(receipt.handoff_eligibility.eligible)

    def test_read_only_sandbox_denies_write_and_dangerous_modes(self) -> None:
        adapter, _ = self.make_adapter()
        with self.assertRaises(CapabilityMismatch):
            adapter.dispatch(envelope())
        with self.assertRaises(Exception):
            CodexAdapter("codex-fixture", runner=CapturedCodexRunner(), sandbox_mode="danger-full-access")

    def test_malformed_jsonl_is_typed_failure(self) -> None:
        adapter, _ = self.make_adapter(CapturedCodexRunner("not-json\n"))
        with self.assertRaises(MalformedOutput):
            adapter.dispatch(read_envelope())

    def test_cancel_and_resume_are_not_synthesized(self) -> None:
        adapter, _ = self.make_adapter()
        with self.assertRaises(UnsupportedExecutorOperation):
            adapter.cancel("fed-task-001")
        with self.assertRaises(UnsupportedExecutorOperation):
            adapter.resume(None)


if __name__ == "__main__":
    unittest.main()
